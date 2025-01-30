from googletrans import Translator

def tarjima(xabar, til):
    tarjimonbek = Translator()
    original_til = tarjimonbek.detect(xabar).lang  # Matnning tilini aniqlash
    if original_til == til:
        return "Matn allaqachon tanlangan tilda yozilgan."
    try:
        return tarjimonbek.translate(xabar, dest=til).text
    except Exception as e:
        return f"Tarjima qilishda xatolik yuz berdi: {e}"
