"""Tek seferlik inceleme: Togg T10F konfigüratörünü masaüstü tarayıcıyla açar,
ekran sırasını, seçenekleri ve seçili durumları inspect/out/ altına yazar."""
import json, os, re
from playwright.sync_api import sync_playwright

OUT = "inspect/out"
os.makedirs(OUT, exist_ok=True)

DUMP_JS = r"""
() => {
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const items = [];
  document.querySelectorAll('input, button, [role=checkbox], [role=radio], [aria-checked], [aria-pressed], [aria-selected], label, li, [class*=option], [class*=card], [class*=item]').forEach(el => {
    if (!vis(el)) return;
    const txt = (el.innerText || el.value || '').replace(/\s+/g, ' ').trim();
    if (!txt || txt.length > 160) return;
    items.push({tag: el.tagName, cls: String(el.className).slice(0, 80),
      checked: el.checked ?? null, aria: el.getAttribute('aria-checked') || el.getAttribute('aria-pressed') || el.getAttribute('aria-selected'),
      type: el.type || null, text: txt});
  });
  return items;
}
"""

def snap(pg, name):
    txt = pg.inner_text("body")
    open(f"{OUT}/{name}.txt", "w", encoding="utf-8").write(txt)
    json.dump(pg.evaluate(DUMP_JS), open(f"{OUT}/{name}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pg.screenshot(path=f"{OUT}/{name}.png", full_page=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(locale="tr-TR", viewport={"width": 1600, "height": 1000},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36")
    pg = ctx.new_page()
    pg.goto("https://configurator.togg.com.tr/t10f", wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(15000)
    snap(pg, "01_ilk")
    try:
        pg.get_by_text("T10F V2 RWD Uzun Menzil", exact=False).first.click(timeout=10000)
        pg.wait_for_timeout(5000)
    except Exception as e:
        open(f"{OUT}/hata.txt", "a").write(f"V2 tik: {e}\n")
    snap(pg, "02_v2rwd")
    b.close()
