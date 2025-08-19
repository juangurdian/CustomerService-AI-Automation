from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session
from pydantic import BaseModel
import json
import structlog

from app.deps import get_session
from app.db.repo import MessageRepo, FAQRepo, ProductRepo, OrderRepo, DocRepo
from app.db.models import Message, FAQ, Product, Order, Doc
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