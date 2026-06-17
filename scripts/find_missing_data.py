"""find_missing_data.py - List augments missing key fields."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

active = [a for a in augs if a.get('status') == 'active']

print('=== Missing effect ===')
for a in active:
    if not a.get('effect'):
        print(f'  {a["id"]}: {a["name"]} [{a["tier"]}]')

print('\n=== Missing effect_en ===')
for a in active:
    if not a.get('effect_en'):
        print(f'  {a["id"]}: {a["name"]} [{a["tier"]}]')

print('\n=== Missing win_rate ===')
for a in active:
    if not a.get('win_rate'):
        print(f'  {a["id"]}: {a["name"]} [{a["tier"]}] rank={a.get("site_rank","-")}')

print('\n=== Missing tags ===')
for a in active:
    if not a.get('tags'):
        print(f'  {a["id"]}: {a["name"]} [{a["tier"]}]')
