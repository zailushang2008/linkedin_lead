from collections.abc import Iterable
from typing import Any
from urllib.parse import urlparse


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = ' '.join(value.split())
        return text or None
    return None


def extract_text_value(value: Any) -> str | None:
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, dict):
        for key in ('text', 'title', 'subtitle', 'primaryText', 'secondaryText'):
            text = extract_text_value(value.get(key))
            if text:
                return text
        attributes = value.get('attributes')
        if isinstance(attributes, list):
            texts = [extract_text_value(item) for item in attributes]
            joined = ' '.join(text for text in texts if text)
            return clean_text(joined)
    if isinstance(value, list):
        texts = [extract_text_value(item) for item in value]
        joined = ' '.join(text for text in texts if text)
        return clean_text(joined)
    return None


def normalize_profile_url(href: str | None) -> str | None:
    if not href:
        return None
    if href.startswith('/in/'):
        href = f'https://www.linkedin.com{href}'
    parsed = urlparse(href)
    if not parsed.scheme or not parsed.netloc:
        return None
    if '/in/' not in parsed.path:
        return None
    normalized_path = parsed.path.rstrip('/') or parsed.path
    return f'{parsed.scheme}://{parsed.netloc}{normalized_path}'


def extract_public_identifier(profile_url: str | None, profile_urn: str | None = None) -> str | None:
    if profile_url and '/in/' in profile_url:
        slug = profile_url.rstrip('/').rsplit('/in/', 1)[-1].strip('/')
        return slug or None
    if profile_urn and profile_urn.startswith('urn:li:'):
        return profile_urn.rsplit(':', 1)[-1] or None
    return None


def walk_dicts(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from walk_dicts(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from walk_dicts(item)


def pick_first_text(node: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        text = extract_text_value(node.get(key))
        if text:
            return text
    return None


def extract_api_result(node: dict[str, Any]) -> dict[str, Any] | None:
    profile_url = None
    for key in ('navigationUrl', 'entityUrl', 'targetUrl', 'profileUrl'):
        profile_url = normalize_profile_url(node.get(key))
        if profile_url:
            break

    if not profile_url:
        template = node.get('navigationUrlTemplate')
        if isinstance(template, str):
            profile_url = normalize_profile_url(template)

    if not profile_url:
        return None

    profile_urn = clean_text(node.get('entityUrn') or node.get('trackingUrn') or node.get('targetUrn'))
    public_identifier = pick_first_text(node, ('publicIdentifier', 'public_id'))
    if not public_identifier:
        public_identifier = extract_public_identifier(profile_url, profile_urn)

    full_name = pick_first_text(node, ('title', 'primaryTitle', 'headlineText', 'name'))
    headline = pick_first_text(node, ('primarySubtitle', 'subtitle', 'occupation', 'headline'))
    location = pick_first_text(node, ('secondarySubtitle', 'location'))
    current_company = pick_first_text(node, ('summary', 'subline', 'currentCompany', 'companyName'))

    if not any((full_name, headline, location, current_company, profile_urn)):
        return None

    return {
        'full_name': full_name,
        'headline': headline,
        'location': location,
        'current_company': current_company,
        'profile_url': profile_url,
        'profile_urn': profile_urn,
        'public_identifier': public_identifier,
    }


def extract_people_from_response(payload: Any) -> list[dict[str, Any]]:
    people: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for node in walk_dicts(payload):
        parsed = extract_api_result(node)
        if not parsed:
            continue
        profile_url = parsed['profile_url']
        if profile_url in seen_urls:
            continue
        seen_urls.add(profile_url)
        people.append(parsed)
    return people


def merge_people_results(
    api_results: list[dict[str, Any]],
    dom_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}

    for source in api_results + dom_results:
        profile_url = source.get('profile_url')
        if not profile_url:
            continue
        target = merged.setdefault(profile_url, {'profile_url': profile_url})
        for key, value in source.items():
            if value and not target.get(key):
                target[key] = value

    return list(merged.values())
