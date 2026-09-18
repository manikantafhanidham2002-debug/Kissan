import json, re
from pathlib import Path
from bs4 import BeautifulSoup
from assets import get_images

ROOT=Path(__file__).resolve().parents[1]
def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower().replace('&',' and ')).strip('-')
def text(s): return BeautifulSoup(str(s or ''),'html.parser').get_text(' ',strip=True)
def main():
    manifest=json.loads((ROOT/'research/pages.json').read_text())
    api=json.loads(json.loads((ROOT/'research/recipes-api.json').read_text())['recipeByGroups'])
    order={r['recipeData']['recipeID']:i for i,r in enumerate(api)}
    products=[]; recipes={}; pages={}
    for url,meta in manifest['pages'].items():
        soup=BeautifulSoup(Path(meta['file']).read_text(),'lxml')
        path=url.replace('https://www.kissan.in','')
        tiles=[]
        for a in soup.select('.pagelist a.cmp-teaser__link'):
            imgs=get_images(a)
            if imgs: tiles.append({'path':a.get('href'),'name':a.get_text(' ',strip=True),'image':imgs[0]})
        pages[path]={'source':url,'images':get_images(soup),'title':text(soup.title).split(' | ')[0],'tiles':tiles}
        for script in soup.find_all('script',type='application/ld+json'):
            try: schema=json.loads(script.string or script.get_text())
            except Exception: continue
            if schema.get('@type')=='Product' and path.startswith('/p/'):
                variants=[]
                for button in soup.select('.product-variant-selector'):
                    gtin=button.get('data-gtin')
                    gal=soup.select_one('.product-media-gallary[data-gtin="'+gtin+'"]')
                    variants.append({'gtin':gtin,'size':button.get_text(' ',strip=True),'images':get_images(gal) if gal else []})
                name=schema['name']; ingredients=schema.get('gs1:ingredientStatement',{}).get('@value','')
                p={'name':name,'slug':slug(name),'path':'/product/'+slug(name)+'/','source':url,'sourcePath':path,'category':schema.get('category',''),'description':text(schema.get('description','')),'ingredients':ingredients,'variants':variants,'images':list(dict.fromkeys(i for v in variants for i in v['images'])),'sku':schema.get('sku'),'country':schema.get('countryOfOrigin',{}).get('name','')}
                if not p['images']:
                    p['images']=[i for i in pages[path]['images'] if '/v1/' in i and not any(n in i for n in ['130211196','123738663'])][:1]
                products.append(p)
            if schema.get('@type')=='Recipe':
                rid=path.split('/')[-1]
                if rid in recipes:
                    recipes[rid]['aliases'].append(path)
                    continue
                def steps(items):
                    out=[]
                    for item in items:
                        if isinstance(item,str): out.append(text(item))
                        elif 'itemListElement' in item: out+=steps(item['itemListElement'])
                        elif 'text' in item: out.append(text(item['text']))
                    return out
                name=schema['name']; key=schema.get('keywords','').lower()
                tags=[x.strip() for x in key.split(',') if x.strip()]
                tags=[t.replace('rolls & warps','rolls & wraps').replace('quick recipe','quick recipes') if t=='quick recipe' or 'warps' in t else t for t in tags]
                record=next((r['recipeData'] for r in api if r['recipeData']['recipeID']==rid),{})
                primary=next((e.get('src') or e.get('data-src') for e in soup.find_all('img') if '/recipes-v3/'+rid+'-' in (e.get('src','')+e.get('data-src',''))),None)
                if not primary: primary=record.get('newImage',[{}])[0].get('default',{}).get('url')
                recipes[rid]={'id':rid,'name':name,'slug':slug(name),'path':'/recipes/'+slug(name)+'/','source':url,'sourcePath':path,'aliases':[path],'image':primary,'description':text(schema.get('description','')),'prep':record.get('prepTime',''),'cook':record.get('cookTime',''),'total':record.get('totalTime',''),'servings':schema.get('recipeYield',''),'tags':tags,'ingredients':[text(v) for v in schema.get('recipeIngredient',[])],'steps':steps(schema.get('recipeInstructions',[])),'nutrition':{k:v for k,v in schema.get('nutrition',{}).items() if not k.startswith('@')},'order':order.get(rid,999),'difficulty':', '.join(record.get('difficulty',[]))}
    products.sort(key=lambda p:({'Fresh Tomato Ketchup':0,'Mixed Fruit Jam':1,'Peanut Butter':2,'Juicy Lemon Squash':3}.get(p['name'],10),p['name']))
    data={'products':products,'recipes':sorted(recipes.values(),key=lambda r:r['order']),'pages':pages,'sourceTotalRecipes':len(api),'sourceTotalProducts':13,'brokenSourceLinks':manifest['failures']}
    (ROOT/'source/content.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    print('CONTENT',len(products),'products',len(recipes),'recipes',sum(len(p['variants']) for p in products),'pack choices')
    print('INCOMPLETE',[(r['name'],len(r['ingredients']),len(r['steps'])) for r in recipes.values() if not r['image'] or not r['ingredients'] or not r['steps']])
if __name__=='__main__': main()
