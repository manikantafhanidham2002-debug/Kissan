"""Author the redesigned, fully static Kissan catalogue from the captured content."""
import json, re, html, shutil
from pathlib import Path
from urllib.parse import quote_plus, urlsplit

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'dist'
D=json.loads((ROOT/'source/content.json').read_text())
A=json.loads((ROOT/'research/assets.json').read_text())['assets'] if (ROOT/'research/assets.json').exists() else json.loads((ROOT/'source/assets-manifest.json').read_text())
USED=set(); ROUTES=[]; REDIRECTS={}
P=D['products']; R=D['recipes']; PAGES=D['pages']
ORIGIN='https://www.kissan.in'
def esc(s): return html.escape(str(s or ''),quote=True)
def asset(u):
    u=u.split('?')[0]; USED.add(u)
    if u not in A: raise ValueError('Missing asset '+u)
    return A[u]['local']
def img(u,alt='',cls='',eager=False):
    v=A[u.split('?')[0]]; w,h=v['display_size']
    return f'<img src="{asset(u)}" alt="{esc(alt)}" class="{cls}" width="{w}" height="{h}" loading="{"eager" if eager else "lazy"}" decoding="async">'
def local_img(path,alt='',cls='',width=1347,height=324):
    return f'<img src="{path}" alt="{esc(alt)}" class="{cls}" width="{width}" height="{height}" loading="eager" decoding="async">'
LOCAL_IMAGE_DIMENSIONS={
    '/assets/kissan-kimchi-kurrentt-spread-v2.png': (1254,1254),
    '/assets/kissan-kimchi-kurrentt-spread-transparent.png': (500,500),
    '/assets/kissan-kimchi-kurrentt-spread-200g.png': (1024,1536),
    '/assets/kissan-kimchi-kurrentt-promotion-benefits.png': (1536,1024),
    '/assets/kissan-kimchi-kurrentt-hero-poster.png': (1122,1402),
    '/assets/kissan-products-lineup.png': (976,270),
}
def product_img(u,alt='',cls='',eager=False):
    if str(u).startswith('/assets/'):
        w,h=LOCAL_IMAGE_DIMENSIONS.get(str(u),(1200,1200))
        local_cls=' '.join(x for x in [cls,'custom-product-image'] if x)
        return local_img(str(u),alt,local_cls,w,h)
    return img(u,alt,cls,eager)
def image_ref(u):
    return str(u) if str(u).startswith('/assets/') else asset(u)
def v1(n): return 'https://assets.unileversolutions.com/v1/'+n
def icon(name):
    paths={'search':'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>','clock':'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>','menu':'<path d="M4 6h16M4 12h16M4 18h16"/>','close':'<path d="m6 6 12 12M6 18 12 6"/>','print':'<path d="M7 8V3h10v5M7 17H4V9h16v8h-3M7 14h10v7H7z"/>','share':'<path d="M12 16V3m-5 5 5-5 5 5M5 13v8h14v-8"/>'}
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+paths[name]+'</svg>'
LOGO=v1('130211196.jpg'); STORY=v1('2329972.jpg'); GENERIC=v1('2341289.jpg')
CATS=[('Ketchup & Sauces','ketchup-sauces','83830788.png'),('Jam','jam','85811802.png'),('Peanut Butter','peanut-butter','103958413.png'),('Squash','squash','93426288.png')]
PRICE_TABLE={
    'Fresh Tomato Ketchup':[149,69,129,249,279,139,39],
    'Mixed Fruit Jam':[125,35,65,165,215],
    'Peanut Butter':[199],
    'Juicy Lemon Squash':[149],
    'Chilli Tomato Sauce':[119,59],
    'Juicy Grape Squash':[149],
    'Juicy Mango Squash':[149],
    'Juicy Orange Squash':[149],
    'Mango Jam':[125,55],
    'No Onion No Garlic Tomato Sauce':[149,249,69],
    'Orange Marmalade':[135],
    'Pineapple Jam':[125],
    'Sweet & Spicy Sauce':[199,69],
    'Kimchi Kurrenttt Spread':[199],
}
RETAILER_URLS=[
    ('BigBasket','https://www.bigbasket.com/ps/?q='),
    ('Blinkit','https://blinkit.com/s/?q='),
    ('Amazon','https://www.amazon.in/s?k='),
]
def variant_price(p,v,index=0):
    raw=v.get('price') if isinstance(v,dict) else None
    if raw is not None:
        try: return int(float(str(raw).replace('₹','').replace(',','').strip()))
        except (TypeError,ValueError): pass
    values=PRICE_TABLE.get(p['name'],[])
    if index < len(values): return values[index]
    return 99
def retailer_url(platform_base,p,v):
    query=quote_plus(f"Kissan {p['name']} {v['size']}")
    return platform_base+query
for p in P: REDIRECTS[p['sourcePath']]=p['path']
for r in R:
    for a in r['aliases']: REDIRECTS[a]=r['path']
REDIRECTS['/p/sweet-spicy-sauce.html/08901030660320']=next(p['path'] for p in P if p['name']=='Sweet & Spicy Sauce')

