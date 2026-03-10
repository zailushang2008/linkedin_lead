from typing import Any

from playwright.async_api import Locator, Page

from app.scraper.playwright_client import (
    ScraperError,
    SelectorMissingError,
    browser_context,
    ensure_logged_in,
    goto_with_timeout,
)


async def _text_or_none(locator: Locator) -> str | None:
    if await locator.count() == 0:
        return None
    text = (await locator.first.inner_text()).strip()
    return text or None


async def _extract_experiences(page: Page) -> list[dict[str, Any]]:
    section = page.locator("section:has(#experience), section[id*='experience']")
    if await section.count() == 0:
        return []

    items = section.first.locator('li.artdeco-list__item, .pvs-list__paged-list-item')
    result: list[dict[str, Any]] = []
    for idx in range(min(await items.count(), 10)):
        item = items.nth(idx)
        title = await _text_or_none(item.locator("span[aria-hidden='true']").first)
        company = await _text_or_none(item.locator('.t-14.t-normal').first)
        duration = await _text_or_none(item.locator('.pvs-entity__caption-wrapper').first)
        if title or company:
            result.append({'title': title, 'company': company, 'duration': duration})
    return result


async def _extract_educations(page: Page) -> list[dict[str, Any]]:
    section = page.locator("section:has(#education), section[id*='education']")
    if await section.count() == 0:
        return []

    items = section.first.locator('li.artdeco-list__item, .pvs-list__paged-list-item')
    result: list[dict[str, Any]] = []
    for idx in range(min(await items.count(), 10)):
        item = items.nth(idx)
        school = await _text_or_none(item.locator("span[aria-hidden='true']").first)
        degree = await _text_or_none(item.locator('.t-14.t-normal').first)
        if school or degree:
            result.append({'school': school, 'degree': degree})
    return result


async def _extract_skills(page: Page) -> list[str]:
    skill_nodes = page.locator("section:has(#skills) span[aria-hidden='true']")
    skills: list[str] = []
    for idx in range(min(await skill_nodes.count(), 20)):
        value = (await skill_nodes.nth(idx).inner_text()).strip()
        if value and value.lower() not in {'skills', 'show all'}:
            skills.append(value)
    # deduplicate preserving order
    deduped: list[str] = []
    seen = set()
    for skill in skills:
        if skill not in seen:
            seen.add(skill)
            deduped.append(skill)
    return deduped


async def _extract_about(page: Page) -> str | None:
    about_locator = page.locator("section:has(#about) .display-flex.ph5.pv3, section:has(#about) .pv-shared-text-with-see-more")
    about_text = await _text_or_none(about_locator)
    return about_text


async def _extract_top_card(page: Page) -> tuple[str | None, str | None, str | None]:
    full_name = await _text_or_none(page.locator('h1'))
    headline = await _text_or_none(page.locator('.text-body-medium'))
    location = await _text_or_none(page.locator('.text-body-small.inline.t-black--light.break-words'))
    return full_name, headline, location


async def scrape_profile(
    profile_url: str,
    cookies_json: str | None = None,
    storage_state_path: str | None = None,
) -> dict[str, Any]:
    if not profile_url.startswith('http'):
        raise ScraperError('profile_url must be a valid absolute URL')

    async with browser_context(cookies_json=cookies_json, storage_state_path=storage_state_path) as context:
        page = await context.new_page()
        await goto_with_timeout(page, profile_url)
        await ensure_logged_in(page)
        await page.wait_for_timeout(1500)

        full_name, headline, location = await _extract_top_card(page)
        if not full_name and not headline:
            raise SelectorMissingError('profile top card selectors not found')

        about = await _extract_about(page)
        experiences = await _extract_experiences(page)
        educations = await _extract_educations(page)
        skills = await _extract_skills(page)

        return {
            'profile_url': profile_url,
            'full_name': full_name,
            'headline': headline,
            'location': location,
            'about': about,
            'experiences': experiences,
            'education': educations,
            'educations': educations,
            'skills': skills,
        }
