"""Validate coverage, provenance, applicability, evidence gates and numbered findings."""
import argparse
from collections import Counter
from pathlib import Path
from common import bundle, index, load_input, read, require, sha, tasks, presentation_groups


def validate_completion(review, page_ids, finding_ids):
    strategy = review.get('review_strategy', 'two-pass')
    require(strategy in ['batch', 'two-pass'], '未知复查策略')
    sr = review.get('self_review', {})
    if strategy == 'batch':
        require(review.get('scope', {}).get('profile') == 'screenshot-only', '扩展实测不可使用 batch')
        visual = review.get('visual_review', {})
        seen = visual.get('page_ids_reviewed', [])
        require(isinstance(seen, list) and len(seen) == len(set(seen)) and set(seen) == set(page_ids)
                and visual.get('notes'), '未完成全部页面的清晰视觉巡检')
        checked = sr.get('finding_ids_rechecked', [])
        require(isinstance(checked, list) and len(checked) == len(set(checked)) and set(checked) == set(finding_ids)
                and sr.get('notes'), '未核对全部已确认问题及报告映射')
    else:
        require(sr.get('all_pages_rechecked') is True and sr.get('all_components_rechecked') is True
                and sr.get('notes'), '未完成全量第二轮复查')
    return strategy


def measurement_gate(rule_id, records, subject_id, input_path, status):
    rows=[]
    for e in records:
        if e['kind']=='measurement':
            path=Path(e['path'])
            if not path.is_absolute(): path=input_path.parent/path
            data=read(path)
            require(isinstance(data.get('measurements'),list), 'measurement 文件缺 measurements 数组')
            rows += [m for m in data['measurements'] if m.get('subject_id')==subject_id]
    kind={'accessibility.target':'touch_target','accessibility.contrast':'contrast','text.line_length':'line_length'}.get(rule_id)
    if not kind: return
    rows=[m for m in rows if m.get('type')==kind]
    require(bool(rows), '缺该对象的具体测量: '+rule_id+' '+subject_id)
    violations=[]
    for m in rows:
        require(m.get('method') and m.get('source'), '测量缺方法及原始来源')
        if kind=='touch_target':
            require(m.get('unit')=='dp' and m.get('actual_hit_area') is True,
                    '触控目标必须测真实热区并以 dp 记录，不能用图标像素替代')
            require(all(isinstance(m.get(k),(int,float)) and m[k]>0 for k in ['width','height']), '热区宽高无效')
            violations.append(m['width'] < 48 or m['height'] < 48)
        elif kind=='contrast':
            require(isinstance(m.get('ratio'),(int,float)) and m['ratio']>=1, '对比度测量无效')
            require(m.get('content_class') in ['large_text','small_text','graphic'] and m.get('class_basis'), '对比度缺对象／字号分类依据')
            require(m.get('foreground') and m.get('background'), '缺对比度原始颜色')
            violations.append(m['ratio'] < (4.5 if m['content_class']=='small_text' else 3))
        else:
            require(m.get('language') and m.get('reading_block') is True and isinstance(m.get('lines'),list) and m['lines'], '行长缺完整阅读文本／语言')
            require(all(isinstance(line,str) for line in m['lines']), '行长需原文逐行字符串')
            require('last_line_included' in m and isinstance(m['last_line_included'],bool), '行长须标明是否包含末行')
            full_lines=m['lines'][:-1] if m['last_line_included'] else m['lines']
            violations.append(any(len(line)<45 or len(line)>75 for line in full_lines) or any(len(line)>75 for line in m['lines']))
    if status=='issue': require(any(violations), '测量数据没有支持所报数值不符合项: '+rule_id)
    else: require(not any(violations), '测量已显示阈值不满足，不可记未发现问题: '+rule_id)