def header():
    catlinks=''.join(f'<a href="/products/{s}.html">{esc(n)}</a>' for n,s,_ in CATS)
    return f'''<a class="skip-link" href="#main">Skip to content</a><div class="announcement">Bringing a little happiness to every meal.</div><header class="site-header"><nav class="wrap nav" aria-label="Main navigation"><a class="logo" href="/" aria-label="Kissan home">{img(LOGO,'Kissan',eager=True)}</a><div class="nav-links" id="main-nav"><details class="nav-dropdown"><summary>Our products</summary><div class="dropdown-panel"><a href="/products.html">All products</a>{catlinks}</div></details><details class="nav-dropdown"><summary>Recipes</summary><div class="dropdown-panel"><a href="/recipes.html">All recipes</a><a href="/recipes/recipes-by-course.html">By course</a><a href="/recipes/recipes-by-product.html">By product</a><a href="/recipes/quick-recipes.html">Quick recipes</a></div></details><a href="/our-story.html">Our story</a><a href="/contact-us.html">Get in touch</a></div><button class="icon-button search-open" aria-label="Search products and recipes">{icon('search')}</button><button class="icon-button menu-button" aria-label="Open menu" aria-expanded="false" aria-controls="main-nav">{icon('menu')}</button></nav></header>'''

def footer():
    products=''.join(f'<a href="/products/{s}.html">{esc(n)}</a>' for n,s,_ in CATS)
    return f'''<footer class="footer"><div class="wrap"><div class="footer-main"><div class="footer-brand"><a class="footer-logo" href="/" aria-label="Kissan home">{img(LOGO,'Kissan')}</a><p class="footer-tagline">A little Kissan.<br>A lot of happiness.</p></div><div><h3>Our favourites</h3><nav class="footer-links">{products}</nav></div><div><h3>Get inspired</h3><nav class="footer-links"><a href="/recipes.html">All recipes</a><a href="/recipes/recipes-by-course/breakfast-recipes.html">Breakfast ideas</a><a href="/recipes/recipes-by-course/snack-recipes.html">Snack time</a><a href="/recipes/quick-recipes.html">Quick recipes</a></nav></div><div><h3>Stay connected</h3><nav class="footer-links"><a href="/our-story.html">Our story</a><a href="/contact-us.html">Contact us</a><a href="/contact-us/faq.html">FAQs</a><a href="https://www.facebook.com/Kissanindia/" target="_blank" rel="noopener">Facebook ↗</a><a href="https://www.youtube.com/kissanindia" target="_blank" rel="noopener">YouTube ↗</a><a href="https://twitter.com/KissanIndia" target="_blank" rel="noopener">X / Twitter ↗</a></nav></div></div><div class="footer-bottom"><span>Kissan brand &amp; imagery © Hindustan Unilever.</span><nav><a href="/sitemap.html">Sitemap</a><a href="https://www.unilevernotices.com/privacy-notices/india-english.html" target="_blank" rel="noopener">Privacy</a><a href="https://www.unilevernotices.com/cookie-notices/india-english.html" target="_blank" rel="noopener">Cookies</a><a href="https://www.hul.co.in/legal/" target="_blank" rel="noopener">Terms of use</a><a href="/accessibility.html">Accessibility</a><button class="back-top">Back to top ↑</button></nav></div><div class="concept-note">Independent website redesign concept. For official brand information, visit <a href="https://www.kissan.in/home.html" target="_blank" rel="noopener">kissan.in</a>.</div><a href="https://www.hul.co.in/" target="_blank" rel="noopener" aria-label="Hindustan Unilever" class="unilever-mark">{img(v1('123738663.png'),'Unilever')}</a></div></footer><dialog class="search-dialog" id="search-dialog" aria-labelledby="search-title"><div class="search-dialog-head"><h2 id="search-title">What are you craving?</h2><button class="icon-button search-close" aria-label="Close search">{icon('close')}</button></div><label class="catalog-search">{icon('search')}<input id="site-search" type="search" placeholder="Search products, ingredients, recipes…" aria-label="Search Kissan"></label><div class="search-results" id="search-results" aria-live="polite"><p class="muted">Try “peanut butter”, “sandwich” or “jam”.</p></div></dialog>'''

def page(path,title,body,desc='',schema=None):
    data=json.dumps(schema,ensure_ascii=False).replace('</','<\\/') if schema else None
    doc=f'''<!doctype html><html lang="en-IN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#b51f26"><meta name="robots" content="noindex,nofollow"><title>{esc(title)} | Kissan Redesign</title><meta name="description" content="{esc(desc or 'Explore Kissan products and recipes. A taste of togetherness for everyday meals.')}"><link rel="stylesheet" href="/styles.css"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%23dc262b'/%3E%3Ctext x='32' y='48' text-anchor='middle' fill='white' font-family='Georgia' font-weight='bold' font-size='48'%3EK%3C/text%3E%3C/svg%3E">{('<script type="application/ld+json">'+data+'</script>') if data else ''}<script src="/app.js" defer></script></head><body>{header()}<main id="main">{body}</main>{footer()}</body></html>'''
    target=OUT/('index.html' if path=='/' else path.strip('/')+('/index.html' if path.endswith('/') else ''))
    target.parent.mkdir(parents=True,exist_ok=True); target.write_text(doc)
    ROUTES.append(path)

