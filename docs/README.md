# WikiLLM

WikiLLM est un projet interactif qui combine quiz et cours pour améliorer votre expérience d'apprentissage. Avec WikiLLM, vous pouvez tester vos connaissances via des quiz générés par l'IA, explorer des cours structurés, bénéficier d'explications détaillées et d'indices, et même simuler des situations d'examen comme le Brevet Blanc.

## Fonctionnalités

- **Quiz Interactifs** : Profitez de quiz dynamiques avec différents modes, comme le mode "speed test" ou normal. Suivez le temps de réponse, consultez des retours détaillés et améliorez vos performances.
- **Explications et Indices** : Après chaque question, accédez à des explications approfondies et utilisez des indices pour mieux comprendre le contenu.
- **Contenus de Cours** : Accédez à des cours complets et structurés sur divers sujets.
- **Simulation de Brevet Blanc** : Simulez l'examen du Brevet français avec des quiz progressifs et obtenez des résultats détaillés.
- **Métriques Utilisateur** : Suivez vos performances grâce à des métriques telles que le temps moyen de réponse, les taux de réussite, etc.
- **Tableau de Bord Administratif** : Les administrateurs peuvent consulter des données agrégées, gérer les quiz et analyser les tendances de performance.

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

1. Créez un fichier `.env` à la racine du projet et ajoutez les variables d'environnement nécessaires, par exemple :

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

## Structure du projet

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

Les contributions sont les bienvenues ! N'hésitez pas à forker le dépôt et à soumettre une pull request avec vos améliorations ou corrections. Consultez le [GitHub Flow](https://guides.github.com/introduction/flow/) pour les directives de gestion des branches.

## Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Contact

Pour toute question ou support, contactez les mainteneurs :

- [Alexis GABRYSCH](https://github.com/AlexisGabrysch)
- [Antoine ORUEZABALA](https://github.com/AntoineORUEZABALA)
- [Lucile PERBET](https://github.com/lucilecpp)
- [Alexis DARDELET](https://github.com/AlexisDardelet)

Consultez le dépôt du projet sur [GitHub](https://github.com/AlexisGabrysch/wikillm).