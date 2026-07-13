#!/usr/bin/env python3
"""
Fetch repository metadata for AI coding agent commits/PRs.

Reads parquet files from fetch_bulk.py, extracts unique repos,
fetches 33 columns of metadata using GraphQL batched queries.

Usage:
    export GH_TOKENS=ghp_aaa,ghp_bbb,ghp_ccc
    python fetch_repo_metadata.py --input output/claude_commits.parquet
    python fetch_repo_metadata.py --input output/cursor_commits.parquet output/cursor_prs.parquet
"""

import argparse
import json
import os
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
import requests
from tqdm.auto import tqdm


# ══════════════════════════════════════════════════════════════
# Config
# ══════════════════════════════════════════════════════════════
BATCH_SIZE = 50  # GraphQL repos per query
SAVE_EVERY = 500  # Checkpoint every N repos
GRAPHQL_URL = "https://api.github.com/graphql"


# ══════════════════════════════════════════════════════════════
# GraphQL Query Template
# ══════════════════════════════════════════════════════════════
REPO_FRAGMENT = """
fragment RepoFields on Repository {
    nameWithOwner
    name
    description
    url
    homepageUrl
    createdAt
    updatedAt
    pushedAt
    stargazerCount
    forkCount
    watchers { totalCount }
    issues(states: OPEN) { totalCount }
    diskUsage
    primaryLanguage { name }
    languages(first: 10) { nodes { name } }
    repositoryTopics(first: 20) { nodes { topic { name } } }
    isFork
    isArchived
    isPrivate
    isTemplate
    hasWikiEnabled
    hasIssuesEnabled
    licenseInfo { key name }
    owner {
        login
        ... on User {
            __typename
            location
            company
            bio
            email
            followers { totalCount }
            createdAt
        }
        ... on Organization {
            __typename
            location
            description
            email
            membersWithRole { totalCount }
            createdAt
        }
    }
    README_md: object(expression: "HEAD:README.md") { ... on Blob { text } }
    README: object(expression: "HEAD:README") { ... on Blob { text } }
    readme_lower: object(expression: "HEAD:readme.md") { ... on Blob { text } }
}
"""

REPO_FRAGMENT_NO_README = """
fragment RepoFields on Repository {
    nameWithOwner
    name
    description
    url
    homepageUrl
    createdAt
    updatedAt
    pushedAt
    stargazerCount
    forkCount
    watchers { totalCount }
    issues(states: OPEN) { totalCount }
    diskUsage
    primaryLanguage { name }
    languages(first: 10) { nodes { name } }
    repositoryTopics(first: 20) { nodes { topic { name } } }
    isFork
    isArchived
    isPrivate
    isTemplate
    hasWikiEnabled
    hasIssuesEnabled
    licenseInfo { key name }
    owner {
        login
        ... on User {
            __typename
            location
            company
            bio
            email
            followers { totalCount }
            createdAt
        }
        ... on Organization {
            __typename
            location
            description
            email
            membersWithRole { totalCount }
            createdAt
        }
    }
}
"""


def build_batch_query(nwos: List[str], include_readme: bool = True) -> str:
    """Build a GraphQL query for multiple repos."""
    fragment = REPO_FRAGMENT if include_readme else REPO_FRAGMENT_NO_README
    queries = []
    for i, nwo in enumerate(nwos):
        owner, name = nwo.split("/", 1)
        # Sanitize for GraphQL alias (alphanumeric + underscore only)
        alias = f"repo_{i}"
        queries.append(f'{alias}: repository(owner: "{owner}", name: "{name}") {{ ...RepoFields }}')

    return f"""
{fragment}
query {{
    {chr(10).join(queries)}
}}
"""


