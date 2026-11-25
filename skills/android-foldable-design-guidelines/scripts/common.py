"""Shared local data validation; no visual judgment or network access."""
import hashlib
import json
import struct
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
KINDS = {'image', 'transition_clip', 'interaction_record', 'measurement',
         'runtime_context', 'receiver_output', 'semantics_record', 'audio_record', 'user_context'}
STATUSES = {'issue', 'no_issue_observed', 'not_applicable', 'not_verified'}
COMPONENT_KINDS = {'text', 'button', 'input', 'navigation', 'list', 'card', 'media', 'overlay', 'other'}

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def index(rows, label):
    require(isinstance(rows, list), label + ' 必须是数组')
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get('id'), str) and row['id'], label + ' 缺 id')
        require(row['id'] not in result, label + ' 重复 id: ' + row['id'])
        result[row['id']] = row
    return result

def bundle():
    data = read(SKILL / 'references/rules.json')
    return data, index(data['rules'], 'rules'), read(SKILL / 'references/official-basis.json')

def check_facts(facts, evidence, label):
    require(isinstance(facts, dict), label + ' facts 必须是对象')
    for name, fact in facts.items():
        require(isinstance(fact, dict) and 'value' in fact, label + ' fact 无 value: ' + name)
        require(fact['value'] is None or isinstance(fact['value'], bool), label + ' 条件只能是 true／false／null: ' + name)
        refs = fact.get('evidence_ids', [])
        require(isinstance(refs, list) and all(x in evidence for x in refs), label + ' fact 引用了未知证据: ' + name)
        if fact['value'] is not None:
            require(bool(refs) and bool(fact.get('reason')), label + ' 已知 fact 必须有证据与理由: ' + name)

def load_input(path):
    path = Path(path).resolve()
    data = read(path)
    require(data.get('schema_version') == 1, '输入 schema_version 必须为 1')
    for original in data.get('capture_sources', []):
        original_path = Path(original['path'])
        if not original_path.is_absolute(): original_path = path.parent / original_path
        require(sha(original_path) == original.get('sha256'), '来源采集清单 hash 不匹配')
    if data.get('original_capture'):
        original = data['original_capture']
        original_path = Path(original['path'])
        if not original_path.is_absolute(): original_path = path.parent / original_path
        require(sha(original_path) == original.get('sha256'), '原始采集文件 hash 不匹配')
    contexts = index(data.get('contexts', []), 'contexts')
    evidence = index(data.get('evidence', []), 'evidence')
    pages = index(data.get('pages', []), 'pages')
    require(bool(pages), '输入没有页面')
    for e in evidence.values():
        require(e.get('kind') in KINDS, '未知证据类型: ' + e['id'])
        require(isinstance(e.get('path'), str), '证据缺 path: ' + e['id'])
        asset = Path(e['path'])
        if not asset.is_absolute():
            asset = path.parent / asset
        require(asset.is_file(), '证据文件不存在: ' + str(asset))
        require(sha(asset) == e.get('sha256'), '证据 hash 不匹配: ' + e['id'])
        require(isinstance(e.get('page_ids'), list) and all(x in pages for x in e['page_ids']), '证据 page_ids 无效: ' + e['id'])
        require(isinstance(e.get('context_ids'), list) and all(x in contexts for x in e['context_ids']), '证据 context_ids 无效: ' + e['id'])
        require(e.get('description'), '证据缺描述: ' + e['id'])
        if e['kind'] == 'image':
            require(all(isinstance(e.get(k), int) and e[k] > 0 for k in ['width_px','height_px']), '图像缺原始宽高: ' + e['id'])
            with asset.open('rb') as f: header = f.read(24)
            if header.startswith(b'\x89PNG\r\n\x1a\n'):
                require(len(header) == 24 and tuple(struct.unpack('>II', header[16:24])) == (e['width_px'],e['height_px']), 'PNG 原始尺寸不符: ' + e['id'])
        if e['kind'] == 'transition_clip':
            require(isinstance(e.get('start_s'), (int,float)) and isinstance(e.get('end_s'), (int,float))
                    and 0 <= e['start_s'] < e['end_s'], '连续片段起止时间无效: ' + e['id'])
            require(e.get('actions') and e.get('before_state') and e.get('after_state'), '连续片段缺动作和前后状态: ' + e['id'])
    component_ids = set()
    for page in pages.values():
        require(page.get('context_id') in contexts, '页面缺上下文: ' + page['id'])
        image = evidence.get(page.get('image_evidence_id'), {})
        require(image.get('kind') == 'image' and page['id'] in image.get('page_ids', []), '页面缺所属原图: ' + page['id'])
        require(page['context_id'] in image['context_ids'], '页面原图上下文不匹配: ' + page['id'])
        require(isinstance(page.get('components'), list), '页面必须登记 components: ' + page['id'])
        for comp in index(page['components'], 'components').values():
            require(comp['id'] not in component_ids, '组件 id 必须全局唯一: ' + comp['id'])
            component_ids.add(comp['id'])
            require(comp.get('kind') in COMPONENT_KINDS and comp.get('description'), '组件缺类型或描述: ' + comp['id'])
            check_facts(comp.get('facts', {}), evidence, comp['id'])
        check_facts(page.get('facts', {}), evidence, page['id'])
    check_facts(data.get('facts', {}), evidence, 'app')
    for context in contexts.values():
        check_facts(context.get('facts', {}), evidence, context['id'])
    return data, contexts, evidence, pages

