"""Validate actual Figma annotations against report.json before publication.

Usage: python3 validate_figma_annotations.py REPORT_DIR
figma-readback.json: nodes with id, type, x, y, width, height, children,
and text, fontSize, fontName, fills for TEXT nodes; layoutMode, itemSpacing,
paddingLeft/Right/Top/Bottom, cornerRadius and fills for frames.
(Also accepts use_figma content[0].text JSON.)
annotation-map.json: {"annotations": [{"context_id": ..., "section": 2 or 3,
"page_id": ..., "number": ..., "bbox_px": [x,y,w,h], "image_node": ...,
"image_crop_px": [x,y,w,h], "badge_node": ..., "badge_text_node": ...,
"target_node": ..., "leader_node": ..., "explanation_title_node": ...,
"explanation_body_nodes": [...], "problem_point_node": ...,
"basis_link_nodes": [...], "basis_summary_node": ...,
"verification_note_node": ...}]}.
Include explanation_card_node and basis_container_node from the renderer.
Read back url and textDecoration on basis-link TEXT nodes. If no related
official clause exists, use basis_unavailable_node instead of links.
Section 3 uses caption_node instead of explanation nodes. Crop is optional
when the full image is displayed. All positions in the readback are local.
"""
import argparse,json
from pathlib import Path

def require(ok,message):
 if not ok:raise ValueError(message)

