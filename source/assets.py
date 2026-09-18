"""Keep every distinct image referenced by the captured public pages."""
import concurrent.futures, hashlib, io, json, re, urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/assets'; OUT.mkdir(parents=True,exist_ok=True)
def canonical(u): return u.split('?')[0].replace('&amp;','&')
def get_images(soup):
    out=[]
    for el in soup.find_all(['img','source']):
        for key in ['src','data-src','srcset','data-srcset']:
            u=el.get(key,'')
            if u.startswith('https://assets.unileversolutions.com/'):
                u=canonical(u)
                if u not in out: out.append(u)
    for el in soup.select('[style]'):
        for u in re.findall(r'https://assets\.unileversolutions\.com/[^\s\)\"\']+',el.get('style','')):
            u=canonical(u)
            if u not in out: out.append(u)
    return out

def main():
    urls=set(); pages={}
    for p in (ROOT/'research/pages').glob('*.html'):
        soup=BeautifulSoup(p.read_text(),'lxml')
        imgs=get_images(soup); urls.update(imgs); pages[p.name]=imgs
    api=json.loads((ROOT/'research/recipes-api.json').read_text())
    for item in json.loads(api['recipeByGroups']):
        urls.update(v['default']['url'] for v in item['recipeData'].get('newImage',[]) if 'default' in v)
    cached={}
    supplied=Path('/workspace/scratch/af137030c8a7/research/assets.json')
    if supplied.exists(): cached={x['url']:x['path'] for x in json.loads(supplied.read_text())}
    old_path=ROOT/'research/assets.json'
    old=json.loads(old_path.read_text()).get('assets',{}) if old_path.exists() else {}
    def download(u):
        if u in old and (ROOT/'dist'/old[u]['local'].lstrip('/')).exists(): return u,old[u],None
        name=('recipe-' if '/recipes-' in u else '')+Path(u).stem+'-'+hashlib.sha256(u.encode()).hexdigest()[:6]+'.webp'
        for attempt in range(3):
            try:
                if u in cached: raw=Path(cached[u]).read_bytes()
                else:
                    req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
                    raw=urllib.request.urlopen(req,timeout=45).read()
                im=Image.open(io.BytesIO(raw)); size=im.size
                im.thumbnail((1800,1800),Image.Resampling.LANCZOS)
                if im.mode not in ('RGB','RGBA'): im=im.convert('RGBA' if 'transparency' in im.info else 'RGB')
                im.save(OUT/name,'WEBP',quality=90,method=4)
                return u,{'local':'/assets/'+name,'original_size':size,'display_size':im.size,'bytes':(OUT/name).stat().st_size},None
            except Exception as e:
                if attempt==2: return u,None,str(e)
    assets={}; failures={}
    print('IMAGES',len(urls),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=14) as pool:
        for u,data,err in pool.map(download,sorted(urls)):
            if err: failures[u]=err; print('FAILED',u,err,flush=True)
            else: assets[u]=data
            if (len(assets)+len(failures))%20==0:
                print('DOWNLOADED',len(assets),'of',len(urls),flush=True)
                old_path.write_text(json.dumps({'assets':assets,'failures':failures,'page_images':pages},indent=2))
    old_path.write_text(json.dumps({'assets':assets,'failures':failures,'page_images':pages},indent=2))
    print('COMPLETE',len(assets),'images',len(failures),'failures',flush=True)
if __name__=='__main__': main()