def applicable(rule, facts):
    """False is meaningful only when supported by evidence; null stays unknown."""
    unknown = False
    for key, expected in rule['conditions'].items():
        value = facts.get(key, {}).get('value')
        if value is None:
            unknown = True
        elif type(value) is not type(expected) or value != expected:
            return 'no'
    return 'unknown' if unknown else 'yes'

def profile_rules(rules, profile):
    config = read(SKILL / 'references/audit-profiles.json')['profiles']
    require(profile in config, '未知审查范围: ' + str(profile))
    allowed = config[profile]['rule_ids']
    return {rid:r for rid,r in rules.items() if allowed is None or rid in allowed}

def tasks(data, contexts, pages, rules, scope):
    rules = profile_rules(rules, scope.get('profile'))
    all_ids = set(pages)
    selected = scope.get('page_ids', [])
    excluded = scope.get('excluded_pages', [])
    require(len(selected) == len(set(selected)) and bool(selected), 'scope 页面重复或为空')
    excluded_ids = [x.get('page_id') for x in excluded]
    require(len(excluded_ids) == len(set(excluded_ids)), '排除页面重复')
    require(set(selected).isdisjoint(excluded_ids) and set(selected) | set(excluded_ids) == all_ids, '每个提交页面必须纳入或明确排除')
    require(all(x.get('reason') for x in excluded), '排除页面须说明理由')
    result = {}
    for pid in selected:
        page = pages[pid]
        global_facts = {**data.get('facts', {}), **contexts[page['context_id']].get('facts', {}), **page.get('facts', {})}
        subjects = [('page', pid, None), ('scenario', pid, None)]
        subjects += [('component', c['id'], c) for c in page['components']]
        for stype, sid, comp in subjects:
            facts = {**global_facts, **(comp.get('facts', {}) if comp else {})}
            for rule in rules.values():
                if rule['subject_type'] != stype:
                    continue
                if comp and comp['kind'] not in rule['component_kinds']:
                    continue
                key = rule['id'] + '::' + stype + '::' + sid
                result[key] = dict(id=key, rule_id=rule['id'], subject_type=stype, subject_id=sid,
                                   page_ids=[pid], applicability_result=applicable(rule, facts), facts=facts)
    return result

def presentation_groups(issue,pages):
 pids=set(loc['page_id'] for loc in issue['locations'])
 groups=issue.get('presentation_groups')
 if groups is None:
  groups=[{'id':pid,'representative_page_id':pid,'covered_page_ids':[pid],'reason':'独立证据状态；未声明同页同位置重复'} for pid in sorted(pids)]
 seen=set();ids=set()
 for group in groups:
  members=group.get('covered_page_ids',[]);rep=group.get('representative_page_id')
  require(group.get('id') and group['id'] not in ids,'报告证据分组 ID 重复或缺失');ids.add(group['id'])
  require(members and len(members)==len(set(members)) and rep in members,'代表图必须属于无重复成员的分组')
  require(set(members)<=pids and not seen.intersection(members),'报告证据分组含额外或重复状态')
  require(group.get('reason'),'报告证据去重缺判断理由')
  require(len({pages[pid]['context_id'] for pid in members})==1,'不同屏幕上下文不能合并报告证据')
  if len(members)>1:
   logical={pages[pid].get('logical_page_id') for pid in members}
   require(None not in logical and '' not in logical and len(logical)==1,'多状态合并必须核对同一业务页面身份')
  seen.update(members)
 require(seen==pids,'报告证据分组遗漏问题状态')
 return groups

