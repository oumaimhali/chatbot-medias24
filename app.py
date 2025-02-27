from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from elasticsearch import Elasticsearch
from openai import OpenAI
from dotenv import load_dotenv
from translate import Translator
import speech_recognition as sr
from pydantic import BaseModel
import logging
import os
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()
logger.info("Variables d'environnement chargées")

app = FastAPI(title="Médias24 ChatBot")
logger.info("Application FastAPI initialisée")

try:
    # Configuration des templates et fichiers statiques
    templates = Jinja2Templates(directory="templates")
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("Templates et fichiers statiques configurés")

    # Configuration Elasticsearch
    es = Elasticsearch(
        os.getenv("ELK_ENDPOINT"),
        basic_auth=(os.getenv("ELK_USERNAME"), os.getenv("ELK_PASSWORD"))
    )
    logger.info("Elasticsearch configuré")

    # Configuration OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("OpenAI configuré")

except Exception as e:
    logger.error(f"Erreur lors de l'initialisation: {str(e)}")
    raise

@app.get("/health")
def health_check():
    logger.info("Health check appelé")
    return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logger.info("Page d'accueil appelée")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(message: str = Form(...), language: str = Form("fr")):
    try:
        logger.info(f"Requête chat reçue: {message}, langue: {language}")
        
        # Recherche dans Elasticsearch
        response = es.search(
            index=os.getenv("ELK_INDEX"),
            body={
                "query": {
                    "multi_match": {
                        "query": message,
                        "fields": ["title", "content", "description"]
                    }
                }
            }
        )
        logger.info(f"Résultats Elasticsearch: {len(response['hits']['hits'])} articles trouvés")

        # Préparation du contexte pour ChatGPT
        articles = response["hits"]["hits"]
        context = "Based on the following articles from Medias24:\n\n"
        for article in articles[:3]:
            context += f"Title: {article['_source'].get('title', '')}\n"
            context += f"Content: {article['_source'].get('content', '')}\n\n"

        # Génération de la réponse avec ChatGPT
        chat_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for Medias24, a Moroccan news website."},
                {"role": "user", "content": f"{context}\n\nQuestion: {message}\nPlease provide a detailed answer in {language}."}
            ]
        )
        logger.info("Réponse ChatGPT générée avec succès")

        response = chat_response.choices[0].message.content
        return {"response": response, "status": "success"}
    except Exception as e:
        logger.error(f"Erreur dans /chat: {str(e)}")
        return {"response": f"Error: {str(e)}", "status": "error"}

@app.post("/audio")
async def process_audio(file: UploadFile = File(...)):
    try:
        logger.info(f"Traitement audio reçu: {file.filename}")
        
        # Sauvegarde temporaire du fichier audio
        temp_file = f"temp_{file.filename}"
        with open(temp_file, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Conversion audio en texte
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_file) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)

        # Suppression du fichier temporaire
        os.remove(temp_file)
        logger.info(f"Audio traité avec succès: {text}")

        return {"text": text, "status": "success"}
    except Exception as e:
        logger.error(f"Erreur dans /audio: {str(e)}")
        return {"text": f"Error: {str(e)}", "status": "error"}

@app.post("/feedback")
async def feedback(feedback_data: dict):
    logger.info(f"Feedback reçu: {feedback_data}")
    return {"status": "success", "message": "Feedback received"}
