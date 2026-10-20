"""Tek seferlik inceleme: Togg sayfalarını masaüstü ve iPhone görünümüyle açar,
tüm link/buton yazılarını ve sipariş geçen metinleri inceleme/out/ altına yazar."""
import json, os
from playwright.sync_api import sync_playwright
OUT = "inceleme/out2"
os.makedirs(OUT, exist_ok=True)
JS = r"""
() => {
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0'; };
  const links = [...document.querySelectorAll('a, button, [role=button]')].map(el => ({
    text: (el.innerText || el.textContent || '').replace(/\s+/g,' ').trim().slice(0,120),
    href: el.href || '', visible: vis(el), cls: String(el.className).slice(0,60)})).filter(x => x.text || x.href);
  const sip = [...document.querySelectorAll('body *')].filter(el => el.children.length < 3 &&
      /sipari|satın|stok|hazır cihaz|teslim/i.test(el.textContent || '') && (el.textContent||'').length < 200)
    .map(el => ({tag: el.tagName, text: el.textContent.replace(/\s+/g,' ').trim(), visible: vis(el), cls: String(el.className).slice(0,60)}));
  const iframes = [...document.querySelectorAll('iframe')].map(f => f.src).filter(Boolean);
  const ins = [...document.querySelectorAll('[class*=ins-], [id*=ins-], [class*=insider], [id*=insider]')]
    .map(el => ({tag: el.tagName, id: el.id, cls: String(el.className).slice(0,80), text: (el.innerText||'').replace(/\s+/g,' ').trim().slice(0,200), visible: vis(el)}));
  return {url: location.href, links, sip, iframes, ins};
}
"""
PROFILES = {
  "desktop": dict(viewport={"width":1600,"height":1000}, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"),
  "iphone": dict(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=3,
     user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"),
}
PAGES = [("ana","https://www.togg.com.tr/"),("t10f","https://www.togg.com.tr/t10f"),("t10x","https://www.togg.com.tr/t10x")]
with sync_playwright() as p:
    b = p.chromium.launch()
    for prof, kw in PROFILES.items():
        ctx = b.new_context(locale="tr-TR", **kw)
        for name, url in PAGES:
            pg = ctx.new_page()
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                try: pg.wait_for_load_state("networkidle", timeout=20000)
                except Exception: pass
                pg.wait_for_timeout(10000)
                json.dump(pg.evaluate(JS), open(f"{OUT}/{prof}_{name}.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
                pg.screenshot(path=f"{OUT}/{prof}_{name}.png")
            except Exception as e:
                open(f"{OUT}/hata.txt","a").write(f"{prof} {name}: {e}\n")
            pg.close()
        ctx.close()
    b.close()
