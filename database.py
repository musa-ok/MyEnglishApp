import sqlite3
import hashlib
from datetime import date, datetime, timedelta

DB_NAME = "vocab.db"


def create_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = create_connection()
    c = conn.cursor()

    # Tablolar
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  xp INTEGER DEFAULT 0,
                  streak INTEGER DEFAULT 0,
                  last_login TEXT,
                  target_level TEXT DEFAULT 'B2')''')

    c.execute('''CREATE TABLE IF NOT EXISTS words 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  english TEXT, 
                  turkish TEXT, 
                  level TEXT, 
                  pos TEXT, 
                  example_sentence TEXT,
                  UNIQUE(english))''')

    c.execute('''CREATE TABLE IF NOT EXISTS user_progress 
                 (user_id INTEGER, 
                  word_id INTEGER, 
                  status TEXT, 
                  FOREIGN KEY(user_id) REFERENCES users(id),
                  FOREIGN KEY(word_id) REFERENCES words(id),
                  UNIQUE(user_id, word_id))''')

    try:
        c.execute("ALTER TABLE users ADD COLUMN target_level TEXT DEFAULT 'B2'")
    except:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0")
    except:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
    except:
        pass

    conn.commit();
    conn.close()


# --- KULLANICI ---
def register_user(username, password):
    conn = create_connection();
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    today = date.today().isoformat()
    try:
        c.execute("INSERT INTO users (username, password, streak, last_login, target_level) VALUES (?, ?, 1, ?, 'B2')",
                  (username, hashed_pw, today))
        conn.commit();
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def login_user(username, password):
    conn = create_connection();
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
    user = c.fetchone()
    if user:
        uid = user[0];
        curr_streak = user[4] if user[4] else 0;
        last_login = user[5];
        today = date.today()
        new_streak = curr_streak
        if last_login:
            l_date = datetime.strptime(last_login, "%Y-%m-%d").date()
            if l_date == today - timedelta(days=1):
                new_streak += 1
            elif l_date < today - timedelta(days=1):
                new_streak = 1
        else:
            new_streak = 1
        c.execute("UPDATE users SET streak=?, last_login=? WHERE id=?", (new_streak, today.isoformat(), uid))
        conn.commit()
        c.execute("SELECT * FROM users WHERE id=?", (uid,))
        user = c.fetchone()
    conn.close();
    return user


def update_target_level(user_id, new_level):
    conn = create_connection();
    c = conn.cursor()
    c.execute("UPDATE users SET target_level = ? WHERE id = ?", (new_level, user_id))
    conn.commit();
    conn.close()


# --- İSTATİSTİK ---
def get_user_stats(user_id):
    conn = create_connection();
    c = conn.cursor()
    c.execute("SELECT count(DISTINCT word_id) FROM user_progress WHERE user_id=? AND status='learned'", (user_id,))
    learned = c.fetchone()[0]
    c.execute("SELECT xp, streak, target_level FROM users WHERE id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return learned, res[0], res[1], (res[2] if res[2] else 'B2')


def add_xp(user_id, amount):
    conn = create_connection();
    c = conn.cursor()
    c.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (amount, user_id))
    conn.commit();
    conn.close()


def get_leaderboard():
    conn = create_connection();
    c = conn.cursor()
    c.execute("SELECT username, xp, streak FROM users ORDER BY xp DESC LIMIT 10")
    res = c.fetchall();
    conn.close();
    return res


def get_level_progress(user_id):
    conn = create_connection();
    c = conn.cursor()
    c.execute("SELECT level, COUNT(DISTINCT english) FROM words GROUP BY level")
    total_counts = {row[0]: row[1] for row in c.fetchall()}
    c.execute('''SELECT w.level, COUNT(DISTINCT w.id) FROM user_progress up 
                 JOIN words w ON up.word_id = w.id 
                 WHERE up.user_id = ? AND up.status = 'learned' 
                 GROUP BY w.level''', (user_id,))
    learned_counts = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    stats = {}
    for lvl in ['A1', 'A2', 'B1', 'B2']:
        tot = total_counts.get(lvl, 0)
        lrn = learned_counts.get(lvl, 0)
        stats[lvl] = {'total': tot if tot > 0 else 1, 'learned': lrn}
    return stats


# --- KELİME ÇEKME ---
def get_new_word_for_user(user_id, target_levels=None):
    conn = create_connection();
    c = conn.cursor()
    if target_levels:
        placeholders = ','.join(['?'] * len(target_levels))
        query = f'''SELECT DISTINCT * FROM words WHERE id NOT IN (SELECT word_id FROM user_progress WHERE user_id = ?) AND level IN ({placeholders}) ORDER BY RANDOM() LIMIT 1'''
        params = [user_id] + target_levels
        c.execute(query, params)
    else:
        query = '''SELECT DISTINCT * FROM words WHERE id NOT IN (SELECT word_id FROM user_progress WHERE user_id = ?) ORDER BY RANDOM() LIMIT 1'''
        c.execute(query, (user_id,))
    word = c.fetchone()
    conn.close()
    return word


# --- BUTON İŞLEMLERİ (DELETE -> INSERT Mantığı) ---
def mark_word_needs_review(user_id, word_id):
    conn = create_connection();
    c = conn.cursor()
    c.execute("DELETE FROM user_progress WHERE user_id=? AND word_id=?", (user_id, word_id))
    c.execute("INSERT INTO user_progress (user_id, word_id, status) VALUES (?, ?, 'needs_review')", (user_id, word_id))
    conn.commit();
    conn.close()


def mark_word_learned(user_id, word_id):
    conn = create_connection();
    c = conn.cursor()
    c.execute("DELETE FROM user_progress WHERE user_id=? AND word_id=?", (user_id, word_id))
    c.execute("INSERT INTO user_progress (user_id, word_id, status) VALUES (?, ?, 'learned')", (user_id, word_id))
    conn.commit();
    conn.close()


def get_quiz_question(user_id, target_levels=None):
    conn = create_connection();
    c = conn.cursor()
    word = None
    params = [user_id]
    level_filter = ""
    if target_levels:
        placeholders = ','.join(['?'] * len(target_levels))
        level_filter = f"AND w.level IN ({placeholders})"
        params += target_levels

    c.execute(
        f'''SELECT DISTINCT w.* FROM words w JOIN user_progress up ON w.id = up.word_id WHERE up.user_id = ? AND up.status = 'needs_review' {level_filter} ORDER BY RANDOM() LIMIT 1''',
        params)
    word = c.fetchone()

    if not word: conn.close(); return None

    c.execute("SELECT turkish FROM words WHERE id != ? ORDER BY RANDOM() LIMIT 3", (word[0],))
    wrong_opts = [r[0] for r in c.fetchall()]
    while len(wrong_opts) < 3: wrong_opts.append("...")
    conn.close()
    return {"id": word[0], "english": word[1], "correct_answer": word[2], "options": wrong_opts + [word[2]]}


def get_learned_words(user_id):
    conn = create_connection();
    c = conn.cursor()
    c.execute(
        "SELECT DISTINCT w.id, w.english, w.turkish, w.level, w.pos, w.example_sentence FROM words w JOIN user_progress up ON w.id = up.word_id WHERE up.user_id = ? AND up.status = 'learned'",
        (user_id,))
    res = c.fetchall();
    conn.close();
    return res


# --- 🔥 GHOST DATA (DÜZELTİLDİ: ÜZERİNE YAZMA ENGELLENDİ) ---
def inject_ghost_data(username="Ghost"):
    conn = create_connection();
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if not user: conn.close(); return
    user_id = user[0]

    learned_list = [("fuel", "yakıt"), ("sandwich", "sandviç"), ("every", "her"), ("gallery", "galeri"),
                    ("nobody", "hiç kimse"), ("girl", "kız"), ("hide", "saklamak"), ("dialogue", "diyalog"),
                    ("important", "önemli"), ("money", "para"), ("rule", "kural"), ("idea", "fikir"), ("song", "şarkı"),
                    ("crazy", "deli"), ("wooden", "ahşap"), ("used to", "alışkın olmak"), ("them", "onlara"),
                    ("win", "kazanmak"), ("apple", "elma"), ("towel", "havlu"), ("nurse", "hemşire"),
                    ("large", "büyük"), ("firstly", "öncelikle"), ("bicycle", "bisiklet"), ("delicious", "lezzetli"),
                    ("spider", "örümcek"), ("colour", "renk"), ("lifestyle", "yaşam tarzı"), ("wall", "duvar"),
                    ("student", "öğrenci"), ("amount", "miktar"), ("billion", "milyar"), ("fruit", "meyve"),
                    ("fail", "başarısız olmak"), ("soon", "yakında"), ("programme", "program"), ("skirt", "etek"),
                    ("she", "o"), ("detail", "detay"), ("point", "nokta"), ("eighty", "seksen"), ("pants", "pantolon"),
                    ("director", "müdür"), ("popular", "popüler"), ("after", "sonrasında"), ("will", "gelecek zaman"),
                    ("dish", "tabak"), ("exist", "var olmak"), ("warm", "ılık"), ("throw", "atmak"),
                    ("several", "birçok"), ("sixty", "altmış"), ("touch", "dokunmak"), ("spoon", "kaşık"),
                    ("save", "kaydetmek"), ("another", "bir diğer"), ("corner", "köşe"), ("small", "küçük"),
                    ("normal", "normal"), ("advice", "tavsiye"), ("education", "eğitim"), ("spelling", "yazım"),
                    ("beginning", "başlangıç"), ("structure", "yapı"), ("personality", "kişilik"),
                    ("buy", "satın almak"), ("March", "Mart"), ("bowl", "tas")]
    review_list = [("track", "izlemek"), ("unemployment", "işsizlik"), ("experience", "deneyim"),
                   ("visitor", "ziyaretçi"), ("device", "cihaz"), ("infinitive", "mastar"), ("field", "alan"),
                   ("position", "konum"), ("disaster", "felaket"), ("happily", "mutlu bir şekilde"),
                   ("possibility", "olasılık"), ("deal", "anlaşmak"), ("tradition", "gelenek"), ("speech", "konuşma"),
                   ("receive", "almak"), ("independent", "bağımsız"), ("evidence", "kanıt"), ("suddenly", "aniden"),
                   ("purpose", "amaç"), ("informal", "resmi olmayan"), ("journey", "seyahat"), ("rise", "yükselmek"),
                   ("pocket", "cep"), ("rubbish", "zırva"), ("pair", "çift")]

    # Fonksiyon: Sadece kullanıcı hiç işlem yapmamışsa ekle
    def safe_insert(u_id, w_id, stat):
        # Kontrol et: Bu kullanıcı bu kelimeyle ilgili herhangi bir kayda sahip mi?
        c.execute("SELECT 1 FROM user_progress WHERE user_id=? AND word_id=?", (u_id, w_id))
        exists = c.fetchone()
        if not exists:
            # Kayıt yoksa ekle (Güvenli)
            c.execute("INSERT INTO user_progress (user_id, word_id, status) VALUES (?, ?, ?)", (u_id, w_id, stat))

    for eng, tur in learned_list:
        try:
            c.execute(
                "INSERT OR IGNORE INTO words (english, turkish, level, pos, example_sentence) VALUES (?, ?, 'A1', 'n.', '-')",
                (eng, tur))
            c.execute("SELECT id FROM words WHERE english=?", (eng,))
            wid = c.fetchone()[0]
            # BURADA KONTROLLÜ EKLEME YAPIYORUZ
            safe_insert(user_id, wid, 'learned')
        except:
            pass

    for eng, tur in review_list:
        try:
            c.execute(
                "INSERT OR IGNORE INTO words (english, turkish, level, pos, example_sentence) VALUES (?, ?, 'B1', 'n.', '-')",
                (eng, tur))
            c.execute("SELECT id FROM words WHERE english=?", (eng,))
            wid = c.fetchone()[0]
            # BURADA KONTROLLÜ EKLEME YAPIYORUZ
            safe_insert(user_id, wid, 'needs_review')
        except:
            pass

    conn.commit();
    conn.close()