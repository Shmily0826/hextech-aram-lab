"""check_wr_format.py - Check win_rate format consistency."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'augments.json'), 'r', encoding='utf-8') as f:
    augs = json.load(f)

active = [a for a in augs if a.get('status') == 'active' and a.get('win_rate')]

# Split into > 1 (percentage) and <= 1 (decimal)
pct_fmt = [(a['id'], a['win_rate']) for a in active if a['win_rate'] > 1]
dec_fmt = [(a['id'], a['win_rate']) for a in active if a['win_rate'] <= 1]

print(f'Percentage format (>1): {len(pct_fmt)} entries')
print(f'  Sample: {pct_fmt[:5]}')
print(f'  Range: {min(x[1] for x in pct_fmt):.2f} - {max(x[1] for x in pct_fmt):.2f}')

print(f'\nDecimal format (<=1): {len(dec_fmt)} entries')
print(f'  All: {dec_fmt}')

# Check if there are exactly 5 decimal format ones (the ones we just added)
dec_ids = [x[0] for x in dec_fmt]
print(f'\nDecimal IDs: {dec_ids}')
