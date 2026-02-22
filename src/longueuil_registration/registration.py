import asyncio
import logging
from dataclasses import dataclass

from playwright.async_api import async_playwright

from .config import Settings

logger = logging.getLogger(__name__)


@dataclass
class Selectors:
    checkbox: str
    search_button: str
    page_link: str
    activity_button_template: str
    cart_button: str
    dossier_input_template: str
    nip_input_template: str
    validate_button: str


DEFAULT_SELECTORS = Selectors(
    checkbox="input[type='checkbox'] + span:text-is('{}')",
    search_button="#ctlBlocRecherche_ctlRechercher",
    page_link="#ctlGrille_ctlPagerHaut_ctlListePages_ctl12_ctlLienPage",
    activity_button_template="#ctlGrille_ctlGrilleActivite_ctlListeAct_ctl0{i}_ctlLigneAct_ctlSelectionPanier_ctlImageButtonSelecteur",
    cart_button="#ctlGrille_ctlMenuActionsBas_ctlAppelPanierIdent",
    dossier_input_template="#ctlPanierActivites_ctlActivites_ctl{i:02d}_ctlRow_ctlListeIdentification_ctlListe_itm0_ctlBloc_ctlDossier",
    nip_input_template="#ctlPanierActivites_ctlActivites_ctl{i:02d}_ctlRow_ctlListeIdentification_ctlListe_itm0_ctlBloc_ctlNip",
    validate_button="#ctlMenuActionBas_ctlAppelPanierConfirm",
)


class RegistrationBot:
    def __init__(self, settings: Settings, selectors: Selectors = DEFAULT_SELECTORS):
        self.settings = settings
        self.selectors = selectors

    async def run(self) -> bool:
        logger.info("Starting registration bot...")
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.settings.headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await self._navigate_and_search(page)
                success = await self._wait_for_availability(page)

                if not success:
                    logger.error("Registration timed out")
                    return False

                await self._select_activities(page)
                await self._fill_credentials(page)
                await self._submit(page)

                logger.info("Registration completed successfully!")
                return True

            except Exception as e:
                logger.error(f"Registration failed: {e}")
                return False
            finally:
                await browser.close()

    async def _navigate_and_search(self, page) -> None:
        logger.info("Opening registration website...")
        await page.goto(self.settings.registration_url)

        logger.info(f"Selecting activity category: {self.settings.activity_category}")
        checkbox_selector = self.selectors.checkbox.format(
            self.settings.activity_category
        )
        await page.locator(checkbox_selector).click()

        logger.info("Clicking search button...")
        await page.locator(self.selectors.search_button).click()

        logger.info("Navigating to results page...")
        await page.locator(self.selectors.page_link).click()

    async def _wait_for_availability(self, page) -> bool:
        logger.info("Waiting for registration to become available...")
        start_time = asyncio.get_running_loop().time()

        while asyncio.get_running_loop().time() - start_time < self.settings.timeout:
            try:
                button = await page.wait_for_selector(
                    self.selectors.activity_button_template.format(i=1),
                    timeout=3000,
                )
                if await button.is_enabled():
                    src = await button.get_attribute("src")
                    if src and "ic_InscrNotNow.gif" not in src:
                        logger.info("Registration is now available!")
                        return True
            except Exception:
                pass

            logger.info("Registration not available yet, refreshing...")
            await asyncio.sleep(self.settings.refresh_interval)
            await page.reload()

        return False

    async def _select_activities(self, page) -> None:
        logger.info("Selecting activities...")
        num_activities = len(self.settings.family_members)

        for i in range(1, num_activities + 1):
            selector = self.selectors.activity_button_template.format(i=i)
            await page.locator(selector).click()
            await asyncio.sleep(0.1)

        logger.info("Adding to cart...")
        await page.locator(self.selectors.cart_button).click()

    async def _fill_credentials(self, page) -> None:
        logger.info("Filling credentials...")
        for i, member in enumerate(self.settings.family_members):
            dossier_selector = self.selectors.dossier_input_template.format(i=i)
            nip_selector = self.selectors.nip_input_template.format(i=i)

            await page.locator(dossier_selector).fill(member.dossier)
            await page.locator(nip_selector).fill(member.nip)
            await asyncio.sleep(0.1)

    async def _submit(self, page) -> None:
        logger.info("Submitting registration...")
        await page.locator(self.selectors.validate_button).click()
        await asyncio.sleep(5)
