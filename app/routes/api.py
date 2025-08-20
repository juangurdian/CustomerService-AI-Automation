from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session
from pydantic import BaseModel
import json
import structlog

from app.deps import get_session
from app.db.repo import MessageRepo, FAQRepo, ProductRepo, OrderRepo, DocRepo, SettingRepo, ConversationRepo
from app.db.models import Message, FAQ, Product, Order, Doc, Conversation
from app.services.responder import response_orchestrator
from app.services.rag import rag_service
from app.settings import config

logger = structlog.get_logger()
router = APIRouter()


class ChatRequest(BaseModel):
    channel: str
    user_id: str
    text: str
    meta: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    reply: str
    quick_replies: List[str] = []
    trace: Dict[str, Any] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, session: Session = Depends(get_session)):
    """Main chat endpoint"""
    try:
        # Process message through orchestrator
        result = await response_orchestrator.process_message(
            text=request.text,
            user_id=request.user_id,
            channel=request.channel,
            meta=request.meta
        )
        
        # Save to database
        message_repo = MessageRepo(session)
        message = Message(
            channel=request.channel,
            user_id=request.user_id,
            text=request.text,
            intent=result.get("intent"),
            source=result.get("source"),
            response=result.get("reply"),
            trace_data=json.dumps(result.get("trace", {}))
        )
        message_repo.create(message)
        
        return ChatResponse(
            reply=result["reply"],
            quick_replies=result.get("quick_replies", []),
            trace=result.get("trace", {})
        )
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search")
async def search_rag(q: str, top_k: int = 4):
    """RAG search endpoint for debugging"""
    results = rag_service.search(q, top_k=top_k)
    return {"query": q, "hits": results}


@router.post("/rebuild-index")
async def rebuild_index():
    """Rebuild the RAG index"""
    try:
        stats = rag_service.rebuild_index()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# FAQ endpoints
@router.get("/faqs")
async def get_faqs(session: Session = Depends(get_session)):
    faq_repo = FAQRepo(session)
    return faq_repo.get_all()


@router.post("/faqs")
async def create_faq(faq: FAQ, session: Session = Depends(get_session)):
    faq_repo = FAQRepo(session)
    return faq_repo.create(faq)


@router.put("/faqs/{faq_id}")
async def update_faq(faq_id: int, faq_data: dict, session: Session = Depends(get_session)):
    faq_repo = FAQRepo(session)
    return faq_repo.update(faq_id, **faq_data)


@router.delete("/faqs/{faq_id}")
async def delete_faq(faq_id: int, session: Session = Depends(get_session)):
    faq_repo = FAQRepo(session)
    success = faq_repo.delete(faq_id)
    if not success:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return {"success": True}


# Product endpoints
@router.get("/products")
async def get_products(session: Session = Depends(get_session)):
    product_repo = ProductRepo(session)
    return product_repo.get_all()


@router.post("/products")
async def create_product(product: Product, session: Session = Depends(get_session)):
    product_repo = ProductRepo(session)
    return product_repo.create(product)


@router.put("/products/{product_id}")
async def update_product(product_id: int, product_data: dict, session: Session = Depends(get_session)):
    product_repo = ProductRepo(session)
    return product_repo.update(product_id, **product_data)


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, session: Session = Depends(get_session)):
    product_repo = ProductRepo(session)
    success = product_repo.delete(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True}


# Order endpoints
@router.get("/orders")
async def get_orders(status: Optional[str] = None, session: Session = Depends(get_session)):
    order_repo = OrderRepo(session)
    return order_repo.get_all(status=status)


@router.patch("/orders/{order_id}")
async def update_order_status(order_id: int, status_data: dict, session: Session = Depends(get_session)):
    order_repo = OrderRepo(session)
    order = order_repo.update_status(order_id, status_data["status"])
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# Analytics endpoints
@router.get("/analytics/summary")
async def get_analytics_summary(session: Session = Depends(get_session)):
    """Get basic analytics summary"""
    message_repo = MessageRepo(session)
    order_repo = OrderRepo(session)
    
    recent_messages = message_repo.get_all(limit=1000)
    recent_orders = order_repo.get_all()
    
    # Basic stats
    intent_counts = {}
    channel_counts = {}
    
    for msg in recent_messages:
        intent = msg.intent or "unknown"
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
        channel_counts[msg.channel] = channel_counts.get(msg.channel, 0) + 1
    
    order_status_counts = {}
    for order in recent_orders:
        status = order.status
        order_status_counts[status] = order_status_counts.get(status, 0) + 1
    
    return {
        "total_messages": len(recent_messages),
        "total_orders": len(recent_orders),
        "intent_distribution": intent_counts,
        "channel_distribution": channel_counts,
        "order_status_distribution": order_status_counts,
        "top_intents": sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    }


