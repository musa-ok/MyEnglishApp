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

# --- CSS (MOBİL SIKIŞTIRMA & KART TASARIMI) ---
st.markdown("""
<style>
    /* 1. Sayfa Boşluklarını Yok Et (Tam Ekran Hisssi) */
    .stApp { background-color: #0E1117; }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* 2. KART BUTONU (Butonu Karta Dönüştürme) */
    /* Streamlit butonunu modifiye ediyoruz */
    div.stButton > button:first-child {
        border-radius: 15px;
        border: 1px solid #30363D;
        transition: transform 0.1s;
    }

    /* 'card-btn' anahtarına sahip butonu hedefle (Python'da key vereceğiz) */
    /* Bu stil, butonu devasa bir karta çevirir */
    .big-card-button {
        height: 300px !important; /* Kart Yüksekliği */
        width: 100% !important;
        background: linear-gradient(145deg, #1e2329, #161b22) !important;
        color: #58A6FF !important;
        font-size: 32px !important;
        font-weight: 800 !important;
        white-space: normal !important; /* Uzun metinleri alt satıra al */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .big-card-button:active { transform: scale(0.98); border-color: #58A6FF; }

    /* 3. ALT BUTONLARI SIKIŞTIRMA (Yan Yana) */
    /* Mobilde butonlar alt alta kaymasın diye zorluyoruz */
    [data-testid="column"] {
        padding: 0px 5px !important; /* Sütun boşluklarını azalt */
        min-width: 0 !important;
    }

    /* Aksiyon Butonları (Küçük) */
    .action-btn { font-size: 18px !important; padding: 0px !important; height: 50px !important; }

    /* Seviye Rozetleri */
    .badge-info { font-size: 12px; color: #888; font-weight: normal; margin-top: 5px; }

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


# --- APP ---
if 'user' not in st.session_state: st.session_state.user = None

if not st.session_state.user:
    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color:#58A6FF;'>🇬🇧 Oxford 3000</h2>", unsafe_allow_html=True)
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

    # Sidebar (Menü)
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user[1]}** | 🔥 {streak} Gün | ⭐ {xp} XP")
        menu = st.radio("Menü", ["⚡ Çalış", "🏆 Quiz", "📚 Listem"])
        if st.button("Çıkış"): st.session_state.user = None; st.rerun()

    # --- 1. ÇALIŞMA KARTLARI (MOBİL VERSİYON) ---
    if menu == "⚡ Çalış":
        # Seviye Yönetimi (Arkaplanda)
        active_levels = ["A1", "A2", "B1", "B2"]  # Hepsini açalım veya user settings'den çekelim

        if 'card_word' not in st.session_state:
            st.session_state.card_word = db.get_new_word_for_user(user_id, active_levels)
            st.session_state.is_flipped = False

        w = st.session_state.card_word

        if w:
            wid, eng, tur, lvl, pos, ex = w if len(w) == 6 else (*w, "Kelime", "-")

            # Kartın İçeriğini Belirle
            if not st.session_state.is_flipped:
                # ÖN YÜZ
                card_text = f"{eng.upper()}\n\n({lvl} • {pos})"
                # CSS ile bu butonu mavi/siyah yapıyoruz
                btn_type = "secondary"
            else:
                # ARKA YÜZ
                card_text = f"{tur}\n\n🇬🇧 {eng}"
                # Çevrilince rengi değişsin (CSS ile border rengi verilebilir)
                btn_type = "primary"

            # --- KART (DEV BUTTON) ---
            # Buradaki hile: Butonun kendisine özel bir CSS class veremesek de
            # sayfanın en üstündeki butonu hedefleyen CSS yazdık.
            # Kartın üzerine tıklayınca state değişecek.

            st.markdown("<style> div.stButton > button { height: 250px; font-size: 28px; } </style>",
                        unsafe_allow_html=True)

            if st.button(card_text, key="flashcard_btn", use_container_width=True):
                st.session_state.is_flipped = not st.session_state.is_flipped
                st.rerun()

            # KARTIN ALTINDAKİ İPUCU
            if not st.session_state.is_flipped:
                st.caption("👆 Çevirmek için karta dokun")
            else:
                st.caption("👆 İngilizcesi için dokun")

            # --- AKSİYON BUTONLARI (SIKIŞTIRILMIŞ) ---
            # Tek satırda 4 işlem: Dinle | Tekrar | Ezberledim | Sonraki
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

            with c1:
                if st.button("🔊", help="Dinle"):
                    autoplay_audio(eng)

            with c2:
                if st.button("🤔", help="Tekrar Listesine At"):
                    db.mark_word_needs_review(user_id, wid)
                    st.toast("Listeye atıldı!", icon="📥")
                    time.sleep(0.5)
                    st.session_state.card_word = db.get_new_word_for_user(user_id, active_levels)
                    st.session_state.is_flipped = False;
                    st.rerun()

            with c3:
                if st.button("✅", type="primary", help="Ezberledim"):
                    db.mark_word_learned(user_id, wid)
                    db.add_xp(user_id, 30)
                    st.toast("+30 XP", icon="🔥")
                    time.sleep(0.5)
                    st.session_state.card_word = db.get_new_word_for_user(user_id, active_levels)
                    st.session_state.is_flipped = False;
                    st.rerun()

            with c4:
                if st.button("➡️", help="Pas Geç"):
                    st.session_state.card_word = db.get_new_word_for_user(user_id, active_levels)
                    st.session_state.is_flipped = False;
                    st.rerun()

        else:
            st.success("Tüm kelimeler bitti! 🎉")

    # --- 2. QUIZ ---
    elif menu == "🏆 Quiz":
        if 'quiz_data' not in st.session_state or st.session_state.quiz_data is None:
            st.session_state.quiz_data = db.get_quiz_question(user_id, ["A1", "A2", "B1", "B2"])
            if st.session_state.quiz_data:
                opts = st.session_state.quiz_data['options'];
                random.shuffle(opts)
                st.session_state.quiz_data['shuffled'] = opts

        q = st.session_state.quiz_data
        if q:
            # Soru Kartı
            st.markdown(
                f"<div style='text-align:center; padding:20px; background:#1e2329; border-radius:15px; margin-bottom:10px;'><h1 style='color:#F2CC60; margin:0;'>{q['english'].upper()}</h1></div>",
                unsafe_allow_html=True)

            # Şıklar (2x2)
            c1, c2 = st.columns(2)
            for i, opt in enumerate(q['shuffled']):
                if (i % 2 == 0 ? c1: c2).button(opt, key=f"q_{i}", use_container_width=True):
                    if opt == q['correct_answer']:
                        st.success("DOĞRU! +20 XP");
                        db.add_xp(user_id, 20);
                        time.sleep(1);
                        st.session_state.quiz_data = None;
                        st.rerun()
                    else:
                        st.error(f"Yanlış! -> {q['correct_answer']}");
                        db.mark_word_needs_review(user_id, q['id']);
                        time.sleep(1.5);
                        st.session_state.quiz_data = None;
                        st.rerun()
            if st.button("Pas Geç", use_container_width=True): st.session_state.quiz_data = None; st.rerun()
        else:
            st.info("Quiz için kelime yok.")

    # --- 3. LİSTEM ---
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