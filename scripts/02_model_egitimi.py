import pandas as pd
import joblib
import os
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# --- AYARLAR ---
GIRIS_DOSYASI = os.path.join("filtrelenmiş_dosya.xlsx")
MODEL_KLASORU = "models"

def model_egit():
    print("⏳ Model eğitimi başlıyor...")
    
    # 1. Veriyi Yükle
    df = pd.read_excel(GIRIS_DOSYASI)
    
    # 2. Özellik Seçimi (Sadece saha oyuncusu yeteneklerini seçiyoruz)
    # Veri setindeki sütun isimlerine göre burayı güncelleyebilirsin
    ozellikler = [
        'overall', 'potential', 'pace', 'shooting', 'passing', 
        'dribbling', 'defending', 'physic'
    ]
    
    # Sütunların varlığını kontrol et
    mevcut_ozellikler = [col for col in ozellikler if col in df.columns]
    X = df[mevcut_ozellikler].fillna(0) # Eksik değerleri 0 ile doldur
    
    print(f"✅ Seçilen özellik sayısı: {len(mevcut_ozellikler)}")

    # 3. Ölçeklendirme (StandardScaler)
    # Not: Ortalama 0, Standart Sapma 1 olacak şekilde veriyi hizalar.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 4. K-Means Uygulama
    # Kaç küme olacağını (n_clusters) projenin detayına göre seçebilirsin. 
    # 10 küme başlangıç için iyidir (Farklı oyuncu tipleri için).
    print("🔄 K-Means algoritması çalıştırılıyor...")
    kmeans = KMeans(n_clusters=10, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X_scaled)
    
    # 5. Modelleri Kaydetme
    # Streamlit sunumunda tekrar eğitmemek için modelleri dışarı aktarıyoruz.
    if not os.path.exists(MODEL_KLASORU):
        os.makedirs(MODEL_KLASORU)
        
    joblib.dump(kmeans, os.path.join(MODEL_KLASORU, "kmeans_model.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_KLASORU, "scaler.pkl"))
    # Kümelenmiş yeni veriyi de kaydedelim
    df.to_excel(os.path.join("trained.xlsx"), index=False)
    
    print("-" * 40)
    print("🎉 MODEL EĞİTİLDİ VE KAYDEDİLDİ!")
    print(f"Modeller '{MODEL_KLASORU}' klasörüne, kümelenmiş veri 'data' klasörüne atıldı.")
    print("-" * 40)

if __name__ == "__main__":
    model_egit()