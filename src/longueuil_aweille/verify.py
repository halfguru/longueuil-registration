import logging
from dataclasses import dataclass
from enum import Enum

from playwright.async_api import Page, async_playwright

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class VerifySelectors:
    carte_acces_input: str
    telephone_input: str
    submit_button: str


DEFAULT_VERIFY_SELECTORS = VerifySelectors(
    carte_acces_input="input[name='numero']",
    telephone_input="input[name='telephone']",
    submit_button="input[name='action'][type='submit']",
)


class VerificationBot:
    def __init__(
        self,
        carte_acces: str,
        telephone: str,
        headless: bool = False,
        timeout: int = 30,
        selectors: VerifySelectors = DEFAULT_VERIFY_SELECTORS,
    ):
        self.carte_acces = carte_acces
        self.telephone = telephone
        self.headless = headless
        self.timeout = timeout
        self.selectors = selectors
        self.verification_url = "https://validationcarteacces.longueuil.quebec/"

    async def run(self) -> VerificationStatus:
        logger.info("Starting credential verification")
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                status = await self._verify(page)
                return status
            except Exception as e:
                logger.error(f"Verification failed: {e}")
                return VerificationStatus.ERROR
            finally:
                await browser.close()

    async def _verify(self, page: Page) -> VerificationStatus:
        logger.info("Opening verification page")
        await page.goto(self.verification_url, wait_until="networkidle")

        await self._fill_form(page)

        logger.info("Submitting form")
        await page.locator(self.selectors.submit_button).first.click()
        await page.wait_for_load_state("networkidle")

        return await self._check_result(page)

    async def _fill_form(self, page: Page) -> None:
        carte_acces_input = page.locator(self.selectors.carte_acces_input)
        telephone_input = page.locator(self.selectors.telephone_input)

        if await carte_acces_input.count() == 0:
            carte_acces_input = page.get_by_label("carte", exact=False).first
        if await telephone_input.count() == 0:
            telephone_input = page.get_by_label("téléphone", exact=False).first

        await carte_acces_input.fill(self.carte_acces)
        await telephone_input.fill(self.telephone)

    async def _check_result(self, page: Page) -> VerificationStatus:
        page_content = await page.locator("body").inner_text()

        invalid_indicators = [
            "n'est pas valide",
            "pas valide",
            "invalide",
            "non trouvé",
            "erreur",
        ]

        for indicator in invalid_indicators:
            if indicator in page_content.lower():
                logger.info("Account verification: INVALID")
                return VerificationStatus.INVALID

        valid_indicators = [
            "Voici les informations",
            "En règle",
            "Statut du dossier",
        ]

        for indicator in valid_indicators:
            if indicator in page_content:
                logger.info("Account verification: VALID")
                return VerificationStatus.VALID

        logger.warning("Could not determine verification status from page content")
        return VerificationStatus.ERROR
