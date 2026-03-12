import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

from playwright.async_api import Page, async_playwright

from .config import Settings
from .status import (
    ActivityStatus,
    RegistrationStatus,
    get_status_from_image_src,
    iterate_pagination,
)

logger = logging.getLogger(__name__)


@dataclass
class ActivityInfo:
    name: str = ""
    age_min: int = 0
    age_max: int = 150
    registration_start: str = ""
    registration_end: str = ""
    status: ActivityStatus = ActivityStatus.AVAILABLE
    warnings: list[str] = field(default_factory=list)


@dataclass
class Selectors:
    keyword_search: str
    search_option_or: str
    available_only_radio: str
    search_button: str
    cart_button: str
    dossier_input_template: str
    nip_input_template: str
    unregister_button_template: str
    validate_button: str


DEFAULT_SELECTORS = Selectors(
    keyword_search="#ctlBlocRecherche_ctlMotsCles_ctlMotsCle",
    search_option_or="#ctlBlocRecherche_ctlMotsCles_ctlOptionOU",
    available_only_radio="input[name*='ctlSelDisponibilite'][value='ctlDispoSeulement']",
    search_button="#ctlBlocRecherche_ctlRechercher",
    cart_button="#ctlGrille_ctlMenuActionsBas_ctlAppelPanierIdent",
    dossier_input_template="#ctlPanierActivites_ctlActivites_ctl{i:02d}_ctlRow_ctlListeIdentification_ctlListe_itm0_ctlBloc_ctlDossier",
    nip_input_template="#ctlPanierActivites_ctlActivites_ctl{i:02d}_ctlRow_ctlListeIdentification_ctlListe_itm0_ctlBloc_ctlNip",
    unregister_button_template="#ctlPanierActivites_ctlActivites_ctl{i:02d}_ctlRow_ctlListeIdentification_ctlListe_itm0_ctlBloc_ctlMoins",
    validate_button="#ctlMenuActionBas_ctlAppelPanierConfirm",
)