def validate(root):
 root=Path(root);report=json.loads((root/'report.json').read_text(encoding='utf-8'))
 style=json.loads((Path(__file__).resolve().parents[1]/'assets/report-style.json').read_text(encoding='utf-8'));cfg=style['figma']
 raw=json.loads((root/'figma-readback.json').read_text(encoding='utf-8'))
 if isinstance(raw,dict) and 'content' in raw:raw=json.loads(raw['content'][0]['text'])
 if isinstance(raw,dict):raw=[raw]
 nodes={}
 def walk(n,x=0,y=0,clips=()):
  x+=n.get('x',0);y+=n.get('y',0)
  box=[x,y,n.get('width',0),n.get('height',0)]
  nodes[n['id']]={**n,'absolute':box,'clipping_ancestors':clips}
  inherited=clips+(tuple(box),) if n.get('clipsContent') else clips
  for child in n.get('children',[]):walk(child,x,y,inherited)
 for node in raw:walk(node)
 expected={}
 for board in report['artboards']:
  for index,section in enumerate(board['sections'],1):
   if index not in (2,3):continue
   for page in section.get('pages',[])+section.get('pending_observations',[]):
    for ann in page.get('annotations',[]):
     key=(board['context_id'],index,page['page_id'],ann['number'],tuple(ann['bbox_px']))
     expected[key]=(page,ann)
 mappings=json.loads((root/'annotation-map.json').read_text(encoding='utf-8'))['annotations'];actual=set();image_origins={}
 for m in mappings:
  key=(m['context_id'],m['section'],m['page_id'],m['number'],tuple(m['bbox_px']))
  require(key in expected and key not in actual,'多余或重复标注映射：'+str(key));actual.add(key)
  page,ann=expected[key]
  def node(field):
   require(m.get(field) in nodes,'缺少实际节点：'+field+' '+str(key))
   n=nodes[m[field]];nx,ny,nw,nh=n['absolute']
   require(all(nx>=cx-.5 and ny>=cy-.5 and nx+nw<=cx+cw+.5 and ny+nh<=cy+ch+.5 for cx,cy,cw,ch in n['clipping_ancestors']),'标注或说明被父容器裁切：'+field)
   return n
  image=node('image_node');badge=node('badge_node');label=node('badge_text_node')
  target=node('target_node');leader=node('leader_node')
  display_number=str(int(m['number'])) if m['number'].isdigit() else m['number']
  require(label.get('text','').strip()==display_number,'截图编号不匹配：'+str(key))
  require(badge['type']=='ELLIPSE' and label['type']=='TEXT','编号须为可编辑圆形和文字')
  require(leader['type']=='LINE' and target['type']=='RECTANGLE','缺少可编辑引线或位置框')
  ix,iy,iw,ih=image['absolute'];bx,by,bw,bh=badge['absolute']
  require(bx+bw<=ix or bx>=ix+iw or by+bh<=iy or by>=iy+ih,'编号覆盖截图：'+str(key))
  lx,ly,lw,lh=label['absolute']
  require(bx<=lx and by<=ly and lx+lw<=bx+bw+.5 and ly+lh<=by+bh+.5,'数字未放在圆形编号内')
  crop=m.get('image_crop_px',[0,0,page['width_px'],page['height_px']]);cx,cy,cw,ch=crop
  require(abs(iw/ih-cw/ch)<.01,'截图显示比例与原图不一致：'+str(key))
  # Same-context figures of the same size must not move when a badge changes side.
  cohort=(m['context_id'],m['section'],round(iw,2),round(ih,2))
  origin=image.get('x',0)
  require(cohort not in image_origins or abs(image_origins[cohort]-origin)<=.5,
          '同列图框原点不一致；不能因标号换侧单独平移截图：'+str(key))
  image_origins[cohort]=origin
  x,y,w,h=ann['bbox_px'];wanted=[ix+(x-cx)*iw/cw,iy+(y-cy)*ih/ch,w*iw/cw,h*ih/ch]
  require(all(abs(a-b)<=3 for a,b in zip(target['absolute'],wanted)),'位置框与原图坐标不匹配：'+str(key))
  if m['section']==2:
   title=node('explanation_title_node').get('text','')
   require(title.startswith(display_number+'｜'),'右侧说明缺同号标题：'+str(key))
   card=node('explanation_card_node');basis=node('basis_container_node')
   for field,value in {'layoutMode':'VERTICAL','paddingLeft':cfg['card_padding_horizontal'],'paddingRight':cfg['card_padding_horizontal'],'paddingTop':cfg['card_padding_vertical'],'paddingBottom':cfg['card_padding_vertical'],'itemSpacing':cfg['card_gap'],'cornerRadius':cfg['card_radius'],'width':cfg['explanation_panel_width']}.items():
    require(card.get(field)==value,'说明卡偏离 Duo 模板：'+field)
   def painted(n,hexcolor):
    wanted=[int(hexcolor[i:i+2],16)/255 for i in (1,3,5)]
    return any(f.get('type')=='SOLID' and f.get('visible',True) and f.get('opacity',1)==1 and all(abs(f['color'][c]-v)<.002 for c,v in zip('rgb',wanted)) for f in n.get('fills',[]))
   require(painted(card,style['card_background']),'说明卡缺模板浅灰底')
   require(basis.get('paddingTop')==cfg['basis_padding_top'] and basis.get('itemSpacing')==cfg['basis_line_gap'],'依据区间距偏离模板')
   body_ids=m.get('explanation_body_nodes',[])
   require(body_ids and all(i in nodes and nodes[i].get('text','').strip() for i in body_ids),'缺少说明正文：'+str(key))
   for i in [m['explanation_title_node']]+body_ids:
    t=nodes[i];heading=i==m['explanation_title_node']
    tx,ty,tw,th=t['absolute']
    require(all(tx>=cx-.5 and ty>=cy-.5 and tx+tw<=cx+cw+.5 and ty+th<=cy+ch+.5 for cx,cy,cw,ch in t['clipping_ancestors']),'说明被父容器裁切：'+i)
    require(t.get('fontSize')==(cfg['card_heading_font_size'] if heading else cfg['body_font_size']),'说明字号偏离 Duo 模板')
    require(t.get('fontName',{}).get('family')==cfg['font_family'] and t.get('fontName',{}).get('style')==('Bold' if heading else 'Regular'),'说明字体偏离模板')
    require(painted(t,style['link'] if i in m.get('basis_link_nodes',[]) else style['card_text']),'说明文字颜色偏离模板')
   require(node('problem_point_node').get('text','').startswith('问题点：'),'说明须使用问题点字段：'+str(key))
   explanation=next((e for e in page.get('explanations',[]) if e['number']==m['number']),None)
   require(explanation and explanation['problem'].rstrip('。') in title,'说明标题与报告的问题类型不一致')
   point=node('problem_point_node')
   require(point.get('text','')[4:].strip()==explanation.get('problem_point',explanation.get('impact','')).strip(),'问题点与报告不一致')
   require(node('explanation_title_node')['absolute'][1]<point['absolute'][1],'标题与问题点顺序错误')
   links=m.get('basis_link_nodes',[])
   if links:
    for i in links:
     require(i in nodes,'缺官方依据链接节点')
     link=nodes[i]
     require(link.get('text')=='官方依据 ↗' and link.get('url','').startswith('https://developer.android.com/'),'缺独立 Google 官方依据链接')
     require(link.get('textDecoration')=='UNDERLINE','官方依据链接缺下划线')
    require(node('basis_summary_node').get('text','').strip(),'缺官方标准摘要')
    require({nodes[i]['url'] for i in links}==set(explanation['official_urls']),'官方依据链接与报告不一致')
    require(point['absolute'][1]<nodes[links[0]]['absolute'][1]<node('basis_summary_node')['absolute'][1],'问题点、依据链接、标准摘要顺序错误')
   else:
    require(node('basis_unavailable_node').get('text','').startswith('官方依据：暂无可直接判定的条款'),'缺官方依据或明确的条款缺口')
   if ann.get('status')=='not_verified':
    require('待核实' in title,'待核实状态未显示：'+str(key))
    require(node('verification_note_node').get('text','').startswith('待核实：'),'待核实项缺判断依据缺口')
  else:require(display_number in node('caption_node').get('text',''),'汇总页缺编号文字')
 require(actual==set(expected),'遗漏标号或文字说明：'+str(set(expected)-actual))
 return len(actual)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('report_dir');args=p.parse_args()
 try:print('标注验收通过：',validate(args.report_dir),'处；仍须目视核对引线和可读性。')
 except (ValueError,KeyError,TypeError,OSError) as e:p.error(str(e))
