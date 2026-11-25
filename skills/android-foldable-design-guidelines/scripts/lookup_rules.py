"""Query exact checks, original quotes, exceptions and supporting source locations."""
import argparse
import json
from common import SKILL, bundle, read, profile_rules

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--category')
    p.add_argument('--rule')
    p.add_argument('--subject', choices=['page','component','scenario'])
    p.add_argument('--profile', choices=['screenshot-only','submitted-evidence'], default='screenshot-only')
    args = p.parse_args()
    _, rules, bases = bundle()
    rules = profile_rules(rules, args.profile)
    sources = {s['id']:s for s in read(SKILL/'references/sources.json')['sources']}
    out = []
    for r in rules.values():
        if args.category and r['category_id'] != args.category: continue
        if args.rule and r['id'] != args.rule: continue
        if args.subject and r['subject_type'] != args.subject: continue
        row = dict(r)
        row['official_basis'] = [bases[b] for b in r['basis_ids']]
        row['supporting_sources'] = [sources[s] for s in r['supporting_source_ids']]
        out.append(row)
    if not out: p.error('没有匹配的检查卡')
    print(json.dumps(sorted(out, key=lambda r:(r['priority'],r['id'])), ensure_ascii=False, indent=2))

if __name__ == '__main__': main()
