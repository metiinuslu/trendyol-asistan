import os
import json
import base64
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROMPT = (
    "You are an expert product content writer for Trendyol Turkey marketplace. "
    "Analyze this product image carefully. "
    "Return ONLY a valid JSON object with NO markdown, NO backticks, NO extra text. "
    "The JSON must have these exact keys: title, description, keywords. "
    "title: SEO-optimized Turkish product title (60-80 chars). "
    "description: Detailed Turkish description with bullet points about features, material, usage, advantages. "
    "keywords: array of minimum 8 Turkish search keywords."
)

@app.post("/api/generate")
async def generate_content(
    image: UploadFile = File(...),
    category: str = Form(""),
    extra: str = Form("")
):
    try:
        image_bytes = await image.read()
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Gorsel 10MB dan buyuk olamaz.")

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        mime_type = image.content_type or "image/jpeg"

        prompt_text = PROMPT
        if category:
            prompt_text += f" Category: {category}."
        if extra:
            prompt_text += f" Extra info: {extra}."

        api_key = os.environ.get("GEMINI_API_KEY")
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

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

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI yaniti parse edilemedi.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=500, detail=f"Gemini API hatasi: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/", StaticFiles(directory="static", html=True), name="static")
