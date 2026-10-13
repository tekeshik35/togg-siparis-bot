"""
Togg sipariş butonu takip botu.

Togg'un sayfalarını gerçek bir tarayıcıyla (Playwright) açar, sayfa tamamen
yüklendikten sonra "Sipariş Ver" benzeri bir buton/metin arar. Bulursa
Telegram'dan mesaj gönderir. Bulamazsa sessiz kalır.

Gerekli ortam değişkenleri (GitHub Secrets):
  TELEGRAM_TOKEN    -> @BotFather'ın verdiği bot token'ı (zorunlu)
  TELEGRAM_CHAT_ID  -> Mesajın gideceği sohbet ID'si (boşsa otomatik bulunur:
                       bota önce Telegram'dan /start yazmanız yeterli)

İsteğe bağlı:
  TEST_MESSAGE=1    -> Kontrol sonucundan bağımsız bir deneme mesajı gönderir
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

from playwright.sync_api import sync_playwright

PAGES = [
    ("Ana sayfa", "https://www.togg.com.tr/"),
    ("T10F sayfası", "https://www.togg.com.tr/t10f"),
    ("T10X sayfası", "https://www.togg.com.tr/t10x"),
]

# Sipariş açıldığında çıkabilecek buton metinleri. Metin önce Türkçe kurallarıyla
# küçük harfe çevrilir (SİPARİŞ -> sipariş), sonra bu kalıplarla aranır. Örnekler:
# "Sipariş Ver", "Siparişinizi Oluşturun", "Sipariş Oluştur", "Ön Sipariş Ver",
# "Siparişi Tamamla", "Hemen Sipariş", "Siparişe Açık", "Satın Al", "Şimdi Al"
_TR = "a-zçğıöşü"
ORDER_RE = re.compile(
    rf"sipari[şs][{_TR}]*\s+(ver|olu[şs]tur|tamamla|ba[şs]lat|yap)"
    rf"|hemen\s+sipari[şs]"
    rf"|sipari[şs]e\s+(a[çc][ıi]k|a[çc][ıi]ld|ba[şs]la)"
    rf"|sat[ıi]n\s+al(?![{_TR}])"
    rf"|[şs]imdi\s+al(?![{_TR}])"
)
# Her zaman sayfada olan, sipariş açılışıyla ilgisi olmayan metinler
IGNORE_RE = re.compile(r"sipari[şs]\s*ve\s*bilgi")

TR_TZ = timezone(timedelta(hours=3))

# Sayfadaki tüm elemanlarda (gizli olanlar dahil) sipariş metni arar
FIND_JS = r"""
(patterns) => {
  const orderRe = new RegExp(patterns.order);
  const ignoreRe = new RegExp(patterns.ignore);
  const hits = [];
  const seen = new Set();
  for (const el of document.querySelectorAll('body *')) {
    if (['SCRIPT','STYLE','NOSCRIPT'].includes(el.tagName)) continue;
    // Sadece kendi metni olan en içteki elemanlara bak
    const own = [...el.childNodes]
      .filter(n => n.nodeType === 3)
      .map(n => n.textContent).join(' ').replace(/\s+/g, ' ').trim();
    const low = own.toLocaleLowerCase('tr-TR');
    if (!own || !orderRe.test(low) || ignoreRe.test(low)) continue;
    const link = el.closest('a');
    const href = link ? link.href : '';
    const key = own + '|' + href;
    if (seen.has(key)) continue;
    seen.add(key);
    const cs = getComputedStyle(el);
    hits.push({
      text: own.slice(0, 120),
      href: href,
      visible: cs.display !== 'none' && cs.visibility !== 'hidden',
    });
  }
  return hits;
}
"""


def telegram(method, params=None):
    token = os.environ["TELEGRAM_TOKEN"].strip()
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params or {}).encode()
    with urllib.request.urlopen(url, data=data, timeout=30) as r:
        return json.loads(r.read().decode())


# Yusuf'un Telegram sohbet ID'si (token olmadan tek başına bir işe yaramaz)
DEFAULT_CHAT_ID = "879287249"


def get_chat_id():
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip() or DEFAULT_CHAT_ID
    if chat_id:
        return chat_id
    updates = telegram("getUpdates").get("result", [])
    for upd in reversed(updates):
        msg = upd.get("message") or upd.get("channel_post") or {}
        if msg.get("chat", {}).get("id"):
            found = str(msg["chat"]["id"])
            print(f"Chat ID otomatik bulundu: {found}")
            return found
    sys.exit(
        "Chat ID bulunamadı. Telegram'da botunuza /start yazın, "
        "sonra iş akışını tekrar çalıştırın."
    )


def send(text):
    chat_id = get_chat_id()
    res = telegram(
        "sendMessage",
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"},
    )
    if not res.get("ok"):
        sys.exit(f"Telegram mesajı gönderilemedi: {res}")
    print("Telegram mesajı gönderildi.")


def check_pages():
    results = []
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            locale="tr-TR",
            viewport={"width": 1600, "height": 1000},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
            ),
        )
        for name, url in PAGES:
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_load_state("networkidle", timeout=20000)
                except Exception:
                    pass
                # Sonradan eklenen butonlar için bekle
                page.wait_for_timeout(8000)
                hits = page.evaluate(
                    FIND_JS, {"order": ORDER_RE.pattern, "ignore": IGNORE_RE.pattern}
                )
                print(f"{name}: {len(hits)} eşleşme")
                for h in hits:
                    results.append((name, url, h))
            except Exception as e:
                errors.append(f"{name}: {e}")
                print(f"HATA {name}: {e}")
            finally:
                page.close()
        browser.close()
    return results, errors


def main():
    now = datetime.now(TR_TZ).strftime("%d.%m.%Y %H:%M")

    if os.environ.get("TEST_MESSAGE") == "1":
        send(f"✅ Togg sipariş botu çalışıyor. Deneme mesajı ({now}).")

    results, errors = check_pages()

    if results:
        lines = [f"🚗 TOGG SİPARİŞ BUTONU GÖRÜNDÜ! ({now})", ""]
        for name, url, h in results:
            lines.append(f"• {name}: \"{h['text']}\"")
            if h["href"]:
                lines.append(f"  Link: {h['href']}")
        lines += [
            "",
            "Hemen Trumore'dan kontrol edin: T10F V2 RWD Uzun Menzil.",
            "Ekleri seçmeyin (ÖTV %25'ten %55'e çıkıyor).",
            "Sayfa: https://www.togg.com.tr/",
        ]
        send("\n".join(lines))
    else:
        print("Sipariş butonu yok. Mesaj gönderilmedi.")

    if len(errors) == len(PAGES):
        # Hiçbir sayfa açılamadıysa iş akışı hata versin ki GitHub e-postayla bildirsin
        sys.exit("Hiçbir sayfa kontrol edilemedi: " + " | ".join(errors))


if __name__ == "__main__":
    main()
