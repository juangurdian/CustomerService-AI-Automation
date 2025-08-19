import re
from typing import Dict, List, Optional, Any
import structlog
from app.settings import config

logger = structlog.get_logger()


class NLUService:
    def __init__(self):
        self.intent_rules = {
            "greeting": [
                r"\b(hola|buenos?|buenas?|saludos?|hi|hello)\b",
                r"\b(qué tal|cómo está|cómo están)\b"
            ],
            "faq": [
                r"\b(horario|abren|cierran|cuando|hora)\b",
                r"\b(ubicación|dirección|donde|dónde)\b",
                r"\b(teléfono|contacto|número)\b",
                r"\b(delivery|envío|reparto)\b",
                r"\b(pago|pagos|efectivo|tarjeta)\b"
            ],
            "menu": [
                r"\b(menú|menu|carta|precios?|precio)\b",
                r"\b(qué tienen|qué hay|productos?|comida)\b",
                r"\b(sabores?|opciones?|variedades?)\b",
                r"\b(promoción|promociones|ofertas?|descuento)\b",
                r"\b(especialidad|recomiendan|mejor)\b"
            ],
            "order": [
                r"\b(quiero|ordenar|pedido|pedir|solicitar)\b",
                r"\b(comprar|llevar|para llevar)\b",
                r"\b(cuánto cuesta|cuánto vale|precio de)\b"
            ],
            "complaint": [
                r"\b(problema|queja|reclamo|malo|mala)\b",
                r"\b(no funciona|no sirve|error)\b",
                r"\b(demora|tardó|lento|espera)\b"
            ],
            "goodbye": [
                r"\b(adiós|chao|bye|hasta luego|gracias)\b",
                r"\b(nos vemos|hasta pronto)\b"
            ]
        }
    
    def detect_intent(self, text: str, rag_results: Optional[List[Dict]] = None) -> str:
        """Detect intent using rules and RAG context"""
        text_lower = text.lower()
        
        # Check rule-based intents
        for intent, patterns in self.intent_rules.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    logger.debug(f"Detected intent '{intent}' via rule: {pattern}")
                    return intent
        
        # Check RAG results for additional context
        if rag_results:
            sources = [r.get("source", "") for r in rag_results]
            if "faq" in sources:
                return "faq"
            elif "menu" in sources:
                return "menu"
        
        # Default intent
        return "unknown"
    
    def extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """Extract entities based on intent"""
        entities = {}
        text_lower = text.lower()
        
        if intent == "order":
            # Extract quantities
            qty_match = re.search(r'(\d+)\s*(unidades?|piezas?|porciones?)?', text_lower)
            if qty_match:
                entities["quantity"] = int(qty_match.group(1))
            
            # Extract product names (simple approach)
            # This could be enhanced with better NER
            products = self._extract_product_mentions(text)
            if products:
                entities["products"] = products
        
        elif intent == "faq":
            # Extract time-related entities
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', text_lower)
            if time_match:
                entities["time"] = time_match.group(0)
        
        return entities
    
    def _extract_product_mentions(self, text: str) -> List[str]:
        """Extract potential product mentions from text"""
        # This is a simple implementation
        # In production, you'd want to match against actual product names
        common_products = [
            "pizza", "hamburguesa", "taco", "burrito", "quesadilla",
            "café", "refresco", "agua", "jugo", "cerveza",
            "ensalada", "sopa", "postre", "helado"
        ]
        
        mentioned = []
        text_lower = text.lower()
        
        for product in common_products:
            if product in text_lower:
                mentioned.append(product)
        
        return mentioned
    
    def get_confidence_score(self, text: str, intent: str) -> float:
        """Get confidence score for detected intent"""
        if intent == "unknown":
            return 0.1
        
        text_lower = text.lower()
        pattern_matches = 0
        total_patterns = 0
        
        if intent in self.intent_rules:
            patterns = self.intent_rules[intent]
            total_patterns = len(patterns)
            
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    pattern_matches += 1
        
        if total_patterns == 0:
            return 0.5
        
        base_confidence = pattern_matches / total_patterns
        # Boost confidence for exact matches
        if pattern_matches > 0:
            base_confidence = min(1.0, base_confidence + 0.3)
        
        return base_confidence


# Global NLU service instance
nlu_service = NLUService()