def crumbs(name,kind=None):
    middle=f'<span>/</span><a href="/{kind.lower()}.html">All {kind.lower()}</a>' if kind else ''
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="/">Home</a>{middle}<span>/</span><span aria-current="page">{esc(name)}</span></nav>'
def section_head(eye,title,label=None,url=None,sub=''):
    return f'<div class="section-head"><div><span class="eyebrow">{eye}</span><h2>{title}</h2>{"<p>"+esc(sub)+"</p>" if sub else ""}</div>{"<a class=text-link href="+esc(url)+">"+label+" <span>→</span></a>" if url else ""}</div>'
def category_cards():
    return '<div class="category-grid">'+''.join(f'<a class="category-card" href="/products/{s}.html"><span class="num">0{i+1} / OUR FAVOURITES</span>{img(v1(image),"Kissan "+n)}<div class="category-bottom"><h3>{esc(n)}</h3><span class="circle-arrow" aria-hidden="true">↗</span></div></a>' for i,(n,s,image) in enumerate(CATS))+'</div>'
def tag_label(r):
    for t in ['breakfast recipes','snack recipes','dessert recipes','rolls & wraps','peanut butter','jam']:
        if t in r['tags']: return t.replace(' recipes','').title()
    return r['difficulty'] or 'Recipe'
def recipe_card(r,filterable=False):
    searchable=' '.join([r['name'],r['description']]+r['tags']+r['ingredients']).lower()
    attrs=f'data-card data-name="{esc(r["name"].lower())}" data-search="{esc(searchable)}" data-tags="{esc(json.dumps(r["tags"]))}" data-time="{esc(r["total"])}"' if filterable else ''
    return f'''<a href="{esc(r['path'])}" class="recipe-card" {attrs}><div class="recipe-image">{img(r['image'],r['name'])}<span class="recipe-tag">{esc(tag_label(r))}</span></div><div class="recipe-meta"><span>{icon('clock')} {esc(r['total'])} mins</span><span>{esc(r['difficulty'])}</span></div><h3>{esc(r['name'])}</h3><p>{esc(r['description'])}</p></a>'''
def representative_note(p):
    return f'<p class="product-representative-note">{esc(p["representativeNote"])}</p>' if p.get('representativeNote') else ''

def product_card(p,filterable=False):
    attrs=f'data-card data-name="{esc(p["name"].lower())}" data-search="{esc((p["name"]+" "+p["category"]+" "+p["description"]).lower())}" data-tags="{esc(json.dumps([p["category"].lower()]))}"' if filterable else ''
    first_price=variant_price(p,p['variants'][0],0) if p.get('variants') else None
    if p.get('representativeNote') and p.get('variants'):
        first_size=esc(p['variants'][0]['size'])
        product_meta=f'<div class="product-card-meta"><span class="product-size">{first_size}</span><span class="product-price">₹{first_price:,}/-</span></div>{representative_note(p)}'
    else:
        price_html=f'<div class="product-price">From ₹{first_price:,}</div>' if first_price is not None else ''
        product_meta=f'<div class="product-size">{len(p["variants"])} pack options <span aria-hidden="true">↗</span></div>{price_html}'
    return f'<a class="product-card" href="{p["path"]}" {attrs}><div class="product-card-image">{product_img(p["images"][0],p["name"])}</div><span class="eyebrow">{esc(p["category"])}</span><h3>{esc(p["name"])}</h3>{product_meta}</a>'

def homepage():
    video_ad='<section class="home-video-ad" aria-label="Kissan video advertisement"><div class="home-video-ad-frame"><video autoplay muted loop playsinline controls preload="metadata" aria-label="Kissan advertisement"><source src="/assets/kissan-home-video-ad-20260918.mp4" type="video/mp4">Your browser does not support the Kissan advertisement video.</video></div></section>'
    categories='<section class="section wrap">'+section_head('Something for everyone','Meet your everyday<br>favourites.','All products','/products.html')+category_cards()+'</section>'
    kimchi=next(p for p in P if p['slug']=='kimchi-kurrentt-spread')
    poster=f'<section class="section wrap kimchi-poster-section"><div class="kimchi-poster-card"><div class="kimchi-poster-copy"><span class="eyebrow">New on the table</span><h2>{esc(kimchi["name"])}</h2><p>Korean boldness, Indian heart. A fiery, flavour-packed spread for everyday cravings.</p><a href="{esc(kimchi["path"])}" class="btn">View the new spread <span>↗</span></a></div><div class="kimchi-poster-visual">'+product_img(kimchi['images'][0],'Kissan '+kimchi['name']+' 200 g jar','kimchi-poster-image',True)+representative_note(kimchi)+'</div></div></section>'
    banners=[('130211203.jpg','Kissan Mixed Fruit Jam campaign'),('130211184.jpg','Kissan No Onion No Garlic Tomato Sauce campaign'),('130211183.jpg','Kissan Fresh Tomato Ketchup campaign'),('130211185.jpg','Kissan Sweet and Spicy Sauce campaign')]
    campaigns='<section class="campaign"><div class="wrap">'+section_head('Goodness, straight from our farms','There’s a story in every spoonful.')+'<div class="carousel" aria-roledescription="carousel" aria-label="Kissan campaigns"><div class="carousel-track" id="campaign-track">'+''.join(f'<div class="campaign-slide" role="group" aria-label="{i+1} of 4">{img(v1(n),a)}</div>' for i,(n,a) in enumerate(banners))+'</div><div class="carousel-footer"><span class="carousel-count" aria-live="polite"><span id="campaign-current">01</span> / 04</span><div class="carousel-controls"><button class="icon-button campaign-prev" aria-label="Previous campaign">←</button><button class="icon-button campaign-next" aria-label="Next campaign">→</button></div></div></div></div></section>'
    recipes='<section class="section wrap">'+section_head('From our kitchen to yours','Small effort.<br>Big happy faces.','All 66 recipes','/recipes.html')+'<div class="recipe-grid">'+''.join(recipe_card(r) for r in R[:6])+'</div></section>'
    story=f'<section class="section wrap"><div class="story-band">{img(STORY,"The farms at the heart of Kissan")}<div class="story-band-copy"><span class="eyebrow">Rooted in goodness</span><h2>Behind every Kissan,<br>there’s a kisan.</h2><p>From the orange groves of Nagpur to the peanut farms of Gujarat, our story begins with the people who grow the ingredients you love.</p><a class="text-link" href="/our-story.html">Discover our story <span>→</span></a></div></div><p class="brand-claims">Kissan: India’s No. 1 Jams and Preserves brand and India’s No. 1 Ketchup brand.<br><small>Source: Euromonitor International Limited, Cooking Ingredients and Meals 2026ed; Retail Value Sales (RSP), 2025 data.</small></p></section>'
    page('/','A taste of togetherness',video_ad+categories+poster+campaigns+recipes+story)
    shutil.copyfile(OUT/'index.html',OUT/'home.html'); ROUTES.append('/home.html')

