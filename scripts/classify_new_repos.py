#!/usr/bin/env python3
"""
Classify new repositories using the NAICS classifier.
Uses batch inference (batch_size=32) and dedup against historical classified repos.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEDUP_FILE = Path('data/classified_repos.txt')
DAILY_DIR = Path('data/daily')


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


def load_classifier():
    from transformers import pipeline
    token = os.environ.get('HF_TOKEN') or None
    return pipeline(
        'text-classification',
        model='aquiro1994/naics-github-classifier',
        device=-1,  # CPU
        token=token,
        truncation=True,
        max_length=512,
    )


def get_repo_text(repo: dict) -> str:
    parts = []
    if repo.get('name'):
        parts.append(repo['name'])
    if repo.get('description'):
        parts.append(repo['description'])
    if repo.get('topics'):
        parts.append(' '.join(repo['topics']))
    return ' '.join(parts)[:200]


def main():
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
    input_file = DAILY_DIR / f'{yesterday}.json'
    output_file = DAILY_DIR / f'{yesterday}_classified.json'

    if not input_file.exists():
        print(f'No input file found: {input_file}')
        return

    with open(input_file) as f:
        data = json.load(f)

    # Load already-classified repos for dedup
    already_classified = load_classified_set()
    print(f'Already classified repos in history: {len(already_classified):,}')

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
        # Still output the file (empty) so update_data.py doesn't fail
        # But include already-known repos with their previous classifications
        with open(output_file, 'w') as f:
            json.dump([], f)
        return

    print(f'Classifying {len(new_repos)} new repositories (batch_size=32)...')

    classifier = load_classifier()

    # Prepare texts for batch classification
    repo_list = []
    texts = []
    for nwo, repo in new_repos.items():
        text = get_repo_text(repo)
        if text.strip():
            repo_list.append((nwo, repo))
            texts.append(text)

    # Batch classify
    BATCH_SIZE = 32
    all_predictions = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        try:
            predictions = classifier(batch)
            all_predictions.extend(predictions)
        except Exception as e:
            print(f'  Error on batch {i // BATCH_SIZE}: {e}')
            # Fall back to one-by-one for this batch
            for text in batch:
                try:
                    pred = classifier(text)[0]
                    all_predictions.append(pred)
                except Exception:
                    all_predictions.append({'label': '54', 'score': 0.0})

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
