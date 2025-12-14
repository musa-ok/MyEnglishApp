import requests
import json

# --- BURAYA ANAHTARINI YAPISTIR (Tırnakların içine) ---
# Resimdeki ...WbT4 ile biten kodu buraya yapıştır
API_KEY = "AIzaSyA8fyqzn7OGkMAepIaf_fyLbaLf5b5WbT4"


# ------------------------------------------------------

def get_ai_feedback(word, sentence):
    """
    Kütüphane kullanmadan direkt Google sunucularına istek atar.
    Bu yöntem takılma yapmaz.
    """
    # Anahtar kontrolü
    if not API_KEY or "BURAYA" in API_KEY:
        return "⚠️ Hata: API Key girilmemiş! ai_manager.py dosyasını açıp şifreni yapıştır."

    # Google'ın Hızlı Modeli (Gemini 1.5 Flash) adresi
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

    headers = {'Content-Type': 'application/json'}

    # Yapay zekaya gidecek mesaj
    prompt_text = f"""
    Sen çok yardımsever ve eğlenceli bir İngilizce öğretmenisin.
    Öğrenci '{word}' kelimesini kullanarak şu cümleyi kurdu: "{sentence}"

    Lütfen Türkçe olarak:
    1. Cümlede gramer hatası var mı?
    2. Kelime doğru anlamda kullanılmış mı?
    3. Hata varsa düzeltilmiş halini göster.
    4. Motive edici kısa bir yorum yap (Emoji kullan).
    """

    data = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }

    try:
        # İsteği gönder (Postacı yola çıktı 📨)
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)

        if response.status_code == 200:
            # Cevap başarılı geldi, içinden metni alalım
            result = response.json()
            try:
                text = result['candidates'][0]['content']['parts'][0]['text']
                return text
            except:
                return "Cevap geldi ama okuyamadım. Tekrar dene."
        else:
            return f"Bir sorun oldu. Hata Kodu: {response.status_code} (API Key'in doğru mu?)"

    except Exception as e:
        return f"Bağlantı hatası: {str(e)}"