RECIPE_FILTERS=['Breakfast recipes','Snack recipes','Dessert recipes','Ketchup & Sauces','Peanut Butter','Jam','Rolls & Wraps','Sandwich recipes','Quick recipes','Tiffin recipes','Sweet recipes','Chatpata recipes']
def catalogue(path,title,kind,tag='',intro=''):
    isrecipe=kind=='recipes'; cards=R if isrecipe else P
    filters=[('All recipes','')]+[(t,t.lower()) for t in RECIPE_FILTERS]+[('Recipes by course','recipes by course'),('Recipes by product','recipes by product')] if isrecipe else [('All products','')]+[(n,n.lower()) for n,_,_ in CATS]
    pills=filters[:4] if isrecipe else filters
    filterhtml=''.join(f'<button class="pill {"active" if value==tag else ""}" data-filter="{esc(value)}" aria-pressed="{str(value==tag).lower()}">{esc(label)}</button>' for label,value in pills)
    choices='<label class="sr-only" for="category-filter">Recipe category</label><select id="category-filter" aria-label="Recipe category">'+''.join(f'<option value="{esc(v)}" {"selected" if v==tag else ""}>{esc(n)}</option>' for n,v in filters)+'</select>' if isrecipe else ''
    toolbar=f'<div class="catalog-toolbar"><div class="filter-pills">{filterhtml}</div><div class="catalog-options"><label class="catalog-search">{icon("search")}<input id="catalog-query" type="search" placeholder="Search {kind}…" aria-label="Search {kind}"></label>{choices}<select id="catalog-sort" aria-label="Sort {kind}"><option value="featured">Featured</option><option value="az">A to Z</option><option value="za">Z to A</option>{"<option value=quickest>Quickest first</option>" if isrecipe else ""}</select></div></div>'
    tiles=PAGES.get(path,{}).get('tiles',[])
    tilehtml='<div class="recipe-browse-tiles">'+''.join(f'<a href="{esc(t["path"])}">{img(t["image"],t["name"])}<span>{esc(t["name"])} <b>↗</b></span></a>' for t in tiles)+'</div>' if tiles else ''
    heading=f'<div class="page-heading"><span class="eyebrow">{"Good food. Great ideas." if isrecipe else "Your everyday favourites"}</span><h1>{esc(title)}</h1><p>{esc(intro or ("Find something delicious for every craving, every meal and every moment in between." if isrecipe else "A little sweet, a little tangy, a whole lot of delicious. Find your favourite Kissan."))}</p></div>'
    product_hero=''
    if path=='/products.html':
        banners=[
            ('/assets/kissan-kimchi-kurrenttt-wide-banner.png','Kimchi Kurrenttt Spread: bold, spicy flavour for everyday meals',2048,684,'promotion'),
            ('/assets/kissan-products-lineup-wide-banner.png','All Kissan products and pack formats',976,270,'lineup'),
        ]
        slides=''.join(f'<div class="products-banner-slide products-banner-slide--{kind}" role="group" aria-roledescription="slide" aria-label="{i+1} of 2" aria-hidden="{str(i!=0).lower()}" data-products-slide>{local_img(image,alt,"products-hero-image",width,height)}</div>' for i,(image,alt,width,height,kind) in enumerate(banners))
        product_hero=f'<section class="products-hero-banner products-banner-carousel" data-products-carousel role="region" aria-roledescription="carousel" aria-label="Featured Kissan products"><nav class="products-hero-breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><span aria-current="page">All Products</span></nav><h1 class="sr-only">All products</h1><div class="products-banner-viewport"><div class="products-banner-track" id="products-banner-track" aria-live="off">{slides}</div></div><div class="products-banner-controls"><span class="products-banner-count"><span data-products-current>01</span> / 02</span><div class="products-banner-buttons"><button type="button" class="products-banner-pause" data-products-pause aria-controls="products-banner-track" aria-label="Pause automatic banner rotation">Pause</button><button type="button" class="icon-button" data-products-prev aria-controls="products-banner-track" aria-label="Previous banner">←</button><button type="button" class="icon-button" data-products-next aria-controls="products-banner-track" aria-label="Next banner">→</button></div></div></section>'
        heading=''
    grid='<div class="'+('recipe-grid' if isrecipe else 'product-grid')+'" id="catalog-grid">'+''.join(recipe_card(x,True) if isrecipe else product_card(x,True) for x in cards)+'</div>'
    empty='<div class="no-results" id="catalog-empty" hidden><h3>Nothing on the menu just yet.</h3><p>Try a different search or clear your filters.</p><button class="btn outline more-space" id="clear-filters">Clear filters</button></div>'
    bottom=''
    for u in PAGES.get(path,{}).get('images',[]):
        if u in [v1('2328723.jpg'),v1('2328730.jpg'),v1('2380218.jpg'),GENERIC]: bottom+=f'<div class="catalog-banner">{img(u,title+" original Kissan banner")}</div>'
    if path=='/recipes.html':
        fallback='https://assets.unileversolutions.com/recipes-v3/115576-default.jpg'
        bottom+=f'<div class="recipe-inspiration">{img(fallback,"A Kissan recipe serving suggestion")}<div><span class="eyebrow">Make room for something delicious</span><h2>Give your everyday<br>a tasty little twist.</h2><a href="/recipes/quick-recipes.html" class="text-link">Explore quick recipes <span>→</span></a></div></div>'
    body=f'{product_hero}<div class="wrap">{"" if product_hero else crumbs(title)}{heading}{tilehtml}<section class="catalog-layout" data-catalog="{kind}" data-initial-tag="{esc(tag)}">{toolbar}<div class="result-bar"><span id="catalog-count" aria-live="polite">{len(cards)} {kind}</span><button class="back-top" id="reset-catalog">Reset filters</button></div>{grid}{empty}<div class="load-more-wrap"><button id="load-more" class="btn outline" hidden>Show more recipes <span>↓</span></button></div>{bottom}</section></div>'
    page(path,title,body,intro)

