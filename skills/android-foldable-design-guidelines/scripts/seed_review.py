"""Create unjudged review records without interpreting images or claiming compliance."""
import argparse
import os
from pathlib import Path
from common import bundle, load_input, sha, tasks, write

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input'); p.add_argument('output')
    p.add_argument('--profile', choices=['screenshot-only','submitted-evidence'], default='screenshot-only')
    args = p.parse_args()
    output = Path(args.output).resolve()
    if output.exists(): p.error('输出已存在；不覆盖已有审查')
    source = Path(args.input).resolve()
    try:
        data, contexts, _, pages = load_input(source)
        meta, rules, _ = bundle()
        scope = {'profile':args.profile,'page_ids':list(pages),'excluded_pages':[]}
        expected = tasks(data, contexts, pages, rules, scope)
        records = []
        for t in expected.values():
            rule = rules[t['rule_id']]
            records.append({k:t[k] for k in ['id','rule_id','subject_type','subject_id','page_ids']} | dict(
                status='not_verified', applicability=dict(result=t['applicability_result'],reason='尚未逐项核对适用条件',evidence_ids=[]),
                evidence_ids=[], observation='尚未审查；需查看原始证据', exception_review='',
                evaluated_basis_ids=[], coverage_details=dict(tested_actions=[], missing_actions=[], notes='尚未核对'),
                priority=rule['priority']))
        review=dict(schema_version=1,rule_version=meta['rule_version'], input_path=os.path.relpath(source, output.parent),input_sha256=sha(source),scope=scope,
                    checks=records,findings=[],inventory_review=dict(page_ids_verified=[],notes=''),
                    self_review=dict(all_pages_rechecked=False,all_components_rechecked=False,notes=''))
        write(output, review)
        print('生成',len(records),'条待审查记录；未判断任何问题。')
    except (ValueError, KeyError, TypeError, OSError) as e:
        p.error(str(e))

if __name__ == '__main__': main()
