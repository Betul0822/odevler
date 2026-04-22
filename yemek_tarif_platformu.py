import json
import os
import uuid
from datetime import datetime

# ==========================================
# 1. VERİTABANI YÖNETİMİ (SQL MANTIKLI JSON)
# ==========================================
class Veritabani:
    def __init__(self, dosya_adi="platform_db.json"):
        self.dosya_adi = dosya_adi
        # SQL Tabloları mantığında 3 ana yapı
        self.data = {
            "kullanicilar": {},      # PK: kullanici_id
            "tarifler": {},          # PK: tarif_id
            "degerlendirmeler": {}   # PK: degerlendirme_id, FK: kullanici_id, tarif_id
        }
        self.baglanti_ac()

    def baglanti_ac(self):
        """Veritabanı dosyasını okur, yoksa oluşturur."""
        if os.path.exists(self.dosya_adi):
            try:
                with open(self.dosya_adi, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                self.kaydet()
        else:
            self.kaydet()

    def kaydet(self):
        """Değişiklikleri JSON dosyasına (veritabanına) commit eder."""
        with open(self.dosya_adi, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)


# ==========================================
# 2. SINIFLAR (OOP PRENSİPLERİ)
# ==========================================
class Malzeme:
    def __init__(self, ad, miktar):
        self.malzeme_adi = ad
        self.miktar = miktar

    def to_dict(self):
        return {"malzeme_adi": self.malzeme_adi, "miktar": self.miktar}

class Tarif:
    def __init__(self, ad, kategori, hazirlama_suresi, tarif_id=None):
        # UUID ile benzersiz ID ataması (SQL'deki Auto-Increment PK mantığı)
        self.tarif_id = tarif_id if tarif_id else str(uuid.uuid4())[:8]
        self.tarif_adi = ad
        self.kategori = kategori
        self.hazirlama_suresi = hazirlama_suresi
        self.malzemeler = []

    def malzeme_ekle(self, malzeme_nesnesi):
        self.malzemeler.append(malzeme_nesnesi)

    def tarif_ekle(self, db_nesnesi):
        """Tarifi veritabanındaki 'tarifler' tablosuna ekler (INSERT)."""
        db_nesnesi.data["tarifler"][self.tarif_id] = {
            "tarif_adi": self.tarif_adi,
            "kategori": self.kategori,
            "hazirlama_suresi": self.hazirlama_suresi,
            "malzemeler": [m.to_dict() for m in self.malzemeler]
        }
        db_nesnesi.kaydet()
        print(f"\n[+] '{self.tarif_adi}' tarifi sisteme başarıyla eklendi. (ID: {self.tarif_id})")

    def tarif_guncelle(self, db_nesnesi, yeni_ad=None, yeni_kategori=None, yeni_sure=None):
        """Mevcut tarifi veritabanında günceller (UPDATE)."""
        if self.tarif_id in db_nesnesi.data["tarifler"]:
            if yeni_ad: self.tarif_adi = yeni_ad
            if yeni_kategori: self.kategori = yeni_kategori
            if yeni_sure: self.hazirlama_suresi = yeni_sure
            
            # Sınıftaki güncel veriyi DB'ye yaz
            self.tarif_ekle(db_nesnesi) 
            print(f"\n[*] '{self.tarif_id}' numaralı tarif güncellendi.")
        else:
            print("\n[-] Hata: Güncellenecek tarif bulunamadı.")


class Kullanici:
    def __init__(self, ad, kullanici_id=None):
        self.kullanici_id = kullanici_id if kullanici_id else str(uuid.uuid4())[:8]
        self.ad = ad

    def kullanici_kaydet(self, db_nesnesi):
        """Kullanıcıyı veritabanına ekler."""
        if self.kullanici_id not in db_nesnesi.data["kullanicilar"]:
            db_nesnesi.data["kullanicilar"][self.kullanici_id] = {"ad": self.ad}
            db_nesnesi.kaydet()

    def tarif_degerlendir(self, tarif_id, puan, yorum, db_nesnesi):
        """Değerlendirmeler tablosuna Foreign Key'ler ile kayıt atar (INSERT)."""
        if tarif_id not in db_nesnesi.data["tarifler"]:
            print("\n[-] Hata: Böyle bir tarif sistemde yok.")
            return

        degerlendirme_id = str(uuid.uuid4())[:12]
        db_nesnesi.data["degerlendirmeler"][degerlendirme_id] = {
            "tarif_id": tarif_id,
            "kullanici_id": self.kullanici_id,
            "puan": puan,
            "yorum": yorum,
            "tarih": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        db_nesnesi.kaydet()
        print(f"\n[+] Değerlendirmeniz alındı. Teşekkürler {self.ad}!")


# ==========================================
# 3. KONSOL ARAYÜZÜ (MAIN LOOP)
# ==========================================
def ana_menu():
    db = Veritabani()
    
    print("-" * 40)
    print("  Mutfak Sanatları & Tarif Platformu  ")
    print("-" * 40)
    kullanici_adi = input("Lütfen kullanıcı adınızı girin: ")
    
    # Kullanıcıyı bul veya oluştur
    aktif_kullanici = None
    for k_id, k_data in db.data["kullanicilar"].items():
        if k_data["ad"].lower() == kullanici_adi.lower():
            aktif_kullanici = Kullanici(ad=k_data["ad"], kullanici_id=k_id)
            break
            
    if not aktif_kullanici:
        aktif_kullanici = Kullanici(ad=kullanici_adi)
        aktif_kullanici.kullanici_kaydet(db)
        print(f"Yeni profil oluşturuldu. Hoş geldin, {kullanici_adi}!")
    else:
        print(f"Tekrar hoş geldin, {aktif_kullanici.ad}!")

    while True:
        print("\n--- MENÜ ---")
        print("1. Yeni Tarif Ekle")
        print("2. Tarifleri Listele")
        print("3. Tarif Değerlendir")
        print("4. Çıkış")
        secim = input("Seçiminiz (1-4): ")

        if secim == "1":
            ad = input("Tarif Adı: ")
            kategori = input("Kategori (Ana Yemek, Tatlı vb.): ")
            sure = input("Hazırlama Süresi (Dk): ")
            yeni_tarif = Tarif(ad, kategori, f"{sure} dk")
            
            while True:
                malz_ad = input("Malzeme Adı (Bitirmek için 'q' veya boş bırakın): ")
                if not malz_ad or malz_ad.lower() == 'q':
                    break
                malz_mik = input(f"{malz_ad} için miktar (örn: 200gr, 1 tatlı kaşığı): ")
                yeni_tarif.malzeme_ekle(Malzeme(malz_ad, malz_mik))
                
            yeni_tarif.tarif_ekle(db)

        elif secim == "2":
            if not db.data["tarifler"]:
                print("\nHenüz sistemde tarif bulunmuyor.")
                continue
                
            print("\n--- SİSTEMDEKİ TARİFLER ---")
            for t_id, t_veri in db.data["tarifler"].items():
                print(f"ID: {t_id} | {t_veri['tarif_adi']} ({t_veri['kategori']}) - {t_veri['hazirlama_suresi']}")
                print("Malzemeler: ", ", ".join([f"{m['miktar']} {m['malzeme_adi']}" for m in t_veri['malzemeler']]))
                
                # Bu tarifin değerlendirmelerini bul (SQL JOIN mantığı)
                yorumlar = [d for d in db.data["degerlendirmeler"].values() if d["tarif_id"] == t_id]
                if yorumlar:
                    ort_puan = sum(int(y["puan"]) for y in yorumlar) / len(yorumlar)
                    print(f"⭐️ Ortalama Puan: {ort_puan:.1f}/5.0 ({len(yorumlar)} değerlendirme)")
                print("-" * 30)

        elif secim == "3":
            t_id = input("Değerlendirmek istediğiniz Tarifin ID'sini girin: ")
            puan = input("Puanınız (1-5): ")
            yorum = input("Yorumunuz: ")
            if puan.isdigit() and 1 <= int(puan) <= 5:
                aktif_kullanici.tarif_degerlendir(t_id, puan, yorum, db)
            else:
                print("Lütfen 1 ile 5 arasında geçerli bir puan girin.")

        elif secim == "4":
            print("Platformdan çıkılıyor. İyi günler!")
            break
        else:
            print("Geçersiz seçim!")

if __name__ == "__main__":
    ana_menu()