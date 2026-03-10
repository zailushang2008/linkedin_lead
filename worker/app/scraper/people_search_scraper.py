import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from playwright.async_api import Locator, Page

from app.scraper.playwright_client import (
    LoginRequiredError,
    ScraperError,
    SelectorMissingError,
    browser_context,
    ensure_logged_in,
    goto_with_timeout,
)

logger = logging.getLogger(__name__)
DEBUG_DIR = Path('/app/debug')

SCREEN_SELECTOR = '[data-sdui-screen="com.linkedin.sdui.flagshipnav.search.SearchResultsPeople"]'
LISTITEM_SELECTOR = '[role="listitem"]'
PROFILE_LINK_SELECTOR = "a[href*='/in/']"


def _people_search_url(keywords: str, page: int) -> str:
    encoded_keywords = quote_plus(keywords)
    return f'https://www.linkedin.com/search/results/people/?keywords={encoded_keywords}&page={page}'


async def _first_text(locator: Locator) -> str | None:
    if await locator.count() == 0:
        return None
    text = (await locator.first.inner_text()).strip()
    return text or None


def _normalize_profile_url(href: str | None) -> str | None:
    if not href:
        return None
    if href.startswith('http'):
        return href.split('?')[0]
    if href.startswith('/in/'):
        return f'https://www.linkedin.com{href}'.split('?')[0]
    return None


async def _extract_profile_urn(item: Locator) -> str | None:
    for attr in ('data-chameleon-result-urn', 'data-urn', 'data-id'):
        value = await item.get_attribute(attr)
        if value:
            return value
    return None


async def _extract_from_listitem(item: Locator) -> dict[str, Any] | None:
    profile_link = item.locator(PROFILE_LINK_SELECTOR)
    if await profile_link.count() == 0:
        return None

    href = await profile_link.first.get_attribute('href')
    profile_url = _normalize_profile_url(href)
    if not profile_url:
        return None

    full_name = (await profile_link.first.inner_text()).strip() if await profile_link.first.count() else None

    # strategy: extract from same listitem text blocks; missing fields are allowed
    headline = await _first_text(item.locator('.t-14.t-black.t-normal, .entity-result__primary-subtitle'))
    location = await _first_text(item.locator('.t-14.t-normal.t-black--light, .entity-result__secondary-subtitle'))
    current_company = await _first_text(item.locator('.entity-result__summary, .t-14.t-normal'))

    return {
        'full_name': full_name or None,
        'headline': headline,
        'location': location,
        'current_company': current_company,
        'profile_url': profile_url,
        'profile_urn': await _extract_profile_urn(item),
    }


async def _save_debug_artifacts(page: Page, reason: str) -> tuple[str, str]:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    screenshot_path = DEBUG_DIR / f'people_search_{stamp}.png'
    html_path = DEBUG_DIR / f'people_search_{stamp}.html'

    await page.screenshot(path=str(screenshot_path), full_page=True)
    html_path.write_text(await page.content(), encoding='utf-8')
    logger.error('people_search debug saved reason=%s screenshot=%s html=%s', reason, screenshot_path, html_path)
    return str(screenshot_path), str(html_path)


async def _get_people_listitems(page: Page) -> Locator:
    area = page.locator(SCREEN_SELECTOR)
    await page.wait_for_timeout(1500)

    if await area.count() > 0:
        return area.first.locator(LISTITEM_SELECTOR)

    page_title = await page.title()
    lower_url = page.url.lower()
    if any(marker in lower_url for marker in ['linkedin.com/login', '/checkpoint/', '/challenge/']):
        await _save_debug_artifacts(page, 'login_or_challenge_redirect')
        raise LoginRequiredError(f'linkedin redirected to auth/challenge page. url={page.url} title={page_title}')

    await _save_debug_artifacts(page, 'search_people_area_not_found')
    raise SelectorMissingError(
        f'cannot locate SearchResultsPeople area selector={SCREEN_SELECTOR}. url={page.url} title={page_title}'
    )


async def scrape_people_search(
    keywords: str,
    page: int,
    cookies_json: str | None = None,
    storage_state_path: str | None = None,
) -> list[dict[str, Any]]:
    if not keywords.strip():
        raise ScraperError('keywords cannot be empty')

    url = _people_search_url(keywords=keywords, page=page)
    async with browser_context(cookies_json=cookies_json, storage_state_path=storage_state_path) as context:
        page_obj = await context.new_page()
        await goto_with_timeout(page_obj, url)
        await ensure_logged_in(page_obj)

        page_title = await page_obj.title()
        logger.info('people_search navigation final_url=%s page_url=%s title=%s', url, page_obj.url, page_title)

        listitems = await _get_people_listitems(page_obj)
        total_listitems = await listitems.count()

        parsed: list[dict[str, Any]] = []
        skipped_non_profile = 0
        skipped_upsell_or_noise = 0

        for idx in range(total_listitems):
            item = listitems.nth(idx)

            # only keep list items with /in/ links
            if await item.locator(PROFILE_LINK_SELECTOR).count() == 0:
                skipped_non_profile += 1
                continue

            raw_text = ((await item.inner_text()) or '').strip()
            lower_text = raw_text.lower()
            if '领英会员' in raw_text or 'linkedin premium' in lower_text or '/search/results/' in lower_text:
                skipped_upsell_or_noise += 1
                continue

            extracted = await _extract_from_listitem(item)
            if extracted:
                parsed.append(extracted)

            if len(parsed) >= 10:
                break

        logger.info(
            'people_search listitem_stats total=%s valid_profiles=%s skipped_non_profile=%s skipped_upsell_or_noise=%s',
            total_listitems,
            len(parsed),
            skipped_non_profile,
            skipped_upsell_or_noise,
        )

        if len(parsed) == 0:
            await _save_debug_artifacts(page_obj, 'no_in_profile_links_found')
            raise SelectorMissingError(
                f'no valid /in/ profile links found in SearchResultsPeople listitems. '
                f'total_listitems={total_listitems} url={page_obj.url} title={page_title}'
            )

        # target at least first 5 valid profiles when available
        return parsed[:10]
