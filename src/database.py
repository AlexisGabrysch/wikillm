import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np

# Initialiser le modèle SentenceTransformer une seule fois
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def get_embedding(documents: List[str]) -> np.ndarray:
    """
    Génère des embeddings pour une liste de documents en utilisant un modèle pré-entraîné SentenceTransformer.

    Args:
        documents (List[str]): Une liste de chaînes de caractères (documents) pour lesquels les embeddings doivent être générés.

    Returns:
        np.ndarray: Un tableau NumPy contenant les embeddings pour chaque document.
    """
    if isinstance(documents, str):
        documents = [documents]
    return model.encode(documents).astype(np.float32)

class CustomEmbeddingFunction:
    def __init__(self, embed_fn, dimension: int):
        self.embed_fn = embed_fn
        self.dimension = dimension

    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Génère les embeddings pour une liste de documents.

        Args:
            input (List[str]): Une liste de chaînes de caractères (documents).

        Returns:
            List[List[float]]: Une liste d'arrays représentant les embeddings.
        """
        embeddings = self.embed_fn(input)
        return embeddings.tolist()

class DatabaseManager:
    def __init__(self, db_path="./chromadb_data"):
        # Créer une fonction d'embedding personnalisée
        embedding_function = CustomEmbeddingFunction(
            embed_fn=get_embedding,
            dimension=384  # Assurez-vous que la dimension correspond au modèle utilisé
        )
        
        # Initialiser le client ChromaDB avec la fonction d'embedding personnalisée
        self.client = chromadb.PersistentClient(
            path=db_path,  # Assurez-vous que le chemin est correct
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Créer ou obtenir la collection avec la fonction d'embedding personnalisée
        self.collection = self.client.get_or_create_collection(
            name="wikipedia_articles",
            embedding_function=embedding_function,
        )

    def add_article(self, title: str, content: str, links: List[str] = None, metadata: Dict[str, Any] = None) -> None:
        if metadata is None:
            metadata = {}
        metadata["title"] = title
        if links:
            metadata["links"] = ", ".join(links)  # Convertir la liste en chaîne séparée par des virgules
        self.collection.add(documents=[content], metadatas=[metadata], ids=[title])

    def query_article(self, title: str) -> str:
        results = self.collection.query(query_texts=[title], n_results=1)
        if results["documents"] and results["documents"][0]:
            return results["documents"][0][0]  # Accéder correctement au premier résultat
        return "Article non trouvé."

    def get_stats(self) -> Dict[str, Any]:
        try:
            num_documents = self.collection.count()
            return {"num_documents": num_documents}
        except AttributeError:
            print("La méthode 'count' n'est pas disponible. Veuillez vérifier la documentation de ChromaDB.")
            return {"num_documents": "Inconnu"}

    def get_topics(self) -> List[str]:
        try:
            # Récupérer tous les documents en utilisant une requête vide
            results = self.collection.query(query_texts=[""], n_results=6)
            metadatas = results.get("metadatas", [[]])[0]
            titles = {metadata.get("title") for metadata in metadatas if "title" in metadata}
            return list(titles)
        except Exception as e:
            print(f"Erreur lors de la récupération des sujets : {e}")
            return []

    def list_all_documents(self) -> None:
        try:
            results = self.collection.query(query_texts=[""], n_results=6)
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            for doc, meta in zip(documents, metadatas):
                print(f"Titre: {meta.get('title', 'Pas de Titre')}, Contenu: {doc[:100]}...")
        except Exception as e:
            print(f"Erreur lors de la liste des documents: {e}")