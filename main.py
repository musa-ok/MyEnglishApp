import streamlit as st
import time
import random
import base64
from io import BytesIO
from gtts import gTTS
import database as db

# 1. AYARLAR
st.set_page_config(page_title="Oxford 3000 Coach", page_icon="🇬🇧", layout="wide")

try:
    db.init_db()
except Exception as e:
    st.error(f"DB Hatası: {e}")

# --- CSS TASARIM ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    .block-container { padding-top: 2rem !important; max-width: 800px; }

    /* KART TASARIMI */
    .card-container {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363D;
        border-radius: 24px;
        padding: 40px 20px;
        min-height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        transition: transform 0.3s ease, border-color 0.3s ease;
        margin-bottom: 20px;
    }
    .card-container:hover { border-color: #58A6FF; transform: translateY(-5px); }

    .word-main {
        font-size: 48px; font-weight: 800;
        background: -webkit-linear-gradient(45deg, #58A6FF, #1f6feb);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .word-meaning { font-size: 42px; font-weight: 700; color: #7EE787; margin-bottom: 10px; }
    .meta-info { font-size: 14px; color: #8b949e; background: rgba(255,255,255,0.05); padding: 5px 15px; border-radius: 20px; margin-top: 10px; display: inline-block; }

    /* BUTONLAR */
    div.stButton > button { border-radius: 12px; font-weight: 600; border: 1px solid #30363D; height: 55px; transition: all 0.2s; }
    div.stButton > button:active { transform: scale(0.96); }
</style>
""", unsafe_allow_html=True)


# --- YARDIMCI ---
def autoplay_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        fp = BytesIO();
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        md = f"""<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>"""
        st.markdown(md, unsafe_allow_html=True)
    except:
        st.toast("Ses hatası")


# --- UYGULAMA ---
if 'user' not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    c1, c2, c3 = st.columns([1, 6, 1])
    with c2:
        st.markdown("<h1 style='text-align:center; color:#58A6FF;'>🇬🇧 Oxford 3000</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Giriş", "Kayıt"])
        with t1:
            u = st.text_input("Kullanıcı");
            p = st.text_input("Şifre", type="password")
            if st.button("Giriş Yap", type="primary", use_container_width=True):
                user = db.login_user(u, p)
                if user:
                    st.session_state.user = user; st.rerun()
                else:
                    st.error("Hatalı!")
        with t2:
            nu = st.text_input("Kullanıcı", key="nu");
            np = st.text_input("Şifre", type="password", key="np")
            if st.button("Kayıt Ol", use_container_width=True):
                if db.register_user(nu, np): st.success("Tamam!"); st.info("Giriş yapabilirsin.")
else:
    user_id = st.session_state.user[0]
    learned_count, xp, streak, db_target_level = db.get_user_stats(user_id)

    # --- SIDEBAR ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user[1]}**")
        st.write(f"🔥 {streak} Gün | ⭐ {xp} XP")
        st.divider()
        menu = st.radio("Menü", ["⚡ Çalış", "🏆 Quiz", "🥇 Liderler", "📚 Listem"])
        if st.button("Çıkış"): st.session_state.user = None; st.rerun()

    # --- 1. ÇALIŞMA SAYFASI ---
    if menu == "⚡ Çalış":
        active_levels = ["A1", "A2", "B1", "B2"]

        if 'card_word' not in st.session_state:
            st.session_state.card_word = db.get_new_word_for_user(user_id, active_levels)
            st.session_state.is_flipped = False

        w = st.session_state.card_word

        if w:
            wid, eng, tur, lvl, pos, ex = w if len(w) == 6 else (*w, "Kelime", "-")

            if not st.session_state.is_flipped:
                # ÖN YÜZ
                html_content = f"""
                <div class="card-container">
                    <div style="font-size:14px; color:#8b949e; margin-bottom:15px;">İNGİLİZCESİ</div>
                    <div class="word-main">{eng.upper()}</div>
                    <div class="meta-info">{lvl} • {pos}</div>
                </div>"""
                btn_label = "🔄 Kartı Çevir"
            else:
                # ARKA YÜZ
                html_content = f"""
                <div class="card-container" style="border-color: #7EE787;">
                    <div style="font-size:14px; color:#8b949e; margin-bottom:15px;">ANLAMI</div>
                    <div class="word-meaning">{tur}</div>
                    <div style="margin-top:20px; color:#ccc;">🇬🇧 {eng}</div>
                </div>"""
                btn_label = "🔄 Ön Yüze Dön"

            st.markdown(html_content, unsafe_allow_html=True)

            if st.button(btn_label, use_container_width=True):
                st.session_state.is_flipped = not st.session_state.is_flipped
                st.rerun()

            st.write("")

            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            with c1:
                if st.button("🔊", help="Dinle", use_container_width=True): autoplay_audio(eng)
            with c2:
                if st.button("🤔", help="Tekrar Listesine At", use_container_width=True):
                    db.mark_word_needs_review(user_id, wid)
                    st.toast("Listeye alındı", icon="📥")
                    time.sleep(0.5)
                    st.session_state.card_word = db.get_new_word_for_user(user_id, active_levels)
                    st.session_state.is_flipped = False;
                    st.rerun()
            with c3:
                if st.button("✅", type="primary", help="Ezberledim", use_container_width=True):
                    db.mark_word_learned(user_id, wid)
                    db.add_xp(user_id, 30)
                    st.toast("+30 XP", icon="🔥");
                    time.sleep(0.5)
                    st.session_state.card_word = db.get_new_word_for_user(user_id, active_levels)
                    st.session_state.is_flipped = False;
                    st.rerun()
            with c4:
                if st.button("➡️", help="Pas Geç", use_container_width=True):
                    st.session_state.card_word = db.get_new_word_for_user(user_id, active_levels)
                    st.session_state.is_flipped = False;
                    st.rerun()
        else:
            st.success("Tebrikler! Bu seviyeyi bitirdin.")

    # --- 2. QUIZ ---
    elif menu == "🏆 Quiz":
        # Veri kontrol
        if 'quiz_data' not in st.session_state or st.session_state.quiz_data is None:
            st.session_state.quiz_data = db.get_quiz_question(user_id, ["A1", "A2", "B1", "B2"])
            if st.session_state.quiz_data:
                opts = st.session_state.quiz_data['options']
                random.shuffle(opts)
                st.session_state.quiz_data['shuffled'] = opts

        q = st.session_state.quiz_data

        if q:
            st.markdown(
                f"<div style='text-align:center; padding:30px; background:#1e2329; border-radius:20px; margin-bottom:20px; border:1px solid #30363D;'><h1 style='color:#F2CC60; margin:0;'>{q['english'].upper()}</h1></div>",
                unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            for i, opt in enumerate(q['shuffled']):
                col_to_use = c1 if i % 2 == 0 else c2
                if col_to_use.button(opt, key=f"q_{i}", use_container_width=True):
                    if opt == q['correct_answer']:
                        st.success("DOĞRU! +20 XP")
                        db.add_xp(user_id, 20)
                        db.mark_word_learned(user_id, q['id'])  # Listeden düşür
                        time.sleep(0.5);
                        st.session_state.quiz_data = None;
                        st.rerun()
                    else:
                        st.error(f"Yanlış! -> {q['correct_answer']}")
                        time.sleep(1.5);
                        st.session_state.quiz_data = None;
                        st.rerun()
            if st.button("Pas Geç", use_container_width=True):
                st.session_state.quiz_data = None;
                st.rerun()
        else:
            # Liste boşsa burası çalışır
            st.balloons()
            st.markdown(
                """<div style='text-align:center; padding:40px; background:#161b22; border-radius:20px; border:1px solid #7EE787;'><h2 style='color:#7EE787;'>Tebrikler! 🎉</h2><p style='font-size:18px; color:#ccc;'>Tekrar listen tertemiz. Bilmediğin kelime kalmadı!</p></div>""",
                unsafe_allow_html=True)

    # --- 3. LİDERLER ---
    elif menu == "🥇 Liderler":
        st.subheader("🏆 Şampiyonlar Ligi")
        leaders = db.get_leaderboard()
        for i, (u, x, s) in enumerate(leaders):
            bg = "#1f2428" if u != st.session_state.user[1] else "#263645"
            border = "1px solid #30363D" if u != st.session_state.user[1] else "2px solid #58A6FF"
            icon = ["🥇", "🥈", "🥉"][i] if i < 3 else "🎖️"
            st.markdown(
                f"""<div style='background:{bg}; border:{border}; padding:15px; border-radius:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;'><div style='display:flex; align-items:center; gap:10px;'><span style='font-size:24px;'>{icon}</span><span style='font-weight:bold; color:#c9d1d9;'>{u}</span></div><div style='text-align:right;'><div style='color:#F2CC60; font-weight:bold;'>{x} XP</div><div style='font-size:12px; color:#8b949e;'>🔥 {s} gün</div></div></div>""",
                unsafe_allow_html=True)

    # --- 4. LİSTEM ---
    elif menu == "📚 Listem":
        t1, t2 = st.tabs(["✅ Ezber", "🤔 Tekrar"])
        with t1:
            w = db.get_learned_words(user_id)
            if w:
                st.caption(f"{len(w)} kelime")
                for i in w:
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"**{i[1]}**: {i[2]}")
                    if c2.button("♻️", key=f"rev_{i[0]}"):
                        db.mark_word_needs_review(user_id, i[0]);
                        st.rerun()
        with t2:
            r = db.create_connection().cursor().execute(
                "SELECT w.id, w.english, w.turkish FROM words w JOIN user_progress up ON w.id = up.word_id WHERE up.user_id = ? AND up.status = 'needs_review'",
                (user_id,)).fetchall()
            if r:
                for i in r:
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"🔴 **{i[1]}**: {i[2]}")
                    if c2.button("✅", key=f"lrn_{i[0]}"):
                        db.mark_word_learned(user_id, i[0]);
                        st.rerun()
            else:
                st.success("Temiz!")