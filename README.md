# Chatbot Médias24

Chatbot intelligent pour Médias24 avec les fonctionnalités suivantes :

- Recherche et résumé d'articles
- Support multilingue
- Reconnaissance vocale
- Interface responsive
- Intégration avec Elasticsearch et ChatGPT
- Système de feedback

## Installation

1. Cloner le repository
2. Installer les dépendances : `pip install -r requirements.txt`
3. Configurer les variables d'environnement dans `.env`
4. Lancer l'application : `python main.py`

## Variables d'environnement requises

- `ELK_ENDPOINT` : URL Elasticsearch
- `ELK_USERNAME` : Nom d'utilisateur Elasticsearch
- `ELK_PASSWORD` : Mot de passe Elasticsearch
- `ELK_INDEX` : Index Elasticsearch
- `OPENAI_API_KEY` : Clé API OpenAI
