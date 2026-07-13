#!/usr/bin/env python3
"""
Bulk fetch of PRs/commits from GitHub API for all AI coding agents.
Multi-token rotation, recursive date-splitting, checkpoint/resume.

Usage:
    export GH_TOKENS=ghp_aaa,ghp_bbb,ghp_ccc
    python fetch_bulk.py --agent claude --start 2026-01-01 --end 2026-03-11
"""

import argparse
import json
import os
import re
import time
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import List, Set

import pandas as pd
import requests
from tqdm.auto import tqdm


# ══════════════════════════════════════════════════════════════
# Config
# ══════════════════════════════════════════════════════════════
SAVE_EVERY = 1000

AGENTS = {
    "claude": {
        "search_url": "https://api.github.com/search/commits",
        "search_query": '"Co-Authored-By" "noreply@anthropic.com"',
        "date_field": "committer-date",
        "sort_field": "committer-date",
        "key_field": "sha",
        "extract_fn": "extract_commit",
        "output_file": "claude_commits",
    },
    "copilot": {
        "search_url": "https://api.github.com/search/issues",
        "search_query": "is:pr head:copilot",
        "date_field": "created",
        "sort_field": "created",
        "key_field": "pr_id",
        "extract_fn": "extract_pr",
        "output_file": "copilot_prs",
    },
    "codex": {
        "search_url": "https://api.github.com/search/issues",
        "search_query": "is:pr head:codex",
        "date_field": "created",
        "sort_field": "created",
        "key_field": "pr_id",
        "extract_fn": "extract_pr",
        "output_file": "codex_prs",
    },
    "cursor": {
        "search_url": "https://api.github.com/search/issues",
        "search_query": "is:pr head:cursor",
        "date_field": "created",
        "sort_field": "created",
        "key_field": "pr_id",
        "extract_fn": "extract_pr",
        "output_file": "cursor_prs",
    },
    "jules": {
        "search_url": "https://api.github.com/search/commits",
        "search_query": "author:google-labs-jules[bot]",
        "date_field": "committer-date",
        "sort_field": "committer-date",
        "key_field": "sha",
        "extract_fn": "extract_jules_commit",
        "output_file": "jules_commits",
    },
    "cursor_commits": {
        "search_url": "https://api.github.com/search/commits",
        "search_query": '"Co-authored-by" "cursoragent@cursor.com"',
        "date_field": "committer-date",
        "sort_field": "committer-date",
        "key_field": "sha",
        "extract_fn": "extract_commit",
        "output_file": "cursor_commits",
    },
    "copilot_commits": {
        "search_url": "https://api.github.com/search/commits",
        "search_query": '"Co-authored-by" "copilot"',
        "date_field": "committer-date",
        "sort_field": "committer-date",
        "key_field": "sha",
        "extract_fn": "extract_commit",
        "output_file": "copilot_commits",
    },
    "codex_commits": {
        "search_url": "https://api.github.com/search/commits",
        "search_query": '"Co-authored-by: Codex"',
        "date_field": "committer-date",
        "sort_field": "committer-date",
        "key_field": "sha",
        "extract_fn": "extract_commit",
        "output_file": "codex_commits",
    },
}


