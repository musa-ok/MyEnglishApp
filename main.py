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

try:
    db.init_db()
except Exception as e:
    st.error(f"DB Hatası: {e}")

# --- GELİŞMİŞ CSS (MOBİL & ESTETİK) ---
st.markdown("""
<style>
    /* Genel Ayarlar */
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }

    /* Mobil Uyumlu Kart */
    .card-container {
        background: linear-gradient(145deg, #1e2329, #161b22);
        padding: 30px 20px;
        border-radius: 20px;
        box-shadow: 5px 5px 15px #0b0d11, -5px -5px 15px #212933;
        text-align: center;
        margin-bottom: 25px;
        border: 1px solid #30363D;
        color: #fff;
    }

    /* Kelime Stili */
    .english-word { 
        color: #58A6FF !important; 
        font-size: 48px; 
        font-weight: 800; 
        margin: 10px 0;
        text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
    }

    /* Responsive Font (Telefonda küçülsün) */
    @media (max-width: 600px) {
        .english-word { font-size: 36px; }
        .card-container { padding: 20px 10px; }
    }

    /* Input Alanları */
    .stTextInput input, .stTextArea textarea { 
        background-color: #0d1117 !important; 
        color: #c9d1d9 !important; 
        border: 1px solid #30363D !important; 
        border-radius: 12px;
    }

    /* Butonlar - Tam Genişlik ve Yuvarlak */
    .stButton button { 
        border-radius: 12px; 
        font-weight: 600; 
        width: 100%; 
        padding: 0.5rem 1rem;
        transition: transform 0.1s;
    }
    .stButton button:active { transform: scale(0.98); }

    /* Özel Buton Renkleri */
    /* Primary (Ezberledim): Yeşil */
    /* Secondary (Emin Değilim): Turuncu */

    /* Rozetler */
    .badge { 
        display: inline-block; 
        padding: 5px 12px; 
        border-radius: 20px; 
        font-size: 12px; 
        font-weight: bold; 
        margin: 4px; 
        color: #000 !important;
    }
    .badge-level { background-color: #D2A8FF; } /* Mor */
    .badge-pos { background-color: #7EE787; }   /* Yeşil */

    /* Puan Kutusu */
    .score-box {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
    }
    .score-val { font-size: 28px; font-weight: 900; color: #F2CC60; }

    /* Liste Tablosu */
    [data-testid="stDataFrame"] { border: 1px solid #30363D; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)


# --- FONKSİYONLAR ---
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
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO();
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        md = f"""<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>"""
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.toast("Ses hatası", icon="⚠️")


# --- APP ---
if 'user' not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; color:#58A6FF;'>🇬🇧 Oxford 3000</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Giriş", "Kayıt"])
        with t1:
            u = st.text_input("Kullanıcı Adı");
            p = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap", type="primary"):
                user = db.login_user(u, p)
                if user:
                    st.session_state.user = user; st.rerun()
                else:
                    st.error("Hatalı!")
        with t2:
            nu = st.text_input("Kullanıcı", key="nu");
            np = st.text_input("Şifre", type="password", key="np")
            if st.button("Kayıt Ol"):
                if db.register_user(nu, np):
                    st.success("Tamam!"); st.info("Giriş yapabilirsin.")
                else:
                    st.error("Alınmış.")
else:
    user_id = st.session_state.user[0];
    username = st.session_state.user[1]
    learned_count, xp, streak = db.get_user_stats(user_id)
    rank_title, min_xp, max_xp = get_user_rank(xp)
    level_stats = db.get_level_progress(user_id)

    with st.sidebar:
        st.markdown(
            f"<div class='score-box'><div style='font-size:12px; color:#8b949e;'>XP PUANIN</div><div class='score-val'>{xp}</div><div>{rank_title}</div></div>",
            unsafe_allow_html=True)
        st.markdown(
            f"<div style='text-align:center; margin-bottom:15px; background:#21262d; padding:8px; border-radius:10px;'>🔥 {streak} Günlük Seri</div>",
            unsafe_allow_html=True)

        target_choice = st.selectbox("🎯 Hedef Seviye", ["A1", "A2", "B1", "B2"], index=3)
        active_levels = ["A1"]
        if "A2" in target_choice: active_levels += ["A2"]
        if "B1" in target_choice: active_levels += ["A2", "B1"]
        if "B2" in target_choice: active_levels += ["A2", "B1", "B2"]
        st.session_state.active_levels = active_levels

        st.markdown("### 📊 İlerleme")
        for lvl in active_levels:
            stats = level_stats.get(lvl, {'total': 0, 'learned': 0})
            if stats['total'] > 0:
                pc = stats['learned'] / stats['total']
                st.markdown(
                    f"<div style='font-size:12px; display:flex; justify-content:space-between;'><span>{lvl}</span><span>%{int(pc * 100)}</span></div>",
                    unsafe_allow_html=True)
                st.progress(min(pc, 1.0))

        st.divider()
        menu = st.radio("Menü", ["⚡ Çalış", "🏆 Quiz", "🥇 Liderler", "📚 Listem"])
        if st.button("Çıkış"): st.session_state.user = None; st.rerun()

    # --- 1. ÇALIŞMA KARTLARI ---
    if menu == "⚡ Çalış":
        if 'card_word' not in st.session_state:
            st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels)

        w = st.session_state.card_word
        if w:
            wid, eng, tur, lvl, pos, ex = w if len(w) == 6 else (*w, "Kelime", "-")

            st.markdown(f"""
            <div class="card-container">
                <div class="english-word">{eng.upper()}</div>
                <div>
                    <span class="badge badge-level">{lvl}</span>
                    <span class="badge badge-pos">{pos}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Mobilde butonları hizalamak için columns kullanıyoruz
            c_audio, c_next = st.columns([1, 1])
            with c_audio:
                if st.button("🔊 Dinle"): autoplay_audio(eng)
            with c_next:
                if st.button("Sonraki ➡️"):
                    st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels);
                    st.rerun()

            with st.expander("🇹🇷 Anlamı ve Örnek"):
                st.markdown(f"### {tur}")
                st.info(f"Examples: {ex}")

            st.markdown("---")

            # Cümle Kontrol
            sent = st.text_area("Cümle kur (10 XP):", placeholder="I want to go...")
            if st.button("✨ Yapay Zekaya Sor"):
                if len(sent) > 3:
                    with st.spinner("Hoca bakıyor..."):
                        f = ai.get_ai_feedback(eng, sent);
                        st.success(f);
                        db.add_xp(user_id, 10);
                        st.balloons()

            st.markdown("---")
            st.caption("Bu kelimeyi ne yapalım?")

            # AKSİYON BUTONLARI (MOBİL DOSTU)
            # 3 Buton Yan Yana
            col_unsure, col_learn = st.columns(2)

            with col_unsure:
                # Turuncu renkte 'Emin Değilim' butonu
                if st.button("🤔 Emin Değilim\n(Listeye At)"):
                    db.mark_word_needs_review(user_id, wid)
                    st.toast("Tekrar listesine eklendi!", icon="📝")
                    time.sleep(0.5)
                    st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels)
                    st.rerun()

            with col_learn:
                # Yeşil renkte 'Ezberledim' butonu (type='primary')
                if st.button("✅ Ezberledim\n(+30 XP)", type="primary"):
                    db.mark_word_learned(user_id, wid)
                    db.add_xp(user_id, 30)
                    st.success("Süpersin!")
                    time.sleep(0.5)
                    st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels)
                    st.rerun()

        else:
            st.success("Bu seviyedeki tüm kelimeleri bitirdin!")

    # --- 2. QUIZ ---
    elif menu == "🏆 Quiz":
        st.subheader("🚀 Hızlı Quiz")
        if 'quiz_data' not in st.session_state or st.session_state.quiz_data is None:
            # Önce 'needs_review' olanları getirir, yoksa rastgele
            st.session_state.quiz_data = db.get_quiz_question(user_id, st.session_state.active_levels)
            if st.session_state.quiz_data:
                opts = st.session_state.quiz_data['options'];
                random.shuffle(opts)
                st.session_state.quiz_data['shuffled'] = opts

        q = st.session_state.quiz_data
        if q:
            # Quiz Kartı
            st.markdown(f"""
            <div class="card-container" style="padding:15px; margin-bottom:15px;">
                <h2 style="color:#F2CC60; margin:0;">{q['english'].upper()}</h2>
            </div>
            """, unsafe_allow_html=True)

            # Şıklar
            cols = st.columns(2)  # 2x2 düzen
            clicked = False
            for i, opt in enumerate(q['shuffled']):
                if cols[i % 2].button(opt, key=f"q_{i}", use_container_width=True):
                    if opt == q['correct_answer']:
                        st.success("DOĞRU! 🎉 +20 XP")
                        db.add_xp(user_id, 20)