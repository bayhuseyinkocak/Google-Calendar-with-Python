# Google Calendar Paneli — Kurulum Kılavuzu

Bu uygulama, Google Takvim hesabınızdaki etkinlikleri **yalnızca okumak** için Google'ın iznini (`calendar.readonly` kapsamı) kullanır. Hiçbir etkinlik eklemez, değiştirmez veya silmez.

Uygulamayı ilk kez çalıştırmadan önce aşağıdaki adımları tamamlamanız gerekir. Tahmini süre: **10–15 dakika**. Adımları sırayla ve eksiksiz uygulayın.

> Google Cloud Console arayüzü zaman zaman değişir ve dili tarayıcınıza göre Türkçe veya İngilizce olabilir. Aşağıda iki dildeki ad isimleri birlikte verilmiştir.

## Gereksinimler

- Python 3.9 veya üstü (terminalde `python3 --version` yazarak kontrol edin)
- Bir Google (Gmail) hesabı
- İnternet bağlantısı ve bir tarayıcı

## 1. Google Cloud projesi oluşturun

1. Tarayıcıda **https://console.cloud.google.com** adresini açın ve Google hesabınızla oturum açın.
2. Sayfanın sol üstündeki proje seçicisine tıklayın → **Yeni proje / New project**.
3. Proje adı olarak örneğin `Takvim Paneli` yazın → **Oluştur / Create**.
4. Proje oluşunca, proje seçiciden bu projenin seçili olduğundan emin olun.

## 2. Google Calendar API'sini etkinleştirin

1. Sol menüden **API'ler ve Hizmetler / APIs & Services → Kitaplık / Library** sayfasına girin.
2. Arama kutusuna **Google Calendar API** yazın ve listede **Google Calendar API**'yi açın.
3. **Etkinleştir / Enable** düğmesine basın.

## 3. OAuth izin (onay) ekranını ayarlayın

1. **API'ler ve Hizmetler → OAuth izin ekranı / OAuth consent screen** sayfasına girin
   (yeni arayüzde bu sayfa **Google Auth Platform** adıyla da geçebilir).
2. **Kullanıcı türü / User type** olarak **Harici / External** seçip **Oluştur / Create** deyin.
3. **Uygulama bilgileri**: Uygulama adı `Takvim Paneli`; **kullanıcı destek e-postası** ve
   **geliştirici iletişim e-postası** olarak kendi adresinizi seçin → kaydedip devam edin.
4. **Kapsamlar / Scopes** adımında **Kapsam ekle / Add scope** deyin; listeden Google Calendar API
   altındaki **`.../auth/calendar.readonly`** kapsamını (Yalnızca takvimleri ve etkinlikleri görüntüleme)
   seçip ekleyin → kaydedip devam edin.
5. **Test kullanıcıları / Test users** adımında **+ Kullanıcı ekle / Add users** ile
   **kendi Gmail adresinizi** ekleyin → kaydedip devam edin.
   Bu adım zorunludur; adresinizi eklemezseniz girişiniz `access_blocked` hatasıyla reddedilir.

## 4. OAuth istemci kimliğini oluşturun (credentials.json)

1. **API'ler ve Hizmetler → Kimlik Bilgileri / Credentials** sayfasına girin.
2. Üstteki **+ Kimlik bilgisi oluştur / Create credentials → OAuth istemci kimliği / OAuth client ID** seçin.
3. **Uygulama türü / Application type: Web uygulaması / Web application**; ad olarak `Takvim Paneli (yerel)` yazın.
4. **Yetkili yönlendirme URI'leri / Authorized redirect URIs** bölümünde **+ URI ekle / Add URI** düğmesine
   basın ve aşağıdaki adresi **birebir aynı** yazın:

   ```
   http://localhost:8080/oauth2callback
   ```

   Önemli: `127.0.0.1` değil `localhost` yazın; sondaki `/oauth2callback` dahil olmalı, öncesinde de
   sonra da fazladan karakter olmamalı.

5. **Oluştur / Create** deyin. Açılan pencerede **JSON'u indir / Download JSON** düğmesine basın.
   İnen dosya `client_secret_….apps.googleusercontent.com.json` gibi bir ad taşır.

## 5. İndirdiğiniz dosyayı proje klasörüne yerleştirin

İndirdiğiniz JSON dosyasını bu projenin klasörüne taşıyın ve adını **`credentials.json`** olarak
değiştirin. Sonuçta dosya tam şu yolda olmalı:

```
<proje klasörü>/credentials.json
```

## 6. Uygulamayı çalıştırın

Proje klasöründe bir terminal açın ve sırayla şunları çalıştırın:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

- İlk iki komut yalnızca **ilk kurulumda** gereklidir.
- Not: Yeni bir terminal açtığınızda 2. satırı (`source .venv/bin/activate`) tekrar çalıştırmanız gerekir.
- Uygulamayı durdurmak için terminalde **Ctrl+C** tuşlayın.

Ardından tarayıcıda şu adresi açın:

```
http://localhost:8080
```

## 7. İlk girişte Google onayı

1. Panel sizi Google'ın hesap seçim ekranına yönlendirir; hesabınızı seçin.
2. **Takvimlerinizi görüntüleme** (`calendar.readonly`) izmi istendiğini görürsünüz → **İzin ver / Allow**.
3. **"Google bu uygulamayı doğrulamadı / Google hasn't verified this app"** benzeri bir uyarı çıkarsa
   endişlenmeyin — uygulamayı Test modunda tuttuğumuz için normaldir:
   **Gelişmiş / Advanced** → **Takvim Paneli'ne git / Go to … (unsafe)** → devam edip izni verin.
4. Onaydan sonra panel açılır ve yaklaşan etkinlikleriniz listelenir.

## Sık karşılaşılan sorunlar

| Sorun | Çözüm |
|---|---|
| `Error 400: redirect_uri_mismatch` | 4. adımdaki yönlendirme URI'si birebir aynı olmalı: `http://localhost:8080/oauth2callback` |
| `Error 403: access_blocked` | Gmail adresinizi Test kullanıcıları listesine eklemediniz (3. adım, 5. madde) |
| `invalid_client` / kimlik bilgisi hatası | `credentials.json` bozuk ya da eski; 4. adımda yeniden indirin |
| `Address already in use` (8080 dolu) | `app.py` içindeki `PORT` değerini değiştirin **ve** Cloud Console'daki yönlendirme URI'sini aynı portla güncelleyin |
| 7 günde bir yeniden giriş istiyor | Test modunda Google, yenileme anahtarını yaklaşık 7 gün sonunda düşürür. Kalıcı çözüm: OAuth izin ekranında uygulamayı **Yayınla / Publish** (salt-okunur kapsam genelde ek doğrulama istemez) |
| `ModuleNotFoundError` | Sanal ortamı etkinleştirdiniz mi? `source .venv/bin/activate` |
| `credentials.json bulunamadı` hatası | Dosya doğru klasörde ve tam olarak `credentials.json` adında mı? Uzantı `.json` olmalı |

## Güvenlik notları

- `credentials.json` ve `token.json` hesabınıza özel erişim anahtarlarıdır: kimseyle paylaşmayın,
  GitHub gibi ortamlara yüklemeyin (`.gitignore` bu iki dosyayı zaten hariç tutar).
- Panel yalnızca sizin bilgisayarınızda `127.0.0.1:8080` üzerinden erişilebilir; internete açılmaz.
