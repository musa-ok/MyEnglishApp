import requests
import streamlit as st

# YENİ ADRES: router.huggingface.co
API_URL = "https://router.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"


def get_ai_feedback(word, sentence):
    try:
        # Token'ı al
        api_token = st.secrets["HUGGINGFACE_API_KEY"]
    except:
        return "⚠️ Hata: HUGGINGFACE_API_KEY bulunamadı! Secrets ayarlarını kontrol et."

    headers = {"Authorization": f"Bearer {api_token}"}

    # Prompt
    prompt = f"""<s>[INST] Sen yardımsever bir İngilizce öğretmenisin.
    Öğrenci '{word}' kelimesini kullanarak şu cümleyi kurdu: "{sentence}"

    Lütfen Türkçe olarak şu 3 maddeyi cevapla:
    1. Gramer hatası var mı?
    2. Kelime doğru anlamda kullanılmış mı?
    3. Hata varsa düzelt ve motive edici kısa bir yorum yap. [/INST]
    """

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 250,
            "return_full_text": False,
            "temperature": 0.7
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)  # Süreyi biraz uzattım (20sn)

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0]['generated_text']
            else:
                return "Cevap boş döndü."

        elif "loading" in response.text.lower():
            return "⏳ Model şu an uyanıyor, sunucu soğuk. 20 saniye sonra tekrar bas çalışacak!"

        else:
            return f"Hata oluştu: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Bağlantı hatası: {str(e)}"