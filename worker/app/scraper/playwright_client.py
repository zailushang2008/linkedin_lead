import json
import logging
from contextlib import asynccontextmanager
from typing import Any

from playwright.async_api import BrowserContext, Error as PlaywrightError, Page, TimeoutError as PlaywrightTimeoutError, async_playwright

from app.config import settings

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    pass


class PageTimeoutError(ScraperError):
    pass


class LoginRequiredError(ScraperError):
    pass


class RedirectLoopError(ScraperError):
    pass


class SelectorMissingError(ScraperError):
    pass


def _normalize_cookie(cookie: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        'name': cookie.get('name'),
        'value': cookie.get('value'),
        'domain': cookie.get('domain', '.linkedin.com'),
        'path': cookie.get('path', '/'),
    }
    if 'expires' in cookie:
        normalized['expires'] = cookie['expires']
    if 'httpOnly' in cookie:
        normalized['httpOnly'] = cookie['httpOnly']
    if 'secure' in cookie:
        normalized['secure'] = cookie['secure']
    if 'sameSite' in cookie:
        normalized['sameSite'] = cookie['sameSite']
    return normalized


def parse_cookies_json(cookies_json: str | None) -> list[dict[str, Any]]:
    if not cookies_json:
        return []
    parsed = json.loads(cookies_json)
    if not isinstance(parsed, list):
        raise ScraperError('linkedin cookies must be a JSON array')
    return [_normalize_cookie(item) for item in parsed if isinstance(item, dict) and item.get('name') and item.get('value')]


def resolve_linkedin_auth(
    storage_state_path: str | None,
    cookies_json: str | None,
) -> tuple[str | None, str | None]:
    state_path = storage_state_path or settings.linkedin_storage_state_path
    raw_cookies = cookies_json or settings.linkedin_cookies_json
    if state_path and raw_cookies:
        logger.warning('both storage_state_path and cookies_json provided; using storage_state_path only to avoid redirect loops')
        raw_cookies = None
    return state_path, raw_cookies


async def ensure_logged_in(page: Page) -> None:
    current = page.url.lower()
    if 'linkedin.com/login' in current or '/checkpoint/' in current:
        raise LoginRequiredError(f'linkedin session invalid or login required: {page.url}')
    title = (await page.title()).lower()
    if 'err_too_many_redirects' in title:
        raise RedirectLoopError(
            'linkedin navigation hit ERR_TOO_MANY_REDIRECTS; use a fresh storage_state_path and avoid mixing cookies_json with storage_state_path'
        )


@asynccontextmanager
async def browser_context(
    headless: bool | None = None,
    storage_state_path: str | None = None,
    cookies_json: str | None = None,
):
    run_headless = settings.playwright_headless if headless is None else headless
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=run_headless)
        state_path, raw_cookies = resolve_linkedin_auth(storage_state_path=storage_state_path, cookies_json=cookies_json)
        context_kwargs = {}
        if state_path:
            context_kwargs['storage_state'] = state_path
        context: BrowserContext = await browser.new_context(**context_kwargs)
        try:
            cookies = parse_cookies_json(raw_cookies)
            if cookies:
                await context.add_cookies(cookies)
            yield context
        finally:
            await context.close()
            await browser.close()


async def goto_with_timeout(page: Page, url: str, wait_until: str = 'domcontentloaded') -> None:
    try:
        await page.goto(url, wait_until=wait_until, timeout=settings.playwright_timeout_ms)
    except PlaywrightTimeoutError as exc:
        raise PageTimeoutError(f'timeout while opening {url}') from exc
    except PlaywrightError as exc:
        if 'ERR_TOO_MANY_REDIRECTS' in str(exc):
            raise RedirectLoopError(
                f'linkedin navigation hit ERR_TOO_MANY_REDIRECTS for {url}; use a valid storage_state_path and do not mix it with cookies_json'
            ) from exc
        raise
