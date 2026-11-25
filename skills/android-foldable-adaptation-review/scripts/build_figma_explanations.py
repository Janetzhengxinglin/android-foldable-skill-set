"""Generate native Figma explanation cards from report data and the Duo template.

python3 build_figma_explanations.py REPORT_DIR CONTEXT_ID PANEL_NODE_ID
Outputs JavaScript for use_figma. It does not publish or judge findings.
PANEL_NODE_ID must be the explanation-only stack in the authorized report.
Existing children of that stack are replaced; screenshots stay untouched.
"""
import argparse,json
from pathlib import Path

def generate(report_dir,context_id,panel_id):
 root=Path(report_dir);report=json.loads((root/'report.json').read_text(encoding='utf-8'))
 style=json.loads((Path(__file__).resolve().parents[1]/'assets/report-style.json').read_text(encoding='utf-8'))
 board=next(b for b in report['artboards'] if b['context_id']==context_id)
 section=next(s for s in board['sections'] if 'pages' in s and 'pending_observations' in s)
 explanations={}
 for page in section['pages']+section['pending_observations']:
  for item in page.get('explanations',[]):explanations.setdefault(item['number'],item)
 payload={'panel_id':panel_id,'style':style,'items':list(explanations.values())}
 return 'const payload='+json.dumps(payload,ensure_ascii=False)+';'+chr(10)+r'''
const panel=await figma.getNodeByIdAsync(payload.panel_id);
if(!panel || panel.type!=='FRAME')throw new Error('说明区节点不是 Frame');
let page=panel;while(page.type!=='PAGE')page=page.parent;
await figma.setCurrentPageAsync(page);
for(const family of ['Regular','Bold'])await figma.loadFontAsync({family:'Inter',style:family});
const oldTexts=panel.findAllWithCriteria({types:['TEXT']});
for(const t of oldTexts)for(const s of t.getStyledTextSegments(['fontName']))await figma.loadFontAsync(s.fontName);
const removed=panel.children.map(n=>n.id);for(const n of [...panel.children])n.remove();
const cfg=payload.style.figma;
panel.layoutMode='VERTICAL';panel.resize(cfg.explanation_panel_width,100);
panel.primaryAxisSizingMode='AUTO';panel.counterAxisSizingMode='FIXED';panel.itemSpacing=cfg.card_stack_gap;
panel.paddingTop=0;panel.paddingBottom=0;panel.paddingLeft=0;panel.paddingRight=0;panel.fills=[];
const created=[];const mappings=[];
function color(hex){return {r:parseInt(hex.slice(1,3),16)/255,g:parseInt(hex.slice(3,5),16)/255,b:parseInt(hex.slice(5,7),16)/255};}
function stack(parent,width,name){const n=figma.createAutoLayout();parent.appendChild(n);n.name=name;
 n.layoutMode='VERTICAL';n.resize(width,100);n.primaryAxisSizingMode='AUTO';n.counterAxisSizingMode='FIXED';n.fills=[];created.push(n.id);return n;}
function text(parent,width,value,bold=false,link=null){const n=figma.createText();parent.appendChild(n);
 n.fontName={family:'Inter',style:bold?'Bold':'Regular'};n.fontSize=bold?cfg.card_heading_font_size:cfg.body_font_size;
 n.lineHeight={unit:'PERCENT',value:cfg.line_height_percent};n.resize(width,100);n.textAutoResize='HEIGHT';n.characters=value;
 n.name=value;n.fills=[{type:'SOLID',color:color(link?payload.style.link:payload.style.card_text)}];
 if(link){n.hyperlink={type:'URL',value:link};n.textDecoration='UNDERLINE';}created.push(n.id);return n;}
for(const item of payload.items){
 const number=/^[0-9]+$/.test(item.number)?String(Number(item.number)):item.number;
 const card=stack(panel,cfg.explanation_panel_width,number+'｜'+item.problem);
 card.paddingTop=cfg.card_padding_vertical;card.paddingBottom=cfg.card_padding_vertical;
 card.paddingLeft=cfg.card_padding_horizontal;card.paddingRight=cfg.card_padding_horizontal;
 card.itemSpacing=cfg.card_gap;card.cornerRadius=cfg.card_radius;
 card.fills=[{type:'SOLID',color:color(payload.style.card_background)}];
 const w=cfg.explanation_panel_width-2*cfg.card_padding_horizontal;
 const pending=item.status==='not_verified';
 const qualifier=pending?' · 待核实':(item.status==='observed'?'':' · 需要修改');
 const title=text(card,w,number+'｜'+item.problem.replace(/。$/,'')+qualifier,true);
 const point=text(card,w,'问题点：'+(item.problem_point??item.impact));
 const basis=stack(card,w,'官方依据');basis.paddingTop=cfg.basis_padding_top;basis.itemSpacing=cfg.basis_line_gap;
 const links=[];let summary=null,unavailable=null;
 if(item.official_urls.length){
  for(const url of item.official_urls)links.push(text(basis,w,'官方依据 ↗',false,url).id);
  summary=text(basis,w,item.requirement_wording);
 }else unavailable=text(basis,w,'官方依据：暂无可直接判定的条款');
 let verification=null;if(pending)verification=text(card,w,'待核实：'+item.verification_note);
 mappings.push({number:item.number,display_number:number,explanation_card_node:card.id,
  explanation_title_node:title.id,problem_point_node:point.id,basis_container_node:basis.id,
  basis_link_nodes:links,basis_summary_node:summary?.id,basis_unavailable_node:unavailable?.id,
  verification_note_node:verification?.id,explanation_body_nodes:[point.id,...links,summary?.id,unavailable?.id,verification?.id].filter(Boolean)});
}
return {mutatedNodeIds:[panel.id],createdNodeIds:created,removedNodeIds:removed,explanation_mappings:mappings};
'''

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('report_dir');p.add_argument('context_id');p.add_argument('panel_id');a=p.parse_args()
 print(generate(a.report_dir,a.context_id,a.panel_id))
