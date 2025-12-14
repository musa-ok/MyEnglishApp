import sqlite3
import hashlib
from datetime import date, datetime, timedelta

DB_NAME = "vocab.db"


def create_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = create_connection()
    c = conn.cursor()

    # 1. Kullanıcılar
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT, 
                  xp INTEGER DEFAULT 0,
                  streak INTEGER DEFAULT 0,
                  last_login TEXT)''')

    # 2. Kelimeler
    c.execute('''CREATE TABLE IF NOT EXISTS words 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  english TEXT, 
                  turkish TEXT, 
                  level TEXT,
                  pos TEXT, 
                  example_sentence TEXT)''')

    # 3. İlerleme
    c.execute('''CREATE TABLE IF NOT EXISTS user_progress 
                 (user_id INTEGER, 
                  word_id INTEGER, 
                  status TEXT, 
                  FOREIGN KEY(user_id) REFERENCES users(id),
                  FOREIGN KEY(word_id) REFERENCES words(id))''')

    # Eski veritabanı varsa hata vermesin diye kolon eklemeleri
    try:
        c.execute("ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0")
        c.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
    except:
        pass

    conn.commit()
    conn.close()


# --- KULLANICI İŞLEMLERİ ---
def register_user(username, password):
    conn = create_connection()
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    today = date.today().isoformat()
    try:
        c.execute("INSERT INTO users (username, password, streak, last_login) VALUES (?, ?, 1, ?)",
                  (username, hashed_pw, today))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def login_user(username, password):
    conn = create_connection()
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
    user = c.fetchone()

    if user:
        # Streak (Seri) Hesaplama
        user_id = user[0]
        current_streak = user[4] if user[4] else 0
        last_login_str = user[5]
        today = date.today()

        new_streak = current_streak

        if last_login_str:
            last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
            if last_login_date == today - timedelta(days=1):
                new_streak += 1  # Dün girmiş, seri artıyor
            elif last_login_date < today - timedelta(days=1):
                new_streak = 1  # Dünden önce girmiş, seri sıfırlandı
        else:
            new_streak = 1

        c.execute("UPDATE users SET streak=?, last_login=? WHERE id=?", (new_streak, today.isoformat(), user_id))
        conn.commit()
        c.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user = c.fetchone()

    conn.close()
    return user


def get_user_stats(user_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT count(*) FROM user_progress WHERE user_id=? AND status='learned'", (user_id,))
    res = c.fetchone()
    learned_count = res[0] if res else 0

    c.execute("SELECT xp, streak FROM users WHERE id=?", (user_id,))
    res_user = c.fetchone()
    xp = res_user[0] if res_user else 0
    streak = res_user[1] if res_user else 0

    conn.close()
    return learned_count, xp, streak


def add_xp(user_id, amount):
    conn = create_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def get_leaderboard():
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT username, xp, streak FROM users ORDER BY xp DESC LIMIT 10")
    leaders = c.fetchall()
    conn.close()
    return leaders


# --- SEVİYE VE İLERLEME DETAYLARI ---
def get_level_progress(user_id):
    """
    Her seviye için toplam ve öğrenilen kelime sayısını döner.
    Örn: {'A1': {'total': 500, 'learned': 50}, 'A2': ...}
    """
    conn = create_connection()
    c = conn.cursor()

    # 1. Toplam kelimeler
    c.execute("SELECT level, COUNT(*) FROM words GROUP BY level")
    total_counts = {row[0]: row[1] for row in c.fetchall()}

    # 2. Öğrenilen kelimeler
    c.execute('''
        SELECT w.level, COUNT(*) 
        FROM user_progress up 
        JOIN words w ON up.word_id = w.id 
        WHERE up.user_id = ? AND up.status = 'learned' 
        GROUP BY w.level
    ''', (user_id,))
    learned_counts = {row[0]: row[1] for row in c.fetchall()}

    conn.close()

    # Listeyi düzenle
    stats = {}
    for lvl in ['A1', 'A2', 'B1', 'B2']:
        stats[lvl] = {
            'total': total_counts.get(lvl, 0),
            'learned': learned_counts.get(lvl, 0)
        }
    return stats


# --- KELİME ÇEKME (FİLTRELİ) ---
def get_new_word_for_user(user_id, target_levels=None):
    conn = create_connection()
    c = conn.cursor()

    if target_levels:
        # Sadece seçilen seviyelerden (Örn: A1, A2) getir
        placeholders = ','.join(['?'] * len(target_levels))
        query = f'''
            SELECT * FROM words 
            WHERE id NOT IN (SELECT word_id FROM user_progress WHERE user_id = ?) 
            AND level IN ({placeholders})
            ORDER BY RANDOM() LIMIT 1
        '''
        params = [user_id] + target_levels
        c.execute(query, params)
    else:
        # Filtre yoksa hepsinden getir
        query = '''SELECT * FROM words WHERE id NOT IN (SELECT word_id FROM user_progress WHERE user_id = ?) ORDER BY RANDOM() LIMIT 1'''
        c.execute(query, (user_id,))

    word = c.fetchone()
    conn.close()
    return word


def get_quiz_question(user_id, target_levels=None):
    # Quiz sorusu da seçilen seviyeden gelmeli
    word = get_new_word_for_user(user_id, target_levels)
    if not word:
        return None

    conn = create_connection()
    c = conn.cursor()
    # Şıklar rastgele herhangi bir seviyeden gelebilir (kafa karıştırmak için) veya aynı seviyeden seçilebilir.
    # Şimdilik rastgele getiriyoruz.
    c.execute("SELECT turkish FROM words WHERE id != ? ORDER BY RANDOM() LIMIT 3", (word[0],))
    wrong_opts = [row[0] for row in c.fetchall()]

    conn.close()
    return {
        "id": word[0],
        "english": word[1],
        "correct_answer": word[2],
        "options": wrong_opts + [word[2]]
    }


def mark_word_learned(user_id, word_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM user_progress WHERE user_id=? AND word_id=?", (user_id, word_id))
    if c.fetchone():
        c.execute("UPDATE user_progress SET status='learned' WHERE user_id=? AND word_id=?", (user_id, word_id))
    else:
        c.execute("INSERT INTO user_progress (user_id, word_id, status) VALUES (?, ?, 'learned')", (user_id, word_id))
    conn.commit()
    conn.close()


def get_learned_words(user_id):
    conn = create_connection()
    c = conn.cursor()
    query = '''SELECT w.english, w.turkish, w.level, w.pos, w.example_sentence FROM words w JOIN user_progress up ON w.id = up.word_id WHERE up.user_id = ? AND up.status = 'learned' '''
    c.execute(query, (user_id,))
    words = c.fetchall()
    conn.close()
    return words


def insert_bulk_words(word_list):
    conn = create_connection()
    c = conn.cursor()
    if word_list:
        try:
            if len(word_list[0]) == 5:
                c.executemany("INSERT INTO words (english, turkish, level, pos, example_sentence) VALUES (?,?,?,?,?)",
                              word_list)
            else:
                c.executemany(
                    "INSERT INTO words (english, turkish, level, pos, example_sentence) VALUES (?,?,?, 'n.', ?)",
                    word_list)
        except:
            pass
    conn.commit()
    conn.close()