import streamlit as st
import time
import pandas as pd
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

# --- CSS (Kart Tasarımı) ---
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }

    /* Kart Kutusu */
    .card-container {
        background: linear-gradient(145deg, #1e2329, #161b22);
        padding: 40px 20px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        text-align: center;
        margin-bottom: 25px;
        border: 1px solid #30363D;
        color: #fff;
        min-height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: all 0.3s ease;
    }

    .card-container:hover { transform: translateY(-5px); border-color: #58A6FF; }

    .english-word { color: #58A6FF !important; font-size: 52px; font-weight: 800; text-shadow: 0 0 15px rgba(88, 166, 255, 0.4); }
    .turkish-word { color: #7EE787 !important; font-size: 42px; font-weight: 700; text-shadow: 0 0 15px rgba(126, 231, 135, 0.4); }

    /* Example text sınıfını kaldırdık ama CSS'i dursa zararı olmaz */
    .example-text { font-size: 18px; color: #ccc; font-style: italic; margin-top: 15px; }

    /* Butonlar */
    .stButton button { border-radius: 12px; font-weight: 600; width: 100%; height: 50px; transition: transform 0.1s; }
    .stButton button:active { transform: scale(0.98); }

    .badge { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 14px; font-weight: bold; margin: 4px; color: #000 !important; }
    .badge-level { background-color: #D2A8FF; } 
    .badge-pos { background-color: #7EE787; }

    .score-box { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    .score-val { font-size: 28px; font-weight: 900; color: #F2CC60; }
    .list-item { background-color: #161b22; border: 1px solid #30363d; padding: 12px; border-radius: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
</style>
""", unsafe_allow_html=True)


# --- YARDIMCI ---
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

    learned_count, xp, streak, db_target_level = db.get_user_stats(user_id)
    rank_title, min_xp, max_xp = get_user_rank(xp)
    level_stats = db.get_level_progress(user_id)

    with st.sidebar:
        st.markdown(
            f"<div class='score-box'><div style='font-size:12px; color:#8b949e;'>XP PUANIN</div><div class='score-val'>{xp}</div><div>{rank_title}</div></div>",
            unsafe_allow_html=True)
        st.markdown(
            f"<div style='text-align:center; margin-bottom:15px; background:#21262d; padding:8px; border-radius:10px;'>🔥 {streak} Günlük Seri</div>",
            unsafe_allow_html=True)

        # SEVİYE AYARI
        level_options = ["A1", "A2", "B1", "B2"]
        try:
            default_index = level_options.index(db_target_level)
        except:
            default_index = 3

        selected_level_short = st.selectbox("🎯 Hedef Seviye", level_options, index=default_index)

        if selected_level_short != db_target_level:
            db.update_target_level(user_id, selected_level_short)
            st.toast(f"Seviye {selected_level_short} olarak kaydedildi!", icon="💾")

        active_levels = ["A1"]
        if "A2" in selected_level_short: active_levels += ["A2"]
        if "B1" in selected_level_short: active_levels += ["A2", "B1"]
        if "B2" in selected_level_short: active_levels += ["A2", "B1", "B2"]
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

    # --- 1. ÇALIŞMA KARTLARI (Flashcard Modu) ---
    if menu == "⚡ Çalış":
        if 'card_word' not in st.session_state:
            st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels)
            st.session_state.is_flipped = False

        w = st.session_state.card_word

        if w:
            # ex (örnek cümle) hala veritabanından geliyor ama kullanmayacağız
            wid, eng, tur, lvl, pos, ex = w if len(w) == 6 else (*w, "Kelime", "-")

            if 'current_word_id' not in st.session_state: st.session_state.current_word_id = wid
            if st.session_state.current_word_id != wid:
                st.session_state.current_word_id = wid
                st.session_state.is_flipped = False

            if not st.session_state.is_flipped:
                # --- ÖN YÜZ ---
                card_html = f"""
                <div class="card-container">
                    <div class="english-word">{eng.upper()}</div>
                    <div style="margin-top:10px;">
                        <span class="badge badge-level">{lvl}</span>
                        <span class="badge badge-pos">{pos}</span>
                    </div>
                    <div style="margin-top:20px; font-size:12px; color:#666;">(Anlamını görmek için çevir)</div>
                </div>
                """
                btn_label = "🔄 Kartı Çevir"
            else:
                # --- ARKA YÜZ (SADELEŞTİRİLDİ) ---
                # Örnek cümle div'i kaldırıldı
                card_html = f"""
                <div class="card-container" style="border-color: #7EE787;">
                    <div class="turkish-word">{tur}</div>
                    <div style="margin-top:30px; font-size:12px; color:#666;">(İngilizcesi: {eng})</div>
                </div>
                """
                btn_label = "🔄 Ön Yüze Dön"

            st.markdown(card_html, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if st.button("🔊 Dinle"): autoplay_audio(eng)
            with c2:
                if st.button(btn_label, use_container_width=True):
                    st.session_state.is_flipped = not st.session_state.is_flipped
                    st.rerun()
            with c3:
                if st.button("Sonraki ➡️"):
                    st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels)
                    st.session_state.is_flipped = False
                    st.rerun()

            st.markdown("---")
            st.caption("Bu kelimeyi biliyor musun?")

            col_unsure, col_learn = st.columns(2)
            with col_unsure:
                if st.button("🤔 Tekrar Listesine At"):
                    db.mark_word_needs_review(user_id, wid)
                    st.toast("Listeye eklendi!", icon="📝")
                    time.sleep(0.5)
                    st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels)
                    st.session_state.is_flipped = False
                    st.rerun()
            with col_learn:
                if st.button("✅ Ezberledim (+30)", type="primary"):
                    db.mark_word_learned(user_id, wid)
                    db.add_xp(user_id, 30)
                    st.success("Süpersin!")
                    time.sleep(0.5)
                    st.session_state.card_word = db.get_new_word_for_user(user_id, st.session_state.active_levels)
                    st.session_state.is_flipped = False
                    st.rerun()

        else:
            st.success("Bu seviyedeki tüm kelimeleri bitirdin!")

    # --- 2. QUIZ ---
    elif menu == "🏆 Quiz":
        st.subheader("🚀 Hızlı Quiz")
        if 'quiz_data' not in st.session_state or st.session_state.quiz_data is None:
            st.session_state.quiz_data = db.get_quiz_question(user_id, st.session_state.active_levels)
            if st.session_state.quiz_data:
                opts = st.session_state.quiz_data['options'];
                random.shuffle(opts)
                st.session_state.quiz_data['shuffled'] = opts

        q = st.session_state.quiz_data
        if q:
            st.markdown(f"""
            <div class="card-container" style="padding:20px; min-height:150px;">
                <h2 style="color:#F2CC60; margin:0;">{q['english'].upper()}</h2>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(2)
            for i, opt in enumerate(q['shuffled']):
                if cols[i % 2].button(opt, key=f"q_{i}", use_container_width=True):
                    if opt == q['correct_answer']:
                        st.success("DOĞRU! 🎉 +20 XP");
                        db.add_xp(user_id, 20);
                        time.sleep(1);
                        st.session_state.quiz_data = None;
                        st.rerun()
                    else:
                        st.error(f"Yanlış! Doğrusu: {q['correct_answer']}");
                        db.mark_word_needs_review(user_id, q['id']);
                        time.sleep(2);
                        st.session_state.quiz_data = None;
                        st.rerun()
            if st.button("Pas Geç", type="secondary"): st.session_state.quiz_data = None; st.rerun()
        else:
            st.info("Quiz için kelime bulunamadı.")

    # --- 3. LİDERLER ---
    elif menu == "🥇 Liderler":
        st.subheader("🏆 Şampiyonlar Ligi")
        leaders = db.get_leaderboard()
        for i, (u, x, s) in enumerate(leaders):
            bg = "#1f2428" if u != username else "#263645"
            border = "1px solid #30363D" if u != username else "2px solid #58A6FF"
            icon = ["🥇", "🥈", "🥉"][i] if i < 3 else "🎖️"
            st.markdown(
                f"""<div style='background:{bg}; border:{border}; padding:15px; border-radius:12px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;'><div style='display:flex; align-items:center; gap:10px;'><span style='font-size:24px;'>{icon}</span><span style='font-weight:bold; color:#c9d1d9;'>{u}</span></div><div style='text-align:right;'><div style='color:#F2CC60; font-weight:bold;'>{x} XP</div><div style='font-size:12px; color:#8b949e;'>🔥 {s} gün</div></div></div>""",
                unsafe_allow_html=True)

    # --- 4. LİSTEM ---
    elif menu == "📚 Listem":
        t1, t2 = st.tabs(["✅ Ezberlenenler", "🤔 Tekrar Listesi"])

        with t1:
            learned_words = db.get_learned_words(user_id)
            if not learned_words:
                st.info("Henüz ezberlenen kelime yok.")
            else:
                st.write(f"**Toplam:** {len(learned_words)} kelime")
                for w in learned_words:
                    wid, eng, tur, lvl, pos, ex = w
                    col_txt, col_btn = st.columns([4, 1])
                    with col_txt:
                        st.markdown(
                            f"""<div class="list-item"><div><span style="font-size:18px; color:#58A6FF; font-weight:bold;">{eng}</span><span style="color:#ccc;"> : {tur}</span><div style="font-size:12px; color:#666; margin-top:4px;">{lvl} • {pos}</div></div></div>""",
                            unsafe_allow_html=True)
                    with col_btn:
                        if st.button("♻️ Tekrar", key=f"rev_{wid}"):
                            db.mark_word_needs_review(user_id, wid)
                            st.toast(f"{eng} geri alındı!", icon="♻️")
                            time.sleep(0.5);
                            st.rerun()

        with t2:
            conn = db.create_connection();
            c = conn.cursor()
            c.execute(
                "SELECT w.id, w.english, w.turkish, w.example_sentence FROM words w JOIN user_progress up ON w.id = up.word_id WHERE up.user_id = ? AND up.status = 'needs_review'",
                (user_id,))
            r_data = c.fetchall();
            conn.close()

            if not r_data:
                st.success("Tekrar listen tertemiz! 🎉")
            else:
                st.info(f"{len(r_data)} kelime tekrar bekliyor.")
                for item in r_data:
                    wid, eng, tur, ex = item
                    with st.expander(f"🔴 {eng} ({tur})", expanded=False):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            # Burada örnek cümle boşluk doldurma vardı, onu da kaldırdım çünkü 'hepsi aynı' dedin
                            # Sadece anlamını gösterelim
                            st.write(f"**Anlamı:** {tur}")
                            if st.text_input("Kelimeyi yaz:", key=f"in_{wid}") == eng: st.success("Doğru!")
                        with c2:
                            if st.button("🔊 Dinle", key=f"s_{wid}"): autoplay_audio(eng)
                            if st.button("✅ Öğrendim", key=f"L_{wid}", type="primary"):
                                db.mark_word_learned(user_id, wid)
                                st.rerun()