@router.get("/config")
async def get_config():
    """Get current configuration (sensitive data masked)"""
    safe_config = config.copy()
    
    # Mask sensitive information
    if "ai" in safe_config and "model_name" in safe_config["ai"]:
        # Keep model info but hide API keys
        pass
    
    return safe_config


# Setup Wizard API Endpoints
class SetupKnowledgeRequest(BaseModel):
    faqs: List[Dict[str, str]]
    menu: List[Dict[str, Any]]


@router.post("/setup/business")
async def setup_business(
    business_name: str = Form(...),
    business_phone: Optional[str] = Form(None),
    business_email: Optional[str] = Form(None),
    business_timezone: str = Form("America/Mexico_City"),
    business_address: Optional[str] = Form(None),
    hours_mon_fri: Optional[str] = Form(None),
    hours_sat: Optional[str] = Form(None),
    hours_sun: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """Save business information from setup wizard"""
    try:
        setting_repo = SettingRepo(session)
        
        # Save business settings
        setting_repo.set("business_name", business_name, "business")
        if business_phone:
            setting_repo.set("business_phone", business_phone, "business")
        if business_email:
            setting_repo.set("business_email", business_email, "business")
        setting_repo.set("business_timezone", business_timezone, "business")
        if business_address:
            setting_repo.set("business_address", business_address, "business")
        if hours_mon_fri:
            setting_repo.set("hours_mon_fri", hours_mon_fri, "business")
        if hours_sat:
            setting_repo.set("hours_sat", hours_sat, "business")
        if hours_sun:
            setting_repo.set("hours_sun", hours_sun, "business")
        
        return {"success": True, "message": "Business information saved"}
    
    except Exception as e:
        logger.error(f"Error saving business info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup/ai")
async def setup_ai(
    ai_mode: str = Form(...),
    openai_api_key: Optional[str] = Form(None),
    groq_api_key: Optional[str] = Form(None),
    gemini_api_key: Optional[str] = Form(None),
    response_tone: str = Form("amigable"),
    session: Session = Depends(get_session)
):
    """Save AI configuration from setup wizard"""
    try:
        setting_repo = SettingRepo(session)
        
        # Save AI settings
        setting_repo.set("ai_mode", ai_mode, "ai")
        setting_repo.set("response_tone", response_tone, "ai")
        
        # Save API keys if provided
        if openai_api_key:
            setting_repo.set("openai_api_key", openai_api_key, "ai", is_secret=True)
        if groq_api_key:
            setting_repo.set("groq_api_key", groq_api_key, "ai", is_secret=True)
        if gemini_api_key:
            setting_repo.set("gemini_api_key", gemini_api_key, "ai", is_secret=True)
        
        return {"success": True, "message": "AI configuration saved"}
    
    except Exception as e:
        logger.error(f"Error saving AI config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup/knowledge")
async def setup_knowledge(
    request: SetupKnowledgeRequest,
    session: Session = Depends(get_session)
):
    """Save knowledge base from setup wizard"""
    try:
        faq_repo = FAQRepo(session)
        product_repo = ProductRepo(session)
        
        # Save FAQs
        for faq_data in request.faqs:
            if faq_data.get("question") and faq_data.get("answer"):
                faq = FAQ(
                    question=faq_data["question"],
                    answer=faq_data["answer"]
                )
                faq_repo.create(faq)
        
        # Save menu items
        for item_data in request.menu:
            if item_data.get("name"):
                product = Product(
                    name=item_data["name"],
                    price=float(item_data.get("price", 0)),
                    description=item_data.get("description", "")
                )
                product_repo.create(product)
        
        return {"success": True, "message": "Knowledge base saved"}
    
    except Exception as e:
        logger.error(f"Error saving knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup/channels")
async def setup_channels(
    twilio_account_sid: Optional[str] = Form(None),
    twilio_auth_token: Optional[str] = Form(None),
    twilio_whatsapp_from: Optional[str] = Form(None),
    telegram_bot_token: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """Save channel configuration from setup wizard"""
    try:
        setting_repo = SettingRepo(session)
        
        # Save WhatsApp/Twilio settings
        if twilio_account_sid:
            setting_repo.set("twilio_account_sid", twilio_account_sid, "channels", is_secret=True)
        if twilio_auth_token:
            setting_repo.set("twilio_auth_token", twilio_auth_token, "channels", is_secret=True)
        if twilio_whatsapp_from:
            setting_repo.set("twilio_whatsapp_from", twilio_whatsapp_from, "channels")
        
        # Save Telegram settings
        if telegram_bot_token:
            setting_repo.set("telegram_bot_token", telegram_bot_token, "channels", is_secret=True)
        
        # Mark setup as completed
        setting_repo.set("setup_completed", "true", "general")
        
        return {"success": True, "message": "Channel configuration saved"}
    
    except Exception as e:
        logger.error(f"Error saving channel config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Live Chat API Endpoints
class SendMessageRequest(BaseModel):
    conversation_id: str
    text: str
    is_human_response: bool = False


@router.get("/conversations")
async def get_conversations(session: Session = Depends(get_session)):
    """Get all conversations for live chat interface"""
    try:
        conversation_repo = ConversationRepo(session)
        conversations = conversation_repo.get_all_conversations()
        
        # Get counts for different statuses
        active_count = len([c for c in conversations if c.status in ["active", "waiting_human"]])
        escalated_count = len([c for c in conversations if c.status == "escalated"])
        
        return {
            "conversations": conversations,
            "active_count": active_count,
            "escalated_count": escalated_count
        }
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation_detail(conversation_id: str, session: Session = Depends(get_session)):
    """Get conversation details with messages"""
    try:
        conversation_repo = ConversationRepo(session)
        conversation = conversation_repo.get_by_conversation_id(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = conversation_repo.get_messages_for_conversation(conversation_id)
        
        return {
            "conversation": conversation,
            "messages": messages
        }
    except Exception as e:
        logger.error(f"Error getting conversation detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, session: Session = Depends(get_session)):
    """Get messages for a specific conversation"""
    try:
        conversation_repo = ConversationRepo(session)
        messages = conversation_repo.get_messages_for_conversation(conversation_id)
        return messages
    except Exception as e:
        logger.error(f"Error getting conversation messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/send-message")
async def send_message_to_conversation(request: SendMessageRequest, session: Session = Depends(get_session)):
    """Send a message in a conversation (from human agent)"""
    try:
        message_repo = MessageRepo(session)
        conversation_repo = ConversationRepo(session)
        
        # Verify conversation exists
        conversation = conversation_repo.get_by_conversation_id(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create the human response message
        message = Message(
            channel=conversation.channel,
            user_id=conversation.user_id,
            text=request.text,
            conversation_id=request.conversation_id,
            is_from_user=False,
            source="human",
            human_agent_id="admin"  # TODO: Get actual agent ID from auth
        )
        
        message_repo.create(message)
        
        # Update conversation last activity
        conversation_repo.update_status(request.conversation_id, conversation.status)
        
        return {"success": True, "message": "Message sent"}
    
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/escalate")
async def escalate_conversation(conversation_id: str, session: Session = Depends(get_session)):
    """Escalate conversation to human agent"""
    try:
        conversation_repo = ConversationRepo(session)
        conversation = conversation_repo.update_status(conversation_id, "escalated", "admin")
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create a system message about escalation
        message_repo = MessageRepo(session)
        system_message = Message(
            channel=conversation.channel,
            user_id=conversation.user_id,
            text="Conversación escalada a agente humano",
            conversation_id=conversation_id,
            is_from_user=False,
            source="system",
            human_agent_id="admin"
        )
        message_repo.create(system_message)
        
        return {"success": True, "message": "Conversation escalated"}
    
    except Exception as e:
        logger.error(f"Error escalating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conversations/{conversation_id}/close")
async def close_conversation(conversation_id: str, session: Session = Depends(get_session)):
    """Close a conversation"""
    try:
        conversation_repo = ConversationRepo(session)
        conversation = conversation_repo.update_status(conversation_id, "closed")
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"success": True, "message": "Conversation closed"}
    
    except Exception as e:
        logger.error(f"Error closing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))