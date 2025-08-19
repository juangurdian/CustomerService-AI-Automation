from typing import List, Dict, Any, Optional
import httpx
import structlog
from openai import OpenAI
import google.generativeai as genai

from app.settings import settings, config

logger = structlog.get_logger()


class LLMService:
    def __init__(self):
        self.ai_mode = config.get("ai", {}).get("mode", "rag_only")
        self.model_name = config.get("ai", {}).get("model_name", "gpt-4o-mini")
        self.temperature = config.get("ai", {}).get("temperature", 0.2)
        self.max_tokens = config.get("ai", {}).get("max_tokens", 500)
        
        # Initialize clients
        self.openai_client = None
        self.groq_client = None
        
        if settings.openai_api_key:
            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        
        if settings.groq_api_key:
            self.groq_client = OpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
    
    async def generate_response(
        self, 
        user_message: str, 
        context_docs: List[Dict[str, Any]] = None,
        intent: str = "unknown"
    ) -> Dict[str, Any]:
        """Generate response using configured LLM"""
        
        if self.ai_mode == "rag_only":
            return self._generate_template_response(user_message, context_docs, intent)
        
        elif self.ai_mode == "api_llm":
            return await self._generate_api_response(user_message, context_docs, intent)
        
        elif self.ai_mode == "local_llm":
            return await self._generate_ollama_response(user_message, context_docs, intent)
        
        else:
            logger.warning(f"Unknown AI mode: {self.ai_mode}")
            return self._generate_template_response(user_message, context_docs, intent)
    
    def _generate_template_response(
        self, 
        user_message: str, 
        context_docs: List[Dict[str, Any]], 
        intent: str
    ) -> Dict[str, Any]:
        """Generate response using templates and RAG context"""
        
        if not context_docs:
            return {
                "text": config.get("responses", {}).get("fallback", "No entendí tu consulta."),
                "source": "fallback"
            }
        
        # Use the best matching document
        best_doc = context_docs[0]
        response_text = ""
        
        if best_doc["source"] == "faq":
            response_text = best_doc["metadata"]["answer"]
        elif best_doc["source"] == "menu":
            meta = best_doc["metadata"]
            response_text = f"{meta['name']} - ${meta['price']}"
            if meta.get("description"):
                response_text += f"\n{meta['description']}"
        elif best_doc["source"] == "document":
            response_text = best_doc["text"]
        
        return {
            "text": response_text,
            "source": "rag_template",
            "confidence": best_doc.get("score", 0.0)
        }
    
    async def _generate_api_response(
        self, 
        user_message: str, 
        context_docs: List[Dict[str, Any]], 
        intent: str
    ) -> Dict[str, Any]:
        """Generate response using API LLM"""
        
        # Build context from RAG results
        context = ""
        if context_docs:
            context = "\n\nContexto relevante:\n"
            for doc in context_docs[:3]:  # Use top 3 results
                if doc["source"] == "faq":
                    context += f"FAQ: {doc['metadata']['question']} -> {doc['metadata']['answer']}\n"
                elif doc["source"] == "menu":
                    meta = doc["metadata"]
                    context += f"Producto: {meta['name']} - ${meta['price']}"
                    if meta.get("description"):
                        context += f" - {meta['description']}"
                    context += "\n"
                else:
                    context += f"Info: {doc['text'][:200]}...\n"
        
        # Build prompt
        business_info = config.get("business", {})
        system_prompt = f"""Eres el asistente virtual de {business_info.get('name', 'nuestro negocio')}.

Información del negocio:
- Dirección: {business_info.get('address', 'No especificada')}
- Horarios: {business_info.get('hours', {})}
- Teléfono: {business_info.get('phone', 'No especificado')}

Instrucciones:
- Responde de forma {config.get('responses', {}).get('tone', 'amigable')} y directa
- Usa máximo 2-3 oraciones
- Si no tienes información específica, sugiere contactar directamente
- Para pedidos, guía al cliente paso a paso
{context}"""

        try:
            if "gpt" in self.model_name.lower() and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                text = response.choices[0].message.content
            
            elif "llama" in self.model_name.lower() and self.groq_client:
                response = self.groq_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                text = response.choices[0].message.content
            
            elif "gemini" in self.model_name.lower() and settings.gemini_api_key:
                model = genai.GenerativeModel('gemini-pro')
                full_prompt = f"{system_prompt}\n\nUsuario: {user_message}"
                response = model.generate_content(full_prompt)
                text = response.text
            
            else:
                raise Exception(f"No API client available for model: {self.model_name}")
            
            return {
                "text": text,
                "source": "api_llm",
                "model": self.model_name
            }
        
        except Exception as e:
            logger.error(f"Error generating API response: {e}")
            return self._generate_template_response(user_message, context_docs, intent)
    
    async def _generate_ollama_response(
        self, 
        user_message: str, 
        context_docs: List[Dict[str, Any]], 
        intent: str
    ) -> Dict[str, Any]:
        """Generate response using local Ollama"""
        
        try:
            # Build context similar to API response
            context = ""
            if context_docs:
                context = "\n\nContexto:\n"
                for doc in context_docs[:2]:
                    context += f"- {doc['text'][:150]}...\n"
            
            business_info = config.get("business", {})
            prompt = f"""Responde como asistente de {business_info.get('name')}.
            
Usuario: {user_message}
{context}

Respuesta (máximo 2 oraciones):"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.ollama_host}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "num_predict": self.max_tokens
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "text": result.get("response", "").strip(),
                        "source": "local_llm",
                        "model": self.model_name
                    }
                else:
                    raise Exception(f"Ollama API error: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error with Ollama: {e}")
            return self._generate_template_response(user_message, context_docs, intent)


# Global LLM service instance
llm_service = LLMService()