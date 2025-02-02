# WikiLLM 📚


WikiLLM est un projet interactif qui combine quiz et cours pour améliorer votre expérience d'apprentissage. Basé sur le programme officiel, cette application vous permet de tester vos connaissances à l'aide de quiz générés par l'IA, d'explorer des cours structurés en Histoire, Physique-Chimie et Sciences de la Vie et de la Terre (SVT). Chaque contenu est conçu pour suivre les attentes académiques, avec des explications détaillées et des indices pour renforcer votre compréhension. 

De plus, vous pouvez vous entraîner dans des conditions d'examen réelles grâce à des simulations comme le Brevet Blanc, afin de mieux vous préparer aux évaluations officielles.

Les questions des quiz sont générées par l'API Mistral en utilisant des données scrappées de [School Move](https://www.schoolmouv.fr/). Cela permet de garantir que les questions sont alignées avec les programmes académiques.

## Table des Matières
- [Fonctionnalités](#fonctionnalités)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Accès en ligne](#accès-en-ligne)
- [Technologie utilisées](#technologie-utilisées)
- [Architecture du projet](#architecture-du-projet)
- [Contribution](#contribution)
- [Licence](#licence)
- [Contact](#contact)

## Fonctionnalités

- **Quiz Interactifs** 📝 : Profitez de quiz dynamiques avec différents modes, comme le mode "speed test" ou normal. Suivez le temps de réponse, consultez des retours détaillés et améliorez vos performances.
- **Explications et Indices** 💡 : Après chaque question, accédez à des explications approfondies et utilisez des indices pour mieux comprendre le contenu.
- **Contenus de Cours** 📖 : Accédez à des cours complets et structurés sur divers sujets.
- **Simulation de Brevet Blanc** 🎓 : Simulez l'examen du Brevet avec des quiz progressifs et obtenez des résultats détaillés.
- **Métriques Utilisateur** 📊 : Suivez vos performances grâce à des métriques telles que le temps moyen de réponse, les taux de réussite, etc.
- **Tableau de Bord Administratif** 🛠️ : Les administrateurs peuvent consulter des données agrégées, gérer les quiz et analyser les tendances de performance.


## Installation

Assurez-vous d'avoir [Python 3.10](https://www.python.org/downloads/release/python-310/) installé. Suivez ensuite ces étapes pour installer l'environnement :

```bash
# Créez un nouvel environnement Conda
conda create -n wikillm python==3.10

# Activez l'environnement
conda activate wikillm

# Accédez au répertoire du projet
cd wikillm

# Installez les dépendances
pip install -r requirements.txt
```

## Configuration


1. Créez un fichier `.env` à la racine du projet et ajoutez la variable d'environnement [Mistral](https://console.mistral.ai/) :

   ```
   MISTRAL_API_KEY=your_mistral_api_key_here
   ```

2. Vous pouvez également ajuster certains paramètres dans le fichier `.streamlit/config.toml` si nécessaire.

## Utilisation

Pour lancer l'application, exécutez :

```bash
streamlit run app.py
```

Cela lancera l'application WikiLLM. Vous pouvez utiliser la barre latérale pour naviguer entre le tableau de bord principal, le panneau d'administration et la simulation du Brevet Blanc.

## Accès en ligne

Vous pouvez également consulter le site en ligne à l'adresse suivante : [https://wikillm.streamlit.app/](https://wikillm.streamlit.app/)

## Technologie utilisées

- **Python** 🐍 : Langage principal utilisé pour le développement.
- **Streamlit** 📊 : Framework utilisé pour créer l'application web interactive.
- **Mistral** 🌐 : API utilisée pour certaines fonctionnalités de l'application.
- **Conda** 📦 : Gestionnaire d'environnements pour gérer les dépendances.


## Architecture du projet

```
.env
.gitignore
.streamlit/
    config.toml
app.py
docs/
    README.md
pages/
    admin.py
    brevet.py
    ressources/
        components.py
requirements.txt
src/
    db/
        utils.py
    metrics_database.py
    ml_model.py
    rag.py
    scrapper.py
```

- **app.py** : Point d'entrée principal de l'application.
- **pages/** : Contient les pages supplémentaires (Dashboard admin, Brevet Blanc, etc.).
- **pages/ressources/components.py** : Composants UI, dialogues et éléments de navigation.
- **src/** : Logique principale comprenant les utilitaires de la base de données, la gestion des métriques, le modèle ML et le scrapping des données.
- **docs/** : Documentation et fichiers associés au projet.

## Contribution

Les contributions sont les bienvenues ! Pour participez suivez ces étapes : 

1. Forkez le repo

2. Créez votre branche
```
git checkout -b feature/AmazingFeature
```
3. Commit vos changements
```
git commit -m 'Add some AmazingFeature'
```
4. Push dans la branch
```
git push origin feature/AmazingFeature
```

5. Ouvrez une Pull Request

Consultez le [GitHub Flow](https://guides.github.com/introduction/flow/) pour les directives de gestion des branches.

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Contact

Pour toute question ou support, contactez les mainteneurs :

- [Alexis GABRYSCH](https://github.com/AlexisGabrysch)
- [Antoine ORUEZABALA](https://github.com/AntoineORUEZABALA)
- [Lucile PERBET](https://github.com/lucilecpp)
- [Alexis DARDELET](https://github.com/AlexisDardelet)

Consultez le dépôt du projet sur [GitHub](https://github.com/AlexisGabrysch/wikillm).
