import streamlit as st
import time
import pandas as pd
import random
import base64
from io import BytesIO
from gtts import gTTS
import database as db
import ai_manager as ai

# 1. AYARLAR
st.set_page_config(page_title="Oxford 3000 AI Coach", page_icon="🇬🇧", layout="wide")

# Veritabanını başlat
try:
    db.init_db()
except Exception as e:
    st.error(f"Veritabanı hatası: {e}")

# --- TEMA & CSS ---
st.markdown("""
<style>
    /* Ana Arka Plan */
    .stApp { background-color: #0E1117 !important; color: #FAFAFA !important; }

    /* Yan Menü */
    [data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }

    /* Kart Tasarımı */
    .card-container {
        background-color: #FFFFFF !important;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        text-align: center;
        margin-bottom: 25px;
        color: #333 !important;
    }

    /* Kelime Rengi */
    .english-word { color: #2E86C1 !important; font-size: 60px; font-weight: 900; margin: 0; }

    /* Inputlar */
    .stTextInput input, .stTextArea textarea { background-color: #262730 !important; color: #FAFAFA !important; border: 1px solid #4A4A4A !important; border-radius: 10px; }

    /* Butonlar */
    .stButton button { border-radius: 8px; font-weight: bold; width: 100%; }

    /* Rozetler */
    .badge { display: inline-block; padding: 6px 14px; border-radius: 12px; font-size: 14px; font-weight: bold; margin: 5px; color: #fff !important; }
    .badge-level { background-color: #F1C40F !important; color: #000 !important; }
    .badge-pos { background-color: #E74C3C !important; }

    /* Puan Kutusu (Sidebar) */
    .score-box {
        background-color: #21262d;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .score-val { font-size: 24px; font-weight: bold; color: #58a6ff; }
    .score-label { font-size: 12px; color: #8b949e; }

    /* İlerleme Çubuğu */
    .level-stat { margin-bottom: 5px; font-size: 13px; color: #ccc; }
    .stProgress > div > div > div > div { background-color: #2E86C1; }

    /* Sıralama Kartı */
    .rank-card {
        background-color: #FFFFFF !important;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        color: #333 !important;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }

    /* Yazı Renkleri */
    h1, h2, h3 { color: #3498DB !important; }
</style>
""", unsafe_allow_html=True)


# --- RÜTBE FONKSİYONU (ZORLAŞTIRILMIŞ) ---
def get_user_rank(xp):
    if xp < 500:
        return "Çaylak 👶", 0, 500
    elif xp < 2500:
        return "Hırslı Öğrenci 🤓", 500, 2500
    elif xp < 7000:
        return "Kelime Avcısı 🏹", 2500, 7000
    elif xp < 15000:
        return "B2 Master 😎", 7000, 15000
    else:
        return "Grand Master 🔥", 15000, 50000


def autoplay_audio(text):
    """Sesi arka planda otomatik çalar"""
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        # Sesi base64'e çevirip HTML player içine gömüyoruz
        b64 = base64.b64encode(fp.getvalue()).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.toast("Ses çalınamadı (İnternet?)", icon="⚠️")


# --- OTURUM ---
if 'user' not in st.session_state:
    st.session_state.user = None

# ================= GİRİŞ EKRANI =================
if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🇬🇧 Oxford 3000</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
        with tab1:
            u = st.text_input("Kullanıcı Adı")
            p = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap"):
                user = db.login_user(u, p)
                if user:
                    st.session_state.user = user
                    st.success("Giriş Başarılı!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Hatalı!")
        with tab2:
            nu = st.text_input("Yeni Kullanıcı", key="nu")
            np = st.text_input("Yeni Şifre", type="password", key="np")
            if st.button("Kayıt Ol"):
                if db.register_user(nu, np):
                    st.success("Kayıt Başarılı!")
                else:
                    st.error("Bu isim alınmış.")

