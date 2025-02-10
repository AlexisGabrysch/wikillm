from sklearn.ensemble import RandomForestClassifier
from itertools import product

def get_thresholds():
    """Get the thresholds for classifying students based on quiz scores."""
    return {
            "bad": 7,
            "neutral": 13,
            "good": 20
        }

def generate_recommendations(classifications):
    """Generate recommendations based on classifications using a machine learning model."""
    # Convert text levels to numerical values
    level_mapping = {
        "bad": 7,
        "neutral": 13,
        "good": 20,
        # Ajout des variations possibles pour gérer tous les cas
        "En difficulté": 7,
        "Niveau Correct": 13,
        "Déjà Prêt pour le Brevet": 20
    }

    # Prepare the input for prediction
    levels = [
        level_mapping.get(classifications.get("Histoire", "bad"), 7),
        level_mapping.get(classifications.get("SVT", "bad"), 7),
        level_mapping.get(classifications.get("Physique-chimie", "bad"), 7)
    ]

    # Generate all possible combinations
    X_train = list(product([7, 13, 20], repeat=3))
    
    # Define matching recommendations for each combination
    y_train = [
        # [7,7,7] - All bad
        "Revoir les bases de chaque matière.",
        # [7,7,13] - Histoire bad, SVT bad, PC neutral
        "Revoir les bases en Histoire et SVT, approfondir les notions en Physique-chimie.",
        # [7,7,20] - Histoire bad, SVT bad, PC good
        "Revoir les bases en Histoire et SVT. Continuer à exceller en Physique-chimie.",
        # [7,13,7] - Histoire bad, SVT neutral, PC bad
        "Revoir les bases en Histoire et Physique-chimie, approfondir les notions en SVT.",
        # [7,13,13] - Histoire bad, rest neutral
        "Revoir les bases en Histoire, approfondir les notions en SVT et Physique-chimie.",
        # [7,13,20] - Histoire bad, SVT neutral, PC good
        "Revoir les bases en Histoire. Approfondir les notions en SVT. Continuer à exceller en Physique-chimie.",
        # [7,20,7] - Histoire bad, SVT good, PC bad
        "Revoir les bases en Histoire et Physique-chimie. Continuer à exceller en SVT.",
        # [7,20,13] - Histoire bad, SVT good, PC neutral
        "Revoir les bases en Histoire. Continuer à exceller en SVT. Approfondir les notions en Physique-chimie.",
        # [7,20,20] - Histoire bad, rest good
        "Revoir les bases en Histoire. Continuer à exceller en SVT et Physique-chimie.",
        # [13,7,7] - Histoire neutral, rest bad
        "Approfondir les notions en Histoire. Revoir les bases en SVT et Physique-chimie.",
        # [13,7,13] - Histoire neutral, SVT bad, PC neutral
        "Revoir les bases en SVT. Approfondir les notions en Histoire et Physique-chimie.",
        # [13,7,20] - Histoire neutral, SVT bad, PC good
        "Revoir les bases en SVT. Approfondir les notions en Histoire. Continuer à exceller en Physique-chimie.",
        # [13,13,7] - Histoire neutral, SVT neutral, PC bad
        "Revoir les bases en Physique-chimie. Approfondir les notions en Histoire et SVT.",
        # [13,13,13] - All neutral
        "Approfondir les notions dans chaque matière.",
        # [13,13,20] - Histoire neutral, SVT neutral, PC good
        "Approfondir les notions en Histoire et SVT. Continuer à exceller en Physique-chimie.",
        # [13,20,7] - Histoire neutral, SVT good, PC bad
        "Revoir les bases en Physique-chimie. Approfondir les notions en Histoire. Continuer à exceller en SVT.",
        # [13,20,13] - Histoire neutral, SVT good, PC neutral
        "Approfondir les notions en Histoire et Physique-chimie. Continuer à exceller en SVT.",
        # [13,20,20] - Histoire neutral, rest good
        "Approfondir les notions en Histoire. Continuer à exceller en SVT et Physique-chimie.",
        # [20,7,7] - Histoire good, rest bad
        "Revoir les bases en SVT et Physique-chimie. Continuer à exceller en Histoire.",
        # [20,7,13] - Histoire good, SVT bad, PC neutral
        "Revoir les bases en SVT. Approfondir les notions en Physique-chimie. Continuer à exceller en Histoire.",
        # [20,7,20] - Histoire good, SVT bad, PC good
        "Revoir les bases en SVT. Continuer à exceller en Histoire et Physique-chimie.",
        # [20,13,7] - Histoire good, SVT neutral, PC bad
        "Revoir les bases en Physique-chimie. Approfondir les notions en SVT. Continuer à exceller en Histoire.",
        # [20,13,13] - Histoire good, rest neutral
        "Approfondir les notions en SVT et Physique-chimie. Continuer à exceller en Histoire.",
        # [20,13,20] - Histoire good, SVT neutral, PC good
        "Approfondir les notions en SVT. Continuer à exceller en Histoire et Physique-chimie.",
        # [20,20,7] - Histoire good, SVT good, PC bad
        "Revoir les bases en Physique-chimie. Continuer à exceller en Histoire et SVT.",
        # [20,20,13] - Histoire good, SVT good, PC neutral
        "Approfondir les notions en Physique-chimie. Continuer à exceller en Histoire et SVT.",
        # [20,20,20] - All good
        "Continuer à exceller dans chaque matière."
    ]

    # Ensure the number of samples in X_train and y_train are consistent
    assert len(X_train) == len(y_train), "Inconsistent number of samples in X_train and y_train"

    # Train the model
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    # Predict recommendations
    
    recommendation = model.predict([levels])[0]
    return recommendation









    