def elapsed_str(start):
    secs = (datetime.now() - start).total_seconds()
    h, m = int(secs // 3600), int((secs % 3600) // 60)
    return f"{h}h{m:02d}m" if h > 0 else f"{m}m{int(secs % 60):02d}s"


# ══════════════════════════════════════════════════════════════
# Exponential backoff (from rest_client.py)
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
# Multi-Token Client
# ══════════════════════════════════════════════════════════════
class MultiTokenClient:
    SEARCH_RATE_LIMIT = 30
    SEARCH_RATE_WINDOW = 60

    def __init__(self, tokens: List[str], search_url: str):
        self.search_url = search_url
        self.clients = []
        for token in tokens:
            session = requests.Session()
            session.headers.update({
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            })
            self.clients.append({
                "session": session,
                "search_requests": [],
                "rate_limit_remaining": None,
                "rate_limit_reset": None,
            })
        self._idx = 0
        self._total_requests = 0
        print(f"  {len(tokens)} tokens -> {len(tokens) * self.SEARCH_RATE_LIMIT} req/min max")

    def _next_client(self):
        client = self.clients[self._idx]
        self._idx = (self._idx + 1) % len(self.clients)
        return client

    def _wait_for_rate_limit(self, client):
        now = time.time()
        window_start = now - self.SEARCH_RATE_WINDOW
        client["search_requests"] = [t for t in client["search_requests"] if t > window_start]
        if len(client["search_requests"]) >= self.SEARCH_RATE_LIMIT:
            oldest = min(client["search_requests"])
            wait_time = oldest + self.SEARCH_RATE_WINDOW - now + 1
            if wait_time > 0:
                print(f"  Token {self._idx}: rate limit. Waiting {wait_time:.0f}s...")
                time.sleep(wait_time)
        if client["rate_limit_remaining"] is not None and client["rate_limit_remaining"] < 5:
            if client["rate_limit_reset"]:
                wait_time = (client["rate_limit_reset"] - datetime.now()).total_seconds()
                if wait_time > 0:
                    print(f"  Token {self._idx}: GitHub limit low. Waiting {wait_time:.0f}s...")
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
    def search(self, query, sort="created", order="desc", per_page=100, page=1):
        client = self._next_client()
        self._wait_for_rate_limit(client)
        params = {
            "q": query, "sort": sort, "order": order,
            "per_page": min(per_page, 100), "page": page,
        }
        client["search_requests"].append(time.time())
        self._total_requests += 1
        response = client["session"].get(self.search_url, params=params)
        self._update_rate_limit(client, response.headers)
        if response.status_code == 403:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                time.sleep(int(retry_after))
                return self.search(query, sort, order, per_page, page)
            if "secondary rate limit" in response.text.lower():
                print("  Secondary rate limit. Waiting 60s...")
                time.sleep(60)
                return self.search(query, sort, order, per_page, page)
        response.raise_for_status()
        return response.json()

    def get_count(self, query, sort="created"):
        result = self.search(query, sort=sort, per_page=1, page=1)
        return result.get("total_count", 0)

    def get_rate_info(self):
        now = time.time()
        total = sum(
            len([t for t in c["search_requests"] if t > now - self.SEARCH_RATE_WINDOW])
            for c in self.clients
        )
        cap = len(self.clients) * self.SEARCH_RATE_LIMIT
        return f"Requests this window: {total}/{cap} | Total API calls: {self._total_requests:,}"


# ══════════════════════════════════════════════════════════════
# Extract functions
# ══════════════════════════════════════════════════════════════
def extract_claude_model(msg):
    m = re.search(
        r'Co-Authored-By:\s*Claude\s*([^<]*)?<[^>]*@anthropic\.com>',
        msg, re.IGNORECASE,
    )
    if m:
        part = (m.group(1) or "").strip()
        return part if part else "Claude"
    return ""


def extract_commit(item):
    ci = item.get("commit", {})
    a = ci.get("author", {})
    c = ci.get("committer", {})
    r = item.get("repository", {})
    au = item.get("author", {}) or {}
    msg = ci.get("message", "")
    return {
        "sha": item.get("sha", ""),
        "repo_nwo": r.get("full_name", ""),
        "repo_url": r.get("html_url", ""),
        "commit_url": item.get("html_url", ""),
        "message": msg,
        "committed_date": c.get("date", ""),
        "authored_date": a.get("date", ""),
        "author_name": a.get("name", ""),
        "author_email": a.get("email", ""),
        "author_login": au.get("login", ""),
        "committer_name": c.get("name", ""),
        "committer_email": c.get("email", ""),
        "claude_model": extract_claude_model(msg),
    }


def extract_jules_commit(item):
    ci = item.get("commit", {})
    a = ci.get("author", {})
    c = ci.get("committer", {})
    r = item.get("repository", {})
    return {
        "sha": item.get("sha", ""),
        "repo_nwo": r.get("full_name", ""),
        "message": ci.get("message", ""),
        "author_name": a.get("name", ""),
        "author_email": a.get("email", ""),
        "author_date": a.get("date", ""),
        "committer_name": c.get("name", ""),
        "committer_email": c.get("email", ""),
        "committer_date": c.get("date", ""),
        "html_url": item.get("html_url", ""),
    }


def extract_pr(item):
    repo_url = item.get("repository_url", "")
    repo_nwo = repo_url.split("/repos/")[-1] if "/repos/" in repo_url else ""
    pri = item.get("pull_request", {})
    return {
        "pr_id": item.get("id"),
        "pr_number": item.get("number"),
        "pr_url": item.get("html_url", ""),
        "title": item.get("title", ""),
        "state": item.get("state", ""),
        "created_at": item.get("created_at", ""),
        "updated_at": item.get("updated_at", ""),
        "closed_at": item.get("closed_at"),
        "user_login": item.get("user", {}).get("login", ""),
        "repo_nwo": repo_nwo,
        "head_ref": "",
        "base_ref": "",
        "pr_api_url": pri.get("url", ""),
    }


EXTRACT_FNS = {
    "extract_commit": extract_commit,
    "extract_jules_commit": extract_jules_commit,
    "extract_pr": extract_pr,
}


# ══════════════════════════════════════════════════════════════
# Paginated search
# ══════════════════════════════════════════════════════════════
def paginated_search(client, query, sort_field, extract_fn, max_pages=10):
    items = []
    page = 1
    while page <= max_pages:
        try:
            result = client.search(query=query, sort=sort_field, per_page=100, page=page)
        except Exception as ex:
            print(f"\n  Error paginated (page {page}): {ex}")
            break
        page_items = result.get("items", [])
        if not page_items:
            break
        items.extend([extract_fn(i) for i in page_items])
        if page * 100 >= result.get("total_count", 0):
            break
        page += 1
    return items


# ══════════════════════════════════════════════════════════════
# Checkpoint helpers
# ══════════════════════════════════════════════════════════════
def atomic_write_json(path, data):
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)  # replace() works on Windows (overwrites existing)


