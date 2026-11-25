"""Sample and finalize Android recording evidence, without deciding adaptation defects."""
import argparse,hashlib,json,math,shutil,struct,subprocess,sys
from pathlib import Path
from image_batches import candidate_plan
from sequential_frames import sequential_sample, extract_frame, probe as shared_probe

VERSION='0.2.9'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def run(args):
    r=subprocess.run(args,text=True,capture_output=True)
    require(r.returncode==0,r.stderr[-2000:] or '命令失败')
    return r.stdout

def probe(video):
    return shared_probe(video)

def frame(video,time,output):
    return extract_frame(video,time,output)

def sample(video,out,interval,keep_all=False):
    require(interval>=0.1,'采样间隔至少 0.1 秒；更短动作可按时间补帧')
    out=Path(out).resolve();require(not out.exists(),'候选目录已存在；新建目录保留旧结果')
    out.mkdir(parents=True);(out/'source').mkdir();(out/'candidates').mkdir()
    source=out/'source'/('recording'+Path(video).suffix.lower());shutil.copyfile(video,source)
    meta=probe(source);items=[]
    for row in sequential_sample(source,out/'candidates',interval):
        path=Path(row['path'])
        items.append({**row,'id':path.stem,'path':str(path.relative_to(out))})
    plan,representatives=candidate_plan(items,24,keep_all)
    write(out/'candidate-groups.json',plan)
    sheet_input=out/'sheet-input';sheet_input.mkdir()
    for i,item in enumerate(representatives):
        shutil.copyfile(out/item['path'],sheet_input/('frame-%05d.png'%i))
    run(['ffmpeg','-v','error','-i',str(sheet_input/'frame-%05d.png'),
         '-vf','scale=200:300:force_original_aspect_ratio=decrease,pad=200:300:(ow-iw)/2:(oh-ih)/2,tile=6x4:padding=8:margin=8','-vsync','0',str(out/'contact-sheet-%03d.png')])
    write(out/'sample.json',{'schema_version':1,'capture_version':VERSION,'video':str(source.relative_to(out)),
          'video_sha256':sha(source),'metadata':meta,'interval_s':interval,'decoder':'sequential-source-pts-v1','candidates':items,'candidate_groups':'candidate-groups.json'})
    print('候选帧',len(items),'张；拼图代表帧',len(representatives),'张；须展开分组分类全部候选并补查时间间隔，尚未确认页面。')

