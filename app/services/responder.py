from typing import Dict, Any, List, Optional
import json
import structlog
from datetime import datetime

from app.services.rag import rag_service
from app.services.nlu import nlu_service
from app.services.llm import llm_service
from app.services.flows import flow_engine
from app.settings import config

logger = structlog.get_logger()


class ResponseOrchestrator:
    def __init__(self):
        self.config = config
    
    async def process_message(
        self,
        text: str,
        user_id: str,
        channel: str,
        meta: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Main orchestrator for processing incoming messages"""
        
        logger.info(f"Processing message from {user_id} on {channel}: {text[:50]}...")
        
        # Check if user has an active flow
        if flow_engine.is_flow_active(user_id):
            return await self._handle_flow_message(user_id, text)
        
        # Check for flow triggers
        flow_trigger = self._check_flow_triggers(text)
        if flow_trigger:
            return flow_engine.start_flow(flow_trigger, user_id, channel)
        
        # Perform RAG search
        rag_results = rag_service.search(
            text,
            top_k=config.get("retrieval", {}).get("top_k", 4),
            min_score=config.get("retrieval", {}).get("min_score", 0.5)
        )
        
        # Detect intent
        intent = nlu_service.detect_intent(text, rag_results)
        confidence = nlu_service.get_confidence_score(text, intent)
        
        # Generate response
        response_data = await self._generate_response(text, intent, rag_results)
        
        # Add quick replies based on intent
        quick_replies = self._get_quick_replies(intent, response_data)
        
        # Build trace for debugging
        trace = {
            "intent": intent,
            "confidence": confidence,
            "source": response_data.get("source", "unknown"),
            "rag_hits": len(rag_results),
            "rag_results": [
                {
                    "text": r["text"][:100] + "..." if len(r["text"]) > 100 else r["text"],
                    "score": r["score"],
                    "source": r["source"]
                }
                for r in rag_results[:3]
            ]
        }
        
        return {
            "reply": response_data["text"],
            "quick_replies": quick_replies,
            "trace": trace,
            "intent": intent,
            "source": response_data.get("source", "unknown")
        }
    
    async def _handle_flow_message(self, user_id: str, text: str) -> Dict[str, Any]:
        """Handle message within an active flow"""
        
        # Check for flow cancellation
        if text.lower() in ["cancelar", "cancel", "salir", "exit", "stop"]:
            flow_engine.cancel_flow(user_id)
            return {
                "reply": "Operación cancelada. ¿En qué más te puedo ayudar?",
                "quick_replies": config.get("responses", {}).get("quick_replies", []),
                "trace": {"intent": "cancel_flow", "source": "flow_engine"}
            }
        
        return flow_engine.process_message(user_id, text)
    
    def _check_flow_triggers(self, text: str) -> Optional[str]:
        """Check if message should trigger a flow"""
        text_lower = text.lower()
        
        # Order flow triggers
        order_keywords = ["quiero", "ordenar", "pedido", "pedir", "comprar", "solicitar"]
        if any(keyword in text_lower for keyword in order_keywords):
            if config.get("orders", {}).get("enable", True):
                return "quick_order"
        
        return None
    
    async def _generate_response(
        self,
        text: str,
        intent: str,
        rag_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate appropriate response based on intent and context"""
        
        # Handle greeting
        if intent == "greeting":
            business_name = config.get("business", {}).get("name", "nuestro negocio")
            greeting = config.get("responses", {}).get("greeting", "¡Hola!")
            return {
                "text": greeting.format(business_name=business_name),
                "source": "template"
            }
        
        # Handle goodbye
        if intent == "goodbye":
            return {
                "text": "¡Gracias por contactarnos! Que tengas un buen día.",
                "source": "template"
            }
        
        # Use LLM service for complex responses
        if rag_results or intent in ["faq", "menu"]:
            return await llm_service.generate_response(text, rag_results, intent)
        
        # Fallback response
        fallback = config.get("responses", {}).get("fallback", "No entendí tu consulta.")
        return {
            "text": fallback,
            "source": "fallback"
        }
    
    def _get_quick_replies(self, intent: str, response_data: Dict[str, Any]) -> List[str]:
        """Get appropriate quick replies based on intent"""
        
        if intent == "greeting":
            return config.get("responses", {}).get("quick_replies", [])
        
        elif intent == "menu":
            return ["Hacer pedido", "Ver horarios", "Ubicación"]
        
        elif intent == "faq":
            return ["Ver menú", "Hacer pedido", "Más información"]
        
        elif intent == "order":
            return ["Continuar pedido", "Ver menú", "Cancelar"]
        
        else:
            return ["Ver menú", "Horarios", "Contacto"]
    
    def get_business_hours_text(self) -> str:
        """Get formatted business hours"""
        hours = config.get("business", {}).get("hours", {})
        if not hours:
            return "Consulta nuestros horarios directamente."
        
        text = "Nuestros horarios:\n"
        for day, time in hours.items():
            day_name = {
                "mon_fri": "Lunes a Viernes",
                "sat": "Sábado", 
                "sun": "Domingo"
            }.get(day, day.title())
            text += f"• {day_name}: {time}\n"
        
        return text.strip()
    
    def get_business_info_text(self) -> str:
        """Get formatted business information"""
        business = config.get("business", {})
        
        info = f"📍 {business.get('name', 'Nuestro negocio')}\n"
        
        if business.get("address"):
            info += f"Dirección: {business['address']}\n"
        
        if business.get("phone"):
            info += f"Teléfono: {business['phone']}\n"
        
        if business.get("email"):
            info += f"Email: {business['email']}\n"
        
        return info.strip()


# Global response orchestrator instance
response_orchestrator = ResponseOrchestrator()