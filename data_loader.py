import database as db
import re
from deep_translator import GoogleTranslator
from tqdm import tqdm  # İlerleme çubuğu için

# Veritabanını sıfırdan kur
db.init_db()


def clean_and_parse(filename="oxford.txt"):
    parsed_words = []

    print("📖 Dosya okunuyor...")
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"🔄 {len(lines)} kelime çevriliyor... Bu işlem biraz sürebilir, kahveni al bekle ☕")

    translator = GoogleTranslator(source='en', target='tr')

    # Regex ile satırı parçala: "abandon v. B2" -> "abandon", "v.", "B2"
    # Bu regex karmaşık formatları da yakalar
    pattern = re.compile(r"([a-zA-Z\s\-]+)\s([a-z\.,\/]+)\s([A-C][1-2])")

    for line in tqdm(lines):
        line = line.strip()
        if not line: continue

        match = pattern.search(line)
        if match:
            word = match.group(1).strip()
            pos = match.group(2).strip()  # Part of Speech (n., v., adj.)
            level = match.group(3).strip()

            # KELİME FİİL Mİ? (v. içeriyor mu?)
            search_word = word
            if "v." in pos:
                search_word = "to " + word  # Fiil ise 'to' ekleyip çevir ki mastar gelsin (mek/mak)

            try:
                # Çeviri yap
                turkish = translator.translate(search_word)

                # Basit bir örnek cümle (Placeholder)
                # İstersen burayı da AI ile doldurabiliriz ama 3000 tane için API parası gider.
                # Şimdilik kelimeyi örnek olarak kaydediyoruz.
                example = f"I learned the word {word} today."

                parsed_words.append((word, turkish, level, pos, example))

            except Exception as e:
                print(f"Hata ({word}): {e}")

    return parsed_words


if __name__ == "__main__":
    try:
        kelimeler = clean_and_parse()
        print(f"\n📦 {len(kelimeler)} kelime veritabanına yükleniyor...")
        db.insert_bulk_words(kelimeler)
        print("✅ İŞLEM TAMAM! 3000 Kelime cebinde.")
    except FileNotFoundError:
        print("❌ HATA: 'oxford.txt' dosyası bulunamadı. Lütfen kelime listesini bu isimle kaydet.")