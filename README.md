# � Rissala - AI-Powered Arabic Library Wrapper

**Rissala** (رسالة) est une plateforme intelligente conçue pour explorer et interagir avec les vastes ressources de la littérature arabe, notamment via l'intégration d'une bibliothèque et des modèles d'IA avancés.

## ✨ Fonctionnalités

- 🔍 **Recherche Intelligente** : Recherche sémantique et par mots-clés dans les textes classiques.
- 🤖 **Moteur d'IA** : Analyse, résumé et explication de textes via OpenAI ou des modèles locaux (Ollama/ALLaM).
- 🌍 **Interface Multilingue** : Support complet du Français et de l'Arabe.
- 👤 **Gestion de Compte** : Système d'authentification complet (Django-allauth) avec profils personnalisés.
- 📱 **Design Moderne** : Interface responsive et élégante utilisant TailwindCSS.

## 🚀 Installation Locale

### Prérequis
- Python 3.10+
- Git

### Étapes
1. **Cloner le projet** :
   ```bash
   git clone https://github.com/mikaellll/rissala.git
   cd rissala
   ```

2. **Créer un environnement virtuel** :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

3. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer l'environnement** :
   Copiez le fichier `.env.example` vers `.env` et remplissez vos clés API.
   ```bash
   cp .env.example .env
   ```

5. **Lancer les migrations et le serveur** :
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## 🌐 Déploiement

Le projet est prêt pour un déploiement sur **Render.com**.
- Utilisez le fichier `render.yaml` pour une configuration automatique.
- La commande de build est `./build.sh`.
- La commande de lancement est `gunicorn rissala_core.wsgi`.

## 🛠️ Stack Technique

- **Backend** : Django 5.0
- **Base de données** : SQLite (Dev) / PostgreSQL (Prod)
- **IA** : LangChain, OpenAI, Ollama
- **UI** : TailwindCSS, Flowbite
- **Statique** : WhiteNoise
- **Serveur Web** : Gunicorn

## 📜 Licence
Ce projet est sous licence MIT.