def atomic_write_text(path, lines):
    tmp = path.with_suffix(".txt.tmp")
    with open(tmp, "w") as f:
        for line in lines:
            f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())
    tmp.replace(path)  # replace() works on Windows (overwrites existing)


def load_seen_keys(checkpoint_dir: Path, agent_key: str) -> Set[str]:
    seen = set()
    sha_file = checkpoint_dir / f"seen_keys_{agent_key}.txt"
    if sha_file.exists():
        with open(sha_file) as f:
            for line in f:
                k = line.strip()
                if k:
                    seen.add(k)
        print(f"  KEYS LOADED: {len(seen):,} from {sha_file.name}")
    return seen


def load_manifest(checkpoint_dir: Path, agent_key: str) -> dict:
    mf = checkpoint_dir / f"manifest_{agent_key}.json"
    if mf.exists():
        with open(mf) as f:
            data = json.load(f)
        complete = sum(1 for v in data.values() if v.get("status") == "complete")
        partial = sum(1 for v in data.values() if v.get("status") == "partial")
        print(f"  MANIFEST: {len(data)} days ({complete} complete, {partial} partial)")
        return data
    return {}


# ══════════════════════════════════════════════════════════════
# Main fetch with recursive date-splitting
# ══════════════════════════════════════════════════════════════
def fetch_agent(client, agent_cfg, start_date, end_date,
                output_dir, checkpoint_dir, agent_name):

    run_start = datetime.now()
    run_id = f"v{run_start.strftime('%Y%m%d_%H%M')}"
    last_hourly_log = run_start

    search_query = agent_cfg["search_query"]
    date_field = agent_cfg["date_field"]
    sort_field = agent_cfg["sort_field"]
    key_field = agent_cfg["key_field"]
    extract_fn = EXTRACT_FNS[agent_cfg["extract_fn"]]
    output_file = agent_cfg["output_file"]
    agent_key = agent_name.capitalize()

    seen_keys = load_seen_keys(checkpoint_dir, agent_key)
    initial_keys = len(seen_keys)
    manifest = load_manifest(checkpoint_dir, agent_key)

    new_results = []
    last_save_count = 0
    days_completed_this_run = []
    skip_count = sum(1 for v in manifest.values() if v.get("status") == "complete")

    print(f"\n{'=' * 60}")
    print(f"  FETCHING: {agent_name.upper()} (run {run_id})")
    print(f"  Query: {search_query}")
    print(f"  Range: {start_date} to {end_date}")
    print(f"  Known keys: {initial_keys:,}")
    print(f"  Days complete (SKIP): {skip_count}")
    partial_days = [d for d, v in manifest.items() if v.get("status") == "partial"]
    if partial_days:
        print(f"  Days partial (re-scan): {partial_days}")
    print(f"{'=' * 60}")

    total_days = (end_date - start_date).days + 1
    ranges = []
    current_day = start_date
    while current_day <= end_date:
        s = datetime.combine(current_day, datetime.min.time())
        e = datetime.combine(current_day, datetime.max.time().replace(microsecond=0))
        ranges.append((s, e, False))
        current_day += timedelta(days=1)

    print(f"  Total days: {total_days}, to process: {total_days - skip_count}")

    label = "commits" if "commit" in sort_field else "PRs"
    current_processing_day = None
    day_start_time = None
    day_new_count = 0

    def save_checkpoint():
        jsonl_path = output_dir / f"{output_file}.jsonl"
        tmp = jsonl_path.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            for item in new_results:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(jsonl_path)  # replace() works on Windows
        try:
            pd.DataFrame(new_results).to_parquet(
                output_dir / f"{output_file}.parquet", index=False
            )
        except Exception as ex:
            print(f"  Warning parquet: {ex}")
        atomic_write_text(checkpoint_dir / f"seen_keys_{agent_key}.txt", list(seen_keys))
        atomic_write_json(checkpoint_dir / f"manifest_{agent_key}.json", manifest)
        size_mb = jsonl_path.stat().st_size / 1024 / 1024
        print(f"  Saved: {len(new_results):,} new items ({size_mb:.1f} MB)")

    def finalize_day(day_str, new_count):
        if day_str not in manifest:
            manifest[day_str] = {}
        prev = manifest[day_str].get("items", 0)
        manifest[day_str].update({
            "status": "complete",
            "items": prev + new_count,
            "reviewed": manifest[day_str].get("reviewed", False),
            "run": run_id,
            "completed_at": datetime.now().isoformat(),
        })
        atomic_write_json(checkpoint_dir / f"manifest_{agent_key}.json", manifest)

    with tqdm(desc=agent_name, unit=label[:2]) as pbar:
        while ranges:
            s, e, is_time_range = ranges.pop(0)

            if not is_time_range:
                day_str = str(s.date())
                day_info = manifest.get(day_str, {})
                day_status = day_info.get("status", "pending")

                if current_processing_day and current_processing_day != day_str:
                    el = elapsed_str(day_start_time)
                    print(f"  [{elapsed_str(run_start)}] Day {current_processing_day} COMPLETE: +{day_new_count:,} new ({el})")
                    finalize_day(current_processing_day, day_new_count)
                    days_completed_this_run.append(current_processing_day)

                if day_status == "complete":
                    pbar.set_description(f"{agent_name} {day_str} SKIP")
                    continue

                current_processing_day = day_str
                day_start_time = datetime.now()
                day_new_count = 0

                manifest[day_str] = {
                    "status": "partial",
                    "items": day_info.get("items", 0),
                    "reviewed": day_info.get("reviewed", False),
                    "run": run_id,
                }
                atomic_write_json(checkpoint_dir / f"manifest_{agent_key}.json", manifest)

                if day_status == "partial":
                    pbar.set_description(f"{agent_name} {day_str} (resuming)")
                    print(f"  [{elapsed_str(run_start)}] Day {day_str} RESUMING (was partial)")
                else:
                    pbar.set_description(f"{agent_name} {day_str}")

            if is_time_range:
                date_filter = f"{date_field}:{s.isoformat()}..{e.isoformat()}"
            else:
                date_filter = f"{date_field}:{s.date()}..{e.date()}"
            query = f"{search_query} {date_filter}"

            count = None
            for retry in range(3):
                try:
                    count = client.get_count(query, sort=sort_field)
                    break
                except Exception as ex:
                    if retry < 2:
                        time.sleep(5 * (retry + 1))
                    else:
                        ranges.append((s, e, is_time_range))

            if count is None or count == 0:
                continue

            if count <= 1000:
                if is_time_range:
                    pbar.set_description(f"{agent_name} {s.date()} {s.hour:02d}:{s.minute:02d} ({count:,})")
                items = paginated_search(client, query, sort_field, extract_fn)
                for item in items:
                    key = item[key_field]
                    if key not in seen_keys:
                        seen_keys.add(key)
                        new_results.append(item)
                        day_new_count += 1
                        pbar.update(1)
                if len(new_results) - last_save_count >= SAVE_EVERY:
                    save_checkpoint()
                    last_save_count = len(new_results)
                    total = initial_keys + len(new_results)
                    rate = len(new_results) / max((datetime.now() - run_start).total_seconds(), 1) * 3600
                    print(f"  [{elapsed_str(run_start)}] Total: {total:,} | New: +{len(new_results):,} | Rate: {rate:,.0f}/h")
                if (datetime.now() - last_hourly_log).total_seconds() >= 3600:
                    print(f"\n  {'=' * 50}")
                    print(f"  HOURLY REPORT [{elapsed_str(run_start)}]")
                    print(f"  New: +{len(new_results):,} | Total: {initial_keys + len(new_results):,}")
                    print(f"  Day: {current_processing_day} | Days done: {len(days_completed_this_run)}")
                    print(f"  {client.get_rate_info()}")
                    print(f"  {'=' * 50}\n")
                    last_hourly_log = datetime.now()
            else:
                if not is_time_range:
                    days = (e.date() - s.date()).days
                    if days > 0:
                        mid_date = s.date() + timedelta(days=days // 2)
                        mid_dt = datetime.combine(mid_date, datetime.max.time().replace(microsecond=0))
                        next_dt = datetime.combine(mid_date + timedelta(days=1), datetime.min.time())
                        ranges.insert(0, (next_dt, e, False))
                        ranges.insert(0, (s, mid_dt, False))
                    else:
                        day_start_dt = datetime.combine(s.date(), datetime.min.time())
                        for hour_offset in [18, 12, 6, 0]:
                            interval_start = day_start_dt.replace(hour=hour_offset)
                            if hour_offset == 18:
                                interval_end = day_start_dt.replace(hour=23, minute=59, second=59)
                            else:
                                interval_end = day_start_dt.replace(hour=hour_offset + 5, minute=59, second=59)
                            ranges.insert(0, (interval_start, interval_end, True))
                else:
                    total_seconds = (e - s).total_seconds()
                    if total_seconds > 3600:
                        mid = s + timedelta(seconds=total_seconds / 2)
                        mid = mid.replace(second=0, microsecond=0)
                        ranges.insert(0, (mid, e, True))
                        ranges.insert(0, (s, mid - timedelta(seconds=1), True))
                    elif total_seconds > 600:
                        interval_mins = max(1, int(total_seconds / 60 / 6))
                        intervals = []
                        current = s
                        while current < e:
                            interval_end = min(current + timedelta(minutes=interval_mins) - timedelta(seconds=1), e)
                            intervals.append((current, interval_end, True))
                            current = interval_end + timedelta(seconds=1)
                        for interval in reversed(intervals):
                            ranges.insert(0, interval)
                    elif total_seconds > 60:
                        intervals = []
                        current = s
                        while current < e:
                            interval_end = min(current + timedelta(minutes=1) - timedelta(seconds=1), e)
                            intervals.append((current, interval_end, True))
                            current = interval_end + timedelta(seconds=1)
                        for interval in reversed(intervals):
                            ranges.insert(0, interval)
                    else:
                        if total_seconds > 10:
                            intervals = []
                            current = s
                            while current < e:
                                interval_end = min(current + timedelta(seconds=10) - timedelta(seconds=1), e)
                                intervals.append((current, interval_end, True))
                                current = interval_end + timedelta(seconds=1)
                            for interval in reversed(intervals):
                                ranges.insert(0, interval)
                        else:
                            pbar.set_description(f"{agent_name} {s.date()} {s.hour:02d}:{s.minute:02d}:{s.second:02d} (>1000, max)")
                            items = paginated_search(client, query, sort_field, extract_fn, max_pages=10)
                            for item in items:
                                key = item[key_field]
                                if key not in seen_keys:
                                    seen_keys.add(key)
                                    new_results.append(item)
                                    day_new_count += 1
                                    pbar.update(1)
                            if len(new_results) - last_save_count >= SAVE_EVERY:
                                save_checkpoint()
                                last_save_count = len(new_results)

    if current_processing_day and day_start_time:
        el = elapsed_str(day_start_time)
        print(f"  [{elapsed_str(run_start)}] Day {current_processing_day} COMPLETE: +{day_new_count:,} new ({el})")
        finalize_day(current_processing_day, day_new_count)
        days_completed_this_run.append(current_processing_day)

    save_checkpoint()

    total = initial_keys + len(new_results)
    summary = {
        "run": run_id, "agent": agent_name,
        "started_at": run_start.isoformat(),
        "ended_at": datetime.now().isoformat(),
        "elapsed": str(datetime.now() - run_start).split(".")[0],
        "days_completed": days_completed_this_run,
        "new_items": len(new_results), "total_items": total,
    }
    log_path = checkpoint_dir / f"run_log_{agent_key}.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(summary) + "\n")

    print(f"\n  DONE {agent_name.upper()}: {total:,} total (+{len(new_results):,} new)")
    print(f"  Time: {str(datetime.now() - run_start).split('.')[0]}")
    print(f"  Days completed: {len(days_completed_this_run)}")
    print(f"  {client.get_rate_info()}")
    return new_results


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="Bulk fetch GitHub data for AI coding agents"
    )
    parser.add_argument("--agent", required=True, choices=list(AGENTS.keys()))
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--checkpoint-dir", default="checkpoints")
    args = parser.parse_args()

    tokens_str = os.environ.get("GH_TOKENS", "")
    if tokens_str:
        tokens = [t.strip() for t in tokens_str.split(",") if t.strip()]
    else:
        single = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not single:
            raise RuntimeError("Set GH_TOKENS (comma-separated) or GH_TOKEN env var")
        tokens = [single]

    agent_cfg = AGENTS[args.agent]
    start_date = date.fromisoformat(args.start)
    end_date = date.fromisoformat(args.end)

    output_dir = Path(args.output_dir)
    checkpoint_dir = Path(args.checkpoint_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    client = MultiTokenClient(tokens, agent_cfg["search_url"])
    fetch_agent(client, agent_cfg, start_date, end_date,
                output_dir, checkpoint_dir, args.agent)


if __name__ == "__main__":
    main()
