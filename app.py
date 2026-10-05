import os
from datetime import datetime, timedelta

from flask import Flask, redirect, render_template, request, session, url_for
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google, http://localhost yönlendirmesine izin verir; oauthlib bunu
# yalnızca aşağıdaki ortam değişkeni varlık kabul eder.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

PORT = 8080
CLIENT_SECRETS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
REDIRECT_URI = f"http://localhost:{PORT}/oauth2callback"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
KAC_GUN_ILERISI = 30
TAKVIM_BASI_ETKINLIK = 25
CACHE_SANIYE = 60

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
VARSAYILAN_RENK = "#3f51b5"

app = Flask(__name__)
app.secret_key = os.urandom(32)

_cache = {"zaman": None, "gruplar": None, "eposta": ""}


def kimlik_bilgileri():
    """token.json'dan geçerli kimlik döndürür; yoksa veya yenilenemiyorsa None."""
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    except Exception:
        return None
    if creds.valid:
        return creds
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            try:
                os.remove(TOKEN_FILE)
            except FileNotFoundError:
                pass
            return None
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        return creds
    return None


def _ayristir(zaman_alani):
    """Google'ın start/end alanını yerel saatli datetime'a çevirir.
    Tüm gün etkinlikleri için ikinci değer True döner."""
    if "date" in zaman_alani:
        dt = datetime.strptime(zaman_alani["date"], "%Y-%m-%d").astimezone()
        return dt, True
    iso = zaman_alani["dateTime"].replace("Z", "+00:00")
    return datetime.fromisoformat(iso).astimezone(), False


def etkinlikleri_topla(service):
    """Hesaptaki tüm takvimlerden yaklaşan etkinlikleri gün gün gruplayıp döndürür."""
    takvimler = service.calendarList().list().execute().get("items", [])
    simdi = datetime.now().astimezone()
    bugun_basi = simdi.replace(hour=0, minute=0, second=0, microsecond=0)
    son_gun = bugun_basi + timedelta(days=KAC_GUN_ILERISI)

    eposta = ""
    hepsi = []
    for takvim in takvimler:
        if takvim.get("deleted") or takvim.get("hidden"):
            continue
        if takvim.get("primary"):
            eposta = takvim.get("id", "")
        try:
            yanit = service.events().list(
                calendarId=takvim["id"],
                timeMin=bugun_basi.isoformat(),
                timeMax=son_gun.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=TAKVIM_BASI_ETKINLIK,
            ).execute()
        except HttpError:
            continue
        takvim_adi = takvim.get("summaryOverride") or takvim.get("summary") or "Takvim"
        renk = takvim.get("backgroundColor") or VARSAYILAN_RENK
        for etkinlik in yanit.get("items", []):
            if etkinlik.get("status") == "cancelled" or "start" not in etkinlik:
                continue
            bas_dt, tum_gun = _ayristir(etkinlik["start"])
            if bas_dt >= son_gun:
                continue
            son_dt, _ = _ayristir(etkinlik.get("end") or etkinlik["start"])
            if not tum_gun and son_dt <= simdi:
                continue
            if tum_gun:
                gun_sayisi = (son_dt.date() - bas_dt.date()).days or 1
                saat_yazi = ("Tüm gün" if gun_sayisi == 1
                             else f"Tüm gün ({gun_sayisi} gün)")
            else:
                saat_yazi = f"{bas_dt.strftime('%H:%M')} – {son_dt.strftime('%H:%M')}"
            hepsi.append({
                "bas_dt": bas_dt,
                "baslik": etkinlik.get("summary") or "(Başlıksız etkinlik)",
                "takvim": takvim_adi,
                "renk": renk,
                "yer": etkinlik.get("location", ""),
                "saat_yazi": saat_yazi,
                "link": etkinlik.get("htmlLink", ""),
            })

    hepsi.sort(key=lambda e: e["bas_dt"])
    bugun = simdi.date()
    gruplar = []
    for etkinlik in hepsi:
        gun = etkinlik["bas_dt"].date()
        if gruplar and gruplar[-1]["tarih"] == gun:
            gruplar[-1]["etkinlikler"].append(etkinlik)
        else:
            gruplar.append({
                "tarih": gun,
                "baslik": f"{gun.day} {AYLAR[gun.month - 1]} {gun.year}, {GUNLER[gun.weekday()]}",
                "rozet": ("Bugün" if gun == bugun
                          else "Yarın" if gun == bugun + timedelta(days=1) else ""),
                "etkinlikler": [etkinlik],
            })
    return gruplar, eposta


@app.route("/")
def panel():
    creds = kimlik_bilgileri()
    if creds is None:
        return redirect(url_for("giris_yap"))
    simdi = datetime.now()
    if (_cache["zaman"] is None
            or _cache["gruplar"] is None
            or (simdi - _cache["zaman"]).total_seconds() > CACHE_SANIYE):
        try:
            service = build("calendar", "v3", credentials=creds)
            _cache["gruplar"], _cache["eposta"] = etkinlikleri_topla(service)
            _cache["zaman"] = simdi
        except HttpError as hata:
            if hata.resp.status == 401:
                try:
                    os.remove(TOKEN_FILE)
                except FileNotFoundError:
                    pass
                return redirect(url_for("giris_yap"))
            return render_template(
                "error.html",
                baslik="Google Calendar'a ulaşılamadı",
                mesaj="Google Calendar API'si bir hata döndürdü. "
                      "İnternet bağlantınızı kontrol edip sayfayı yenileyin.",
                detay=str(hata)[:800],
            )
    return render_template("index.html", gruplar=_cache["gruplar"],
                          eposta=_cache["eposta"])


@app.route("/login")
def giris_yap():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return render_template(
            "error.html",
            baslik="Kurulum tamamlanmadı",
            mesaj="credentials.json dosyası bulunamadı. Google Cloud'dan "
                  "indirdiğiniz OAuth istemci anahtarını proje klasörüne "
                  "credentials.json adıyla yerleştirin.",
            kurulum=True,
        )
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    yetki_url, durum = flow.authorization_url(access_type="offline", prompt="consent")
    session["durum"] = durum
    return redirect(yetki_url)


@app.route("/oauth2callback")
def geri_cagirma():
    kayitli = session.get("durum")
    if not kayitli or kayitli != request.args.get("state"):
        return render_template(
            "error.html",
            baslik="Giriş tamamlanamadı",
            mesaj="Güvenlik doğrulaması eşleşmedi. Panele dönüp tekrar giriş yapın.",
        )
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES,
        redirect_uri=REDIRECT_URI, state=kayitli,
    )
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as hata:
        return render_template(
            "error.html",
            baslik="Giriş tamamlanamadı",
            mesaj="Google ile kimlik doğrulama sırasında bir hata oluştu. "
                  "Tekrar deneyin.",
            detay=str(hata)[:800],
        )
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(flow.credentials.to_json())
    _cache["zaman"] = None
    return redirect(url_for("panel"))


@app.route("/logout")
def cikis():
    try:
        os.remove(TOKEN_FILE)
    except FileNotFoundError:
        pass
    _cache["zaman"] = None
    return redirect(url_for("panel"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)
