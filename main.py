import os
import json
import base64
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

app = FastAPI(title="Trendyol Ürün Asistanı")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

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

        user_text = PROMPT
        if category:
            user_text += f"\n\nKategori: {category}"
        if extra:
            user_text += f"\nEk bilgi: {extra}"

        image_part = {
            "mime_type": image.content_type or "image/jpeg",
            "data": base64.b64encode(image_bytes).decode("utf-8")
        }

        response = model.generate_content([
            user_text,
            {"inline_data": image_part}
        ])

        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI yanıtı parse edilemedi.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="static", html=True), name="static")
