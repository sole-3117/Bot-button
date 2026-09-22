Rejachi Bot

Belgilangan vaqtda vazifalarni eslatib turadigan Telegram bot.

Xususiyatlar
– ➕ Vazifa qo'shish (nom, sana, vaqt)
– 🔔 Sozlanuvchi oldindan eslatma (5/15/30/60 daqiqa)
– 🔁 Takrorlanish: kunlik, haftalik, oylik, maxsus interval
– ✅ Vazifani "Toʻlash" tugmasi bilan bajarilgan deb belgilash
– 🗑 Vazifani oʻchirish
– 📋 Faol va bajarilgan vazifalar roʻyxati

Oʻrnatish (lokal)
pip install -r requirements.txt
cp .env.example .env
# .env faylida BOT_TOKEN ni kiriting (@BotFather dan oling)
python main.py

Koyeb'ga deploy qilish
1. Loyihani GitHub'ga push qiling.
2. Koyeb'da yangi Service yarating → GitHub repo tanlang.
3. Build: avtomatik aniqlanadi (Python, requirements.txt).
4. Run command: python main.py
5. Environment Variables bo'limida qo'shing:
6. BOT_TOKEN — BotFather'dan olingan token
7. DB_PATH — rejachi.db (default yetarli)
8. Deploy tugmasini bosing.

Eslatma: SQLite fayli konteyner qayta ishga tushganda oʻchishi mumkin — Koyeb'ning persistent volume xususiyatidan foydalaning yoki keyinchalik PostgreSQL'ga oʻting.

Fayl strukturasi
rejachi-bot/
├── main.py                  # Kirish nuqtasi, handler'larni ulash
├── config.py                 # Sozlamalar
├── database.py                # SQLite CRUD funksiyalari
├── handlers/
│   ├── start.py               # /start va asosiy menyu
│   └── task_handlers.py       # Vazifa yaratish/ko'rish/o'chirish
├── utils/
│   └── scheduler.py           # Eslatma va muddat tekshiruvi (job_queue)
├── requirements.txt
├── .env.example
└── README.md

Keyingi qadamlar (kengaytirish uchun)
– Vazifani tahrirlash (nom/vaqt oʻzgartirish)
– Kategoriya/teglar
– Bir nechta til qoʻllab-quvvatlash
– PostgreSQL'ga oʻtish (production uchun)