# ══════════════════════════════════════════════════════════════
# Exponential backoff
# ══════════════════════════════════════════════════════════════
def exponential_backoff(max_retries=3, base_delay=2.0, max_delay=60.0,
                        exponential_base=2.0, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    print(f"  Retry {attempt+1}/{max_retries} after {delay:.1f}s: {str(e)[:100]}")
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════
# Multi-Token GraphQL Client
# ══════════════════════════════════════════════════════════════
class MultiTokenGraphQLClient:
    def __init__(self, tokens: List[str]):
        self.clients = []
        for token in tokens:
            session = requests.Session()
            session.headers.update({
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            })
            self.clients.append({
                "session": session,
                "rate_limit_remaining": None,
                "rate_limit_reset": None,
            })
        self._idx = 0
        self._total_requests = 0
        print(f"  {len(tokens)} tokens available for GraphQL")

    def _next_client(self):
        client = self.clients[self._idx]
        self._idx = (self._idx + 1) % len(self.clients)
        return client

    def _wait_if_rate_limited(self, client):
        if client["rate_limit_remaining"] is not None and client["rate_limit_remaining"] < 100:
            if client["rate_limit_reset"]:
                wait_time = (client["rate_limit_reset"] - datetime.now()).total_seconds()
                if wait_time > 0:
                    print(f"  Token {self._idx}: Rate limit low. Waiting {wait_time:.0f}s...")
                    time.sleep(wait_time + 5)

    def _update_rate_limit(self, client, headers):
        if "X-RateLimit-Remaining" in headers:
            client["rate_limit_remaining"] = int(headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in headers:
            client["rate_limit_reset"] = datetime.fromtimestamp(
                int(headers["X-RateLimit-Reset"])
            )

    @exponential_backoff(max_retries=3, base_delay=2.0,
                         exceptions=(requests.exceptions.RequestException,))
    def query(self, graphql_query: str) -> dict:
        client = self._next_client()
        self._wait_if_rate_limited(client)

        self._total_requests += 1
        response = client["session"].post(
            GRAPHQL_URL,
            json={"query": graphql_query}
        )
        self._update_rate_limit(client, response.headers)

        if response.status_code == 403:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                time.sleep(int(retry_after))
                return self.query(graphql_query)
            if "secondary rate limit" in response.text.lower():
                print("  Secondary rate limit. Waiting 60s...")
                time.sleep(60)
                return self.query(graphql_query)

        response.raise_for_status()
        return response.json()

    def get_stats(self) -> str:
        return f"Total GraphQL calls: {self._total_requests}"


# ══════════════════════════════════════════════════════════════
# Extract metadata from GraphQL response
# ══════════════════════════════════════════════════════════════
def extract_repo_metadata(data: dict, include_readme: bool = True) -> Optional[Dict]:
    """Extract 33 columns of metadata from GraphQL repo response."""
    if data is None:
        return None

    # Basic info
    result = {
        "nwo": data.get("nameWithOwner", ""),
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "url": data.get("url", ""),
        "homepage_url": data.get("homepageUrl", ""),

        # Timestamps
        "created_at": data.get("createdAt", ""),
        "updated_at": data.get("updatedAt", ""),
        "pushed_at": data.get("pushedAt", ""),

        # Metrics
        "stars": data.get("stargazerCount", 0),
        "forks": data.get("forkCount", 0),
        "watchers": data.get("watchers", {}).get("totalCount", 0),
        "open_issues": data.get("issues", {}).get("totalCount", 0),
        "disk_usage_kb": data.get("diskUsage", 0),

        # Languages & Topics
        "primary_language": (data.get("primaryLanguage") or {}).get("name", ""),
        "languages": [n.get("name", "") for n in (data.get("languages", {}).get("nodes", []))],
        "topics": [n.get("topic", {}).get("name", "") for n in (data.get("repositoryTopics", {}).get("nodes", []))],

        # Flags
        "is_fork": data.get("isFork", False),
        "is_archived": data.get("isArchived", False),
        "is_private": data.get("isPrivate", False),
        "is_template": data.get("isTemplate", False),
        "has_wiki": data.get("hasWikiEnabled", False),
        "has_issues": data.get("hasIssuesEnabled", False),

        # License
        "license_key": (data.get("licenseInfo") or {}).get("key", ""),
        "license_name": (data.get("licenseInfo") or {}).get("name", ""),
    }

    # Owner info
    owner = data.get("owner", {}) or {}
    owner_type = owner.get("__typename", "")
    result.update({
        "owner_login": owner.get("login", ""),
        "owner_type": owner_type,
        "owner_location": owner.get("location", ""),
        "owner_company": owner.get("company", "") if owner_type == "User" else "",
        "owner_bio": owner.get("bio", "") if owner_type == "User" else owner.get("description", ""),
        "owner_email": owner.get("email", ""),
        "owner_followers": (
            owner.get("followers", {}).get("totalCount", 0) if owner_type == "User"
            else owner.get("membersWithRole", {}).get("totalCount", 0)
        ),
        "owner_created_at": owner.get("createdAt", ""),
    })

    # README content (try multiple locations)
    if include_readme:
        readme_content = ""
        for key in ["README_md", "README", "readme_lower"]:
            obj = data.get(key)
            if obj and isinstance(obj, dict) and obj.get("text"):
                readme_content = obj["text"]
                break
        result["readme_content"] = readme_content
    else:
        result["readme_content"] = ""

    return result


# ══════════════════════════════════════════════════════════════
# Checkpoint helpers
# ══════════════════════════════════════════════════════════════
def atomic_write_json(path: Path, data):
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)


def load_checkpoint(checkpoint_path: Path) -> Dict:
    """Load checkpoint with completed repos and results."""
    if checkpoint_path.exists():
        with open(checkpoint_path) as f:
            data = json.load(f)
        print(f"  Loaded checkpoint: {len(data.get('completed', []))} repos done")
        return data
    return {"completed": [], "results": []}


def save_checkpoint(checkpoint_path: Path, completed: List[str], results: List[Dict]):
    """Save checkpoint atomically."""
    atomic_write_json(checkpoint_path, {
        "completed": completed,
        "results": results,
        "saved_at": datetime.now().isoformat(),
    })


# ══════════════════════════════════════════════════════════════
# Main fetch logic
# ══════════════════════════════════════════════════════════════
def fetch_repo_metadata(
    client: MultiTokenGraphQLClient,
    nwos: List[str],
    checkpoint_path: Path,
    output_path: Path,
    include_readme: bool = True,
    dry_run: bool = False,
):
    """Fetch metadata for all repos with checkpoint/resume."""
    run_start = datetime.now()

    # Load checkpoint
    checkpoint = load_checkpoint(checkpoint_path)
    completed_set: Set[str] = set(checkpoint.get("completed", []))
    results: List[Dict] = checkpoint.get("results", [])

    # Filter out already completed
    pending = [nwo for nwo in nwos if nwo not in completed_set]

    print(f"\n{'=' * 60}")
    print(f"  REPO METADATA FETCH")
    print(f"  Total unique repos: {len(nwos):,}")
    print(f"  Already completed: {len(completed_set):,}")
    print(f"  Pending: {len(pending):,}")
    print(f"  Include README: {include_readme}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"{'=' * 60}")

    if dry_run:
        print("\n  DRY RUN - no requests will be made")
        return

    if not pending:
        print("  All repos already fetched!")
        return

    # Process in batches
    batches = [pending[i:i + BATCH_SIZE] for i in range(0, len(pending), BATCH_SIZE)]
    completed_list = list(completed_set)
    last_save = len(completed_list)
    errors = []

    with tqdm(total=len(pending), desc="Fetching", unit="repo") as pbar:
        for batch in batches:
            try:
                query = build_batch_query(batch, include_readme)
                response = client.query(query)

                if "errors" in response:
                    for err in response["errors"]:
                        print(f"\n  GraphQL error: {err.get('message', err)[:100]}")

                data = response.get("data", {})

                for i, nwo in enumerate(batch):
                    alias = f"repo_{i}"
                    repo_data = data.get(alias)

                    if repo_data:
                        metadata = extract_repo_metadata(repo_data, include_readme)
                        if metadata:
                            results.append(metadata)
                    else:
                        # Repo might be deleted, private, or renamed
                        errors.append({"nwo": nwo, "error": "not_found"})

                    completed_list.append(nwo)
                    pbar.update(1)

                # Checkpoint every SAVE_EVERY repos
                if len(completed_list) - last_save >= SAVE_EVERY:
                    save_checkpoint(checkpoint_path, completed_list, results)
                    last_save = len(completed_list)
                    elapsed = (datetime.now() - run_start).total_seconds()
                    rate = len(completed_list) / elapsed * 3600 if elapsed > 0 else 0
                    print(f"\n  Checkpoint: {len(results):,} repos | Rate: {rate:,.0f}/h")

            except Exception as e:
                print(f"\n  Batch error: {e}")
                # Still save progress
                save_checkpoint(checkpoint_path, completed_list, results)
                raise

    # Final save
    save_checkpoint(checkpoint_path, completed_list, results)

    # Write outputs
    print(f"\n  Writing outputs...")

    # JSONL
    jsonl_path = output_path.with_suffix(".jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Parquet
    if results:
        df = pd.DataFrame(results)
        df.to_parquet(output_path, index=False)
        print(f"  Parquet: {output_path} ({len(df):,} rows, {len(df.columns)} cols)")

    # Summary
    elapsed = datetime.now() - run_start
    print(f"\n  DONE: {len(results):,} repos fetched")
    print(f"  Errors: {len(errors):,}")
    print(f"  Time: {str(elapsed).split('.')[0]}")
    print(f"  {client.get_stats()}")

    if errors:
        errors_path = output_path.with_name(output_path.stem + "_errors.json")
        with open(errors_path, "w") as f:
            json.dump(errors, f, indent=2)
        print(f"  Errors saved to: {errors_path}")


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="Fetch repository metadata from GitHub GraphQL API"
    )
    parser.add_argument(
        "--input", "-i",
        nargs="+",
        required=True,
        help="Input parquet file(s) with repo_nwo column"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output parquet path (default: output/<input_stem>_repos_metadata.parquet)"
    )
    parser.add_argument(
        "--checkpoint-dir",
        default="checkpoints",
        help="Checkpoint directory (default: checkpoints)"
    )
    parser.add_argument(
        "--no-readme",
        action="store_true",
        help="Skip fetching README content (faster, smaller output)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show plan without making requests"
    )
    args = parser.parse_args()

    # Load tokens
    tokens_str = os.environ.get("GH_TOKENS", "")
    if tokens_str:
        tokens = [t.strip() for t in tokens_str.split(",") if t.strip()]
    else:
        single = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not single:
            raise RuntimeError("Set GH_TOKENS (comma-separated) or GH_TOKEN env var")
        tokens = [single]

    # Collect unique repos from all input files
    all_nwos = set()
    for input_path in args.input:
        path = Path(input_path)
        if not path.exists():
            print(f"Warning: {path} not found, skipping")
            continue

        df = pd.read_parquet(path)
        if "repo_nwo" not in df.columns:
            print(f"Warning: {path} has no 'repo_nwo' column, skipping")
            continue

        nwos = df["repo_nwo"].dropna().unique()
        all_nwos.update(nwos)
        print(f"  Loaded {len(nwos):,} unique repos from {path.name}")

    if not all_nwos:
        print("No repos found in input files")
        return

    nwos_list = sorted(all_nwos)
    print(f"  Total unique repos across all inputs: {len(nwos_list):,}")

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Use first input stem for naming
        first_input = Path(args.input[0])
        stem = first_input.stem.replace("_commits", "").replace("_prs", "")
        output_path = first_input.parent / f"{stem}_repos_metadata.parquet"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Checkpoint path
    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / f"repo_metadata_{output_path.stem}.json"

    # Create client and fetch
    client = MultiTokenGraphQLClient(tokens)
    fetch_repo_metadata(
        client=client,
        nwos=nwos_list,
        checkpoint_path=checkpoint_path,
        output_path=output_path,
        include_readme=not args.no_readme,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