def buy_panel(p,variants):
    groups=[]
    for i,v in enumerate(variants):
        price=variant_price(p,v,i)
        links=''.join(f'<a class="retailer-option" data-retailer-link data-platform="{esc(platform)}" href="{esc(retailer_url(base,p,v))}" target="_blank" rel="noopener"><span><strong>{esc(platform)}</strong><small>Shop this pack ↗</small></span><b>₹{price:,}</b></a>' for platform,base in RETAILER_URLS)
        groups.append(f'<div class="buy-options" data-buy-options="{i}" {"hidden" if i else ""}>{links}</div>')
    first=variants[0] if variants else {'size':'','price':0}
    first_price=variant_price(p,first,0)
    first_platform=RETAILER_URLS[0][0]
    first_url=retailer_url(RETAILER_URLS[0][1],p,first)
    return f'''<div class="buy-panel" data-buy-panel><div class="buy-panel-head"><div><span class="eyebrow">Buy online</span><h3>Choose where to buy</h3></div><strong class="buy-price" data-buy-price>₹{first_price:,}</strong></div><a class="btn buy-now" data-buy-now href="{esc(first_url)}" target="_blank" rel="noopener">Buy now on <span data-buy-now-platform>{esc(first_platform)}</span> ↗</a><p class="form-note">Choose BigBasket, Blinkit or Amazon. Prices are indicative; the retailer shows the final cost.</p>{''.join(groups)}</div>'''

