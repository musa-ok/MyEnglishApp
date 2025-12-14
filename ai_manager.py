import requests
import streamlit as st
import time

# MODELDEN MODELE GEÇİŞ: Zephyr (Kilitsiz ve çok zekidir)
# Eğer router hatası alırsan URL'yi 'api-inference' olarak değiştirmeyi de deneyebilirsin ama şimdilik router kalsın.
API_URL = "https://router.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"


def get_ai_feedback(word, sentence):
    try:
        api_token = st.secrets["HUGGINGFACE_API_KEY"]
    except:
        return "⚠️ Hata: HUGGINGFACE_API_KEY bulunamadı! Secrets ayarlarını kontrol et."

    headers = {"Authorization": f"Bearer {api_token}"}

    prompt = f"""<|system|>
    Sen yardımsever bir İngilizce öğretmenisin. Türkçe cevap veriyorsun.</s>
    <|user|>
    Öğrenci '{word}' kelimesini kullanarak şu cümleyi kurdu: "{sentence}"

    Lütfen Türkçe olarak şu 3 maddeyi cevapla:
    1. Gramer hatası var mı?
    2. Kelime doğru anlamda kullanılmış mı?
    3. Hata varsa düzelt ve motive edici kısa bir yorum yap.</s>
    <|assistant|>"""

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 250,
            "return_full_text": False,
            "temperature": 0.7
        }
    }

    try:
        # İstek gönder
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)

        # 1. BAŞARILI DURUM
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0]['generated_text']
            return "Cevap boş döndü."

        # 2. MODEL UYUYORSA (503 Hatası verir)
        elif response.status_code == 503 or "loading" in response.text.lower():
            return "⏳ Model şu an uyanıyor (Soğuk Başlangıç). Lütfen 20 saniye bekleyip tekrar butona bas!"

        # 3. DİĞER HATALAR
        else:
            # Eğer router yine sorun çıkarırsa eski adrese dönmeyi önereceğiz
            return f"Hata: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Bağlantı hatası: {str(e)}"