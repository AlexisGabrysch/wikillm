import os
from typing import Any, List, Dict
from dotenv import load_dotenv, find_dotenv
import litellm  
from .metrics_database import RAGMetricsDatabase

import re
import numpy as np
from ecologits import EcoLogits
from .db import utils as db_utils
import time
from functools import wraps
# Charger les variables d'environnement
load_dotenv(find_dotenv())
print("Chargement des variables d'environnement...")

if os.getenv("MISTRAL_API_KEY") is None:
    raise ValueError("La clé d'API MISTRAL n'a pas été trouvée. Veuillez vérifier votre fichier .env.")
else:
    print("Clé d'API MISTRAL trouvée.")

def track_latency(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = func(self, *args, **kwargs)  # Pass self explicitly here.
        end_time = time.time()
        latency = end_time - start_time
        self.latency = latency
        return result
    return wrapper


class RAGPipeline:
    """Retrieval-Augmented Generation Pipeline for enhanced Q&A."""


    def __init__(
        self,
        generation_model: str,
        max_tokens: int = 2000,
        top_n: int = 1,
        temperature: float = 0.5
        
    ) -> None:
        self.llm = generation_model
        self.max_tokens = max_tokens
        self.top_n = top_n
        self.temperature = temperature
        EcoLogits.init(providers="litellm", electricity_mix_zone="FRA")
        self.metrics_db = RAGMetricsDatabase()
        self.quizdb = db_utils.QuizDatabase()

  


    def _get_energy_usage(self, response : litellm.ModelResponse) -> tuple[float, float]:
        energy_usage = getattr(response.impacts.energy.value, "min", response.impacts.energy.value)
        gwp = getattr(response.impacts.gwp.value, "min", response.impacts.gwp.value)
        return energy_usage, gwp
    
    def get_price_query(self, model: str, input_tokens: int, output_tokens: int) -> tuple[float, float]:
       
        pricing = {
            "ministral-8b-latest": {"input": 0.095, "output": 0.095},
            "mistral-large-latest": {"input": 1.92, "output": 5.75}}
        cost_input = (input_tokens / 1_000_000) * pricing[model]["input"]
        cost_output = (output_tokens / 1_000_000) * pricing[model]["output"]
        return cost_input, cost_output

 
 
   
    def build_prompt(self, context_course: List[str], topic: str, previous_questions: List[Dict[str, str]] = None, role: str = "assistant") -> List[Dict[str, str]]:
        """
        Construit un prompt pour générer une nouvelle question à choix multiples sur un sujet donné.
        Le prompt inclut des instructions pour varier la formulation et la difficulté des questions.
        
        Args:
            context_course (List[str]): Liste des éléments de contexte du cours.
            topic (str): Le sujet pour lequel générer la question.
            previous_questions (List[Dict[str, str]], optionnel): Liste de questions déjà posées pour éviter les répétitions.
            role (str): Le rôle pour lequel construire le prompt. Par défaut "assistant".
        
        Returns:
            List[Dict[str, str]]: Le prompt structuré au format (role, content).
        
        Raises:
            ValueError: Si le rôle spécifié n'est pas "assistant".
        """
        if role == "assistant":
            
            
            # Construction de l'historique des questions déjà posées, le cas échéant
            history_text = ""
            if previous_questions:
                history_text = "\nQuestions déjà posées:\n" + "\n".join(
                    [f"{i+1}. {q['question']}" for i, q in enumerate(previous_questions)]
                )
            
            # Assemblage du prompt complet avec une instruction pour varier la difficulté et la formulation
            prompt = [
                {"role": "system", "content": "Tu es un assistant pédagogique pour le programme de collège français."},
                {"role": "assistant", "content": (
                    f"Génère une nouvelle question à choix multiples sur le topic '{topic}' qui demande réflexion. "
                    "Essaie de varier la difficulté et la formulation par rapport aux questions déjà posées. "
                    "Si les questions précédentes étaient de difficulté standard, propose une question plus difficile "
                    "en approfondissant certains aspects ou en abordant des angles moins évidents."
                    "Tu ne dois pas répéter les questions déjà posées.\n\n"
                    "Tu dois respecter le format suivant :\n"
                    "--------------------------------------------------\n"
                    "Question: [Votre question ici]\n"
                    "1. [Première option]\n"
                    "2. [Deuxième option]\n"
                    "3. [Troisième option]\n"
                    "4. [Quatrième option]\n"
                    "Correct Answer: [Numéro de l'option correcte]\n"
                    "Explanation: [Explication détaillée ici]\n"
                    "Hint: [Indice utile ici]\n"
                    "--------------------------------------------------\n\n"
                    "Assure-toi que la question comporte exactement quatre options dont une seule est correcte, "
                    "et qu'un indice est fourni sans révéler la réponse."
                )},
                {"role": "user", "content": f"Contexte du cours : {', '.join(context_course)}' Questions deja générées :' {history_text}"},
            ]
            
            return prompt
        
        if role == "summary":
            prompt = [
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant pédagogique spécialisé dans le programme de collège français. "
                        "Ton objectif est de proposer un résumé clair, concis et structuré sur un sujet donné, "
                        "en veillant à expliquer les notions essentielles et à conclure de manière synthétique."
                    )
                },
                {
                    "role": "assistant",
                    "content": (
                        f"Génère un résumé clair et concis pour le chapitre ou sujet suivant : '{topic}'. "
                        f"Le résumé doit être complet et reformulé en deux ou trois paragraphes, en utilisant une liste à puces si nécessaire. "
                        "commencer par une brève introduction et se terminer par une conclusion concise."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Voici le contenu du cours : {', '.join(context_course)}. "
                        "Réduis-le à l'essentiel tout en conservant la cohérence et la fin du texte."
                    )
                },
            ]
            return prompt
        
        raise ValueError(f"Le rôle '{role}' n'est pas pris en charge. Utilisez 'assistant' ou 'summary'.")




    @track_latency
    def generate(self, prompt: List[Dict[str, str]]) -> litellm.ModelResponse:
        """
        Sends the prompt to the language model using default provider and model from self.
        """
        response = litellm.completion(
            model=f"mistral/{self.llm}",
            messages=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return response

    def metrics(self, response: litellm.ModelResponse) -> dict:
        energy_usage, gwp = self._get_energy_usage(response)
        # Use prompt_tokens and completion_tokens instead of non-existent input_tokens/output_tokens
        price_input, price_output = self.get_price_query(
            self.llm,
            response.usage.prompt_tokens,
            response.usage.completion_tokens
        )
        txt = response.choices[0].message.content
        latency = getattr(self, "latency", 0)
        
        return {
            "response": txt,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "energy_usage": energy_usage,
            "gwp": gwp,
            "price_input": price_input,
            "price_output": price_output,
            "latency": latency
        }


    def fetch_context(self, topic: str) -> List[str]:
        """
        Fetches the context from the database based on the topic.
        """
        context = db_utils.get_contents_per_theme_as_dict(db_path='src/db/courses.db', theme=topic)
        return context
    
    
    
    def generate_summary(self,chapitre : str,  txt: str) -> str:
        prompt = self.build_prompt( context_course=[txt], topic=chapitre, role="summary")
        response = self.generate(prompt)
        metrics = self.metrics(response)
        print(metrics)
        self.metrics_db.insert_metric(
            input_tokens=metrics["prompt_tokens"],
            output_tokens=metrics["completion_tokens"],
            price_input=metrics["price_input"],
            price_output=metrics["price_output"],
            latency=metrics["latency"],
            gwp=metrics["gwp"],
            energy_usage=metrics["energy_usage"]
        )
        return response.choices[0].message.content
        


    def generate_quizz_questions(self, topic: str, nbr_questions: int = 5) -> List[Dict[str, Any]]:
        context_course_dict = self.fetch_context(topic)
        
        if not context_course_dict:
            raise ValueError(f"Aucun contexte trouvé pour le topic '{topic}'.")

        generated_questions = []
        for i in range(nbr_questions):
            print(f"Generating question {i}...")
            idx = np.random.randint(0, len(context_course_dict))
            context_course = list(context_course_dict.keys())[idx]

            prompt = self.build_prompt(
                context_course=[context_course],  # Expecting a List[str]
                topic=topic, 
                previous_questions=generated_questions, 
                role="assistant"
            )
            response = self.generate(prompt=prompt)
            metrics = self.metrics(response)
            print(metrics)
            self.metrics_db.insert_metric(
                input_tokens=metrics["prompt_tokens"],
                output_tokens=metrics["completion_tokens"],
                price_input=metrics["price_input"],
                price_output=metrics["price_output"],
                latency=metrics["latency"],
                gwp=metrics["gwp"],
                energy_usage=metrics["energy_usage"]
            )
            # Parse la question générée
            new_question = self.parse_questions(response.choices[0].message.content)
            # Si le parse retourne plusieurs questions, prendre la première
            if new_question and isinstance(new_question, list):
                generated_questions.append(new_question[0])
            else:
                # En cas d'erreur de format, on ajoute une question d'erreur pour éviter la répétition
                generated_questions.append({
                    "question": "Erreur de format lors de la génération de la question.",
                    "options": [],
                    "correct_index": -1,
                    "explanation": "",
                    "hint": ""
                })
        return generated_questions
            
       
    
    def parse_questions(self,content: str) -> list:
        """
        Parse le contenu généré par le modèle et extrait une liste de questions formatées.
        
        Chaque question doit suivre le format :
            Question: [Votre question ici]
            1. [Première option]
            2. [Deuxième option]
            3. [Troisième option]
            4. [Quatrième option]
            Correct Answer: [Numéro de l'option correcte]
            Explanation: [Explication détaillée ici]
            Hint: [Indice utile ici]
            
        Args:
            content (str): Le texte contenant une ou plusieurs questions.
            
        Returns:
            list: Une liste de dictionnaires avec les clés "question", "options",
                "correct_index", "explanation" et "hint".
                Si aucun format n'est détecté, une liste contenant un message d'erreur est retournée.
        """
        pattern = re.compile(
            r"Question:\s*(.*?)\s*\r?\n+"
            r"1\.\s*(.*?)\s*\r?\n+"
            r"2\.\s*(.*?)\s*\r?\n+"
            r"3\.\s*(.*?)\s*\r?\n+"
            r"4\.\s*(.*?)\s*\r?\n+"
            r"Correct Answer:\s*(\d+)\s*\r?\n+"
            r"Explanation:\s*(.*?)\s*\r?\n+"
            r"Hint:\s*(.*?)(?:\r?\n|$)",
            re.DOTALL | re.IGNORECASE
        )
        
        questions = []
        for match in pattern.finditer(content.strip()):
            question_text, opt1, opt2, opt3, opt4, correct_str, explanation, hint = match.groups()
            correct_index = int(correct_str) - 1  # Passage en index 0-based
            questions.append({
                "question": question_text.strip(),
                "options": [opt1.strip(), opt2.strip(), opt3.strip(), opt4.strip()],
                "correct_index": correct_index,
                "explanation": explanation.strip(),
                "hint": hint.strip()
            })
        
        if not questions:
            # Si aucun match n'est trouvé, retourner un message d'erreur
            return [{
                "question": "Format incorrect ou information incomplète.",
                "options": [],
                "correct_index": -1,
                "explanation": "",
                "hint": ""
            }]
        
        return questions

    def save_questions(self, questions: List[Dict[str, Any]], subject: str, chapter: str) -> None:
        """
        Enregistre les questions générées dans la base de données.
        
        Args:
            questions (List[Dict[str, Any]]): Une liste de dictionnaires contenant les questions à enregistrer.
        """
        for question in questions:
                # Récupère les options, et complète avec "N/A" si moins de 4 options sont disponibles.
                options = question.get("options", [])
                while len(options) < 4:
                    options.append("N/A")
                
                self.quizdb.insert_question(
                    question_text=question["question"],
                    option1=options[0],
                    option2=options[1],
                    option3=options[2],
                    option4=options[3],
                    correct_index=question.get("correct_index", -1),
                    subject=subject,
                    chapter=chapter,
                    hint=question.get("hint", ""),
                    explanation=question.get("explanation", "")
                )
        print(f'Questions {chapter}  enregistrées dans la base de données.')
            
    
    

if __name__ == "__main__":
    pipeline = RAGPipeline(
        generation_model="mistral-large-latest",
        max_tokens=1500,
        temperature=0.8,
        top_n=1
    )
    # # quizz = pipeline.generate_quizz_questions("L'Europe, un théâtre majeur des guerres totales (1914-1945)", nbr_questions=10)
    # # quizz = pipeline.generate_quizz_questions("Le monde depuis 1945", nbr_questions=10)
    # quizz = pipeline.generate_quizz_questions("Françaises et Français dans une République repensée", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="Histoire", chapter="Françaises et Français dans une République repensée")
    
    # quizz = pipeline.generate_quizz_questions("Le monde depuis 1945", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="Histoire", chapter="Le monde depuis 1945")
    
    # quizz = pipeline.generate_quizz_questions("L'Europe, un théâtre majeur des guerres totales (1914-1945)", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="Histoire", chapter="L'Europe, un théâtre majeur des guerres totales (1914-1945)")
    
    # quizz = pipeline.generate_quizz_questions("La planète Terre, l'environnement et l'action humaine", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="SVT", chapter="La planète Terre, l'environnement et l'action humaine")
    
    # quizz = pipeline.generate_quizz_questions("Le climat et la météorologie", nbr_questions=7)
    # pipeline.save_questions(quizz, subject="SVT", chapter="Le climat et la météorologie")

    # quizz = pipeline.generate_quizz_questions("L'exploitation des ressources naturelles", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="SVT", chapter="L'exploitation des ressources naturelles")  
    
    # quizz = pipeline.generate_quizz_questions("Écosystèmes et activités humaines", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="SVT", chapter="Écosystèmes et activités humaines")  
    
    # quizz = pipeline.generate_quizz_questions("Nutrition et organisation des animaux", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="SVT", chapter="Nutrition et organisation des animaux")  
    
    # quizz = pipeline.generate_quizz_questions("Reproduction sexuée et asexuée : dynamique des populations", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="SVT", chapter="Reproduction sexuée et asexuée : dynamique des populations")  
    
    # quizz = pipeline.generate_quizz_questions("La parenté des êtres vivants", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="SVT", chapter="La parenté des êtres vivants")  
    
#     quizz = pipeline.generate_quizz_questions("Diversité et stabilité génétique des êtres vivants", nbr_questions=10)
#     pipeline.save_questions(quizz, subject="SVT", chapter="Diversité et stabilité génétique des êtres vivants")  
    
#     quizz = pipeline.generate_quizz_questions("Le fonctionnement de l'organisme", nbr_questions=10)
#     pipeline.save_questions(quizz, subject="SVT", chapter="Le fonctionnement de l'organisme")  
    
#     quizz = pipeline.generate_quizz_questions("Système nerveux et comportement responsable", nbr_questions=10)
#     pipeline.save_questions(quizz, subject="SVT", chapter="Système nerveux et comportement responsable")  

#     quizz = pipeline.generate_quizz_questions("Alimentation et digestion", nbr_questions=10)
#     pipeline.save_questions(quizz, subject="SVT", chapter="Alimentation et digestion")  

#     quizz = pipeline.generate_quizz_questions("Le monde microbien et la santé", nbr_questions=10)
#     pipeline.save_questions(quizz, subject="SVT", chapter="Le monde microbien et la santé")  
    
#     quizz = pipeline.generate_quizz_questions("Reproduction et comportements sexuels responsables", nbr_questions=10)
#     pipeline.save_questions(quizz, subject="SVT", chapter="Reproduction et comportements sexuels responsables")     
# ###
#     quizz = pipeline.generate_quizz_questions("Les états de la matière", nbr_questions=10)
#     pipeline.save_questions(quizz, subject="Physique-chimie", chapter="Les états de la matière")     
 
#     quizz = pipeline.generate_quizz_questions("Les transformations chimiques", nbr_questions=10)
#     pipeline.save_questions(quizz, subject="Physique-chimie", chapter="Les transformations chimiques")  
    
    # quizz = pipeline.generate_quizz_questions("L'organisation de la matière dans l'Univers", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="Physique-chimie", chapter="L'organisation de la matière dans l'Univers")  

    # quizz = pipeline.generate_quizz_questions("Mouvements et interactions", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="Physique-chimie", chapter="Mouvements et interactions")  
 
    # quizz = pipeline.generate_quizz_questions("L'énergie", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="Physique-chimie", chapter="L'énergie")  
    
    # quizz = pipeline.generate_quizz_questions("Les circuits électriques", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="Physique-chimie", chapter="Les circuits électriques")  
    
    # quizz = pipeline.generate_quizz_questions("Les signaux", nbr_questions=10)
    # pipeline.save_questions(quizz, subject="Physique-chimie", chapter="Les signaux")    
 
    
    print("Génération de questions terminée.")