def product_page(p):
    variants=p['variants']; main=p['images'][0]
    options=''.join(f'<button class="pack-option {"active" if i==0 else ""}" data-variant="{i}" aria-pressed="{str(i==0).lower()}">{esc(v["size"])}</button>' for i,v in enumerate(variants))
    galleries=''
    for i,v in enumerate(variants):
        imgs=v['images'] or [main]
        thumbs=''.join(f'<button class="thumb {"active" if j==0 else ""}" data-gallery-image="{esc(image_ref(u))}" aria-label="View {esc(v["size"])} image {j+1}" aria-pressed="{str(j==0).lower()}">{product_img(u,p["name"]+" "+v["size"])}</button>' for j,u in enumerate(imgs))
        galleries+=f'<div class="variant-gallery" data-variant-gallery="{i}" {"hidden" if i else ""}><div class="product-stage">{product_img(imgs[0],p["name"]+" "+v["size"],"selected-product-image",i==0)}</div>{representative_note(p)}<div class="thumbs">{thumbs}</div></div>'
    if not galleries: galleries='<div class="product-stage">'+product_img(main,p['name'],eager=True)+'</div>'+representative_note(p)
    ingredient=f'<details class="disclosure"><summary>Ingredients</summary><div>{esc(html.unescape(p["ingredients"]))}</div></details>' if p['ingredients'] else ''
    promotion=f'<section class="product-promotion" aria-label="{esc(p["name"])} promotion">{product_img(p["promotionImage"],p["name"]+" promotion","product-promotion-image",True)}</section>' if p.get('promotionImage') else ''
    related=[x for x in P if x['category']==p['category'] and x!=p]
    relatedrecipes=[r for r in R if p['category'].lower() in r['tags']][:3]
    relatedhtml='<section class="section related">'+section_head('More to love','Find your next favourite.')+'<div class="product-grid">'+''.join(product_card(x) for x in related)+'</div></section>' if related else ''
    if relatedrecipes: relatedhtml+='<section class="section related">'+section_head('A little kitchen inspiration','Put a delicious idea on the table.','See recipes','/recipes.html?category='+p['category'].lower().replace(' ','%20').replace('&','%26'))+'<div class="recipe-grid">'+''.join(recipe_card(r) for r in relatedrecipes)+'</div></section>'
    detail_class='product-detail kimchi-product-detail' if p.get('slug')=='kimchi-kurrentt-spread' else 'product-detail'
    description_html=''
    if p.get('descriptionParagraphs'):
        paragraphs=''.join(f'<p>{esc(text)}</p>' for text in p['descriptionParagraphs'])
        flavours=''.join(f'<li><span aria-hidden="true">{esc(emoji)}</span><span>{esc(label)}</span></li>' for emoji,label in p.get('flavourProfile',[]))
        flavour_html=f'<div class="product-flavour-profile"><h3>Key flavour profile</h3><ul>{flavours}</ul></div>' if flavours else ''
        description_html=f'<section class="product-story" aria-labelledby="product-story-title"><div class="product-story-copy"><span class="eyebrow">Everyday flavour booster</span><h2 id="product-story-title">About {esc(p["name"])}</h2>{paragraphs}</div>{flavour_html}</section>'
    body=f'''<div class="wrap">{crumbs(p['name'],'Products')}{promotion}<section class="{detail_class}" data-product><div>{galleries}</div><div class="product-detail-copy"><span class="eyebrow">Kissan · {esc(p['category'])}</span><h1>{esc(p['name'])}</h1><p class="product-description">{esc(p['description'])}</p><div class="pack-label">Choose your pack</div><div class="pack-options" aria-label="Pack sizes">{options}</div>{buy_panel(p,variants)}{ingredient}<details class="disclosure"><summary>Product information</summary><div>Country of origin: {esc(p['country'])}.<br>For nutrition, storage instructions and allergen information, refer to the label on your chosen pack.</div></details></div></section>{description_html}{relatedhtml}</div>'''
    page(p['path'],p['name'],body,p['description'])

TAG_PATHS={'breakfast recipes':'/recipes/recipes-by-course/breakfast-recipes.html','snack recipes':'/recipes/recipes-by-course/snack-recipes.html','dessert recipes':'/recipes/recipes-by-course/dessert-recipes.html','ketchup & sauces':'/recipes/recipes-by-product/ketchup-and-sauces.html','peanut butter':'/recipes/recipes-by-product/peanut-butter.html','jam':'/recipes/recipes-by-product/jam.html','rolls & wraps':'/recipes/quick-recipes/rolls-and-wraps-recipes.html','sandwich recipes':'/recipes/quick-recipes/sandwich-recipes.html','quick recipes':'/recipes/quick-recipes.html'}
def recipe_page(r):
    categories=''.join(f'<a class="pill" href="{p}">{esc(t.title())}</a>' for t,p in TAG_PATHS.items() if t in r['tags'])
    ingredients=''.join(f'<label class="ingredient"><input type="checkbox" aria-label="Mark {esc(i)} as prepared"><span>{esc(i)}</span></label>' for i in r['ingredients'])
    directions=''.join(f'<li><div>{esc(s)}</div></li>' for s in r['steps'])
    nutrition=''.join(f'<div>{esc(re.sub(r"(?<!^)(?=[A-Z])"," ",k).replace(" Content","").capitalize())}<strong>{esc(v)}</strong></div>' for k,v in r['nutrition'].items())
    nutritional=f'<details class="disclosure"><summary>Nutritional information</summary><div><p class="form-note">Values supplied with the original recipe.</p><div class="nutri-table">{nutrition}</div></div></details>' if nutrition else ''
    related=sorted([x for x in R if x!=r],key=lambda x:len(set(x['tags'])&set(r['tags'])),reverse=True)[:3]
    body=f'''<div class="wrap">{crumbs(r['name'],'Recipes')}<section class="recipe-top"><div class="recipe-top-image">{img(r['image'],r['name'],eager=True)}</div><div><span class="eyebrow">{esc(tag_label(r))} · {esc(r['difficulty'])}</span><h1>{esc(r['name'])}</h1><p>{esc(r['description'])}</p><div class="recipe-stats"><div><strong>{esc(r['prep'])} <small>min</small></strong><small>Preparation</small></div><div><strong>{esc(r['cook'])} <small>min</small></strong><small>Cooking</small></div><div><strong>{esc(r['servings'])}</strong><small>Servings</small></div></div><div class="hero-actions"><button class="btn print-recipe">Print recipe <span>↗</span></button><button class="icon-button share-recipe" aria-label="Copy recipe link">{icon('share')}</button><span class="share-status" role="status"></span></div></div></section><section class="recipe-body"><aside class="ingredients"><h2>Ingredients</h2><p class="form-note">For {esc(r['servings'])} servings</p>{ingredients}</aside><div class="method"><h2>Let’s make it.</h2><ol>{directions}</ol>{nutritional}<div class="recipe-category-links more-space">{categories}</div></div></section><p class="print-origin">Kissan recipe · {esc(r['source'])}</p><section class="section related">{section_head('Keep the good food coming','You might also love.','All recipes','/recipes.html')}<div class="recipe-grid">{''.join(recipe_card(x) for x in related)}</div></section></div>'''
    schema={'@context':'https://schema.org','@type':'Recipe','name':r['name'],'description':r['description'],'prepTime':'PT'+str(r['prep'])+'M','cookTime':'PT'+str(r['cook'])+'M','recipeYield':str(r['servings']),'recipeIngredient':r['ingredients'],'recipeInstructions':[{'@type':'HowToStep','text':s} for s in r['steps']]}
    page(r['path'],r['name'],body,r['description'],schema)

