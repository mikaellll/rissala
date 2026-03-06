# 📚 Shamela IA Wrapper

Un wrapper intelligent autour de la bibliothèque islamique **shamela.ws**. Ce projet permet de rechercher et d'interroger le patrimoine islamique arabe classique en utilisant l'IA (RAG - Retrieval-Augmented Generation).

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.0-green)
![IA](https://img.shields.io/badge/AI-OpenAI%20%2F%20Ollama-orange)

## ✨ Fonctionnalités

- **Recherche IA (RAG) :** Posez des questions complexes et obtenez des réponses basées sur les textes de Shamela.
- **Indexation Locale :** Utilise FAISS pour une recherche vectorielle rapide dans les extraits de livres importés.
- **Double Backend IA :** Configurez soit OpenAI (GPT-4o-mini), soit une IA locale via Ollama.
- **Fetcher Éthique :** Importation respectueuse des métadonnées et textes de shamela.ws avec cache et rate-limiting.
- **Support Multilingue :** Interface et réponses en Français et Arabe (Support RTL complet).
- **Design Moderne :** Interface fluide avec Tailwind CSS, support mode sombre, et animations.
- **Dashboard Admin :** Gestion complète des utilisateurs, livres et historique des requêtes.

---

## 🚀 Installation Locale

### 1. Cloner le projet et préparer l'environnement
```bash
git clone <votre-repo>
cd shamela_ia_wrapper
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration (`.env`)
Copiez le fichier d'exemple et remplissez vos clés :
```bash
cp .env.example .env
```
Paramètres importants :
- `AI_BACKEND`: `openai` ou `ollama`.
- `OPENAI_API_KEY`: Votre clé OpenAI.
- `OLLAMA_HOST`: `http://localhost:11434` (si local).

### 3. Initialiser la base de données
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Importer les premiers livres (Seed)
Cette commande télécharge les métadonnées et quelques pages des livres classiques (Bukhari, Muslim, etc.) pour peupler l'index IA.
```bash
python manage.py import_shamela
```

### 5. Lancer le serveur
```bash
python manage.py runserver
```
Accédez à `http://127.0.0.1:8000`.

---

## 🤖 Configuration IA Locale (Ollama)

Si vous ne souhaitez pas utiliser OpenAI, installez **Ollama** et téléchargez un modèle performant en arabe :
```bash
ollama pull iKhalid/ALLaM:7b
# Ou un autre modèle arabe-friendly
```
Assurez-vous que `AI_BACKEND=ollama` et `OLLAMA_MODEL=iKhalid/ALLaM:7b` sont définis dans votre `.env`.

---

## ☁️ Déploiement sur Render.com (Niveau Gratuit)

1. **GitHub :** Poussez votre code sur un dépôt GitHub.
2. **Nouveau Service Web :** Créez un "Web Service" sur Render.
3. **Runtime :** Python 3.
4. **Build Command :** `pip install -r requirements.txt`
5. **Start Command :** `gunicorn shamela_ia_wrapper.wsgi`
6. **Variables d'environnement :**
   - Ajoutez toutes les variables de votre `.env` dans l'onglet "Environment" de Render.
   - `DEBUG=False`
   - `ALLOWED_HOSTS=votre-app.onrender.com`
   - `DATABASE_URL`: Render fournit une URL pour ses bases de données Postgres.
7. **Base de données :** Créez une instance "Render PostgreSQL" et liez-la à votre service web.

---

## 🛠 Commandes Utiles

- **Importer des livres spécifiques :** `python manage.py import_shamela --ids 1 10 100`
- **Réinitialiser l'index IA :** `python manage.py import_shamela --rebuild-index`
- **Recherche via shell :** Accédez à la logique RAG via `python manage.py shell`.

---

## ⚖️ Responsabilité & Sources
Ce projet est un outil éducatif. Les contenus proviennent de [shamela.ws](https://shamela.ws). Les utilisateurs sont encouragés à vérifier les sources originales. L'IA peut générer des erreurs ("hallucinations"), restez vigilants.
