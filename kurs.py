import sqlite3
import os

# --- 1. OOP SINIFLARI (VERİ MODELLERİ) ---

class Kisi:
    """Öğrenci ve Eğitmen için temel sınıf (Kalıtım/Inheritance)"""
    def __init__(self, ad):
        self.ad = ad

class Egitmen(Kisi):
    def __init__(self, egitmen_id, ad, uzmanlik):
        super().__init__(ad)
        self.egitmen_id = egitmen_id
        self.uzmanlik = uzmanlik

    def __str__(self):
        return f"{self.ad} ({self.uzmanlik})"

class Ogrenci(Kisi):
    def __init__(self, ogrenci_id, ad, email):
        super().__init__(ad)
        self.ogrenci_id = ogrenci_id
        self.email = email
        self.__kayitli_kurslar = [] # Kapsülleme (Encapsulation)

    def kursa_ekle(self, kurs_adi):
        if kurs_adi not in self.__kayitli_kurslar:
            self.__kayitli_kurslar.append(kurs_adi)

    def kurs_listesi(self):
        print(f"\n--- {self.ad} Adlı Öğrencinin Kursları ---")
        if not self.__kayitli_kurslar:
            print("Kayıtlı olunan herhangi bir kurs bulunmamaktadır.")
        else:
            for i, kurs in enumerate(self.__kayitli_kurslar, 1):
                print(f"{i}. {kurs}")
        print("------------------------------------------")

class Kurs:
    def __init__(self, kurs_id, kurs_adi, egitmen, kontenjan):
        self.kurs_id = kurs_id
        self.kurs_adi = kurs_adi
        self.egitmen = egitmen # Composition
        self.kontenjan = kontenjan
        self.kayitli_ogrenciler = []

    def __str__(self):
        kalan_yer = self.kontenjan - len(self.kayitli_ogrenciler)
        return f"[{self.kurs_id}] {self.kurs_adi} | Eğitmen: {self.egitmen.ad} | Kalan Kontenjan: {kalan_yer}/{self.kontenjan}"


# --- 2. VERİTABANI ERİŞİM KATMANI ---

class VeritabaniYoneticisi:
    """Tüm SQL işlemlerinin yürütüldüğü sınıf."""
    def __init__(self, db_ismi="kurs_platformu.db"):
        self.conn = sqlite3.connect(db_ismi)
        self.cursor = self.conn.cursor()
        self.tablolari_kur()

    def tablolari_kur(self):
        # Eğitmenler Tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS egitmenler (
                id TEXT PRIMARY KEY,
                ad TEXT NOT NULL,
                uzmanlik TEXT NOT NULL
            )
        ''')
        # Öğrenciler Tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ogrenciler (
                id TEXT PRIMARY KEY,
                ad TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        ''')
        # Kurslar Tablosu (egitmen_id Yabancı Anahtar - Foreign Key)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kurslar (
                id TEXT PRIMARY KEY,
                ad TEXT NOT NULL,
                egitmen_id TEXT NOT NULL,
                kontenjan INTEGER NOT NULL,
                FOREIGN KEY (egitmen_id) REFERENCES egitmenler (id)
            )
        ''')
        # Çoktan Çoğa İlişki İçin Ara Tablo
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kayitlar (
                ogrenci_id TEXT,
                kurs_id TEXT,
                PRIMARY KEY (ogrenci_id, kurs_id),
                FOREIGN KEY (ogrenci_id) REFERENCES ogrenciler (id),
                FOREIGN KEY (kurs_id) REFERENCES kurslar (id)
            )
        ''')
        self.conn.commit()

    def calistir_ve_kaydet(self, sorgu, parametreler=()):
        try:
            self.cursor.execute(sorgu, parametreler)
            self.conn.commit()
            return True, "Başarılı"
        except sqlite3.IntegrityError as e:
            return False, f"Veritabanı Kural İhlali: {e}"
        except Exception as e:
            return False, f"Hata: {e}"

    def sorgu_getir(self, sorgu, parametreler=()):
        self.cursor.execute(sorgu, parametreler)
        return self.cursor.fetchall()


# --- 3. PLATFORM YÖNETİCİSİ (İŞ MANTIĞI) ---