def validate(review_path):
    review_path=Path(review_path).resolve();review=read(review_path)
    meta,rules,bases=bundle()
    require(review.get('schema_version')==1 and review.get('rule_version')==meta['rule_version'], '审查版本不匹配')
    source=Path(review['input_path'])
    if not source.is_absolute(): source=review_path.parent/source
    source=source.resolve()
    require(sha(source)==review.get('input_sha256'), '审查输入改变，需重新核对结论')
    data,contexts,evidence,pages=load_input(source)
    scope=review['scope']
    require(scope.get('profile') in ['screenshot-only','submitted-evidence'], '未知审查方式')
    expected=tasks(data,contexts,pages,rules,scope)
    checks=index(review.get('checks',[]),'checks')
    require(set(checks)==set(expected), '存在漏检／额外检查记录：'+str(sorted(set(expected)-set(checks))[:6]))
    inventory=review.get('inventory_review',{})
    require(set(inventory.get('page_ids_verified',[]))==set(scope['page_ids']) and inventory.get('notes'), '未确认全部受审页面组件库存')
    allowed={'id','check_ids','problem','impact','priority','requirement_wording','basis_ids','locations','presentation_groups'}
    findings=index(review.get('findings',[]),'findings')
    issue_to_finding={}
    for f in findings.values():
        require(set(f)<=allowed, '问题记录含建议／未经支持字段: '+f['id'])
        require(f.get('check_ids') and len(f['check_ids'])==len(set(f['check_ids'])), '问题缺检查关联或重复: '+f['id'])
        require(f.get('problem') and f.get('impact'), '问题缺现象或影响: '+f['id'])
        merged_bases=set();page_ids=set();wording=set();priorities=[]
        for cid in f['check_ids']:
            require(cid in checks and checks[cid]['status']=='issue', '只能汇总已确认 issue: '+cid)
            require(cid not in issue_to_finding, '同一检查重复计入问题: '+cid)
            issue_to_finding[cid]=f['id']
            r=rules[checks[cid]['rule_id']]
            merged_bases.update(r['basis_ids']);page_ids.update(checks[cid]['page_ids'])
            wording.add(r['requirement_wording']);priorities.append(r['priority'])
        require(len(wording)==1 and f.get('requirement_wording') in wording, '不得将 should 与强制条款混为同一问题')
        require(set(f.get('basis_ids',[]))==merged_bases, '问题官方依据不完整或混入其他要求')
        require(f.get('priority') in [1,2] and f['priority']<=min(priorities), '问题处理顺序无效')
        locs=f.get('locations',[])
        require(locs and {l.get('page_id') for l in locs}==page_ids, '问题发生页面缺失: '+f['id'])
        for cid in f['check_ids']:
            check=checks[cid]
            if check['subject_type']=='component':
                require(any(l.get('component_id')==check['subject_id'] and l.get('page_id') in check['page_ids'] for l in locs), '归组后遗漏了问题组件位置: '+cid)
        presentation_groups(f,pages)
        for loc in locs:
            pid=loc['page_id']; image=evidence[pages[pid]['image_evidence_id']]
            if 'component_id' in loc:
                require(loc['component_id'] in {c['id'] for c in pages[pid]['components']}, '标注组件不属于该页')
            if 'bbox_px' in loc:
                b=loc['bbox_px']
                require(isinstance(b,list) and len(b)==4 and all(isinstance(x,(int,float)) for x in b), '标注坐标格式无效')
                x,y,w,h=b
                require(x>=0 and y>=0 and w>0 and h>0 and x+w<=image['width_px'] and y+h<=image['height_px'], '标注超出原图')
            require('bbox_px' in loc or loc.get('scenario_description'), '须提供静态位置或动态场景说明')
    for cid,c in checks.items():
        t=expected[cid];r=rules[t['rule_id']]
        require(all(c.get(k)==t[k] for k in ['rule_id','subject_type','subject_id','page_ids']), '检查对象改变: '+cid)
        require(c.get('status') in {'issue','no_issue_observed','not_applicable','not_verified'}, '未知判断状态: '+cid)
        require(c.get('priority')==r['priority'], '检查优先级不匹配: '+cid)
        app=c.get('applicability',{})
        require(app.get('result')==t['applicability_result'] and app.get('reason'), '适用性不符或缺理由: '+cid)
        refs=c.get('evidence_ids',[])
        apprefs=app.get('evidence_ids',[])
        require(isinstance(refs,list) and isinstance(apprefs,list) and all(e in evidence for e in refs+apprefs), '检查引用未知证据: '+cid)
        require(c.get('observation'), '检查缺观察或缺证据说明: '+cid)
        for eid in refs:
            require(set(c['page_ids']) <= set(evidence[eid]['page_ids']), '证据未关联受审页面: '+cid+' '+eid)
        status=c['status']
        if status=='not_applicable':
            require(app['result']=='no' and bool(apprefs), '未知条件不可标记不适用: '+cid)
            false_refs=set()
            for key,value in r['conditions'].items():
                fact=t['facts'].get(key,{})
                if fact.get('value') is not None and (type(fact['value']) is not type(value) or fact['value']!=value):
                    false_refs.update(fact['evidence_ids'])
            require(false_refs and false_refs <= set(apprefs), '不适用须关联否定条件的证据: '+cid)
        if status in ['issue','no_issue_observed']:
            require(app['result']=='yes', '条件未明确不能判错或通过: '+cid)
            require(c.get('exception_review') and set(c.get('evaluated_basis_ids',[]))==set(r['basis_ids']), '缺原文／例外核对: '+cid)
            for key in r['conditions']:
                require(set(t['facts'][key]['evidence_ids'])<=set(apprefs), '适用性缺事实证据: '+cid)
            kinds={evidence[e]['kind'] for e in refs}
            require(all(set(group)&kinds for group in r['evidence_groups']), '证据类型不足: '+cid)
            for eid in refs:
                e=evidence[eid]
                if e['kind']=='runtime_context':
                    require(pages[c['page_ids'][0]]['context_id'] in e['context_ids'], '运行信息与页面环境不匹配: '+cid)
            if any('measurement' in g for g in r['evidence_groups']):
                measurement_gate(r['id'],[evidence[e] for e in refs],c['subject_id'],source,status)
            if r['id']=='stylus.handwriting':
                context=contexts[pages[c['page_ids'][0]]['context_id']]
                if context.get('platform')=='android':
                    require(isinstance(context.get('api'),int) and context['api']>=34, 'Android 手写输入须确认 API>=34')
                else:
                    require(context.get('platform') in ['chromeos','googlebook'] and (context['platform']=='googlebook' or context.get('chromeos_version',0)>=114), '手写平台条件未核实')
        details=c.get('coverage_details',{})
        require(isinstance(details.get('tested_actions'),list) and isinstance(details.get('missing_actions'),list) and details.get('notes'), '缺具体检查范围: '+cid)
        if status in ['issue','no_issue_observed'] and r['subject_type']=='scenario':
            require(bool(details['tested_actions']), '动态结论未记录实际动作: '+cid)
        if status=='issue': require(cid in issue_to_finding, '已确认问题未进入输出: '+cid)
    require(set(issue_to_finding)=={cid for cid,c in checks.items() if c['status']=='issue'}, '问题关联不完整')
    strategy=validate_completion(review, scope['page_ids'], findings)
    return {'review_strategy':strategy,'checks':len(checks),'findings':len(findings),'statuses':dict(Counter(c['status'] for c in checks.values())),
            'observed_contexts':[contexts[x] for x in sorted({pages[p]['context_id'] for p in scope['page_ids']})],
            'conclusion_scope':'仅本次证据范围；不证明全 App 或 Google Play 认证通过'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('review');args=p.parse_args()
    try: print(validate(args.review))
    except (ValueError,KeyError,TypeError,OSError) as e: p.error(str(e))

if __name__=='__main__': main()
