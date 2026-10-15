# Togg Sipariş Botu

Togg'un ana sayfasını, T10F ve T10X sayfalarını 5 dakikada bir gerçek bir tarayıcıyla açar. "Sipariş Ver" butonu görünürse Telegram'dan mesaj atar. Buton yoksa sessiz kalır.

## Kurulum (bir kerelik)

1. **Telegram botu:** Telegram'da `@BotFather`'a `/newbot` yazın, bota isim verin, size verilen **token**'ı kopyalayın.
2. **Bota yazın:** Yeni botunuzu açıp `/start` gönderin (botun size mesaj atabilmesi için gerekli).
3. **Token'ı GitHub'a ekleyin:** Bu repoda **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `TELEGRAM_TOKEN`
   - Secret: BotFather'ın verdiği token
4. **Deneyin:** **Actions** sekmesi → **Togg sipariş kontrolü** → **Run workflow**. Birkaç dakika içinde Telegram'a deneme mesajı gelmeli.

Chat ID'yi ayrıca girmenize gerek yok, bot `/start` mesajınızdan kendisi bulur. İsterseniz loglarda yazan ID'yi `TELEGRAM_CHAT_ID` adıyla secret olarak ekleyebilirsiniz.

## Notlar

- Sipariş açık kaldığı sürece her 5 dakikada bir tekrar mesaj gelir. Siparişi verince ya da gerek kalmayınca **Actions → Togg sipariş kontrolü → ⋯ → Disable workflow** ile durdurun.
- GitHub zamanlanmış işleri birkaç dakika geciktirebilir.
- Repoda 60 gün hiç değişiklik olmazsa GitHub zamanlamayı kendiliğinden durdurur. Gerekirse Actions sekmesinden tekrar açılır.
- Token koda yazılmaz, sadece GitHub Secrets'ta durur.