def story_page():
    body=f'''<div class="wrap">{crumbs('Our story')}<div class="page-heading"><span class="eyebrow">Our roots run deep</span><h1>Behind every Kissan,<br>there’s a kisan.</h1><p>Good food starts with the people who grow it.</p></div><div class="story-visual">{img(STORY,'The Indian farms behind Kissan',eager=True)}</div><article class="editorial"><h2>A journey from farm to family.</h2><p>Kissan’s name comes from a Punjab railway stop where farmers sold freshly harvested fruit during the British era. That local meeting place grew into a familiar name in Indian homes.</p><div class="timeline"><div><strong>1950</strong><p>The UB Group, led by Vittal Mallya, acquired Kissan from Mitchell Bros.</p></div><div><strong>1993</strong><p>Brooke Bond India acquired Kissan. The brand is now part of Hindustan Unilever.</p></div><div><strong>Today</strong><p>Jams, sauces, peanut butter and squash bring farm ingredients to everyday meals.</p></div></div><h2>Growing together.</h2><p>Kissan’s early innovations included canned fruit, vegetables and baked beans. Its work later focused on helping small farmers produce quality ingredients.</p><p>HUL’s partnership with the Maharashtra Government for sustainable tomato sourcing started in 2012 and became self-sustaining in 2015. HUL continued providing a produce buy-back guarantee, alongside guidance on seeds, irrigation and agricultural practices.</p><p>The brand’s published history reports that 76% of its ketchup tomatoes came from sustainable sources in 2019, with around 8,000 farmers growing tomatoes for HUL that year. One introduced variety could be harvested in 90 days, compared with 150–180 days for traditional varieties, and its brighter red colour helped farmers obtain better prices.</p><h2>Ingredients with a sense of place.</h2><p>Nagpur oranges. Lemons from the Himalayan foothills. Kerala pineapples. Karnataka grapes. Gujarat peanuts. Kissan’s range connects familiar flavours with farms across India.</p><p>The farmers behind these ingredients remain central to the Kissan story.</p><a href="/products.html" class="btn">Meet the Kissan family <span>↗</span></a></article><div class="story-visual">{img(GENERIC,'Original Kissan farm and product banner')}</div></div>'''
    page('/our-story.html','Our story',body)

def faq_page():
    faqs=[('What is the orange juice comparison on Kissan Orange Squash?', 'The original product FAQ states that one serving contains 20 times the orange juice of one serving of the leading orange instant drink mix.'),('Which vitamins are present in Kissan Orange Squash?','The brand lists vitamins A, B6, B7 and C.'),('How many glasses does one pack of Kissan Squash make?','The brand’s serving guide gives 25 glasses per pack. Mix 2 tablespoons (30 ml) of squash with one glass (180 ml) of chilled water or soda for a serving.'),('Which pack size is available for Kissan Peanut Butter?','The Creamy Peanut Butter pack listed on the website contains 350 g.'),('Which fruits are in Kissan Mixed Fruit Jam?','The eight-fruit blend contains pineapple, orange, apple, grape, mango, pear, papaya and banana.')]
    rows=''.join(f'<details class="disclosure"><summary>{esc(q)}</summary><div>{esc(a)}</div></details>' for q,a in faqs)
    body=f'<div class="wrap">{crumbs("FAQs")}<div class="page-heading"><span class="eyebrow">A little help from Kissan</span><h1>Your questions, answered.</h1><p>Everything from your favourite ingredients to the perfect glass of squash.</p></div><div class="faq-list">{rows}<p class="more-space">Still have a question? <a href="/contact-us.html" class="text-link">Get in touch →</a></p></div></div>'
    page('/contact-us/faq.html','Frequently asked questions',body)

