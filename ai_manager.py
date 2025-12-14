import requests
import json
import streamlit as st

# Google Gemini API URL'si
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


def get_ai_feedback(word, sentence):
    """
    Gemini API'ye direkt HTTP isteği atar (Kütüphanesiz).
    Bu yöntem donma yapmaz.
    """

    # 1. API Anahtarını Al (Streamlit Secrets'tan)
    try:
        # Streamlit Cloud'daki "Secrets" kısmından şifreyi çeker
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        return "⚠️ Hata: API Anahtarı bulunamadı! Streamlit ayarlarından 'Secrets' kısmına GOOGLE_API_KEY ekle."

    # 2. Yapay Zekaya Gidecek Mesaj (Prompt)
    prompt = f"""
    Sen harika bir İngilizce öğretmenisin.
    Öğrenci '{word}' kelimesini kullanarak şu cümleyi kurdu: "{sentence}"

    Lütfen Türkçe olarak:
    1. Cümlede gramer hatası var mı?
    2. Kelime doğru anlamda kullanılmış mı?
    3. Hata varsa doğrusunu göster.
    4. Kısa ve motive edici bir yorum yap (Emoji kullan).

    Cevabı çok uzun tutma, özet geç.
    """

    # 3. Veriyi Hazırla
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    headers = {'Content-Type': 'application/json'}

    # 4. İsteği Gönder (Postacı Yola Çıktı 📨)
    try:
        response = requests.post(f"{URL}?key={api_key}", headers=headers, data=json.dumps(payload), timeout=10)

        if response.status_code == 200:
            # Cevap geldiyse içini açıp metni alalım
            result = response.json()
            try:
                text = result['candidates'][0]['content']['parts'][0]['text']
                return text
            except:
                return "Cevap geldi ama okuyamadım. Tekrar dene."
        else:
            return f"Bir sorun oldu. Hata Kodu: {response.status_code} (API Key doğru mu?)"

    except Exception as e:
        return f"Bağlantı hatası: {str(e)}"