# ================= UYGULAMA İÇİ =================
else:
    user_id = st.session_state.user[0]
    username = st.session_state.user[1]

    # İstatistikler
    learned_count, xp, streak = db.get_user_stats(user_id)
    rank_title, min_xp, max_xp = get_user_rank(xp)
    level_stats = db.get_level_progress(user_id)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👋 {username}")

        # 1. PUAN KUTUSU (GERİ GELDİ!)
        st.markdown(f"""
        <div class="score-box">
            <div class="score-label">TOPLAM PUAN (XP)</div>
            <div class="score-val">✨ {xp}</div>
            <div style="margin-top:5px; font-size:12px; color:#aaa;">Sonraki Rütbe: {max_xp}</div>
        </div>
        """, unsafe_allow_html=True)

        # 2. STREAK
        st.markdown(f"""
        <div style="background-color:#262730; border:1px solid #333; padding:8px; border-radius:10px; text-align:center; margin-bottom:15px;">
            <h4 style="margin:0; color:#FF5722 !important;">🔥 {streak} Günlük Seri</h4>
        </div>
        """, unsafe_allow_html=True)

        st.info(f"Rütbe: {rank_title}")

        # 3. SEVİYE SEÇİMİ
        st.divider()
        st.markdown("### 🎯 Hedef")
        target_choice = st.selectbox(
            "Seviye Seç:",
            ["A1 (Başlangıç)", "A2 (Temel)", "B1 (Orta)", "B2 (İleri)"],
            index=3
        )

        active_levels = []
        if "A1" in target_choice:
            active_levels = ["A1"]
        elif "A2" in target_choice:
            active_levels = ["A1", "A2"]
        elif "B1" in target_choice:
            active_levels = ["A1", "A2", "B1"]
        elif "B2" in target_choice:
            active_levels = ["A1", "A2", "B1", "B2"]

        st.session_state.active_levels = active_levels

        # 4. İLERLEME ÇUBUKLARI
        st.markdown("### 📊 İlerleme")
        for lvl in active_levels:
            stats = level_stats.get(lvl, {'total': 0, 'learned': 0})
            total = stats['total']
            done = stats['learned']
            if total > 0:
                percent = done / total
                st.markdown(f"<div class='level-stat'><b>{lvl}</b>: {done}/{total} (%{int(percent * 100)})</div>",
                            unsafe_allow_html=True)
                st.progress(min(percent, 1.0))

        st.divider()
        menu = st.radio("Menü", ["⚡ Kartlar", "🏆 Quiz", "🥇 Sıralama", "📚 Listem"])

        st.write("")
        if st.button("Çıkış"):
            st.session_state.user = None
            st.rerun()

    # --- 1. KARTLAR ---
    if menu == "⚡ Kartlar":
        if 'card_word' not in st.session_state:
            st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels)

        word_data = st.session_state.card_word

        if word_data:
            w_id, eng, tur, lvl, pos, ex = word_data if len(word_data) == 6 else (*word_data, "Kelime", "Örnek yok")

            # Kart Tasarımı
            st.markdown(f"""
            <div class="card-container">
                <div class="english-word">{eng.upper()}</div>
                <div style="margin-top:20px;">
                    <span class="badge badge-level">{lvl}</span>
                    <span class="badge badge-pos">{pos}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # SES ÖZELLİĞİ (Butona basınca direkt çalar)
            # Butonu siyah zemine değil, kartın altına koyuyoruz.
            # Butona basıldığında `play_audio` tetiklenir ve sayfa yenilenip sesi gömer.
            if st.button("🔊 Sesi Dinle", type="secondary"):
                autoplay_audio(eng)

            with st.expander("🇹🇷 Türkçesi"):
                st.markdown(f"<h3 style='color:#333 !important;'>{tur}</h3>", unsafe_allow_html=True)
                st.info(f"Örnek: {ex}")

            st.divider()

            sent = st.text_area("Cümle kur, puan kazan:", placeholder="I want to...")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✨ Kontrol Et"):
                    if len(sent) > 3:
                        with st.spinner("İnceleniyor..."):
                            f = ai.get_ai_feedback(eng, sent)
                            st.info(f)
                            db.add_xp(user_id, 10)
                            st.balloons()
            with c2:
                if st.button("✅ Ezberledim (+30)", type="primary"):
                    db.mark_word_learned(user_id, w_id)
                    db.add_xp(user_id, 30)
                    st.success("Ezberlendi!")
                    time.sleep(1)
                    st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels)
                    st.rerun()

            if st.button("Sonraki Kelime ➡️"):
                st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels)
                st.rerun()
        else:
            st.success("Tebrikler! Seçili seviyedeki tüm kelimeler bitti!")

    # --- 2. QUIZ ---
    elif menu == "🏆 Quiz":
        st.subheader("Quiz Modu")
        if 'quiz_data' not in st.session_state or st.session_state.quiz_data is None:
            st.session_state.quiz_data = db.get_quiz_question(user_id, st.session_state.active_levels)

            if st.session_state.quiz_data:
                opts = st.session_state.quiz_data['options']
                random.shuffle(opts)
                st.session_state.quiz_data['shuffled'] = opts

        q = st.session_state.quiz_data

        if q:
            st.markdown(f"""
            <div class="card-container" style="padding:20px;">
                <h1 style="color:#E67E22; margin:0;">{q['english'].upper()}</h1>
            </div>
            """, unsafe_allow_html=True)

            with st.form("quiz_form"):
                ans = st.radio("Doğru cevap hangisi?", q['shuffled'])
                if st.form_submit_button("Cevapla"):
                    if ans == q['correct_answer']:
                        st.success("DOĞRU! +20 XP")
                        db.add_xp(user_id, 20)
                        time.sleep(1.5)
                        st.session_state.quiz_data = None
                        st.rerun()
                    else:
                        st.error(f"Yanlış. Doğrusu: {q['correct_answer']}")
                        time.sleep(2)
                        st.session_state.quiz_data = None
                        st.rerun()
        else:
            st.warning("Quiz için uygun kelime yok.")

    # --- 3. SIRALAMA ---
    elif menu == "🥇 Sıralama":
        st.title("🏆 Liderlik Tablosu")
        leaders = db.get_leaderboard()
        if leaders:
            for i, (u_name, u_xp, u_streak) in enumerate(leaders):
                rank = i + 1
                icon = "🏅"
                if rank == 1:
                    icon = "🥇"
                elif rank == 2:
                    icon = "🥈"
                elif rank == 3:
                    icon = "🥉"

                border_style = "border: 2px solid #3498DB;" if u_name == username else "border: 1px solid #ddd;"

                st.markdown(f"""
                <div class="rank-card" style="{border_style}">
                    <div style="display:flex; align-items:center; gap:15px;">
                        <span style="font-size:30px;">{icon}</span>
                        <div style="text-align:left;">
                            <strong style="font-size:18px; color:#2E86C1;">{u_name}</strong>
                            <div style="font-size:12px; color:#666;">Seri: 🔥 {u_streak} Gün</div>
                        </div>
                    </div>
                    <div style="font-size:20px; font-weight:bold; color:#333;">
                        {u_xp} XP
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Liste boş.")

    # --- 4. LİSTEM ---
    elif menu == "📚 Listem":
        st.subheader("Ezberlediğim Kelimeler")
        l_words = db.get_learned_words(user_id)
        if l_words:
            df = pd.DataFrame(l_words)
            if len(df.columns) == 5:
                df.columns = ["İngilizce", "Türkçe", "Seviye", "Tür", "Örnek"]
            elif len(df.columns) == 4:
                df.columns = ["İngilizce", "Türkçe", "Seviye", "Örnek"]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Listen boş.")