class PlatformManager:
    """Veritabanı ile OOP Sınıflarını senkronize eden ana sistem"""
    def __init__(self):
        self.db = VeritabaniYoneticisi()
        self.egitmenler = {}
        self.ogrenciler = {}
        self.kurslar = {}
        self.sistemi_veritabanindan_ayaga_kaldir()

    def sistemi_veritabanindan_ayaga_kaldir(self):
        # Eğitmenleri çek
        for row in self.db.sorgu_getir("SELECT id, ad, uzmanlik FROM egitmenler"):
            self.egitmenler[row[0]] = Egitmen(row[0], row[1], row[2])
            
        # Öğrencileri çek
        for row in self.db.sorgu_getir("SELECT id, ad, email FROM ogrenciler"):
            self.ogrenciler[row[0]] = Ogrenci(row[0], row[1], row[2])
            
        # Kursları çek
        for row in self.db.sorgu_getir("SELECT id, ad, egitmen_id, kontenjan FROM kurslar"):
            k_id, k_ad, e_id, kont = row
            egitmen_obj = self.egitmenler.get(e_id)
            self.kurslar[k_id] = Kurs(k_id, k_ad, egitmen_obj, kont)
            
        # Kayıtları çek ve ilişkileri kur
        for row in self.db.sorgu_getir("SELECT ogrenci_id, kurs_id FROM kayitlar"):
            o_id, k_id = row
            if o_id in self.ogrenciler and k_id in self.kurslar:
                ogrenci_obj = self.ogrenciler[o_id]
                kurs_obj = self.kurslar[k_id]
                
                kurs_obj.kayitli_ogrenciler.append(ogrenci_obj)
                ogrenci_obj.kursa_ekle(kurs_obj.kurs_adi)

    def egitmen_ekle(self, id, ad, uzmanlik):
        basarili, mesaj = self.db.calistir_ve_kaydet(
            "INSERT INTO egitmenler (id, ad, uzmanlik) VALUES (?, ?, ?)", (id, ad, uzmanlik)
        )
        if basarili:
            self.egitmenler[id] = Egitmen(id, ad, uzmanlik)
            print(f"✅ Eğitmen '{ad}' sisteme eklendi ve veritabanına kaydedildi.")
        else:
            print(f"❌ Kayıt başarısız: Bu Eğitmen ID zaten kullanılıyor olabilir.")

    def ogrenci_ekle(self, id, ad, email):
        basarili, mesaj = self.db.calistir_ve_kaydet(
            "INSERT INTO ogrenciler (id, ad, email) VALUES (?, ?, ?)", (id, ad, email)
        )
        if basarili:
            self.ogrenciler[id] = Ogrenci(id, ad, email)
            print(f"✅ Öğrenci '{ad}' sisteme eklendi ve veritabanına kaydedildi.")
        else:
            print(f"❌ Kayıt başarısız: ID veya Email zaten kullanılıyor olabilir.")

    def kurs_olustur(self, kurs_id, kurs_adi, egitmen_id, kontenjan):
        if egitmen_id not in self.egitmenler:
            print("❌ Hata: Belirtilen ID'ye sahip bir eğitmen bulunamadı!")
            return
            
        basarili, mesaj = self.db.calistir_ve_kaydet(
            "INSERT INTO kurslar (id, ad, egitmen_id, kontenjan) VALUES (?, ?, ?, ?)",
            (kurs_id, kurs_adi, egitmen_id, kontenjan)
        )
        if basarili:
            egitmen = self.egitmenler[egitmen_id]
            self.kurslar[kurs_id] = Kurs(kurs_id, kurs_adi, egitmen, kontenjan)
            print(f"✅ Kurs '{kurs_adi}' oluşturuldu ve veritabanına kaydedildi.")
        else:
            print("❌ Kurs oluşturulamadı. Bu Kurs ID zaten kullanılıyor olabilir.")

    def kursa_ogrenci_yazdir(self, ogrenci_id, kurs_id):
        if ogrenci_id not in self.ogrenciler or kurs_id not in self.kurslar:
            print("❌ Hata: Öğrenci veya Kurs bulunamadı!")
            return
            
        ogrenci = self.ogrenciler[ogrenci_id]
        kurs = self.kurslar[kurs_id]
        
        # Kontenjan Kontrolü
        if len(kurs.kayitli_ogrenciler) >= kurs.kontenjan:
            print("❌ Hata: Kurs kontenjanı tamamen dolu!")
            return
            
        basarili, mesaj = self.db.calistir_ve_kaydet(
            "INSERT INTO kayitlar (ogrenci_id, kurs_id) VALUES (?, ?)",
            (ogrenci_id, kurs_id)
        )
        
        if basarili:
            kurs.kayitli_ogrenciler.append(ogrenci)
            ogrenci.kursa_ekle(kurs.kurs_adi)
            print(f"✅ Başarılı: {ogrenci.ad}, {kurs.kurs_adi} kursuna kaydedildi.")
        else:
            print(f"❌ Hata: Öğrenci bu kursa zaten kayıtlı!")

    def tum_kurslari_listele(self):
        print("\n=== AKTİF KURSLAR ===")
        if not self.kurslar:
            print("Henüz açılmış bir kurs yok.")
        for kurs in self.kurslar.values():
            print(kurs)
        print("=====================")


