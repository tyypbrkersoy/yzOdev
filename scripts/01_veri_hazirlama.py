import pandas as pd
import ftfy
import os

# --- AYARLAR ---
# Buraya dosyanın TAM adını yaz. (Uzantısı .csv mi .xlsx mi dikkat et)
# Eğer klasörde fifa_verileri.csv varsa .csv kalsın.
DOSYA_ADI = "fifa_verileri.xlsx" 
GIRIS_DOSYASI = os.path.join("data", DOSYA_ADI)
CIKIS_DOSYASI = os.path.join("data", "fifa_23_cleaned.xlsx")

def veriyi_oku(dosya_yolu):
    """Dosya uzantısına göre otomatik okuma yapar."""
    _, uzanti = os.path.splitext(dosya_yolu)
    
    print(f"📂 Dosya formatı algılandı: {uzanti}")
    
    if uzanti == '.xlsx' or uzanti == '.xls':
        # Excel okurken sep parametresi KULLANILMAZ!
        return pd.read_excel(dosya_yolu)
    
    elif uzanti == '.csv':
        # CSV okurken ; veya , ayıracı denenir.
        try:
            print("   -> Noktalı virgül (;) ile deneniyor...")
            return pd.read_csv(dosya_yolu, sep=";", low_memory=False, encoding='utf-8')
        except UnicodeDecodeError:
            print("   -> UTF-8 yemedi, Latin-1 deneniyor...")
            return pd.read_csv(dosya_yolu, sep=";", low_memory=False, encoding='latin-1')
        except:
            print("   -> Noktalı virgül olmadı, virgül (,) ile deneniyor...")
            return pd.read_csv(dosya_yolu, sep=",", low_memory=False)
    else:
        raise ValueError("❌ Desteklenmeyen dosya formatı! Sadece .csv veya .xlsx")

def veriyi_temizle_ve_hazirla():
    print(f"⏳ İşlem Başlıyor: '{GIRIS_DOSYASI}' okunuyor...")
    
    # 1. AKILLI OKUMA
    try:
        df = veriyi_oku(GIRIS_DOSYASI)
    except FileNotFoundError:
        print(f"❌ HATA: Dosya bulunamadı! '{GIRIS_DOSYASI}' yolunu kontrol et.")
        print("   İpucu: Dosyayı 'data' klasörünün içine attın mı?")
        return
    except Exception as e:
        print(f"❌ Kritik Hata: {e}")
        return

    print(f"✅ Veri Başarıyla Okundu. Satır Sayısı: {len(df)}")

    # 2. Temizlik
    print("🧹 Boş satırlar temizleniyor...")
    df = df.dropna(how='all')
    
    # 3. Yinelenen Oyuncuları Temizle (Aggregation)
    print("🔄 Yinelenen oyuncular birleştiriliyor...")
    
    # ID yoksa isim kullan, varsa ID kullan
    grup_sutunu = 'player_id' if 'player_id' in df.columns else 'short_name'
    print(f"   -> Gruplama anahtarı: {grup_sutunu}")

    df_sayisal = df.groupby(grup_sutunu).mean(numeric_only=True)
    
    metin_adaylari = ['short_name', 'long_name', 'player_positions', 'club_name', 'nationality_name', 'preferred_foot']
    mevcut_metinler = [col for col in metin_adaylari if col in df.columns]
    
    df_metin = df.groupby(grup_sutunu)[mevcut_metinler].first()
    
    df_final = pd.concat([df_metin, df_sayisal], axis=1).reset_index()
    
    # 4. Karakter Düzeltme
    print("✨ Karakterler düzeltiliyor...")
    for col in mevcut_metinler:
        df_final[col] = df_final[col].astype(str).apply(ftfy.fix_text).str.strip()

    # 5. Kaydet
    print(f"💾 Dosya kaydediliyor: {CIKIS_DOSYASI}")
    df_final.round(0).to_excel(CIKIS_DOSYASI, index=False)
    
    print("-" * 40)
    print(f"🎉 İŞLEM TAMAMLANDI! Dosya hazır.")
    print("-" * 40)

if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
    veriyi_temizle_ve_hazirla()