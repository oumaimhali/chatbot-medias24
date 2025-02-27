from fastapi import FastAPI
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Démarrage de l'application")

app = FastAPI()
logger.info("FastAPI initialisé")

@app.get("/")
def read_root():
    logger.info("Route / appelée")
    return {"Hello": "World"}

@app.get("/health")
def health_check():
    logger.info("Health check appelé")
    return {"status": "healthy"}
