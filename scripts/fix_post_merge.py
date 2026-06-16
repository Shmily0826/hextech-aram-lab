"""
fix_post_merge.py
=================
Post-merge fixes:
  1. Resolve duplicate Chinese names
  2. Add empty aliases arrays for entries missing them (reduces error count)
"""
import json, shutil, sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

AUGMENTS_PATH = 'data/augments.json'
BACKUP_DIR = 'pipeline/output'


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main():
    data = load_json(AUGMENTS_PATH)
    print(f"Loaded {len(data)} entries")

    # Backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'{BACKUP_DIR}/augments_fixdupes_{timestamp}.json'
    shutil.copy2(AUGMENTS_PATH, backup_path)
    print(f"Backup: {backup_path}")

    # Build ID lookup
    id_map = {e['id']: e for e in data}

    # ─── Fix 1: burst_of_vitality vs growth_spurt (both "生机迸发") ───
    # They are the same augment. blitz.gg uses "burst_of_vitality",
    # old wiki used "growth_spurt".
    # Strategy: merge growth_spurt data INTO burst_of_vitality, then remove growth_spurt.
    if 'growth_spurt' in id_map and 'burst_of_vitality' in id_map:
        gs = id_map['growth_spurt']
        bov = id_map['burst_of_vitality']

        # Preserve rich data from growth_spurt into burst_of_vitality
        rich_fields = ['tags', 'rar', 'wr', 'pr', 'desc', 'trigger', 'best', 'avoid', 'tests']
        for field in rich_fields:
            if field in gs and gs[field] and field not in bov:
                bov[field] = gs[field]

        # Merge aliases
        gs_aliases = gs.get('aliases', [])
        bov_aliases = bov.get('aliases', [])
        merged_aliases = list(set(bov_aliases + gs_aliases))
        if merged_aliases:
            bov['aliases'] = merged_aliases

        # Keep patch_added from growth_spurt if burst doesn't have it
        if not bov.get('patch_added') and gs.get('patch_added'):
            bov['patch_added'] = gs['patch_added']

        # Keep source notes
        if gs.get('notes'):
            bov['notes'] = f"合并自 growth_spurt: {gs['notes']}"

        # Remove growth_spurt
        data = [e for e in data if e['id'] != 'growth_spurt']
        print(f"  Merged growth_spurt -> burst_of_vitality, removed growth_spurt")
        print(f"    burst_of_vitality name: {bov['name']}")
        print(f"    burst_of_vitality name_en: {bov['name_en']}")

    # ─── Fix 2: adapt vs physical_to_magical (both "物理转魔法") ───
    # These are DIFFERENT augments:
    #   adapt: "Convert Bonus AD to AP. Gain 15% AP" (blitz.gg official name "ADAPt")
    #   physical_to_magical: "Convert 20% physical damage to magic damage" (old manual data)
    # Strategy: rename adapt to "适应" to distinguish, keep physical_to_magical as "物理转魔法"
    if 'adapt' in id_map:
        adapt_entry = id_map['adapt']
        old_name = adapt_entry['name']
        adapt_entry['name'] = '适应'
        # Add old name as alias for searchability
        aliases = adapt_entry.get('aliases', [])
        if old_name not in aliases:
            aliases.append(old_name)
        adapt_entry['aliases'] = aliases
        print(f"  Renamed adapt: '{old_name}' -> '适应' (kept '{old_name}' as alias)")

    # ─── Fix 3: Ensure all entries have aliases field (empty array if missing) ───
    alias_added = 0
    for e in data:
        if 'aliases' not in e:
            e['aliases'] = []
            alias_added += 1
    print(f"  Added empty aliases to {alias_added} entries")

    # ─── Save ───
    save_json(AUGMENTS_PATH, data)
    print(f"\nSaved {len(data)} entries to {AUGMENTS_PATH}")

    # Verify no more duplicates
    names = {}
    for e in data:
        n = e['name']
        names.setdefault(n, []).append(e['id'])
    dupes = {n: ids for n, ids in names.items() if len(ids) > 1}
    if dupes:
        print(f"\nWARNING: Still have {len(dupes)} duplicate names:")
        for n, ids in dupes.items():
            print(f"  '{n}': {ids}")
    else:
        print(f"\nNo duplicate names remaining.")


if __name__ == '__main__':
    main()
