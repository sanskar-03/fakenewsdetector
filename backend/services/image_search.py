import io, os, json, requests
from PIL import Image

_CLIP=None
_PROCESSOR=None

def _bing_visual(url, timeout):
    key=os.getenv('BING_VISUAL_SEARCH_KEY') or os.getenv('BING_SUBSCRIPTION_KEY')
    if not key: return None
    endpoint='https://api.bing.microsoft.com/v7.0/images/visualsearch'
    headers={'Ocp-Apim-Subscription-Key':key,'User-Agent':'Aletheia/4.0'}
    knowledge=json.dumps({'imageInfo':{'url':url}})
    try:
        r=requests.post(endpoint,headers=headers,params={'mkt':'en-us'},files={'knowledgeRequest':(None,knowledge)},timeout=timeout); r.raise_for_status(); data=r.json(); results=[]
        for tag in data.get('tags',[]):
            for action in tag.get('actions',[]):
                vals=(action.get('data') or {}).get('value') or []
                if isinstance(vals,dict): vals=[vals]
                for item in vals:
                    if isinstance(item,dict):
                        page=item.get('hostPageUrl') or item.get('webSearchUrl') or item.get('url') or ''
                        image=item.get('contentUrl') or item.get('thumbnailUrl') or ''
                        if page or image: results.append({'page_url':page,'image_url':image,'action':action.get('actionType','')})
        seen=set(); clean=[]
        for x in results:
            k=x.get('page_url') or x.get('image_url')
            if k and k not in seen: seen.add(k); clean.append(x)
        return {'provider':'bing_visual_search','status':'LIVE_RESULTS','results':clean[:30],'total_results':len(clean)}
    except Exception as exc: return {'provider':'bing_visual_search','status':'ERROR','results':[],'total_results':0,'error':str(exc)}

def _clip_consistency(image, claim):
    global _CLIP,_PROCESSOR
    if not claim: return None
    try:
        from transformers import CLIPModel, CLIPProcessor
        import torch
        if _CLIP is None:
            _CLIP=CLIPModel.from_pretrained('openai/clip-vit-base-patch32'); _PROCESSOR=CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32'); _CLIP.eval()
        inputs=_PROCESSOR(text=[claim],images=image,return_tensors='pt',padding=True)
        with torch.no_grad():
            out=_CLIP(**inputs)
            img=out.image_embeds; txt=out.text_embeds
            img=img/img.norm(dim=-1,keepdim=True); txt=txt/txt.norm(dim=-1,keepdim=True)
            cosine=float((img*txt).sum(dim=-1)[0])
        normalized=max(0.0,min(1.0,(cosine+1.0)/2.0))
        return {'model':'openai/clip-vit-base-patch32','cosine_similarity':round(cosine,4),'claim_consistency':round(normalized,4),
                'status':'CONSISTENT' if normalized>=0.60 else 'LOW_CONSISTENCY'}
    except Exception as exc: return {'status':'UNAVAILABLE','error':str(exc)}

def verify_image(url, known_images=None, threshold=8, timeout=8, claim=None):
    import imagehash
    r=requests.get(url,timeout=timeout,headers={'User-Agent':'Mozilla/5.0 Aletheia/4.0'}); r.raise_for_status()
    image=Image.open(io.BytesIO(r.content)).convert('RGB'); target=imagehash.phash(image); matches=[]
    for item in known_images or []:
        try:
            rr=requests.get(item,timeout=timeout,headers={'User-Agent':'Mozilla/5.0 Aletheia/4.0'}); rr.raise_for_status(); h=imagehash.phash(Image.open(io.BytesIO(rr.content)).convert('RGB')); d=target-h
            if d<=threshold: matches.append({'url':item,'distance':d,'match_type':'reference_hash'})
        except Exception: pass
    semantic=_clip_consistency(image,claim)
    live=_bing_visual(url,timeout)
    status='MATCH' if matches else ('LIVE_RESULTS' if live and live.get('status')=='LIVE_RESULTS' and live.get('total_results',0)>0 else 'NO_MATCH')
    return {'status':status,'verified':bool(matches),'hash':str(target),'threshold':threshold,'matches':matches,'total_matches':len(matches),
            'semantic_consistency':semantic,'live_visual':live,'note':'Visual search/context consistency is not proof that an image is authentic.'}
