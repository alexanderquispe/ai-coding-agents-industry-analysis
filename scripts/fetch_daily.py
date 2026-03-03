#!/usr/bin/env python3
"""
Fetch yesterday's PRs/commits from GitHub API for all AI coding agents.
Uses hour-splitting when results exceed 1000 (GitHub Search API limit).
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path

GITHUB_TOKEN = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise RuntimeError('Missing GH_TOKEN or GITHUB_TOKEN environment variable')

HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

AGENTS = {
    'claude': {
        'search_type': 'commits',
        'query_base': 'author-name:"Claude" author-email:noreply@anthropic.com',
        'date_field': 'committer-date',
    },
    'copilot': {
        'search_type': 'issues',
        'query_base': 'is:pr head:copilot',
        'date_field': 'created',
    },
    'codex': {
        'search_type': 'issues',
        'query_base': 'is:pr head:codex',
        'date_field': 'created',
    },
    'cursor': {
        'search_type': 'issues',
        'query_base': 'is:pr head:cursor/',
        'date_field': 'created',
    },
}

OUTPUT_DIR = Path('data/daily')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Rate limit: ~30 req/min for Search API
REQUEST_DELAY = 2.1  # seconds between requests (safe margin)


def _api_request(url, headers, params):
    """Make a single API request with rate limit handling."""
    while True:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 403:
            reset = int(response.headers.get('X-RateLimit-Reset', 0))
            wait = max(reset - int(time.time()), 10)
            print(f'    Rate limited, waiting {wait}s...')
            time.sleep(wait + 1)
            continue
        if response.status_code in (422, 500, 502, 503):
            print(f'    Error {response.status_code}, stopping')
            return None
        if response.status_code != 200:
            print(f'    Error: {response.status_code} - {response.text[:200]}')
            return None

        return response.json()


def _get_total_count(query, search_type):
    """Get total_count for a query without fetching items."""
    if search_type == 'commits':
        url = 'https://api.github.com/search/commits'
        headers = {**HEADERS, 'Accept': 'application/vnd.github.cloak-preview+json'}
    else:
        url = 'https://api.github.com/search/issues'
        headers = HEADERS

    params = {'q': query, 'per_page': 1, 'page': 1}
    data = _api_request(url, headers, params)
    time.sleep(REQUEST_DELAY)

    if data is None:
        return 0
    return data.get('total_count', 0)


def _fetch_paginated(query, search_type, max_pages=10):
    """Fetch all pages of a query (up to max_pages * 100 = 1000 items)."""
    if search_type == 'commits':
        url = 'https://api.github.com/search/commits'
        headers = {**HEADERS, 'Accept': 'application/vnd.github.cloak-preview+json'}
    else:
        url = 'https://api.github.com/search/issues'
        headers = HEADERS

    all_items = []
    page = 1

    while page <= max_pages:
        params = {'q': query, 'per_page': 100, 'page': page, 'sort': 'created', 'order': 'asc'}
        data = _api_request(url, headers, params)
        time.sleep(REQUEST_DELAY)

        if data is None:
            break

        items = data.get('items', [])
        if not items:
            break

        all_items.extend(items)
        if len(items) < 100:
            break
        page += 1

    return all_items


def search_with_splitting(query_base, date_field, date_str, search_type):
    """
    Smart fetching with hour-splitting when results exceed 1000.

    1. Count total results for the full day
    2. If <= 1000: fetch normally with pagination
    3. If > 1000: split into 6-hour blocks, then 1-hour if still > 1000
    4. Dedup by item id
    """
    # Full day query
    day_query = f'{query_base} {date_field}:{date_str}'
    total = _get_total_count(day_query, search_type)
    print(f'    Total count: {total:,}')

    if total == 0:
        return []

    if total <= 1000:
        print(f'    Fetching directly (≤1000)')
        return _fetch_paginated(day_query, search_type)

    # Hour-splitting needed
    print(f'    Splitting by hours (>{1000} results)')
    all_items = {}  # id -> item for dedup

    # Try 6-hour blocks first
    hour_blocks = [(0, 6), (6, 12), (12, 18), (18, 24)]

    for start_h, end_h in hour_blocks:
        start_time = f'{date_str}T{start_h:02d}:00:00Z'
        end_time = f'{date_str}T{end_h:02d}:00:00Z' if end_h < 24 else f'{date_str}T23:59:59Z'
        block_query = f'{query_base} {date_field}:{start_time}..{end_time}'

        block_total = _get_total_count(block_query, search_type)
        print(f'    Block {start_h:02d}-{end_h:02d}: {block_total:,} results')

        if block_total == 0:
            continue

        if block_total <= 1000:
            items = _fetch_paginated(block_query, search_type)
            for item in items:
                item_id = item.get('node_id') or item.get('id') or id(item)
                all_items[item_id] = item
        else:
            # Split further into individual hours
            print(f'    Sub-splitting block {start_h:02d}-{end_h:02d} into hours')
            for hour in range(start_h, end_h):
                h_start = f'{date_str}T{hour:02d}:00:00Z'
                h_end = f'{date_str}T{hour:02d}:59:59Z'
                h_query = f'{query_base} {date_field}:{h_start}..{h_end}'

                h_total = _get_total_count(h_query, search_type)
                if h_total == 0:
                    continue
                if h_total > 1000:
                    print(f'      Hour {hour:02d}: {h_total:,} (capped at 1000)')
                else:
                    print(f'      Hour {hour:02d}: {h_total:,}')

                items = _fetch_paginated(h_query, search_type)
                for item in items:
                    item_id = item.get('node_id') or item.get('id') or id(item)
                    all_items[item_id] = item

    print(f'    Total unique items after dedup: {len(all_items):,}')
    return list(all_items.values())


def extract_repos_from_commits(items):
    repos = {}
    for item in items:
        repo_info = item.get('repository', {})
        nwo = repo_info.get('full_name', '')
        if nwo and nwo not in repos:
            repos[nwo] = {
                'full_name': nwo,
                'name': nwo.split('/')[-1],
                'description': repo_info.get('description') or '',
            }
    return repos


def extract_repos_from_prs(items):
    repos = {}
    for item in items:
        repo_url = item.get('repository_url', '')
        nwo = repo_url.split('/repos/')[-1] if '/repos/' in repo_url else ''
        if not nwo:
            html = item.get('html_url', '')
            parts = html.replace('https://github.com/', '').split('/')
            nwo = f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else ''
        if nwo and nwo not in repos:
            repos[nwo] = {
                'full_name': nwo,
                'name': nwo.split('/')[-1],
                'description': '',
            }
    return repos


def main():
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

    print(f'Fetching data for {yesterday}...\n')

    results = {}

    for agent_id, config in AGENTS.items():
        print(f'=== {agent_id} ===')

        items = search_with_splitting(
            config['query_base'],
            config['date_field'],
            yesterday,
            config['search_type']
        )
        print(f'  Found {len(items)} items')

        if config['search_type'] == 'commits':
            repos = extract_repos_from_commits(items)
        else:
            repos = extract_repos_from_prs(items)

        results[agent_id] = {
            'date': yesterday,
            'item_count': len(items),
            'repo_count': len(repos),
            'repos': list(repos.values())
        }
        print(f'  Unique repos: {len(repos)}\n')

    output_file = OUTPUT_DIR / f'{yesterday}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f)

    print(f'Saved to {output_file}')
    for agent_id, data in results.items():
        print(f'  {agent_id}: {data["repo_count"]} repos ({data["item_count"]} items)')


if __name__ == '__main__':
    main()