def contact_page():
    body=f'''<div class="wrap">{crumbs('Contact us')}<div class="page-heading"><span class="eyebrow">We’re here to help</span><h1>Let’s talk.</h1><p>A question, a suggestion, or a story from your kitchen?</p></div><section class="contact-grid"><div class="contact-info"><h2>A little conversation<br>goes a long way.</h2><p>Reach the Kissan consumer care team using the contact details published on the original website.</p><a class="contact-method" href="tel:18001022221"><span>Call consumer care</span><strong>1800 10 22 221</strong></a><a class="contact-method" href="mailto:lever.care@unilever.com"><span>Email consumer care</span><strong>lever.care@unilever.com</strong></a><p>For a product concern, include the pack details and a daytime phone number so the team can follow up.</p><a class="text-link" href="https://www.kissan.in/contact-us.html" target="_blank" rel="noopener">Official contact page <span>↗</span></a></div><form class="contact-form" id="contact-form"><h2>Write to Kissan</h2><label>Your name *<input required name="name" autocomplete="name"></label><label>Email address *<input required type="email" name="email" autocomplete="email"></label><label>What’s it about?<select name="topic"><option>Product enquiry</option><option>Product feedback</option><option>Recipe question</option><option>Other enquiry</option></select></label><label>Your message *<textarea required name="message" rows="5"></textarea></label><p class="form-note">This prepares an email to Kissan in your email app. You can review it before sending.</p><button type="submit" class="btn">Prepare email <span>↗</span></button><div class="form-status" id="contact-status" role="status"></div></form></section></div>'''
    page('/contact-us.html','Contact us',body)

def sitemap_page():
    groups=[('Products',[(p['name'],p['path']) for p in P]),('Recipe categories',[(PAGES[p]['title'],p) for p in PAGES if p.startswith('/recipes')]),('Explore Kissan',[('Home','/'),('All products','/products.html'),('All recipes','/recipes.html'),('Our story','/our-story.html'),('Contact us','/contact-us.html'),('FAQs','/contact-us/faq.html'),('Accessibility','/accessibility.html')]),('All recipes',[(r['name'],r['path']) for r in R])]
    sections=''.join('<section><h2>'+esc(n)+'</h2><ul>'+''.join('<li><a href="'+esc(p)+'">'+esc(t)+'</a></li>' for t,p in vals)+'</ul></section>' for n,vals in groups)
    page('/sitemap.html','Sitemap','<div class="wrap">'+crumbs('Sitemap')+'<div class="page-heading"><span class="eyebrow">Find your way</span><h1>Every delicious corner.</h1></div><div class="sitemap-grid">'+sections+'</div></div>')

def main():
    homepage()
    catalogue('/products.html','The Kissan family.','products')
    for name,s,_ in CATS: catalogue('/products/'+s+'.html',name,'products',name.lower())
    catalogue('/recipes.html','What’s cooking?','recipes')
    for path,meta in PAGES.items():
        if path.startswith('/recipes/'):
            tag=next((t for t,p in TAG_PATHS.items() if p==path),'')
            if not tag:
                tag='recipes by course' if path.endswith('recipes-by-course.html') else 'recipes by product' if path.endswith('recipes-by-product.html') else ''
            catalogue(path,meta['title'],'recipes',tag)
    for p in P: product_page(p)
    for r in R: recipe_page(r)
    story_page(); faq_page(); contact_page(); sitemap_page()
    page('/accessibility.html','Accessibility','<div class="wrap">'+crumbs('Accessibility')+'<article class="editorial"><div class="page-heading"><h1>A place for everyone.</h1></div><p>Use the keyboard to navigate links, open menus and select filters. Press Escape to close the search. Recipe ingredients can be checked off individually, and recipes have a print-friendly view.</p><p>You can use your browser’s zoom controls to enlarge the page. The site follows your device’s reduced-motion preference.</p><div class="accessibility-tools"><button class="btn outline" id="increase-text" aria-pressed="false">Larger text</button><a href="/contact-us.html" class="text-link">Need help? Contact us →</a></div></article></div>')
    page('/404.html','Page not found','<section class="section wrap page-heading"><span class="eyebrow">A little detour</span><h1>Let’s find something delicious.</h1><p>This page isn’t on the menu. Explore the Kissan collection or find a recipe.</p><div class="hero-actions more-space" style="justify-content:center"><a href="/products.html" class="btn">Explore products →</a><a href="/recipes.html" class="btn outline">Browse recipes →</a></div></section>')
    search=[{'name':p['name'],'type':'Product','path':p['path'],'image':image_ref(p['images'][0]),'detail':p['category'],'text':' '.join([p['name'],p['category'],p['description']]).lower()} for p in P]+[{'name':r['name'],'type':'Recipe','path':r['path'],'image':asset(r['image']),'detail':str(r['total'])+' mins · '+r['difficulty'],'text':' '.join([r['name']]+r['tags']+r['ingredients']).lower()} for r in R]
    (OUT/'search.json').write_text(json.dumps(search,ensure_ascii=False))
    (OUT/'_redirects').write_text('\n'.join(f'{src} {dst} 301' for src,dst in REDIRECTS.items())+'\n')
    (OUT/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n')
    report={'products':len(P),'recipes':len(R),'packChoices':sum(len(p['variants']) for p in P),'routes':ROUTES,'aliases':REDIRECTS,'capturedImages':len(A),'usedImages':len(USED),'unusedImages':sorted(set(A)-USED),'sourcePages':len(PAGES),'knownOriginalBrokenLink':'/p/sweet-spicy-sauce.html/08901030660320 (repaired with current /08901030660344 source)'}
    (ROOT/'source/coverage.json').write_text(json.dumps(report,indent=2)); (ROOT/'source/assets-manifest.json').write_text(json.dumps(A,indent=2))
    print('GENERATED',len(ROUTES),'routes',len(REDIRECTS),'original route aliases;',len(USED),'of',len(A),'images used')
    if report['unusedImages']: print('UNUSED',report['unusedImages'])
if __name__=='__main__': main()
