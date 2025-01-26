from database import DatabaseManager

def add_test_documents():
    db_manager = DatabaseManager(db_path="./chromadb_data")
    
    # Liste des articles de test
    articles = [
        {
            "title": "Seconde Guerre mondiale",
            "content": "La Seconde Guerre mondiale est un conflit armé à l'échelle planétaire qui a duré de 1939 à 1945...",
            "links": ["https://fr.wikipedia.org/wiki/Seconde_Guerre_mondiale"],
            "metadata": {"category": "Histoire", "updated": "2025-01-01"}
        },
        {
            "title": "Révolution française",
            "content": "La Révolution française est une période de bouleversements politiques et sociaux en France...",
            "links": ["https://fr.wikipedia.org/wiki/Révolution_française"],
            "metadata": {"category": "Histoire", "updated": "2025-01-01"}
        },
        {
            "title": "Photosynthèse",
            "content": "La photosynthèse est le processus par lequel les plantes, les algues et certaines bactéries convertissent la lumière solaire en énergie chimique...",
            "links": ["https://fr.wikipedia.org/wiki/Photosynthèse"],
            "metadata": {"category": "Biologie", "updated": "2025-01-01"}
        },
        {
            "title": "Révolution industrielle",
            "content": "La Révolution industrielle désigne la transition vers de nouvelles processus de production manufacturière en Europe et en Amérique du Nord...",
            "links": ["https://fr.wikipedia.org/wiki/Révolution_industrielle"],
            "metadata": {"category": "Histoire", "updated": "2025-01-01"}
        },
        {
            "title": "Théorie de la relativité",
            "content": "La théorie de la relativité, élaborée par Albert Einstein, révolutionne notre compréhension de l'espace, du temps et de la gravitation...",
            "links": ["https://fr.wikipedia.org/wiki/Théorie_de_la_relativité"],
            "metadata": {"category": "Physique", "updated": "2025-01-01"}
        },
        {
            "title": "Cellule animale",
            "content": "La cellule animale est l'unité de base de la vie animale, caractérisée par un noyau délimité par une membrane, des organites comme les mitochondries...",
            "links": ["https://fr.wikipedia.org/wiki/Cellule_animale"],
            "metadata": {"category": "Biologie", "updated": "2025-01-01"}
        },
        # Ajoutez autant d'articles que nécessaire
    ]
    
    # Ajouter les articles à la base de données
    for article in articles:
        db_manager.add_article(
            title=article["title"],
            content=article["content"],
            links=article["links"],
            metadata=article["metadata"]
        )
    
    # Afficher les statistiques
    stats = db_manager.get_stats()
    print("Statistiques de la base de données:", stats)
    
    # Afficher les sujets
    topics = db_manager.get_topics()
    print("Sujets disponibles:", topics)
    
    # Lister tous les documents
    db_manager.list_all_documents()

if __name__ == "__main__":
    add_test_documents()