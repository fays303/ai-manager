import os
import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

async def gemini_cagir(prompt: str, sistem: str = "") -> str:
    if not GEMINI_KEY:
        return "GEMINI_API_KEY bulunamadi! Secrets'a ekle."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": sistem or "Sen yardimci bir asistansin."}]},
        "contents": [{"parts": [{"text": prompt}]}]
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, json=payload)
        data = r.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except:
            return f"Hata: {data}"

class Soru(BaseModel):
    mesaj: str

@app.post("/sor")
async def sor(s: Soru):
    plan_prompt = f"""Kullanici sorusu: {s.mesaj}

Sen bir yonetici AI'sin. Bu soruyu analiz et ve 3 farkli uzman bakisiyla cevapla:
1. UZMAN A: Teknik/analitik bakis
2. UZMAN B: Elestirel bakis (eksikleri soyle)
3. UZMAN C: Pratik/uygulamali bakis

Her uzman icin ayri ayri cevap yaz. Sonunda hepsini birlestirip tek bir final cevap ver."""
    
    sonuc = await gemini_cagir(plan_prompt, "Sen coklu uzman goruslerini birlestiren bir yonetici AI'sin.")
    return {"final": sonuc, "girdi": s.mesaj}

@app.get("/", response_class=HTMLResponse)
async def ana_sayfa():
    return """
    <html><head><meta charset="utf-8"><title>AI Yonetici</title>
    <style>
    body{font-family:sans-serif;padding:20px;background:#f0f4f8;max-width:700px;margin:auto}
    h1{color:#1a365d}
    textarea{width:100%;height:100px;padding:10px;font-size:16px;border-radius:8px;border:1px solid #ccc}
    button{background:#2563eb;color:white;padding:12px 24px;border:none;border-radius:8px;font-size:16px;cursor:pointer;margin-top:10px}
    #sonuc{margin-top:20px;padding:15px;background:white;border-radius:8px;white-space:pre-wrap;line-height:1.6}
    .yukleniyor{color:#666;font-style:italic}
    </style></head>
    <body>
    <h1>Yapay Zeka Yoneticisi</h1>
    <p>Sorunuzu yazin. Yonetici AI, farkli uzman bakislariyla cevaplasin.</p>
    <textarea id="soru" placeholder="Sorunuzu buraya yazin..."></textarea>
    <br>
    <button onclick="gonder()">Sor</button>
    <div id="sonuc"></div>
    <script>
    async function gonder(){
        const mesaj = document.getElementById('soru').value;
        if(!mesaj) return;
        const sonuc = document.getElementById('sonuc');
        sonuc.innerHTML = '<div class="yukleniyor">Yonetici AI dusunuyor...</div>';
        try{
            const r = await fetch('/sor',{
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({mesaj:mesaj})
            });
            const data = await r.json();
            sonuc.textContent = data.final;
        }catch(e){
            sonuc.textContent = 'Hata: ' + e.message;
        }
    }
    </script>
    </body></html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
