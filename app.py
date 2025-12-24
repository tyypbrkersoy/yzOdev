import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from scipy.spatial.distance import cdist
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# --- 1. SENİN DOLDURACAĞIN ÖZELLİK LİSTESİ ---
# Excel sütun başlıklarına göre bu listeyi dilediğin gibi güncelle.
# Sadece sayısal (numeric) sütunları eklediğinden emin ol.
TEKNIK_OZELLIKLER = [
    'pace','shooting','passing','dribbling','defending','physic','attacking_crossing','attacking_finishing',
    'attacking_heading_accuracy','attacking_short_passing','skill_dribbling','skill_curve','skill_fk_accuracy',
    'skill_long_passing','skill_ball_control','movement_acceleration','movement_sprint_speed','movement_agility',
    'movement_reactions','movement_balance','power_shot_power','power_jumping','power_stamina','power_strength',
    'power_long_shots','mentality_aggression','mentality_interceptions','mentality_positioning','mentality_vision',
    'mentality_penalties','mentality_composure','defending_marking_awareness','defending_standing_tackle',
    'defending_sliding_tackle','goalkeeping_diving','goalkeeping_handling','goalkeeping_kicking','goalkeeping_positioning',
    'goalkeeping_reflexes','goalkeeping_speed'
]

# Sabit Sütunlar
DOSYA_ADI = "trained.xlsx"
ID_SUTUNU = 'player_id'
ISIM_SUTUNU = 'short_name'
CLUSTER_SUTUNU = 'cluster'

# --- AYARLAR VE CSS ---
pd.set_option('future.no_silent_downcasting', True)
st.set_page_config(page_title="FIFA 23 Scouting Tool", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; background-color: #262730; }
    .main-title { font-size: 36px; font-weight: bold; color: #4CAF50; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- VERİ YÜKLEME ---
@st.cache_data
def veriyi_yukle():
    if os.path.exists(DOSYA_ADI):
        df = pd.read_excel(DOSYA_ADI)
        df.columns = df.columns.str.strip()
        return df
    return None

df = veriyi_yukle()

if df is None:
    st.error(f"❌ '{DOSYA_ADI}' dosyası bulunamadı! Lütfen dosyanın app.py ile aynı dizinde olduğundan emin olun.")
    st.stop()


# --- SESSION STATE (Seçimler için) ---
if 'secilenler' not in st.session_state:
    st.session_state.secilenler = []

# --- ARAYÜZ BAŞLANGIÇ ---
st.markdown('<p class="main-title">⚽ FIFA 23 Akıllı Oyuncu Öneri Sistemi</p>', unsafe_allow_html=True)

# --- 2. ÖZELLİK SEÇİM PENCERESİ (SCROLLABLE) ---
st.subheader("⚙️ Analiz Kriterlerini Seçin")
col_sol, col_sag = st.columns(2)

# Excel'de mevcut olan teknik özellikleri filtrele
mevcut_teknik_listesi = [c for c in TEKNIK_OZELLIKLER if c in df.columns]

with col_sol:
    st.write("📋 **Mevcut Özellikler**")
    arama = st.text_input("Özellik Ara...", placeholder="Örn: pace", label_visibility="collapsed")
    
    with st.container(height=300, border=True):
        mevcutlar = [c for c in mevcut_teknik_listesi if c not in st.session_state.secilenler and arama.lower() in c.lower()]
        m_cols = st.columns(2)
        for i, m_name in enumerate(mevcutlar):
            if m_cols[i % 2].button(f"➕ {m_name}", key=f"add_{m_name}"):
                st.session_state.secilenler.append(m_name)
                st.rerun()

with col_sag:
    st.write("🎯 **Seçilen Kriterler**")
    with st.container(height=300, border=True):
        if not st.session_state.secilenler:
            st.info("Henüz bir özellik seçilmedi. Soldaki listeden ekleyin.")
        else:
            for s_col in st.session_state.secilenler:
                c1, c2 = st.columns([0.85, 0.15])
                c1.success(f"**{s_col}**")
                if c2.button("❌", key=f"del_{s_col}"):
                    st.session_state.secilenler.remove(s_col)
                    st.rerun()

st.divider()

# --- 3. ANALİZ PANELİ ---
c_oyuncu, c_n = st.columns([0.7, 0.3])
secilen_oyuncu_ismi = c_oyuncu.selectbox("Analiz Edilecek Oyuncu:", df[ISIM_SUTUNU].unique())
n_oneri = c_n.number_input("Kaç Benzer Oyuncu Getirilsin?", 1, 10, 4)

if st.button("🚀 ANALİZİ VE GRAFİĞİ ÇALIŞTIR", use_container_width=True):
    if len(st.session_state.secilenler) < 2:
        st.warning("⚠️ Lütfen analiz ve grafik için en az 2 özellik seçin!")
    else:
        # --- HESAPLAMA ---
        target_player = df[df[ISIM_SUTUNU] == secilen_oyuncu_ismi].iloc[0]
        scaler = StandardScaler()
        
        # Sadece seçilen özellikleri kullanıyoruz
        features = st.session_state.secilenler
        X_scaled = scaler.fit_transform(df[features].fillna(0))
        t_scaled = scaler.transform(pd.DataFrame([target_player[features].fillna(0)]))
        
        # Öklid Mesafesi
        df['distance'] = cdist(t_scaled, X_scaled, metric='euclidean').flatten()
        sonuclar = df.sort_values('distance').iloc[1:n_oneri+1]

        # --- GÖRSEL 1: OYUNCU KARTLARI ---
        st.subheader(f"✅ {secilen_oyuncu_ismi} İçin En Benzer Oyuncular")
        card_cols = st.columns(n_oneri)
        for idx, (i, row) in enumerate(sonuclar.iterrows()):
            with card_cols[idx]:
                with st.container(border=True):
                    st.markdown(f"**{row[ISIM_SUTUNU]}**")
                    st.caption(f"Benzerlik: %{max(0, int(100 - row['distance']*10))}")

        st.divider()

        # --- GÖRSEL 2: PCA NOKTA GRAFİĞİ (İNTERAKTİF) ---
        st.subheader("📊 Oyuncu Yetenek Uzayı (Tüm Oyuncular)")
        st.write("Mouse ile noktaların üzerine gelerek oyuncu isimlerini ve konumlarını takip edebilirsiniz.")
        
        pca = PCA(n_components=2)
        components = pca.fit_transform(X_scaled)
        df['x'], df['y'] = components[:, 0], components[:, 1]
        
        # Plotly Express ile İnteraktif Grafik
        fig = px.scatter(
            df, x='x', y='y',
            color=CLUSTER_SUTUNU if CLUSTER_SUTUNU in df.columns else None,
            hover_name=ISIM_SUTUNU,
            hover_data=features[:4], # Hoverda seçilen ilk 4 özelliği göster
            title="Yetenek Segmentasyon Haritası",
            template="plotly_dark",
            color_continuous_scale=px.colors.qualitative.Prism
        )
        
        # Seçilen oyuncuyu özel bir sembolle işaretle
        target_coords = df[df[ISIM_SUTUNU] == secilen_oyuncu_ismi]
        fig.add_trace(go.Scatter(
            x=target_coords['x'], y=target_coords['y'],
            mode='markers+text',
            name='Seçilen Oyuncu',
            text=[secilen_oyuncu_ismi],
            textposition="top center",
            marker=dict(color='white', size=15, symbol='star', line=dict(width=2, color='red'))
        ))

        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)

# --- ALT BİLGİ ---
with st.expander("📂 Ham Veri Setini Görüntüle"):
    st.dataframe(df, use_container_width=True)