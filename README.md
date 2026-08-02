# BIST Sinyal & Bildirim Sistemi

BIST100 hisselerini teknik indikatörlerle (RSI, MACD, SMA20/50, Bollinger Bantları) tarar, sinyal (AL/SAT/BEKLE) değiştiğinde Telegram üzerinden telefonunuza bildirim gönderir ve tarayıcıdan açılabilen bir izleme paneli sunar.

**Bu bir yatırım danışmanlığı aracı değildir.** Ürettiği sinyaller yalnızca standart teknik indikatörlerin matematiksel çıktılarıdır; yatırım kararları tamamen size aittir.

Sistem tamamen ücretsiz servisler üzerinde çalışır: veri kaynağı Yahoo Finance (yfinance), zamanlanmış tarama GitHub Actions, bildirim Telegram Bot, panel Streamlit Community Cloud. Bilgisayarınızın veya telefonunuzun sürekli açık kalması gerekmez.

## Kurulum

### 1. GitHub reposu oluşturma
Bu klasörü GitHub'a **public** bir repo olarak push'layın (public repo'larda Actions dakika limiti yok; private'ta aylık 2000 dakika sınırı var).

```bash
git init
git add .
git commit -m "İlk kurulum"
git branch -M main
git remote add origin <repo-url>
git push -u origin main
```

### 2. Actions yazma izni
Repo → **Settings → Actions → General → Workflow permissions** → "**Read and write permissions**" seçin ve kaydedin. (Tarama görevi `data/state.json`'ı commit'leyebilsin diye gerekli.)

### 3. Telegram bot oluşturma
1. Telegram'da **@BotFather**'a yazın, `/newbot` komutunu gönderin, bot adını belirleyin.
2. Size verilen **token**'ı not edin (örn. `123456:ABC-...`).
3. Oluşturduğunuz bota Telegram'dan bir kez `/start` yazın.
4. Tarayıcıdan şu adresi açın: `https://api.telegram.org/bot<TOKEN>/getUpdates` ve dönen JSON içindeki `"chat":{"id": ...}` değerini **chat_id** olarak not edin.

### 4. GitHub Secrets ekleme
Repo → **Settings → Secrets and variables → Actions → New repository secret**:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `HOLDINGS_JSON` *(opsiyonel)* — elinizdeki hisseleri buraya JSON olarak girin, örn:
  ```json
  {"THYAO.IS": {"shares": 100, "avg_cost": 285.50}}
  ```
  Repo **public** olduğu için pozisyon büyüklüklerinizin herkese açık görünmemesi için bu bilgi koda değil, şifreli GitHub secret'ına girilir; tarama görevi her çalıştığında bunu geçici olarak `config/holdings.json`'a yazar ama asla commit'lemez.

### 5. Streamlit dashboard'ı yayınlama
1. [share.streamlit.io](https://share.streamlit.io) adresine GitHub hesabınızla giriş yapın.
2. "New app" → reponuzu seçin → dosya yolu olarak `dashboard/streamlit_app.py` yazın → Deploy.
3. Aldığınız URL'yi telefonunuzun tarayıcısına yer imi (ana ekrana ekle) olarak kaydedin.
4. (Opsiyonel) Panel herkese açık bir URL olacağı için, gizlilik isterseniz Streamlit app ayarlarından **Secrets** kısmına `DASHBOARD_PASSWORD = "sizin-sifreniz"` ekleyin; panel açılışta şifre soracaktır.

### 6. Takip listesi ve pozisyonlarınız
- `config/watchlist.yaml`: BIST100 listesi hazır gelir (`.IS` uzantılı). Endeks bileşimi çeyreklik güncellendiği için zaman zaman elle kontrol edin.
- Pozisyonlarınız **repoya commit'lenmez** (gizlilik için `.gitignore`'da). İki yerde ayrı ayrı tanımlanır:
  - **Yerel test için**: `config/holdings.example.json`'ı `config/holdings.json` olarak kopyalayıp gerçek verilerinizi girin.
  - **GitHub Actions için**: yukarıdaki `HOLDINGS_JSON` secret'ını girin (adım 4).

  Bu sayede elinizdeki bir hisse SAT sinyaline döndüğünde özel uyarı alırsınız; elinizde olmayan bir hisse için AL sinyali geldiğinde standart bildirim gelir.

## Yerel Test (isteğe bağlı, kurulumdan önce doğrulama için)

```bash
pip install -r requirements.txt
cp .env.example .env   # TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID'yi doldurun
cp config/holdings.example.json config/holdings.json   # gerçek pozisyonlarınızı girin (bu dosya commit'lenmez)

# Birkaç hisseyle kuru çalıştırma (Telegram/commit yapmaz, sonucu ekrana yazar)
python -m app.scan --tickers THYAO.IS,ASELS.IS,EREGL.IS --dry-run --ignore-market-hours

# Telegram bağlantısını test etme
python -m app.notify "Test mesajı"

# Dashboard'ı yerelde çalıştırma
streamlit run dashboard/streamlit_app.py
```

## Nasıl çalışır

- GitHub Actions, hafta içi 09:00-18:00 (TRT) arası 15 dakikada bir tetiklenir; gerçek piyasa saati kontrolü Python içinde yapılır, pencere dışında hiçbir şey göndermez/commit'lemez.
- Her çalışmada RSI/MACD/SMA/Bollinger'dan oluşan 4 indikatörün en az 2'si aynı yönde oy verirse AL/SAT sinyali üretilir (tek indikatörün gürültüsü tek başına bildirim tetiklemez).
- Bildirim **sadece sinyal bir önceki çalışmaya göre değiştiğinde** gönderilir (BEKLE→AL, AL→BEKLE, BEKLE→SAT gibi) — aynı sinyal onlarca kez tekrar tekrar bildirilmez.
- Sonuçlar `data/state.json`'a commit'lenir; dashboard bu dosyayı okur, sayfa her açıldığında yeniden veri çekmez (tek hisse detay grafiği hariç).

## Sınırlamalar

- Yahoo Finance ücretsiz/gecikmeli veridir, birebir gerçek zamanlı değildir.
- BIST100 listesi elle bakım gerektirir (çeyreklik endeks güncellemeleri).
- Bu sistem otomatik emir vermez; sadece bildirim ve panel sağlar.
