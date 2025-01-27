import os
from typing import Any, List, Dict
import uuid
import numpy as np
from numpy.typing import NDArray
from dotenv import load_dotenv, find_dotenv
import litellm  # Change this line to import litellm directly
from .utils import track_latency
from .database import DatabaseManager
import re
import streamlit as st
import asyncio

load_dotenv(find_dotenv())
print("Chargement des variables d'environnement...")
print(os.getenv("MISTRAL_API_KEY"))

class RAGPipeline:
    """Retrieval-Augmented Generation Pipeline for enhanced Q&A."""


    def __init__(
        self,
        generation_model: str,
        role_prompt: str,
        db_path: str,
        max_tokens: int,
        temperature: float,
        top_n: int = 1,
    ):
        self.llm = generation_model
        self.role_prompt = role_prompt
        self.db_manager = DatabaseManager(db_path)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_n = top_n

    def add_document(self, title: str, content: str, links: List[str] = None, metadata: Dict[str, Any] = None) -> None:
        """Adds a document to the database."""
        self.db_manager.add_article(title, content, links, metadata)
        
    @st.cache_data(ttl=100)  # Cache pendant 10 minutes
    def fetch_context_by_topic_cached(_self, topic: str) -> List[str]:
        return _self.fetch_context_by_topic(topic)
    
    def fetch_context_by_topic(self, topic: str) -> List[str]:
        """Retrieves the content of the article based on the topic."""
        content = self.db_manager.query_article(topic)
        if isinstance(content, str) and content != "Article non trouvé.":
            return [content]
        return []

    def get_cosim(self, a: NDArray[np.float32], b: NDArray[np.float32]) -> float:
        """
        Calculates the cosine similarity between two vectors.

        Args:
            a (NDArray[np.float32]): The first vector.
            b (NDArray[np.float32]): The second vector.

        Returns:
            float: The cosine similarity between the two vectors.
        """
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def get_top_similarity(
        self,
        embedding_query: NDArray[np.float32],
        embedding_chunks: NDArray[np.float32],
        corpus: List[str],
    ) -> List[str]:
        """
        Retrieves the top N most similar documents from the corpus based on the query's embedding.

        Args:
            embedding_query (NDArray[np.float32]): The embedding of the query.
            embedding_chunks (NDArray[np.float32]): A NumPy array of embeddings for the documents in the corpus.
            corpus (List[str]): A list of documents (strings) corresponding to the embeddings in `embedding_chunks`.

        Returns:
            List[str]: A list of the most similar documents from the corpus, ordered by similarity to the query.
        """
        cos_dist_list = np.array(
            [
                self.get_cosim(embedding_query, embed_doc)
                for embed_doc in embedding_chunks
            ]
        )
        indices_of_max_values = np.argsort(cos_dist_list)[-self.top_n:][::-1]
        return [corpus[i] for i in indices_of_max_values]

    def build_prompt(
        self, context: List[str], history: List[Dict[str, str]], query: str
    ) -> List[Dict[str, str]]:
        """
        Builds a prompt string for a conversational agent based on the given context and query.

        Args:
            context (List[str]): The context information, typically extracted from books or other sources.
            history (List[Dict[str, str]]): The conversation history.
            query (str): The user's query or question.

        Returns:
            List[Dict[str, str]]: The RAG prompt in the OpenAI format
        """
        context_joined = "\n".join(context)
        system_prompt = self.role_prompt
        history_text = f"# Historique de conversation:\n" + "\n".join(
            [f"{msg['role'].capitalize()} : {msg['content']}" for msg in history]
        )
        context_prompt = f"""Tu disposes de la section "Contexte" pour t'aider à répondre aux questions.
# Contexte:
{context_joined}
"""
        query_prompt = f"""# Question:
{query}

# Réponse:
"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": history_text},
            {"role": "system", "content": context_prompt},
            {"role": "user", "content": query_prompt},
        ]

    @track_latency
    def generate_response(self, prompt: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Generates a response using the Mistral LLM via litellm.

        Args:
            prompt (List[Dict[str, str]]): The prompt messages to send to the model.

        Returns:
            Dict[str, Any]: The response from the model.
        """
        try:
            modified_prompt = prompt + [{
                "role": "system",
                "content": """Format your response as follows:
    Question: [Your question here]
    1. [First option]
    2. [Second option]
    3. [Third option]
    4. [Fourth option]
    Correct Answer: [Number of correct option]
    Explanation: [Detailed explanation here]"""
            }]
            
            response = litellm.completion(
                model=f"mistral/{self.llm}",
                messages=modified_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            # Extract content from response
            content = response.choices[0].message.content
            
            # Format response
            formatted_response = {
                "choices": [{
                    "message": {
                        "content": content
                    }
                }],
                "usage": response.usage if hasattr(response, 'usage') else None
            }
            
            return formatted_response
            
        except Exception as e:
            print(f"Erreur lors de l'appel à litellm : {e}")
            return {
                "choices": [
                    {
                        "message": {
                            "content": """Question: Erreur de génération
    1. Option A
    2. Option B
    3. Option C
    4. Option D
    Correct Answer: 1
    Explanation: Une erreur s'est produite lors de la génération de la question."""
                        }
                    }
                ]
            }

    def parse_quiz_response(self,content: str) -> dict:
        """
        Parses the LLM response to extract question, options, correct answer, and explanation.

        Args:
            content (str): The raw response content from the LLM.

        Returns:
            dict: Containing 'question', 'options', 'correct_index', and 'explanation'.
        """
        print(content)
        pattern = re.compile(
            r"Question:\s*(.*?)\s*\r?\n+"
            r"1\.\s*(.*?)\s*\r?\n+"
            r"2\.\s*(.*?)\s*\r?\n+"
            r"3\.\s*(.*?)\s*\r?\n+"
            r"4\.\s*(.*?)\s*\r?\n+"
            r"Correct Answer:\s*(\d+)\s*\r?\n+"
            r"Explanation:\s*(.*)", re.DOTALL | re.IGNORECASE
        )
        match = pattern.match(content.strip())
        if not match:
            return {
                "question": "Format incorrect ou information incomplète.",
                "options": [],
                "correct_index": -1,
                "explanation": ""
            }

        question, opt1, opt2, opt3, opt4, correct_str, explanation = match.groups()
        correct_index = int(correct_str) - 1  # 0-based index

        return {
            "question": question.strip(),
            "options": [opt1.strip(), opt2.strip(), opt3.strip(), opt4.strip()],
            "correct_index": correct_index,
            "explanation": explanation.strip()
        }
        
    @track_latency
    def generate_hint(self, question: str, context: List[str]) -> str:
        """
        Génère un indice pour la question donnée sans révéler la réponse.
        """
        try:
            prompt = [
                {"role": "system", "content": self.role_prompt},
                {"role": "system", "content": "\n".join(context)},
                {
                    "role": "user",
                    "content": f"Fournis un indice utile pour la question suivante sans révéler la réponse : {question}"
                },
            ]

            response = litellm.completion(
                model=f"mistral/{self.llm}",
                messages=prompt,
                max_tokens=50,  # Ajustez selon vos besoins
                temperature=self.temperature,
            )

            hint = response.choices[0].message.content.strip()
            return hint

        except Exception as e:
            print(f"Erreur lors de la génération de l'indice : {e}")
            return "Désolé, un indice n'est pas disponible pour le moment."
    def generate_quiz_question(self, topic: str) -> Dict[str, Any]:
        """
        Generates a quiz question with four options based on the given topic.

        Args:
            topic (str): The topic for which to generate the quiz question.

        Returns:
            Dict[str, Any]: A dictionary containing the question, options, and the index of the correct answer.
        """
        context = self.fetch_context_by_topic(topic)
        if not context:
            return {"question": "Aucune information trouvée sur ce sujet.", "options": [], "correct_index": -1}

        # Construire le prompt pour générer une question à choix multiples
        query = f"Créer une question à choix multiples sur le sujet suivant : {topic} avec quatre options, dont une seule est correcte."
        prompt = self.build_prompt(context=context, history=[], query=query)
        response = self.generate_response(prompt=prompt)
        response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        quiz_data = self.parse_quiz_response(response_content)
        return quiz_data
    
    
    async def generate_quiz_question_async(self, topic: str) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_quiz_question, topic)
    
    
    def __call__(self, query: str, history: List[Dict[str, str]]) -> str:
        """
        Handles the RAG pipeline for a given query.

        Args:
            query (str): The user query to be processed.
            history (List[Dict[str, str]]): A list of dictionaries containing the conversation history.

        Returns:
            str: The generated response from the model.
        """
        chunks = self.db_manager.query_articles(query_texts=[query], n_results=self.top_n)
        print("Chunks retrieved!")
        if not chunks or not chunks.get("documents"):
            return "Aucun document pertinent trouvé dans la base de données."

        chunks_list: List[str] = chunks["documents"][0]
        print("Building prompt...")
        prompt_rag = self.build_prompt(
            context=chunks_list, history=history, query=query
        )
        response = self.generate_response(prompt=prompt_rag)
        # Stocker la requête dans la base de données si nécessaire
        # self.db_manager.add_query(query=response)
        ai_response = response.get("choices", [{}])[0].get("message", {}).get("content", "Je n'ai pas compris votre demande.")
        return ai_response

    def print_db_stats(self):
        """Prints the database statistics."""
        stats = self.db_manager.get_stats()
        print("Statistiques de la base de données:", stats)
