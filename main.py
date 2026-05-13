import os
import json
import base64
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Trendyol Ürün Asistanı")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROMPT = """Sen Trendyol platformu için uzman bir ürün içerik yazarısın. Bu ürün görselini analiz et ve aşağıdaki formatta SADECE JSON döndür. Başka hiçbir şey yazma, markdown backtick kullanma.

{
  "title": "Trendyol SEO uyumlu ürün başlığı (60-80 karakter, ürün türü + özellik + renk/beden formatında)",
  "description": "Ürün açıklaması (detaylı, bullet point tarzında, ürün özellikleri, malzeme, kullanım alanı, avantajlar. Trendyol alıcısına hitap etsin.)",
  "keywords": ["anahtar", "kelime", "listesi", "en az 8 adet"]
}"""

@app.post("/api/generate")
async def generate_content(
    image: UploadFile = File(...),
    category: str = Form(""),
    extra: str = Form("")
):
    try:
        image_bytes = await image.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Görsel 10MB'dan büyük olamaz.")

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        mime_type = image.content_type or "image/jpeg"

        prompt_text = PROMPT
        if category:
            prompt_text += f"\n\nKategori: {category}"
        if extra:
            prompt_text += f"\nEk bilgi: {extra}"

        api_key = os.environ.get("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt_text},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 1500
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI yanıtı parse edilemedi.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Gemini API hatası: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="static", html=True), name="static")
