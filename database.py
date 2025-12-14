import sqlite3
import hashlib
from datetime import date, datetime, timedelta

DB_NAME = "vocab.db"


def create_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = create_connection()
    c = conn.cursor()

    # Tabloları oluştur
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  xp INTEGER DEFAULT 0,
                  streak INTEGER DEFAULT 0,
                  last_login TEXT,
                  target_level TEXT DEFAULT 'B2')''')  # Yeni sütun eklendi

    c.execute('''CREATE TABLE IF NOT EXISTS words 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  english TEXT, 
                  turkish TEXT, 
                  level TEXT, 
                  pos TEXT, 
                  example_sentence TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS user_progress 
                 (user_id INTEGER, 
                  word_id INTEGER, 
                  status TEXT, 
                  FOREIGN KEY(user_id) REFERENCES users(id),
                  FOREIGN KEY(word_id) REFERENCES words(id))''')

    # Eski kullanıcılarda 'target_level' yoksa ekle (Migration)
    try:
        c.execute("ALTER TABLE users ADD COLUMN target_level TEXT DEFAULT 'B2'")
    except:
        pass  # Zaten varsa hata vermesin

    try:
        c.execute("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0")
        c.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
    except:
        pass

    conn.commit()
    conn.close()


# --- KULLANICI İŞLEMLERİ ---
def register_user(username, password):
    conn = create_connection();
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    today = date.today().isoformat()
    try:
        # Varsayılan seviye B2
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
        uid = user[0]
        curr_streak = user[4] if user[4] else 0
        last_login = user[5]
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
        # Güncel kullanıcıyı tekrar çek
        c.execute("SELECT * FROM users WHERE id=?", (uid,))
        user = c.fetchone()

    conn.close()
    return user


# --- SEVİYE GÜNCELLEME ---
def update_target_level(user_id, new_level):
    conn = create_connection();
    c = conn.cursor()
    c.execute("UPDATE users SET target_level = ? WHERE id = ?", (new_level, user_id))
    conn.commit();
    conn.close()


def get_user_stats(user_id):
    conn = create_connection();
    c = conn.cursor()
    c.execute("SELECT count(*) FROM user_progress WHERE user_id=? AND status='learned'", (user_id,))
    learned = c.fetchone()[0]
    # target_level bilgisini de çekiyoruz (user tablosundaki 6. indeks, veritabanı yapına göre değişebilir ama genelde sondadır)
    c.execute("SELECT xp, streak, target_level FROM users WHERE id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    # learned_count, xp, streak, target_level
    return learned, res[0], res[1], (res[2] if res[2] else 'B2')


# --- DİĞER FONKSİYONLAR ---
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
    c.execute("SELECT level, COUNT(*) FROM words GROUP BY level")
    total_counts = {row[0]: row[1] for row in c.fetchall()}
    c.execute(
        '''SELECT w.level, COUNT(*) FROM user_progress up JOIN words w ON up.word_id = w.id WHERE up.user_id = ? AND up.status = 'learned' GROUP BY w.level''',
        (user_id,))
    learned_counts = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    stats = {}
    for lvl in ['A1', 'A2', 'B1', 'B2']:
        stats[lvl] = {'total': total_counts.get(lvl, 0), 'learned': learned_counts.get(lvl, 0)}
    return stats


def get_new_word_for_user(user_id, target_levels=None):
    conn = create_connection();
    c = conn.cursor()
    if target_levels:
        placeholders = ','.join(['?'] * len(target_levels))
        # learned olmayanları getir (needs_review veya hiç görülmemiş)
        query = f'''SELECT * FROM words WHERE id NOT IN (SELECT word_id FROM user_progress WHERE user_id = ? AND status='learned') AND level IN ({placeholders}) ORDER BY RANDOM() LIMIT 1'''
        params = [user_id] + target_levels
        c.execute(query, params)
    else:
        query = '''SELECT * FROM words WHERE id NOT IN (SELECT word_id FROM user_progress WHERE user_id = ? AND status='learned') ORDER BY RANDOM() LIMIT 1'''
        c.execute(query, (user_id,))
    word = c.fetchone()
    conn.close()
    return word


def mark_word_needs_review(user_id, word_id):
    conn = create_connection();
    c = conn.cursor()
    c.execute("SELECT * FROM user_progress WHERE user_id=? AND word_id=?", (user_id, word_id))
    if c.fetchone():
        c.execute("UPDATE user_progress SET status='needs_review' WHERE user_id=? AND word_id=?", (user_id, word_id))
    else:
        c.execute("INSERT INTO user_progress (user_id, word_id, status) VALUES (?, ?, 'needs_review')",
                  (user_id, word_id))
    conn.commit();
    conn.close()


def mark_word_learned(user_id, word_id):
    conn = create_connection();
    c = conn.cursor()
    c.execute("SELECT * FROM user_progress WHERE user_id=? AND word_id=?", (user_id, word_id))
    if c.fetchone():
        c.execute("UPDATE user_progress SET status='learned' WHERE user_id=? AND word_id=?", (user_id, word_id))
    else:
        c.execute("INSERT INTO user_progress (user_id, word_id, status) VALUES (?, ?, 'learned')", (user_id, word_id))
    conn.commit();
    conn.close()


def get_quiz_question(user_id, target_levels=None):
    conn = create_connection();
    c = conn.cursor()
    word = None
    if target_levels:
        placeholders = ','.join(['?'] * len(target_levels))
        # Önce review gerekenler
        query = f'''SELECT w.* FROM words w JOIN user_progress up ON w.id = up.word_id WHERE up.user_id = ? AND up.status = 'needs_review' AND w.level IN ({placeholders}) ORDER BY RANDOM() LIMIT 1'''
        params = [user_id] + target_levels
        c.execute(query, params)
    else:
        c.execute(
            '''SELECT w.* FROM words w JOIN user_progress up ON w.id = up.word_id WHERE up.user_id = ? AND up.status = 'needs_review' ORDER BY RANDOM() LIMIT 1''',
            (user_id,))
    word = c.fetchone()

    if not word:  # Review yoksa yeni kelime sor (veya öğrendiklerinden sorabilirsin)
        return get_new_word_for_user(user_id, target_levels)

    if not word: conn.close(); return None

    c.execute("SELECT turkish FROM words WHERE id != ? ORDER BY RANDOM() LIMIT 3", (word[0],))
    wrong_opts = [r[0] for r in c.fetchall()]
    conn.close()
    return {"id": word[0], "english": word[1], "correct_answer": word[2], "options": wrong_opts + [word[2]]}


def get_learned_words(user_id):
    conn = create_connection();
    c = conn.cursor()
    c.execute(
        "SELECT w.english, w.turkish, w.level, w.pos, w.example_sentence FROM words w JOIN user_progress up ON w.id = up.word_id WHERE up.user_id = ? AND up.status = 'learned'",
        (user_id,))
    res = c.fetchall();
    conn.close();
    return res


def get_review_words(user_id):
    conn = create_connection();
    c = conn.cursor()
    c.execute(
        "SELECT w.english, w.turkish, w.level, w.pos, w.example_sentence FROM words w JOIN user_progress up ON w.id = up.word_id WHERE up.user_id = ? AND up.status = 'needs_review'",
        (user_id,))
    res = c.fetchall();
    conn.close();
    return res