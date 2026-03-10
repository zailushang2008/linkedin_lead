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


def _people_search_url(keywords: str, page: int) -> str:
    encoded_keywords = quote_plus(keywords)
    return f'https://www.linkedin.com/search/results/people/?keywords={encoded_keywords}&page={page}'


async def _first_text(locator: Locator) -> str | None:
    count = await locator.count()
    if count == 0:
        return None
    text = (await locator.first.inner_text()).strip()
    return text or None


async def _extract_profile_urn(container: Locator) -> str | None:
    for attr in ('data-chameleon-result-urn', 'data-urn', 'data-id'):
        value = await container.get_attribute(attr)
        if value:
            return value
    return None


async def _extract_profile_url(container: Locator) -> str | None:
    profile_link = container.locator("a[href*='/in/']")
    count = await profile_link.count()
    if count == 0:
        return None
    href = await profile_link.first.get_attribute('href')
    if not href:
        return None
    if href.startswith('http'):
        return href.split('?')[0]
    return f'https://www.linkedin.com{href}'.split('?')[0]


async def _extract_person(container: Locator) -> dict[str, Any] | None:
    profile_url = await _extract_profile_url(container)
    if not profile_url:
        return None

    full_name = await _first_text(container.locator('span[aria-hidden="true"]'))
    headline = await _first_text(container.locator('.entity-result__primary-subtitle'))
    location = await _first_text(container.locator('.entity-result__secondary-subtitle'))
    current_company = await _first_text(container.locator('.entity-result__summary'))
    profile_urn = await _extract_profile_urn(container)

    return {
        'full_name': full_name,
        'headline': headline,
        'location': location,
        'current_company': current_company,
        'profile_url': profile_url,
        'profile_urn': profile_urn,
    }


async def _save_debug_artifacts(page: Page, reason: str) -> tuple[str, str]:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    screenshot_path = DEBUG_DIR / f'people_search_{stamp}.png'
    html_path = DEBUG_DIR / f'people_search_{stamp}.html'

    await page.screenshot(path=str(screenshot_path), full_page=True)
    html_path.write_text(await page.content(), encoding='utf-8')

    logger.error(
        'people_search debug saved reason=%s screenshot=%s html=%s',
        reason,
        screenshot_path,
        html_path,
    )
    return str(screenshot_path), str(html_path)


async def _wait_results_or_raise(page: Page) -> Locator:
    primary = page.locator('li.reusable-search__result-container')
    await page.wait_for_timeout(1500)
    if await primary.count() > 0:
        return primary

    fallback = page.locator('div.entity-result')
    if await fallback.count() > 0:
        return fallback

    page_title = await page.title()
    lower_url = page.url.lower()
    lower_title = page_title.lower()

    if any(marker in lower_url for marker in ['linkedin.com/login', '/checkpoint/', '/challenge/']):
        await _save_debug_artifacts(page, 'login_or_challenge_redirect')
        raise LoginRequiredError(
            f'linkedin redirected to auth/challenge page. url={page.url} title={page_title}'
        )

    if 'search/results/people' not in lower_url and 'search' not in lower_title:
        await _save_debug_artifacts(page, 'unexpected_non_search_page')
        raise SelectorMissingError(
            f'current page does not look like people search page. url={page.url} title={page_title}'
        )

    await _save_debug_artifacts(page, 'result_containers_not_found')
    raise SelectorMissingError(
        f'unable to find people search result containers. url={page.url} title={page_title}'
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

        result_nodes = await _wait_results_or_raise(page_obj)
        total = await result_nodes.count()
        limited = min(total, 10)

        parsed: list[dict[str, Any]] = []
        for idx in range(limited):
            item = await _extract_person(result_nodes.nth(idx))
            if item:
                parsed.append(item)

        if not parsed:
            await _save_debug_artifacts(page_obj, 'containers_found_but_no_profiles_parsed')
            raise SelectorMissingError(
                f'people result containers found but no valid profile entries parsed. url={page_obj.url} title={page_title}'
            )

        return parsed