# --- 4. ANA PROGRAM AKIŞI ---

def main():
    print("Veritabanı bağlantısı kuruluyor...")
    sistem = PlatformManager()
    
    # Sistemin boş olmaması için eğer hiç eğitmen yoksa varsayılan bir tane ekleyelim
    if not sistem.egitmenler:
        sistem.db.calistir_ve_kaydet("INSERT INTO egitmenler (id, ad, uzmanlik) VALUES (?, ?, ?)", ("E1", "Ahmet Yılmaz", "Yazılım Mühendisliği"))
        sistem.sistemi_veritabanindan_ayaga_kaldir()
    
    while True:
        print("\n" + "="*35)
        print("🚀 SQL DESTEKLİ KURS PLATFORMU")
        print("="*35)
        print("1. Yeni Öğrenci Ekle")
        print("2. Yeni Kurs Oluştur")
        print("3. Kursları Listele")
        print("4. Öğrenciyi Kursa Kaydet")
        print("5. Öğrencinin Kurslarını Görüntüle")
        print("6. Yeni Eğitmen Ekle")
        print("0. Sistemden Çıkış Yap")
        
        secim = input("\nLütfen bir işlem seçiniz (0-6): ")

        if secim == '0':
            print("Veritabanı bağlantısı kapatılıyor... İyi çalışmalar!")
            sistem.db.conn.close() # Çıkarken SQL bağlantısını güvenle kapatıyoruz
            break 
            
        elif secim == '1':
            o_id = input("Öğrenci ID (örn: O1): ")
            ad = input("Öğrenci Adı: ")
            email = input("Öğrenci Email: ")
            sistem.ogrenci_ekle(o_id, ad, email)
            
        elif secim == '2':
            k_id = input("Kurs ID (örn: K1): ")
            ad = input("Kurs Adı: ")
            print("Mevcut Eğitmenler:", [f"{id}: {e.ad}" for id, e in sistem.egitmenler.items()])
            e_id = input("Eğitmen ID'sini giriniz: ")
            try:
                kontenjan = int(input("Kontenjan (Sayısal değer): "))
                sistem.kurs_olustur(k_id, ad, e_id, kontenjan)
            except ValueError:
                print("❌ Hata: Kontenjan için geçerli bir sayı girmelisiniz.")
                
        elif secim == '3':
            sistem.tum_kurslari_listele()
            
        elif secim == '4':
            o_id = input("Kayıt yapılacak Öğrenci ID: ")
            k_id = input("Kayıt olunacak Kurs ID: ")
            sistem.kursa_ogrenci_yazdir(o_id, k_id)
            
        elif secim == '5':
            o_id = input("Kursları listelenecek Öğrenci ID: ")
            if o_id in sistem.ogrenciler:
                sistem.ogrenciler[o_id].kurs_listesi()
            else:
                print("❌ Hata: Veritabanında böyle bir öğrenci bulunamadı.")
                
        elif secim == '6':
            e_id = input("Eğitmen ID (örn: E2): ")
            ad = input("Eğitmen Adı: ")
            uzmanlik = input("Uzmanlık Alanı (örn: Yapay Zeka): ")
            sistem.egitmen_ekle(e_id, ad, uzmanlik)
            
        else:
            print("Geçersiz seçim! Lütfen menüdeki numaralardan birini giriniz.")

if __name__ == "__main__":
    main()