from app.scraper.people_search_payloads import (
    extract_people_from_response,
    extract_public_identifier,
    merge_people_results,
    normalize_profile_url,
)


def test_normalize_profile_url_strips_query_and_keeps_slug() -> None:
    assert (
        normalize_profile_url('https://www.linkedin.com/in/jane-doe-123/?miniProfileUrn=urn%3Ali%3Afsd_profile%3A123')
        == 'https://www.linkedin.com/in/jane-doe-123'
    )


def test_extract_people_from_voyager_payload() -> None:
    payload = {
        'included': [
            {
                'entityUrn': 'urn:li:fsd_profile:123',
                'navigationUrl': 'https://www.linkedin.com/in/jane-doe-123/?miniProfileUrn=urn%3Ali%3Afsd_profile%3A123',
                'title': {'text': 'Jane Doe'},
                'primarySubtitle': {'text': 'Senior Software Engineer'},
                'secondarySubtitle': {'text': 'San Francisco Bay Area'},
                'summary': {'text': 'OpenAI'},
            }
        ]
    }

    results = extract_people_from_response(payload)

    assert results == [
        {
            'full_name': 'Jane Doe',
            'headline': 'Senior Software Engineer',
            'location': 'San Francisco Bay Area',
            'current_company': 'OpenAI',
            'profile_url': 'https://www.linkedin.com/in/jane-doe-123',
            'profile_urn': 'urn:li:fsd_profile:123',
            'public_identifier': 'jane-doe-123',
        }
    ]


def test_merge_people_results_prefers_non_null_fields() -> None:
    merged = merge_people_results(
        api_results=[
            {
                'profile_url': 'https://www.linkedin.com/in/jane-doe-123',
                'full_name': 'Jane Doe',
                'headline': 'Senior Software Engineer',
                'location': 'San Francisco Bay Area',
                'current_company': 'OpenAI',
                'profile_urn': 'urn:li:fsd_profile:123',
                'public_identifier': 'jane-doe-123',
            }
        ],
        dom_results=[
            {
                'profile_url': 'https://www.linkedin.com/in/jane-doe-123',
                'full_name': 'Jane Doe',
                'headline': None,
                'location': None,
                'current_company': None,
                'profile_urn': None,
                'public_identifier': extract_public_identifier('https://www.linkedin.com/in/jane-doe-123'),
            }
        ],
    )

    assert merged[0]['headline'] == 'Senior Software Engineer'
    assert merged[0]['current_company'] == 'OpenAI'
