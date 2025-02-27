from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from elasticsearch import Elasticsearch
from openai import OpenAI
from dotenv import load_dotenv
from translate import Translator
import speech_recognition as sr
from pydantic import BaseModel
from typing import Optional
import os
import json
import uvicorn
from langdetect import detect

# Chargement des variables d'environnement
load_dotenv()

app = FastAPI(title="Médias24 ChatBot")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration des clients
es = Elasticsearch(
    os.getenv('ELK_ENDPOINT'),
    basic_auth=(os.getenv('ELK_USERNAME'), os.getenv('ELK_PASSWORD')),
    verify_certs=False,
    timeout=30,
    max_retries=3,
    retry_on_timeout=True
)

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class ChatRequest(BaseModel):
    query: str
    target_language: str = "fr"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

def translate_text(text: str, target_lang: str) -> str:
    if target_lang == "fr":
        return text
    try:
        translator = Translator(to_lang=target_lang)
        # Traduire par morceaux car la bibliothèque a une limite de caractères
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        translated_chunks = [translator.translate(chunk) for chunk in chunks]
        return ' '.join(translated_chunks)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def process_audio(audio_file) -> str:
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            # Détection automatique de la langue
            text = recognizer.recognize_google(audio)
            return text
    except Exception as e:
        print(f"Audio processing error: {e}")
        return ""

def search_articles(query: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    must_conditions = [{"match": {"_all": query}}]
    
    if start_date or end_date:
        date_range = {}
        if start_date:
            date_range["gte"] = start_date
        if end_date:
            date_range["lte"] = end_date
        must_conditions.append({"range": {"date": date_range}})
    
    body = {
        "query": {
            "bool": {
                "must": must_conditions
            }
        },
        "size": 50,
        "sort": [{"date": {"order": "asc"}}]
    }
    
    try:
        response = es.search(index=os.getenv('ELK_INDEX'), body=body)
        return response['hits']['hits']
    except Exception as e:
        print(f"Elasticsearch error: {e}")
        return []

def generate_summary(articles: list, query: str, target_lang: str) -> str:
    if not articles:
        return translate_text("Aucun article trouvé pour cette recherche.", target_lang)
    
    context = "Sur la base des articles suivants de Médias24 :\n\n"
    for article in articles:
        source = article['_source']
        context += f"Date: {source.get('date', 'N/A')}\n"
        context += f"Titre: {source.get('titre', 'N/A')}\n"
        context += f"Contenu: {source.get('contenu', 'N/A')}\n\n"

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant spécialisé dans l'analyse et la synthèse d'articles de Médias24. Vos réponses doivent être structurées, chronologiques et mettre en évidence les dates et événements clés."},
                {"role": "user", "content": f"{context}\nQuestion: {query}\n\nVeuillez fournir une synthèse détaillée et chronologique, en mettant en évidence les dates et événements importants."}
            ],
            temperature=0.7
        )
        
        summary = response.choices[0].message.content
        if target_lang != "fr":
            summary = translate_text(summary, target_lang)
        return summary
    except Exception as e:
        print(f"OpenAI error: {e}")
        error_message = "Une erreur s'est produite lors de la génération du résumé."
        return translate_text(error_message, target_lang)

@app.get("/health")
async def health_check():
    try:
        # Vérification de base
        health_status = {
            "status": "healthy",
            "timestamp": "up",
        }
        return JSONResponse(content=health_status, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e)},
            status_code=500
        )

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/chat")
async def chat(request: ChatRequest):
    articles = search_articles(request.query, request.start_date, request.end_date)
    summary = generate_summary(articles, request.query, request.target_language)
    
    return {
        "response": summary,
        "source_count": len(articles),
        "detected_language": detect(request.query)
    }

@app.post("/upload-audio")
async def upload_audio(audio: UploadFile = File(...)):
    text = process_audio(audio.file)
    return {"text": text}

@app.post("/feedback")
async def feedback(feedback: str = Form(...)):
    # Ici vous pouvez implémenter la logique pour stocker les retours utilisateurs
    return {"status": "success", "message": "Merci pour votre retour !"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
