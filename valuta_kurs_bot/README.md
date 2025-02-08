# Trading Signal Telegram Bot

Bu Telegram bot foydalanuvchilarga 5 ta asosiy valyuta juftligi bo'yicha savdo signallarini taqdim etadi.

## O'rnatish

1. Repository-ni clone qiling
2. Kerakli kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

3. `.env` faylini sozlang:
- `TELEGRAM_TOKEN` - Telegram bot token (@BotFather dan olinadi)
- `ADMIN_ID` - Admin Telegram ID raqami

## Ishga tushirish

```bash
python bot.py
```

## Xususiyatlar

- 5 ta valyuta juftligi bo'yicha savdo signallari
- Foydalanuvchi autentifikatsiyasi
- Admin boshqaruvi
- Interaktiv interfeys

## Valyuta juftliklari

- XAU/USD (Oltin va AQSh dollari)
- BTC/USD (Bitcoin va AQSh dollari)
- EUR/USD (Evro va AQSh dollari)
- USD/JPY (AQSh dollari va Yapon iyenasi)
- GBP/USD (Britaniya funt sterlingi va AQSh dollari) 