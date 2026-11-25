"""Build three-part report data from validated judgments; no judgment or publication."""
import argparse,json,os,sys,shutil,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RULES=ROOT/'android-foldable-design-guidelines'
sys.path.insert(0,str(RULES/'scripts'))
from common import read,write,sha,bundle,load_input,require,presentation_groups
from validate_review import validate

def build(run_dir,output):
 run=Path(run_dir).resolve();review_path=run/'review.json'
 summary=validate(review_path);review=read(review_path)
 input_path=Path(review['input_path'])
 if not input_path.is_absolute():input_path=run/input_path
 data,contexts,evidence,pages=load_input(input_path)
 _,rules,bases=bundle();issues=review['findings'];output=Path(output).resolve()
 require(not output.exists(),'报告目录已存在；修订请新建版本目录')
 output.mkdir(parents=True)
 def display_wording(rule):
  value=rule.get('requirement_wording','')
  return rule['title'].rstrip('。')+'。' if value=='official_basic_requirement' else value
 used=sorted({c['rule_id'] for c in review['checks'] if c['status'] in ['issue','no_issue_observed']})
 standards=[{'rule_id':rid,'title':rules[rid]['title'],'applicability':rules[rid]['applies_when'],
             'requirement_wording':display_wording(rules[rid]),
             'official_references':[{'url':bases[x]['url'],'quote':bases[x]['quote']} for x in rules[rid]['basis_ids'] if bases[x]['role']=='minimum_requirement']} for rid in used]
 def asset(pid):
  p=pages[pid];e=evidence[p['image_evidence_id']];path=Path(e['path'])
  if not path.is_absolute():path=input_path.parent/path
  return {'page_id':pid,'page_name':p.get('name',pid),'context':contexts[p['context_id']],
          'image_path':os.path.relpath(path.resolve(),output),'image_sha256':e['sha256'],'width_px':e['width_px'],'height_px':e['height_px']}
 def retained_groups(item):
  locations=item.get('locations')
  if locations is None:locations=[{'page_id':item.get('page_id'),'bbox_px':item.get('bbox_px')}]
  require(isinstance(locations,list) and locations,'保留问题须有非空来源位置')
  for loc in locations:
   pid=loc.get('page_id');require(pid in review['scope']['page_ids'],'保留问题页面不在本次范围')
   box=loc.get('bbox_px')
   require(isinstance(box,(list,tuple)) and len(box)==4 and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in box),'保留问题位置须为四个有限数值')
   x,y,w,h=box;a=asset(pid)
   require(x>=0 and y>=0 and w>0 and h>0 and x+w<=a['width_px'] and y+h<=a['height_px'],'保留问题位置超出原图')
  groups=presentation_groups({'locations':locations,**({'presentation_groups':item['presentation_groups']} if 'presentation_groups' in item else {})},pages)
  for group in groups:
   if len(group['covered_page_ids'])<=1:continue
   members=[loc for loc in locations if loc['page_id'] in group['covered_page_ids']]
   require(all(isinstance(loc.get('component_key'),str) and loc['component_key'].strip() for loc in members),'多状态保留问题去重须有稳定组件标识 component_key')
   all_keys={loc['component_key'] for loc in members}
   rep_keys={loc['component_key'] for loc in members if loc['page_id']==group['representative_page_id']}
   require(all_keys<=rep_keys,'代表图未覆盖组内新增问题位置；须补代表图或拆组')
  return locations,groups
 def number_key(value):
  value=str(value)
  return str(int(value)) if value.isdigit() else value
 def annotation_key(number,loc):
  return (str(number),loc['page_id'],loc.get('component_id'),tuple(loc.get('bbox_px',[])),loc.get('scenario_description'),loc.get('component_key'))
 examples={};all_pages={};by_check={c['id']:c for c in review['checks']};problem_evidence=[];expected=set()
 for issue in sorted(issues,key=lambda f:(f['priority'],f['id'])):
  groups=presentation_groups(issue,pages)
  visible={g['representative_page_id'] for g in groups}
  problem_evidence.append({'number':issue['id'],'locations':issue['locations'],'presentation_groups':groups})
  representatives={}
  for loc in issue['locations']:
   if loc['page_id'] in visible:representatives.setdefault(pages[loc['page_id']]['context_id'],loc['page_id'])
  for first in representatives.values():
   examples.setdefault(first,{**asset(first),'annotations':[],'explanations':[]})
   examples[first]['explanations'].append({'number':issue['id'],'problem':issue['problem'],'impact':issue['impact'],
                                       'requirement_wording':display_wording(rules[by_check[issue['check_ids'][0]]['rule_id']]) if issue['requirement_wording']=='official_basic_requirement' else issue['requirement_wording'],
                                       'official_urls':list(dict.fromkeys(bases[x]['url'] for x in issue['basis_ids']))})
  for loc in issue['locations']:
   pid=loc['page_id'];ann={'number':issue['id'],**loc}
   if pid not in visible:continue
   all_pages.setdefault(pid,{**asset(pid),'annotations':[]})['annotations'].append(ann)
   if pid in representatives.values():examples[pid]['annotations'].append(ann)
  # Dynamic evidence stays attached to examples; static images do not stand in for actions.
  refs=list(dict.fromkeys(e for cid in issue['check_ids'] for e in by_check[cid]['evidence_ids']))
  for eid in refs:
   e=evidence[eid]
   if e['kind']=='image':continue
   path=Path(e['path'])
   if not path.is_absolute():path=input_path.parent/path
   for first in representatives.values():
    examples[first].setdefault('evidence',[]).append({**e,'path':os.path.relpath(path.resolve(),output)})
 # Visible issues explicitly confirmed for this report are not discarded merely
 # because their technical cause or a specific minimum-requirement breach is unknown.
 reported=review.get('reported_issues',[])
 reserved={str(f['id']) for f in issues}
 used_numbers={number_key(x) for x in reserved}
 require(len(used_numbers)==len(reserved),'问题显示编号重复')
 for item in reported:
  number=str(item['number']);require(number_key(number) not in used_numbers,'问题显示编号重复');reserved.add(number);used_numbers.add(number_key(number))
  locations,groups=retained_groups(item);visible={g['representative_page_id'] for g in groups}
  item['_locations']=locations
  problem_evidence.append({'number':number,'classification':'observed','locations':locations,'presentation_groups':groups})
  representatives={}
  for loc in locations:
   if loc['page_id'] in visible:representatives.setdefault(pages[loc['page_id']]['context_id'],loc['page_id'])
  explanation={'number':number,'problem':item['title'],'problem_point':item['phenomenon'],
               'impact':item['phenomenon'],'status':'observed','official_urls':item.get('official_urls',[]),
               'requirement_wording':item.get('basis_summary','暂无可直接判定的条款。')}
  for pid in representatives.values():
   examples.setdefault(pid,{**asset(pid),'annotations':[],'explanations':[]})['explanations'].append(explanation)
  for loc in locations:
   pid=loc['page_id']
   if pid not in visible:continue
   ann={'number':number,**loc,'status':'observed'};expected.add(annotation_key(number,loc))
   all_pages.setdefault(pid,{**asset(pid),'annotations':[]})['annotations'].append(ann)
   if pid in representatives.values():examples[pid]['annotations'].append(ann)
 report={'schema_version':1,'rule_version':review['rule_version'],'review_sha256':sha(review_path),
         'summary':{'finding_count':len(issues),'reviewed_page_count':len(review['scope']['page_ids']),
                    'unverified_check_count':sum(c['status']=='not_verified' for c in review['checks']),
                    'profile':review['scope']['profile'],'statement':('在本次截图审查范围内发现不符合项。' if issues else '在本次截图审查范围内未发现不符合项。') if review['scope']['profile']=='screenshot-only' else ('在本次扩展测试范围内发现不符合项。' if issues else '在本次扩展测试范围内未发现不符合项。')},
         'sections':[{'title':'标准','standards':standards},
                     {'title':'App 问题示例','pages':list(examples.values())},
                     {'title':'问题页面汇总','pages':list(all_pages.values())}],
         'coverage':[{'rule_id':c['rule_id'],'reason':c['observation'],'missing_actions':c['coverage_details']['missing_actions']} for c in review['checks'] if c['status']=='not_verified']}
 expected.update(annotation_key(f['id'],loc) for f in issues for loc in f['locations'] if loc['page_id'] in {g['representative_page_id'] for g in presentation_groups(f,pages)})
 report['problem_evidence']=problem_evidence
 # Contexts come from the reviewed display area, never the padded recording canvas.
 artboards=[]
 pending_numbers={};next_number=1;pending_entries=[]
 for note in review.get('pending_observations',[]):
  require(note.get('id') and note['id'] not in pending_numbers,'待核实项 ID 重复或缺失')
  require(note.get('phenomenon') and note.get('judgment'),'待核实项须有现象和判断依据缺口')
  locations,groups=retained_groups(note)
  while str(next_number) in used_numbers:next_number+=1
  number=str(next_number).zfill(2);reserved.add(number);used_numbers.add(str(next_number));next_number+=1
  pending_numbers[note['id']]=number
  problem_evidence.append({'number':number,'classification':'not_verified','locations':locations,'presentation_groups':groups})
  for group in groups:
   pid=group['representative_page_id']
   annotations=[{'number':number,**loc,'status':'not_verified'} for loc in locations if loc['page_id']==pid]
   expected.update(annotation_key(number,loc) for loc in locations if loc['page_id']==pid)
   entry={**{k:v for k,v in note.items() if k not in ('locations','presentation_groups')},**asset(pid),'number':number,
          'annotations':annotations,'explanations':[{'number':number,'problem':note.get('title',note['phenomenon']),
          'problem_point':note['phenomenon'],'verification_note':note['judgment'],'status':'not_verified',
          'official_urls':note.get('official_urls',[]),'requirement_wording':note.get('basis_summary','暂无可直接判定的条款。')}]}
   pending_entries.append(entry)
   all_pages.setdefault(pid,{**asset(pid),'annotations':[]})['annotations'].extend(annotations)
 actual={annotation_key(a['number'],{**a,'page_id':p['page_id']}) for p in all_pages.values() for a in p['annotations']}
 require(expected==actual,'报告遗漏代表图的问题位置')
 require(reserved=={str(item['number']) for item in problem_evidence},'报告遗漏保留问题的全量证据映射')
 report['summary']['problem_state_count']=len({loc['page_id'] for item in problem_evidence for loc in item['locations']})
 for cid,context in contexts.items():
  pids=[pid for pid in review['scope']['page_ids'] if pages[pid]['context_id']==cid]
  if not pids:continue
  size=context.get('size_px');ratio='比例未知';orientation='方向未知'
  if size and all(isinstance(x,(int,float)) and x>0 for x in size):
   w,h=size;aspect=max(w,h)/min(w,h)
   ratio='1:1' if abs(aspect-1)<.025 else ('4:3' if abs(aspect-4/3)<.025 else str(round(aspect,3))+':1')
   if w!=h:orientation='横向' if w>h else '竖向'
   elif context.get('rotation') is not None:orientation='横向' if context['rotation']%180 else '竖向'
  display={'inner':'内屏','outer':'外屏'}.get(context.get('display'),'屏幕未知')
  ex=[p for p in examples.values() if p['page_id'] in pids]
  gallery=[p for p in all_pages.values() if p['page_id'] in pids]
  numbers=list(dict.fromkeys(a['number'] for p in gallery for a in p['annotations'] if a.get('status')!='not_verified'))
  relevant={c['rule_id'] for c in review['checks'] if set(c['page_ids'])&set(pids) and c['status']=='issue'}
  relevant.update(rid for item in reported if any(loc['page_id'] in pids for loc in item['_locations']) for rid in item.get('related_rule_ids',[]))
  pending=[note for note in pending_entries if note['page_id'] in pids]
  # Generic unknown checks never become retained report items.
  if pending:relevant.add('window.fit')
  selected=[s for s in standards if s['rule_id'] in relevant]
  official=read(Path(__file__).resolve().parents[1]/'assets/official-examples.json')['examples']
  selected_images=[dict(im) for im in official if set(im['rule_ids'])&relevant]
  for im in selected_images:
   source=Path(__file__).resolve().parents[1]/'assets'/im['asset_path']
   target=output/'official-assets'/source.name;target.parent.mkdir(exist_ok=True)
   shutil.copy2(source,target);im['asset_path']=os.path.relpath(target,output);im['image_sha256']=sha(target)
  sections=[{'title':'Google 官方规范示例','standards':selected,'official_examples':selected_images}] if numbers or pending else []
  if numbers or pending:sections += [{'title':'App 问题示例','pages':ex,'pending_observations':pending},{'title':'问题页面汇总','pages':gallery}]
  artboards.append({'context_id':cid,'title':ratio+' '+display+orientation+'适配审查','context':context,'reviewed_page_ids':pids,'finding_numbers':numbers,'pending_observation_count':len({note['number'] for note in pending}),'statement':('确认 '+str(len(numbers))+' 项问题。' if numbers else '本次截图未确认不符合项。'),'sections':sections})
 report['artboards']=artboards
 report['summary']['pending_observation_count']=len(review.get('pending_observations',[]))
 report['summary']['displayed_problem_page_count']=sum(len(b['sections'][2]['pages']) for b in artboards if b['sections'])
 report['summary']['problem_count']=len(issues)+len(reported)
 report['summary']['reported_issue_count']=len(reported)
 if reported:report['summary']['statement']='本次报告列出 '+str(len(issues)+len(reported))+' 项问题。'
 report['presentation_version']='android-screen-report-v1'
 report.pop('sections')  # Only per-screen sections are presentation data.
 write(output/'report.json',report)
 write(output/'figma-plan.json',{'schema_version':1,'report_sha256':sha(output/'report.json'),
       'artboards':artboards,'summary':report['summary'],'coverage':report['coverage'],'style':read(Path(__file__).resolve().parents[1]/'assets/report-style.json'),'layout':{'direction':'top-to-bottom-per-artboard','numbering':'same-across-artboards-and-sections','image_aspect':'preserve-original','labels':'outside-screenshot-in-side-rail','marker':'editable-badge-and-leader','card_background':'app-audit-explanations-including-pending','visible_timecodes':False,'detail_crops':False},
       'publication_status':'not_published'})
 lines=['# 安卓折叠屏适配审查',report['summary']['statement'],'']
 for board in artboards:
  lines += ['## '+board['title'],'',board['statement'],'']
  for section in board['sections']:
   lines += ['### '+section['title'],'']
   if 'standards' in section:
    for standard in section['standards']:
     lines += ['- '+standard['title']+'：'+'、'.join('[官方依据]('+r['url']+')' for r in standard['official_references'])]
   else:
    for note in section.get('pending_observations',[]):
     explanation=note['explanations'][0]
     lines += ['#### '+note['number']+'｜'+explanation['problem']+' · 待核实','','问题点：'+explanation['problem_point'],'']
     lines += ['[官方依据 ↗]('+u+')' for u in explanation['official_urls']]
     lines += [explanation['requirement_wording'],'','待核实：'+explanation['verification_note'],'','![]('+note['image_path']+')','']
    for page in section['pages']:
     lines += ['#### '+page['page_name'],'','![]('+page['image_path']+')','']
     for ex in page.get('explanations',[]):
      lines += [ex['number']+'｜'+ex['problem'].rstrip('。'),'问题点：'+ex['impact'],'官方依据：'+'、'.join('[Google 官方规范]('+u+')' for u in ex['official_urls']),'']
     if not page.get('explanations'):lines += ['问题编号：'+ '、'.join(dict.fromkeys(a['number'] for a in page['annotations'])),'']
 (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print('三段式报告数据已生成；问题',len(issues)+len(reported),'类，去重展示',len(all_pages),'张，后台问题状态',report['summary']['problem_state_count'],'个；尚未发布。')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('run_dir');p.add_argument('output_dir');args=p.parse_args()
 try:build(args.run_dir,args.output_dir)
 except (ValueError,KeyError,TypeError,OSError) as e:p.error(str(e))
if __name__=='__main__':main()
