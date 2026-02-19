"""
Module de Templates de Prompt
Templates de prompts système et utilisateur pour différents modes de consultation.
"""

from typing import Dict, Any, List


class PromptTemplates:
    """
    Templates de prompts centralisés pour les modes de consultation LLM.
    
    Tous les prompts sont en Français et orientés vers des décisions actionnables.
    """
    
    @staticmethod
    def get_system_prompt(mode: str) -> str:
        """
        Obtenir le prompt système pour un mode de consultation.
        
        Args:
            mode: Mode de consultation (compare, budget, policy, free)
        
        Returns:
            Chaîne du prompt système
        """
        prompts = {
            "compare": (
                "Tu es un expert en voyages qui compare des offres de vol. "
                "Ta mission est de fournir une analyse comparative structurée et claire. "
                "Présente les résultats sous forme de tableau comparatif suivi d'une recommandation. "
                "Évalue: prix, durée, escales, flexibilité (bagages et remboursement). "
                "Ton ton est professionnel mais accessible. "
                "Réponds en français, sois concis (max 300 mots)."
            ),
            "budget": (
                "Tu es un conseiller voyage spécialisé dans l'optimisation budgétaire. "
                "Propose EXACTEMENT 3 options adaptées au budget donné: "
                "1) Économique (prix minimal), 2) Équilibré (compromis prix/confort), 3) Confort (qualité maximale). "
                "Pour chaque option, donne le prix estimé et justifie brièvement. "
                "Ton ton est pratique et orienté décision. "
                "Réponds en français, sois concis (max 250 mots)."
            ),
            "policy": (
                "Tu es un expert qui vulgarise les politiques de voyage complexes. "
                "Fournis un résumé clair de la politique mentionnée, suivi de 3-5 points clés. "
                "Explique les implications pratiques pour le voyageur. "
                "Utilise des listes à puces pour la clarté. "
                "Ton ton est pédagogique et rassurant. "
                "Réponds en français, sois concis (max 300 mots)."
            ),
            "free": (
                "Tu es un assistant voyage intelligent qui aide aux décisions pratiques. "
                "Réponds de manière claire et actionnable. "
                "Si la question est vague, pose 1-2 questions de clarification max. "
                "Privilégie les conseils concrets plutôt que les généralités. "
                "Ton ton est amical mais professionnel. "
                "Réponds en français, sois concis (max 300 mots)."
            )
        }
        
        return prompts.get(mode, prompts["free"])
    
    @staticmethod
    def build_user_prompt(mode: str, message: str, context: Dict[str, Any]) -> str:
        """
        Construire le prompt utilisateur en combinant message et contexte pour un mode.
        
        Args:
            mode: Mode de consultation
            message: Message/question de l'utilisateur
            context: Dictionnaire de contexte (offres, réservation, budget, etc.)
        
        Returns:
            Prompt utilisateur formaté
        """
        if mode == "compare":
            return PromptTemplates._build_compare_prompt(message, context)
        elif mode == "budget":
            return PromptTemplates._build_budget_prompt(message, context)
        elif mode == "policy":
            return PromptTemplates._build_policy_prompt(message, context)
        else:  # free
            return PromptTemplates._build_free_prompt(message, context)
    
    @staticmethod
    def _build_compare_prompt(message: str, context: Dict[str, Any]) -> str:
        """Construire le prompt pour la comparaison d'offres"""
        offers = context.get("selected_offers", [])
        
        if not offers:
            return message
        
        # Construire le tableau des offres
        offers_text = "Voici les offres à comparer:\n\n"
        for i, offer in enumerate(offers, 1):
            offers_text += f"**Offre {i} - {offer.get('airline', 'N/A')}**\n"
            offers_text += f"- Prix: {offer.get('price', 0)}€\n"
            offers_text += f"- Trajet: {offer.get('departure', 'N/A')} → {offer.get('destination', 'N/A')}\n"
            offers_text += f"- Dates: {offer.get('depart_date', 'N/A')} → {offer.get('return_date', 'N/A')}\n"
            offers_text += f"- Durée: {offer.get('duration_min', 0)} min\n"
            offers_text += f"- Escales: {offer.get('stops', 0)}\n"
            if offer.get('baggage'):
                offers_text += f"- Bagages: {offer['baggage']}\n"
            if offer.get('refund_policy'):
                offers_text += f"- Remboursement: {offer['refund_policy']}\n"
            offers_text += "\n"
        
        return f"{offers_text}\nQuestion: {message}"
    
    @staticmethod
    def _build_budget_prompt(message: str, context: Dict[str, Any]) -> str:
        """Construire le prompt pour la consultation budgétaire"""
        budget_max = context.get("budget_max")
        user_prefs = context.get("user_prefs", {})
        
        prompt = f"Budget maximum: {budget_max}€\n\n"
        
        if user_prefs:
            prompt += "Préférences:\n"
            for key, value in user_prefs.items():
                prompt += f"- {key}: {value}\n"
            prompt += "\n"
        
        prompt += f"Question: {message}"
        return prompt
    
    @staticmethod
    def _build_policy_prompt(message: str, context: Dict[str, Any]) -> str:
        """Construire le prompt pour l'explication de politique"""
        # Le texte de la politique est généralement dans le message lui-même
        return f"Politique à analyser:\n\n{message}"
    
    @staticmethod
    def _build_free_prompt(message: str, context: Dict[str, Any]) -> str:
        """Construire le prompt pour la consultation libre"""
        # Ajouter tout contexte disponible
        context_text = ""
        
        if context.get("user_prefs"):
            context_text += "\nContexte utilisateur:\n"
            for key, value in context["user_prefs"].items():
                context_text += f"- {key}: {value}\n"
        
        return f"{context_text}\n\nQuestion: {message}"
