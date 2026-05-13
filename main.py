import os
import anthropic
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import json

app = FastAPI(title="Trendyol Ürün Asistanı")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Sen Trendyol platformu için uzman bir ürün içerik yazarısın. Görseli analiz ederek aşağıdaki formatta JSON döndür. SADECE JSON döndür, başka hiçbir şey yazma, markdown backtick kullanma.

Format:
{
  "title": "Trendyol SEO uyumlu ürün başlığı (60-80 karakter, marka + ürün türü + özellik formatında)",
  "description": "Ürün açıklaması (300-500 kelime, bullet point tarzında, ürün özellikleri, malzeme, kullanım alanı, boyut/beden bilgisi, bakım talimatları, avantajlar içersin. Trendyol alıcısına hitap etsin.)",
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

        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        media_type = image.content_type or "image/jpeg"

        user_text = "Bu ürün görselini analiz et ve Trendyol için içerik üret."
        if category:
            user_text += f" Kategori: {category}."
        if extra:
            user_text += f" Ek bilgi: {extra}."

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": user_text
                    }
                ]
            }]
        )

        text = response.content[0].text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI yanıtı parse edilemedi.")
    except anthropic.APIError as e:
        raise HTTPException(status_code=500, detail=f"API hatası: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health():
    return {"status": "ok"}
