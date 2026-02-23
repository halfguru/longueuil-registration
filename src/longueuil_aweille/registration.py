import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from playwright.async_api import Page, async_playwright

from .config import Settings

logger = logging.getLogger(__name__)


class RegistrationStatus(Enum):
    SUCCESS = "success"
    ALREADY_ENROLLED = "already_enrolled"
    INVALID_CREDENTIALS = "invalid_credentials"
    AGE_CRITERIA_NOT_MET = "age_criteria_not_met"
    ACTIVITY_FULL = "activity_full"
    ACTIVITY_CANCELLED = "activity_cancelled"
    REGISTRATION_NEVER_AVAILABLE = "registration_never_available"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Selectors:
    search_button: str
    cart_button: str
    dossier_input_template: str
    nip_input_template: str
    validate_button: str


DEFAULT_SELECTORS = Selectors(
    search_button="#ctlBlocRecherche_ctlRechercher",
    cart_button="#ctlGrille_ctlMenuActionsBas_ctlAppelPanierIdent",
    dossier_input_template="#ctlPanierActivites_ctlActivites_ctl{i:02d}_ctlRow_ctlListeIdentification_ctlListe_itm0_ctlBloc_ctlDossier",
    nip_input_template="#ctlPanierActivites_ctlActivites_ctl{i:02d}_ctlRow_ctlListeIdentification_ctlListe_itm0_ctlBloc_ctlNip",
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
                await self._navigate_to_domain(page)
                result = await self._wait_and_select_activity(page)

                if result == RegistrationStatus.SUCCESS:
                    await self._fill_credentials(page)
                    status = await self._submit(page)

                    if status == RegistrationStatus.SUCCESS:
                        logger.info("Registration completed successfully!")
                    elif status == RegistrationStatus.ALREADY_ENROLLED:
                        logger.info("Already enrolled in this activity")
                    elif status == RegistrationStatus.INVALID_CREDENTIALS:
                        logger.error("Invalid credentials - dossier/NIP not found")
                    elif status == RegistrationStatus.AGE_CRITERIA_NOT_MET:
                        logger.error("Age criteria not met for this activity")

                    return status

                # Activity not found or not available
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

    async def _navigate_to_domain(self, page: Page) -> None:
        logger.info("Opening registration website...")
        await page.goto(self.settings.registration_url, wait_until="networkidle")

        logger.info("Opening Domaines tab...")
        await page.get_by_role("link", name="Domaines").click()
        await page.wait_for_timeout(1000)

        logger.info(f"Selecting domain: {self.settings.domain}")
        domain = self.settings.domain
        checkbox = page.locator(
            f"//*[contains(text(), '{domain}')]/preceding::input[@type='checkbox'][1]"
        )
        await checkbox.first.click()
        await page.wait_for_timeout(1000)

        logger.info("Clicking search button...")
        await page.locator(self.selectors.search_button).click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)

    async def _wait_and_select_activity(self, page: Page) -> RegistrationStatus | None:
        logger.info(f"Searching for activity: {self.settings.activity_name}")
        start_time = asyncio.get_running_loop().time()

        while asyncio.get_running_loop().time() - start_time < self.settings.timeout:
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

        page_links = page.locator("a[id*='ctlLienPage']")
        num_pages = await page_links.count()
        logger.info(f"Found {num_pages} pagination links")

        if num_pages == 0:
            return None

        logger.info(f"Checking {num_pages} pages for activity...")

        for i in range(num_pages):
            page_links = page.locator("a[id*='ctlLienPage']")
            if i >= await page_links.count():
                break

            await page_links.nth(i).click()
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(2000)

            result = await self._try_select_on_page(page)
            if result == RegistrationStatus.SUCCESS:
                return result
            if result is not None:
                self.last_activity_status = result

        return None

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

                # Check for "Inscription en ligne jamais disponible"
                if "jamais disponible" in alt.lower() or "JamaisDispo" in src:
                    logger.info("Activity found but online registration never available")
                    return RegistrationStatus.REGISTRATION_NEVER_AVAILABLE

                # Check if activity is marked as COMPLET or ANNULÉE in the row
                row_content = await parent_row.inner_text()
                if "COMPLET" in row_content.upper():
                    logger.info("Activity found but is COMPLET (full)")
                    return RegistrationStatus.ACTIVITY_FULL
                if "ANNULÉE" in row_content.upper():
                    logger.info("Activity found but is ANNULÉE (cancelled)")
                    return RegistrationStatus.ACTIVITY_CANCELLED

                # Check button indicates not available
                if "NotNow" in src or "Complet" in src:
                    logger.info(f"Found activity but not available: {src}")
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

            await page.locator(dossier_selector).fill(participant.dossier)
            await page.locator(nip_selector).fill(participant.nip)
            await asyncio.sleep(0.1)

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
