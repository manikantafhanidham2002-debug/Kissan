"""Capture the supplied Kissan site's public content and an auditable asset inventory."""
import concurrent.futures, hashlib, json, re, urllib.request, urllib.parse, time
from pathlib import Path
from lxml import html

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'research/pages'; CACHE.mkdir(parents=True,exist_ok=True)
ORIGIN='https://www.kissan.in'
def fetch(url):
    path=CACHE/(hashlib.sha256(url.encode()).hexdigest()[:18]+'.html')
    if path.exists(): return url,path.read_text(),None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=35) as res: body=res.read().decode()
            path.write_text(body)
            return url,body,None
        except Exception as e:
            if attempt==2: return url,'',str(e)
    return url,'','Failed'

def links(body):
    doc=html.fromstring(body)
    found=set()
    for href in doc.xpath('//a/@href'):
        u=urllib.parse.urljoin(ORIGIN,href)
        if u.startswith(ORIGIN+'/') and re.match(r'^/(home|products|recipes|our-story|contact-us|sitemap|p/|r/)',urllib.parse.urlsplit(u).path) and '.html' in u:
            found.add(u.split('#')[0].split('?')[0])
    return found

def main():
    done={}; failures={}; pending={ORIGIN+'/home.html',ORIGIN+'/recipes.html',ORIGIN+'/products.html'}
    api=ROOT/'research/recipes-api.json'
    if api.exists():
        records=json.loads(json.loads(api.read_text())['recipeByGroups'])
        for record in records:
            recipe=record['recipeData']
            pending.add(ORIGIN+'/r/'+recipe['shortTitle']+'.html/'+recipe['recipeID'])
    while pending:
        batch=sorted(pending-set(done)-set(failures)); pending=set()
        if not batch: break
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for url,body,err in pool.map(fetch,batch):
                if err: failures[url]=err; print('FAILED',url,err,flush=True); continue
                done[url]={'file':str(CACHE/(hashlib.sha256(url.encode()).hexdigest()[:18]+'.html')),'bytes':len(body)}
                pending.update(links(body))
                print('OK',len(done),url,flush=True)
        (ROOT/'research/pages.json').write_text(json.dumps({'pages':done,'failures':failures},indent=2))
        if len(done)>300: raise RuntimeError('Unexpected crawl size')
    print('COMPLETE',len(done),'pages',len(failures),'failures',flush=True)
if __name__=='__main__': main()
