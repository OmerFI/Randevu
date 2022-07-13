from dotenv import load_dotenv, find_dotenv
import os
import json
import requests
from tkinter import messagebox
from time import sleep
from datetime import datetime
from utils import sms_send

load_dotenv(find_dotenv())

AUTH_TOKEN = os.getenv("AUTH_TOKEN")
ENDPOINT = "https://prd.mhrs.gov.tr/api/kurum-rss/randevu/slot-sorgulama/arama"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
)
KLINIK = "Deri ve Zührevi Hastalıkları (Cildiye)"
# KLINIK = "Göğüs Hastalıkları"
REQUESTED_HOSPITALS = [
    "İSTANBUL- (AVRUPA)- BAHÇELİEVLER DEVLET HASTANESİ",
    "İSTANBUL- (AVRUPA)- BAKIRKÖY- DR. SADİ KONUK EĞİTİM ARAŞTIRMA HASTANESİ",
    # "İSTANBUL- (AVRUPA)- SİLİVRİ DEVLET HASTANESİ",
]

ONE_MINUTE = 60
FIVE_MINUTES = ONE_MINUTE * 5


with open("klinikler.json", "rb") as f:
    klinikler = json.load(f)

for klinik in klinikler:
    if klinik.get("text") == KLINIK:
        klinik_id = klinik.get("value")
        break
else:
    print("Klinik bulunamadı.")
    exit(1)

try:
    while True:
        print("=" * 75)
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print(f'"{KLINIK}" Randevusu aranıyor...')
        r = requests.post(
            ENDPOINT,
            headers={
                "User-Agent": USER_AGENT,
                "Content-Type": "application/json",
                "Authorization": "Bearer " + AUTH_TOKEN,
            },
            json={
                "aksiyonId": "200",
                "cinsiyet": "F",
                "mhrsHekimId": -1,
                "mhrsIlId": 341,
                "mhrsIlceId": -1,
                "mhrsKlinikId": klinik_id,
                "mhrsKurumId": -1,
                "muayeneYeriId": -1,
                "tumRandevular": False,
                "ekRandevu": True,
                "randevuZamaniList": [],
            },
        )

        data = r.json()
        if (
            data["data"] is None
            and data["errors"][0]["mesaj"]
            == "Başka yerden giriş yaptığınızdan oturum sonlanmıştır. (LGN2001)"
        ):
            print("Auth token is changed, update the .env file.")
            exit(1)
        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)

        hastaneler = set()
        try:
            for hastane in data["data"]["hastane"]:
                hastane_adi = hastane["kurum"]["kurumAdi"]
                hastaneler.add(hastane_adi)
        except:
            print(data["errors"][0]["mesaj"])
            exit(1)

        with open("hastaneler.txt", "wb") as f:
            f.write(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("utf-8") + b"\n"
            )
            f.write(b"================================================\n")
            f.write("\n".join(hastaneler).encode("utf-8"))

        for hastane in hastaneler:
            if hastane in REQUESTED_HOSPITALS:
                message = f"{hastane}'nde randevu bulundu. Hemen randevu al!"

                sms_send_response = sms_send("5533087137", message)
                print(sms_send_response.get("description"))
                messagebox.showinfo("RANDEVU BULUNDU", message)
                print(message)
                break
        else:
            print("Randevu bulunamadı!")
            print("Bir süre bekleniyor...")
            sleep(FIVE_MINUTES)
            continue
        break
except KeyboardInterrupt:
    pass
