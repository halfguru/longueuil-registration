import logging
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import TypeVar

from playwright.async_api import Page

logger = logging.getLogger(__name__)

DEFAULT_REGISTRATION_URL = (
    "https://loisir.longueuil.quebec/inscription/Pages/Anonyme/Resultat/Page.fr.aspx?m=1"
)


class ActivityStatus(Enum):
    AVAILABLE = "available"
    FULL = "full"
    CANCELLED = "cancelled"
    NEVER_AVAILABLE = "never_available"
    NOT_YET = "not_yet"


class RegistrationStatus(Enum):
    SUCCESS = "success"
    UNREGISTERED = "unregistered"
    ALREADY_ENROLLED = "already_enrolled"
    INVALID_CREDENTIALS = "invalid_credentials"
    AGE_CRITERIA_NOT_MET = "age_criteria_not_met"
    ACTIVITY_FULL = "activity_full"
    ACTIVITY_CANCELLED = "activity_cancelled"
    REGISTRATION_NEVER_AVAILABLE = "registration_never_available"
    FAILED = "failed"
    TIMEOUT = "timeout"


def get_status_from_image_src(src: str, alt: str = "") -> ActivityStatus:
    src_lower = src.lower()
    alt_lower = alt.lower()

    if "notnow" in src_lower:
        return ActivityStatus.NOT_YET
    if "jamaisdispo" in src_lower or "jamais disponible" in alt_lower:
        return ActivityStatus.NEVER_AVAILABLE
    if "complet" in src_lower:
        return ActivityStatus.FULL
    if "annule" in src_lower:
        return ActivityStatus.CANCELLED
    return ActivityStatus.AVAILABLE


T = TypeVar("T")

PageCallback = Callable[[Page], Awaitable[T | None]]


async def iterate_pagination(
    page: Page,
    callback: PageCallback[T],
    pagination_selector: str = "a[id*='ctlLienPage']",
) -> T | None:
    result = await callback(page)
    if result is not None:
        return result

    page_links = page.locator(pagination_selector)
    num_pages = await page_links.count()

    for i in range(num_pages):
        page_links = page.locator(pagination_selector)
        if i >= await page_links.count():
            break

        await page_links.nth(i).click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        result = await callback(page)
        if result is not None:
            return result

    return None
