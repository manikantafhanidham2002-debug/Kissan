# Kissan redesign

Static, responsive redesign of the supplied Kissan India website, captured 15 September 2026.

The site includes 13 products, 28 pack choices, all 66 recipes, the brand story, five FAQs, contact details, all original category pages, and 108 distinct source images. The four homepage campaign images remain intact. Each image is optimized locally without dropping source image content. Original detail URLs have redirects to readable new routes, including a repaired Sweet & Spicy navigation URL.

`dist/` is the complete deployable site. No API key, package installation or application server is needed. All food/product assets and the search index are local. Typography uses Google Fonts with system fallbacks.

The original brand contact details and retailer pages are retained. The contact form prepares a reviewable email in the visitor's email client; it does not claim to submit to an unconnected service. Retailer actions open the original Kissan page. This is an independent redesign concept, not the official Kissan website.

## Content and reproducibility

- `source/content.json`: full normalized product and recipe content.
- `source/assets-manifest.json`: exact source image URLs, optimized paths and dimensions.
- `source/coverage.json`: generated routes, original aliases and image coverage.
- `source/build.py`: authors all site HTML from captured data.
- `source/crawl.py`, `source/extract.py`, `source/assets.py`: public-source capture and extraction helpers. The raw HTML cache is temporary and excluded from Git.
- `dist/app.js`, `dist/styles.css`: interactive behaviour and responsive design.

The generator needs Python, BeautifulSoup and Pillow; the published site needs only static hosting.

The optional browser WebMCP search tool feature-detects support and invokes the same visible search flow. A supported browser context was unavailable under this turn's preview permissions, so live WebMCP validation was not performed. Site browser QA was not requested; validation covers content, syntax, assets and route consistency.
