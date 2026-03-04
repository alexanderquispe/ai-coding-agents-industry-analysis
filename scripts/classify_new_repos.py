#!/usr/bin/env python3
"""
Classify new repositories using the NAICS classifier via HF Inference API.
Uses batched HTTP requests (no torch/transformers needed).
Public model: aquiro1994/naics-github-classifier
Automatically finds ALL unclassified daily files.
"""

import json
import time
import requests
from pathlib import Path

DEDUP_FILE = Path('data/classified_repos.txt')
DAILY_DIR = Path('data/daily')

HF_API_URL = 'https://api-inference.huggingface.co/models/aquiro1994/naics-github-classifier'
BATCH_SIZE = 32
MAX_RETRIES = 3
RETRY_DELAY = 20  # seconds (model cold start)


def load_classified_set():
    """Load set of already-classified repo full_names."""
    if not DEDUP_FILE.exists():
        return set()
    with open(DEDUP_FILE) as f:
        return set(line.strip() for line in f if line.strip())


def save_classified_set(classified_set):
    """Save updated set of classified repos."""
    DEDUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DEDUP_FILE, 'w') as f:
        f.write('\n'.join(sorted(classified_set)) + '\n')


def get_repo_text(repo: dict) -> str:
    parts = []
    if repo.get('name'):
        parts.append(repo['name'])
    if repo.get('description'):
        parts.append(repo['description'])
    if repo.get('topics'):
        parts.append(' '.join(repo['topics']))
    return ' '.join(parts)[:200]


def classify_batch(texts: list[str]) -> list[dict]:
    """Classify a batch of texts via HF Inference API."""
    for attempt in range(MAX_RETRIES):
        response = requests.post(
            HF_API_URL,
            json={'inputs': texts},
            headers={'Content-Type': 'application/json'},
        )

        if response.status_code == 200:
            results = response.json()
            # HF returns [[{label, score}, ...], ...] for batch
            predictions = []
            for result in results:
                if isinstance(result, list):
                    best = max(result, key=lambda x: x['score'])
                    predictions.append(best)
                elif isinstance(result, dict):
                    predictions.append(result)
                else:
                    predictions.append({'label': '54', 'score': 0.0})
            return predictions

        if response.status_code == 503:
            wait = RETRY_DELAY * (attempt + 1)
            print(f'    Model loading, waiting {wait}s (attempt {attempt + 1}/{MAX_RETRIES})...')
            time.sleep(wait)
            continue

        print(f'    HF API error {response.status_code}: {response.text[:200]}')
        break

    return [{'label': '54', 'score': 0.0} for _ in texts]


def find_input_files():
    """Find ALL daily files that haven't been classified yet."""
    files = []
    for input_file in sorted(DAILY_DIR.glob('*.json')):
        name = input_file.stem
        if '_classified' in name:
            continue
        if len(name) != 10:  # YYYY-MM-DD
            continue
        output_file = DAILY_DIR / f'{name}_classified.json'
        if not output_file.exists():
            files.append((name, input_file, output_file))
    return files


def main():
    input_files = find_input_files()

    if not input_files:
        print('No unclassified input files found')
        return

    print(f'Found {len(input_files)} file(s) to classify: {", ".join(d for d, _, _ in input_files)}\n')

    # Load already-classified repos for dedup
    already_classified = load_classified_set()
    print(f'Already classified repos in history: {len(already_classified):,}')

    for date, input_file, output_file in input_files:
        print(f'\nProcessing {date}...')

        with open(input_file) as f:
            data = json.load(f)

        # Collect unique repos across all agents
        all_repos = {}
        repo_agents = {}
        for agent_id, agent_data in data.items():
            for repo in agent_data.get('repos', []):
                nwo = repo.get('full_name', '')
                if nwo:
                    all_repos[nwo] = repo
                    if nwo not in repo_agents:
                        repo_agents[nwo] = []
                    repo_agents[nwo].append(agent_id)

        # Filter out already-classified repos
        new_repos = {nwo: repo for nwo, repo in all_repos.items() if nwo not in already_classified}
        skipped = len(all_repos) - len(new_repos)

        if skipped > 0:
            print(f'Skipping {skipped} already-classified repos')

        if not new_repos:
            print('No new repos to classify')
            with open(output_file, 'w') as f:
                json.dump([], f)
            continue

        print(f'Classifying {len(new_repos)} new repositories...')

        # Prepare texts for batch classification
        repo_list = []
        texts = []
        for nwo, repo in new_repos.items():
            text = get_repo_text(repo)
            if text.strip():
                repo_list.append((nwo, repo))
                texts.append(text)

        # Batch classify via HF Inference API
        all_predictions = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            predictions = classify_batch(batch)
            all_predictions.extend(predictions)

            if (i + BATCH_SIZE) % (BATCH_SIZE * 10) == 0 and i > 0:
                print(f'  Classified {min(i + BATCH_SIZE, len(texts))}/{len(texts)}')

        # Build output
        classified = []
        new_classified_names = set()
        for idx, (nwo, repo) in enumerate(repo_list):
            if idx < len(all_predictions):
                pred = all_predictions[idx]
                classified.append({
                    'full_name': nwo,
                    'naics_code': pred['label'],
                    'confidence': round(pred['score'], 4),
                    'agents': sorted(repo_agents.get(nwo, []))
                })
                new_classified_names.add(nwo)

        # Update dedup file
        already_classified.update(new_classified_names)
        save_classified_set(already_classified)

        with open(output_file, 'w') as f:
            json.dump(classified, f, indent=2)

        print(f'Classified {len(classified)} repos')
        print(f'Total classified repos in history: {len(already_classified):,}')

        for agent_id in data.keys():
            count = sum(1 for c in classified if agent_id in c.get('agents', []))
            print(f'  {agent_id}: {count} classified')


if __name__ == '__main__':
    main()