def finalize(out,selection):
    out=Path(out).resolve();source=read(out/'sample.json');spec=read(selection)
    require(not (out/'capture.json').exists(),'capture.json 已存在；修订请使用新的运行目录')
    video=out/source['video'];require(sha(video)==source['video_sha256'],'原始录屏改变')
    require(spec.get('capture_review',{}).get('all_candidates_classified') is True and
            spec['capture_review'].get('all_intervals_reviewed') is True and spec['capture_review'].get('notes'),
            '需完成所有候选及时间间隔的回查')
    classifications=spec.get('candidate_classifications',[])
    require({c.get('id') for c in classifications}=={c['id'] for c in source['candidates']},'每个候选都须分类')
    require(len(classifications)==len(source['candidates']) and all(c.get('classification') in
            ['app_state','duplicate_same_context','transition','loading','external','other'] and c.get('reason') for c in classifications),'候选分类无效或缺理由')
    for c in source['candidates']:require(sha(out/c['path'])==c['sha256'],'候选图片改变: '+c['id'])
    contexts=spec.get('contexts',[]);ids=[c.get('id') for c in contexts]
    require(ids and len(ids)==len(set(ids)),'上下文 id 缺失或重复')
    pages=spec.get('pages',[]);pids=[p.get('id') for p in pages]
    require(pids and len(pids)==len(set(pids)),'页面 id 缺失或重复')
    (out/'images').mkdir(exist_ok=True);evidence=[];result_pages=[]
    for p in pages:
        require(p.get('context_id') in ids and p.get('name') and p.get('selection_reason'),'页面缺状态、名称或选帧理由')
        target=out/'images'/('page-%04d.png'%len(result_pages))
        candidate_id=p.get('candidate_id')
        matches=[c for c in source['candidates'] if (c['id']==candidate_id if candidate_id else abs(c['time_s']-float(p['time_s']))<1e-6)]
        if candidate_id:require(len(matches)==1 and abs(matches[0]['time_s']-float(p['time_s']))<1e-6,'候选与选帧时间不符')
        if source.get('decoder')=='sequential-source-pts-v1' and matches:
            shutil.copyfile(out/matches[0]['path'],target);w,h=struct.unpack('>II',target.read_bytes()[16:24])
        else:w,h=frame(video,float(p['time_s']),target)
        eid='image-'+p['id']
        evidence.append({'id':eid,'kind':'image','path':str(target.relative_to(out)),'sha256':sha(target),
                         'description':p['selection_reason'],'page_ids':[p['id']],'context_ids':[p['context_id']],
                         'width_px':w,'height_px':h,'source_time_s':p['time_s']})
        result_pages.append({'id':p['id'],'name':p['name'],'context_id':p['context_id'],'image_evidence_id':eid,'logical_page_id':p.get('logical_page_id'),'scroll_state':p.get('scroll_state'),
                             'components':[],'facts':{},'capture_state':p.get('state','')})
    for i,t in enumerate(spec.get('transitions',[])):
        require(0<=t['start_s']<t['end_s']<=source['metadata']['duration_s'],'连续片段超出时长')
        require(t.get('page_ids') and set(t['page_ids'])<=set(pids),'连续片段需关联已采集页面')
        require(t.get('context_ids') and set(t['context_ids'])<=set(ids),'连续片段需关联实际环境')
        require(t.get('actions') and t.get('before_state') and t.get('after_state'),'连续片段缺动作与前后状态')
        evidence.append({**t,'id':t.get('id','transition-%03d'%i),'kind':'transition_clip',
                         'path':source['video'],'sha256':source['video_sha256'],'description':t.get('description','连续操作证据')})
    # Extra actual measurements/runtime/receiver records remain distinct from source recording.
    for e in spec.get('additional_evidence',[]):
        f=Path(e['path'])
        if not f.is_absolute():f=Path(selection).resolve().parent/f
        require(f.is_file() and sha(f)==e.get('sha256'),'附加证据不存在或 hash 不符')
        evidence.append({**e,'path':str(f.resolve())})
    require(len({e['id'] for e in evidence})==len(evidence),'证据 id 重复')
    capture={'schema_version':1,'capture_version':VERSION,'contexts':contexts,'evidence':evidence,
             'pages':result_pages,'facts':spec.get('facts',{}),'capture_review':spec['capture_review'],
             'source_recordings':[{'path':source['video'],'sha256':source['video_sha256'],'metadata':source['metadata']}]}
    write(out/'capture.json',capture)
    print('完成',len(pages),'个页面状态与',len(spec.get('transitions',[])),'段连续证据；尚未判断规范。')

def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    a=s.add_parser('sample');a.add_argument('video');a.add_argument('run_dir');a.add_argument('--interval',type=float,default=1);a.add_argument('--keep-all-candidates',action='store_true')
    a=s.add_parser('frame');a.add_argument('video');a.add_argument('seconds',type=float);a.add_argument('output')
    a=s.add_parser('finalize');a.add_argument('run_dir');a.add_argument('selection')
    args=p.parse_args()
    try:
        require(shutil.which('ffmpeg') and shutil.which('ffprobe'),'需要可用的 ffmpeg 和 ffprobe')
        if args.command=='sample':sample(args.video,args.run_dir,args.interval,args.keep_all_candidates)
        elif args.command=='frame':frame(args.video,args.seconds,args.output)
        else:finalize(args.run_dir,args.selection)
    except (ValueError,KeyError,TypeError,OSError) as e:p.error(str(e))
if __name__=='__main__':main()