class RegistrationBot:
    def __init__(self, settings: Settings, selectors: Selectors = DEFAULT_SELECTORS):
        self.settings = settings
        self.selectors = selectors
        self.last_activity_status: RegistrationStatus | None = None

    async def run(self) -> RegistrationStatus:
        logger.info("Starting registration bot...")
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.settings.headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await self._navigate_to_search(page)
                result = await self._wait_and_select_activity(page)

                if result == RegistrationStatus.SUCCESS:
                    await self._fill_credentials(page)
                    status = await self._submit(page)

                    if status == RegistrationStatus.SUCCESS:
                        logger.info("Registration completed successfully!")
                        should_unregister = await self._prompt_unregister()
                        if should_unregister:
                            unregistered = await self._unregister_participants(page)
                            if unregistered:
                                logger.info("Unregistered from activity")
                                await page.wait_for_timeout(500)
                                return RegistrationStatus.UNREGISTERED
                    elif status == RegistrationStatus.ALREADY_ENROLLED:
                        logger.info("Already enrolled in this activity")
                    elif status == RegistrationStatus.INVALID_CREDENTIALS:
                        logger.error("Invalid credentials - dossier/NIP not found")
                    elif status == RegistrationStatus.AGE_CRITERIA_NOT_MET:
                        logger.error("Age criteria not met for this activity")

                    return status

                if self.last_activity_status:
                    logger.error(f"Activity found but: {self.last_activity_status.value}")
                    return self.last_activity_status

                logger.error("Registration timed out - activity not found")
                return RegistrationStatus.TIMEOUT

            except Exception as e:
                logger.error(f"Registration failed: {e}")
                screenshot_path = f"error-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
                return RegistrationStatus.FAILED
            finally:
                await browser.close()

    async def _navigate_to_search(self, page: Page) -> None:
        logger.info("Opening registration website...")
        await page.goto(self.settings.registration_url, wait_until="networkidle")

        logger.info("Selecting 'available only' filter...")
        await page.get_by_role("link", name="Disponibilités").click()
        await page.wait_for_timeout(300)
        await page.locator(self.selectors.available_only_radio).click()
        await page.wait_for_timeout(300)

        logger.info(f"Searching for activity: {self.settings.activity_name}")
        await page.locator(self.selectors.keyword_search).fill(self.settings.activity_name)
        await page.locator(self.selectors.search_option_or).click()
        await page.wait_for_timeout(300)

        if self.settings.domain:
            logger.info("Opening Domaines tab...")
            await page.get_by_role("link", name="Domaines").click()
            await page.wait_for_timeout(500)

            logger.info(f"Selecting domain: {self.settings.domain}")
            checkbox = page.locator(
                f"//*[contains(text(), '{self.settings.domain}')]/preceding::input[@type='checkbox'][1]"
            )
            await checkbox.first.click()
            await page.wait_for_timeout(300)

        logger.info("Clicking search button...")
        await page.locator(self.selectors.search_button).click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)

    async def _wait_and_select_activity(self, page: Page) -> RegistrationStatus | None:
        logger.info(f"Searching for activity: {self.settings.activity_name}")
        start_time = asyncio.get_running_loop().time()
        attempts = 0

        while asyncio.get_running_loop().time() - start_time < self.settings.timeout:
            attempts += 1
            elapsed = int(asyncio.get_running_loop().time() - start_time)
            logger.info(f"Attempt #{attempts} (elapsed: {elapsed}s)")

            result = await self._find_and_select_activity(page)

            if result == RegistrationStatus.SUCCESS:
                logger.info("Activity found and selected!")
                return result

            logger.info("Activity not available yet, refreshing...")
            await asyncio.sleep(self.settings.refresh_interval)
            await page.reload(wait_until="networkidle")
            await page.wait_for_timeout(2000)

        return None

    async def _find_and_select_activity(self, page: Page) -> RegistrationStatus | None:
        result = await self._try_select_on_page(page)
        if result == RegistrationStatus.SUCCESS:
            return result
        if result is not None:
            self.last_activity_status = result

        async def try_page(p: Page) -> RegistrationStatus | None:
            r = await self._try_select_on_page(p)
            if r == RegistrationStatus.SUCCESS:
                return r
            if r is not None:
                self.last_activity_status = r
            return None

        return await iterate_pagination(page, try_page)

    async def _try_select_on_page(self, page: Page) -> RegistrationStatus | None:
        activity_name = self.settings.activity_name

        activity_elements = page.get_by_text(activity_name, exact=False)
        count = await activity_elements.count()
        logger.info(f"Found {count} elements matching '{activity_name}'")

        for i in range(count):
            el = activity_elements.nth(i)
            parent_row = el.locator("xpath=ancestor::tr[1]")
            select_btn = parent_row.locator("input[type='image'][id*='Selecteur']")
            btn_count = await select_btn.count()

            if btn_count > 0:
                btn = select_btn.first
                src = await btn.get_attribute("src") or ""
                alt = await btn.get_attribute("alt") or ""

                status = get_status_from_image_src(src, alt)
                if status == ActivityStatus.NEVER_AVAILABLE:
                    logger.info("Activity found but online registration never available")
                    return RegistrationStatus.REGISTRATION_NEVER_AVAILABLE

                row_content = await parent_row.inner_text()
                if "COMPLET" in row_content.upper():
                    logger.info("Activity found but is COMPLET (full)")
                    return RegistrationStatus.ACTIVITY_FULL
                if "ANNULÉE" in row_content.upper():
                    logger.info("Activity found but is ANNULÉE (cancelled)")
                    return RegistrationStatus.ACTIVITY_CANCELLED

                if status == ActivityStatus.NOT_YET or status == ActivityStatus.FULL:
                    logger.info(f"Found activity but not available: {status.value}")
                    return RegistrationStatus.FAILED

                logger.info("Found activity, clicking select button...")
                await btn.click()
                await page.wait_for_timeout(500)

                logger.info("Adding to cart...")
                await page.locator(self.selectors.cart_button).click()
                await page.wait_for_load_state("networkidle")

                return RegistrationStatus.SUCCESS

        return None

    async def _fill_credentials(self, page: Page) -> None:
        logger.info("Filling credentials...")
        for i, participant in enumerate(self.settings.participants):
            dossier_selector = self.selectors.dossier_input_template.format(i=i)
            nip_selector = self.selectors.nip_input_template.format(i=i)

            await page.locator(dossier_selector).fill(participant.carte_acces)
            await page.locator(nip_selector).fill(participant.telephone)
            await asyncio.sleep(0.1)

    async def _unregister_participants(self, page: Page) -> bool:
        logger.info("Unregistering participants from cart...")
        for i in range(len(self.settings.participants)):
            unregister_selector = self.selectors.unregister_button_template.format(i=i)
            unregister_btn = page.locator(unregister_selector)
            if await unregister_btn.count() > 0:
                await unregister_btn.first.click()
                await page.wait_for_timeout(300)

                confirm_btn = page.locator("input#OUI[value='OUI']")
                if await confirm_btn.count() > 0:
                    await confirm_btn.click()
                    await page.wait_for_timeout(500)
                    logger.info(f"Unregistered participant {i}")

        page_content = await page.locator("body").inner_text()
        if "Nouveau tarif ajusté : N/A" in page_content:
            logger.info("Unregistration confirmed - tariff shows N/A")
            return True
        return False

    async def _prompt_unregister(self) -> bool:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: input("Registration successful! Unregister? [y/N]: ").strip().lower(),
        )
        return response in ("y", "yes")

    async def _submit(self, page: Page) -> RegistrationStatus:
        logger.info("Submitting registration...")
        await page.locator(self.selectors.validate_button).click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        page_content = await page.locator("body").inner_text()

        if "Place réservée" in page_content:
            logger.info("Place reserved - registration successful")
            return RegistrationStatus.SUCCESS

        if "êtes déjà inscrit" in page_content or "déjà inscrit" in page_content.lower():
            logger.info("Already enrolled detected")
            return RegistrationStatus.ALREADY_ENROLLED

        if "Aucun dossier" in page_content or "n'a été retrouvé" in page_content:
            logger.error("Invalid credentials - dossier not found")
            return RegistrationStatus.INVALID_CREDENTIALS

        if "critère d'âge" in page_content or "ne répond pas au critère" in page_content:
            logger.error("Age criteria not met for this activity")
            return RegistrationStatus.AGE_CRITERIA_NOT_MET

        if "Erreur" in page_content or "error" in page_content.lower():
            logger.error("Error detected on page")
            return RegistrationStatus.FAILED

        return RegistrationStatus.SUCCESS
