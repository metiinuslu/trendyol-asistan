# Trendyol Ürün Asistanı

Ürün görseli yükle → AI analiz etsin → Trendyol uyumlu başlık + açıklama + anahtar kelimeler çıksın.

## Kurulum (Local)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload
```
Tarayıcıda: http://localhost:8000

## Railway'e Deploy

1. GitHub'a push et
2. https://railway.app → New Project → Deploy from GitHub
3. Environment Variables ekle:
   - `ANTHROPIC_API_KEY` = sk-ant-xxxxx
4. Deploy et, URL'i al, kullanmaya başla!

## Render'a Deploy

1. GitHub'a push et
2. https://render.com → New Web Service → GitHub repoyu bağla
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Environment Variables:
   - `ANTHROPIC_API_KEY` = sk-ant-xxxxx
6. Deploy!

## Dosya Yapısı

```
trendyol-asistan/
├── main.py          ← FastAPI backend
├── requirements.txt ← Python bağımlılıkları
├── Procfile         ← Railway/Render için
├── static/
│   └── index.html   ← Frontend arayüz
└── README.md
```

## API Endpoint

`POST /api/generate`
- `image` (file): Ürün görseli
- `category` (str, optional): Ürün kategorisi
- `extra` (str, optional): Ek bilgi

Response:
```json
{
  "title": "SEO uyumlu ürün başlığı",
  "description": "Detaylı ürün açıklaması",
  "keywords": ["anahtar", "kelime", "listesi"]
}
```
