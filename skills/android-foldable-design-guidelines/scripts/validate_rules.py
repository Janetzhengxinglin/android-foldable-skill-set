"""Validate primary quotes, source hashes, scope and normative coverage offline."""
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse
from common import SKILL, KINDS, profile_rules, bundle, read, require, sha

class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]; self.ids=set()
    def handle_starttag(self, tag, attrs):
        self.ids.update(v for k,v in attrs if k=='id')
    def handle_data(self, data): self.parts.append(data)

def norm(s): return re.sub(r'\s+', ' ', s).strip()

def validate():
    meta, rules, bases = bundle()
    sources = {s['id']:s for s in read(SKILL/'references/sources.json')['sources']}
    require(len(sources)==len(read(SKILL/'references/sources.json')['sources']), '来源 id 重复')
    parsers={}
    for s in sources.values():
        if s.get('snapshot_path'):
            path=SKILL/s['snapshot_path']
            require(sha(path)==s['sha256'], '来源快照 hash 不符: '+s['id'])
            parser=Text(); parser.feed(path.read_text(encoding='utf-8'));parsers[s['id']]=parser
    for bid,b in bases.items():
        require(b['source_id'] in {'S03','S04'}, '判错主依据只能来自已核实 Tier 3/Core')
        s=sources[b['source_id']]; parser=parsers[b['source_id']]
        require(s.get('reading_status')=='full_body_read', '主依据正文未核实: '+bid)
        require(b['snapshot_sha256']==s['sha256'], '条款 hash 不符: '+bid)
        require(norm(b['quote']) in norm(' '.join(parser.parts)), '原文不能在快照中定位: '+bid)
        u=urlparse(b['url'])
        require(u.hostname=='developer.android.com' and u.fragment==b['official_id'] and u.fragment in parser.ids, '官方定位无效: '+bid)
    visible=profile_rules(rules, 'screenshot-only')
    require(visible and all(r['subject_type'] != 'scenario' and r['evidence_groups'] == [['image']] for r in visible.values()), '截图审查不能包含动态、外设或测量门槛')
    for rid,r in rules.items():
        require(('screenshot-only' in r['profiles']) == (rid in visible), '规则与审查范围映射不一致: '+rid)
    used=set()
    for r in rules.values():
        require(r['lifecycle']=='verified' and r['priority'] in [1,2], '规则状态或优先级无效: '+r['id'])
        require(r['subject_type'] in ['page','component','scenario'], '对象无效: '+r['id'])
        require(r['basis_ids'] and all(x in bases for x in r['basis_ids']), '规则缺原文: '+r['id'])
        require(any(bases[x]['role']=='minimum_requirement' for x in r['basis_ids']), '测试或示例不能单独判错: '+r['id'])
        require(r['evidence_groups'] and all(g for g in r['evidence_groups']), '规则缺证据门槛: '+r['id'])
        require(all(kind in KINDS for group in r['evidence_groups'] for kind in group), '未知证据门槛: '+r['id'])
        require(set(r['test_ids'])=={bases[b]['official_id'] for b in r['basis_ids'] if bases[b]['role']=='official_test'}, '测试映射不一致: '+r['id'])
        require(all(x in sources for x in r['supporting_source_ids']), '规则引用未知来源: '+r['id'])
        used.update(r['basis_ids'])
    covered={bases[x]['official_id'] for x in used if bases[x]['source_id']=='S03'}
    coverage=read(SKILL/'references/source-coverage.json')
    require(len(coverage['tier3_guideline_ids'])==10 and len(coverage['tier3_test_ids'])==12, 'Tier 3 清单不完整')
    require(set(coverage['tier3_guideline_ids']+coverage['tier3_test_ids']) <= covered, 'Tier 3 存在未映射条款或测试')
    require(len(coverage['core_dispositions'])==69, 'Core 处置记录不完整')
    core_included={row['official_id'] for row in coverage['core_dispositions'] if row['disposition']=='included'}
    require(core_included=={bases[x]['official_id'] for x in used if bases[x]['source_id']=='S04' and bases[x]['role']=='minimum_requirement'}, '纳入的 Core 条款存在漏映射')
    require(not set(bases)-used, '存在未被检查卡使用的主依据')
    return dict(rule_version=meta['rule_version'],checks=len(rules),primary_rows=len(bases),sources=len(sources),tier3_guidelines=10,tier3_tests=12)

if __name__=='__main__':
    try: print(validate())
    except (ValueError,KeyError,TypeError,OSError) as e:
        print('INVALID:', e, file=sys.stderr); sys.exit(1)
