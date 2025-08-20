from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session
from typing import Optional, List
import csv
import json
from pathlib import Path
import structlog

from app.deps import get_session
from app.db.repo import MessageRepo, FAQRepo, ProductRepo, OrderRepo, DocRepo, ConversationRepo
from app.db.models import FAQ, Product, Order, Doc
from app.services.rag import rag_service
from app.settings import config, settings, get_dynamic_config

logger = structlog.get_logger()
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, session: Session = Depends(get_session)):
    """Main admin dashboard"""
    message_repo = MessageRepo(session)
    order_repo = OrderRepo(session)
    
    # Get recent stats
    recent_messages = message_repo.get_all(limit=100)
    recent_orders = order_repo.get_all()
    
    stats = {
        "total_messages": len(recent_messages),
        "total_orders": len(recent_orders),
        "new_orders": len([o for o in recent_orders if o.status == "new"]),
        "channels": len(set(m.channel for m in recent_messages))
    }
    
    return templates.TemplateResponse(
        "admin/dashboard_modern.html",
        {"request": request, "config": get_dynamic_config(), "stats": stats}
    )


@router.get("/admin/live-chat", response_class=HTMLResponse)
async def live_chat(request: Request, session: Session = Depends(get_session)):
    """Live chat management page"""
    conversation_repo = ConversationRepo(session)
    conversations = conversation_repo.get_all_conversations()
    
    # Get counts for different statuses
    active_count = len([c for c in conversations if c.status in ["active", "waiting_human"]])
    escalated_count = len([c for c in conversations if c.status == "escalated"])
    
    return templates.TemplateResponse(
        "admin/live_chat.html",
        {
            "request": request, 
            "config": get_dynamic_config(), 
            "conversations": conversations,
            "active_count": active_count,
            "escalated_count": escalated_count
        }
    )


@router.get("/admin/setup", response_class=HTMLResponse)
async def setup_wizard(request: Request, session: Session = Depends(get_session)):
    """Setup wizard page"""
    from app.db.repo import SettingRepo
    
    # Check if setup is already completed
    setting_repo = SettingRepo(session)
    setup_completed = setting_repo.get_value("setup_completed", "false")
    
    return templates.TemplateResponse(
        "admin/setup_wizard.html",
        {"request": request, "config": get_dynamic_config(), "setup_completed": setup_completed == "true"}
    )


@router.get("/admin/onboarding", response_class=HTMLResponse)
async def onboarding(request: Request):
    """Onboarding checklist page"""
    
    # Check completion status
    checks = {
        "env_file": Path(".env").exists(),
        "config_file": Path("config.yaml").exists(),
        "faqs_data": Path("data/faqs.csv").exists(),
        "menu_data": Path("data/menu.csv").exists(),
        "index_built": Path("faiss_index/index.faiss").exists()
    }
    
    return templates.TemplateResponse(
        "admin/onboarding.html",
        {"request": request, "config": get_dynamic_config(), "checks": checks}
    )


@router.get("/admin/knowledge", response_class=HTMLResponse)
async def knowledge_management(request: Request, session: Session = Depends(get_session)):
    """Knowledge base management"""
    faq_repo = FAQRepo(session)
    doc_repo = DocRepo(session)
    
    faqs = faq_repo.get_all()
    docs = doc_repo.get_all()
    
    return templates.TemplateResponse(
        "admin/knowledge.html",
        {"request": request, "config": get_dynamic_config(), "faqs": faqs, "docs": docs}
    )


@router.post("/admin/knowledge/upload-csv")
async def upload_faq_csv(request: Request, file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Upload FAQ CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Must be a CSV file")
    
    try:
        content = await file.read()
        
        # Save to data directory
        csv_path = Path("data/faqs.csv")
        csv_path.parent.mkdir(exist_ok=True)
        
        with open(csv_path, "wb") as f:
            f.write(content)
        
        # Also import to database
        faq_repo = FAQRepo(session)
        
        # Parse CSV and create FAQ records
        content_str = content.decode('utf-8')
        reader = csv.DictReader(content_str.splitlines())
        
        imported_count = 0
        for row in reader:
            if row.get('question') and row.get('answer'):
                faq = FAQ(
                    question=row['question'],
                    answer=row['answer'],
                    tags=row.get('tags', '')
                )
                faq_repo.create(faq)
                imported_count += 1
        
        return RedirectResponse(
            url=f"/admin/knowledge?message=Imported {imported_count} FAQs successfully",
            status_code=303
        )
    
    except Exception as e:
        logger.error(f"Error uploading FAQ CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/menu", response_class=HTMLResponse)
async def menu_management(request: Request, session: Session = Depends(get_session)):
    """Menu/products management"""
    product_repo = ProductRepo(session)
    products = product_repo.get_all(available_only=False)
    
    return templates.TemplateResponse(
        "admin/menu.html",
        {"request": request, "config": get_dynamic_config(), "products": products}
    )


@router.get("/admin/playground", response_class=HTMLResponse)
async def playground(request: Request):
    """Chat testing playground"""
    return templates.TemplateResponse(
        "admin/playground.html",
        {"request": request, "config": get_dynamic_config()}
    )


@router.get("/admin/orders", response_class=HTMLResponse)
async def orders_management(request: Request, session: Session = Depends(get_session)):
    """Orders management"""
    order_repo = OrderRepo(session)
    orders = order_repo.get_all()
    
    return templates.TemplateResponse(
        "admin/orders.html",
        {"request": request, "config": get_dynamic_config(), "orders": orders}
    )


@router.get("/admin/channels", response_class=HTMLResponse)
async def channels_management(request: Request):
    """Channel configuration"""
    
    # Check which channels are properly configured
    channel_status = {
        "web": True,  # Always available
        "whatsapp_twilio": bool(settings.twilio_account_sid and settings.twilio_auth_token),
        "whatsapp_cloud": bool(settings.whatsapp_token and settings.phone_number_id),
        "telegram": bool(settings.telegram_bot_token)
    }
    
    return templates.TemplateResponse(
        "admin/channels.html",
        {"request": request, "config": get_dynamic_config(), "channel_status": channel_status}
    )


@router.get("/admin/analytics", response_class=HTMLResponse)
async def analytics(request: Request, session: Session = Depends(get_session)):
    """Analytics dashboard"""
    message_repo = MessageRepo(session)
    order_repo = OrderRepo(session)
    
    messages = message_repo.get_all(limit=500)
    orders = order_repo.get_all()
    
    # Basic analytics
    analytics_data = {
        "messages_by_channel": {},
        "messages_by_intent": {},
        "orders_by_status": {},
        "daily_activity": {}
    }
    
    for msg in messages:
        # Channel distribution
        channel = msg.channel
        analytics_data["messages_by_channel"][channel] = analytics_data["messages_by_channel"].get(channel, 0) + 1
        
        # Intent distribution
        intent = msg.intent or "unknown"
        analytics_data["messages_by_intent"][intent] = analytics_data["messages_by_intent"].get(intent, 0) + 1
        
        # Daily activity (simplified)
        day = msg.created_at.strftime("%Y-%m-%d")
        analytics_data["daily_activity"][day] = analytics_data["daily_activity"].get(day, 0) + 1
    
    for order in orders:
        status = order.status
        analytics_data["orders_by_status"][status] = analytics_data["orders_by_status"].get(status, 0) + 1
    
    return templates.TemplateResponse(
        "admin/analytics.html",
        {"request": request, "config": get_dynamic_config(), "analytics": analytics_data}
    )


@router.get("/admin/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings and configuration"""
    
    # Mask sensitive settings for display
    safe_settings = {
        "openai_configured": bool(settings.openai_api_key),
        "groq_configured": bool(settings.groq_api_key),
        "gemini_configured": bool(settings.gemini_api_key),
        "twilio_configured": bool(settings.twilio_account_sid),
        "whatsapp_configured": bool(settings.whatsapp_token),
        "telegram_configured": bool(settings.telegram_bot_token)
    }
    
    return templates.TemplateResponse(
        "admin/settings.html",
        {"request": request, "config": get_dynamic_config(), "settings": safe_settings}
    )


@router.post("/admin/rebuild-index")
async def rebuild_index_endpoint(request: Request):
    """Rebuild RAG index endpoint"""
    try:
        stats = rag_service.rebuild_index()
        return RedirectResponse(
            url=f"/admin/knowledge?message=Index rebuilt: {stats['faqs']} FAQs, {stats['menu']} menu items, {stats['docs']} documents",
            status_code=303
        )
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
        return RedirectResponse(
            url=f"/admin/knowledge?error=Error rebuilding index: {str(e)}",
            status_code=303
        )


@router.get("/demo", response_class=HTMLResponse)
async def chat_demo(request: Request):
    """Public chat demo page"""
    return templates.TemplateResponse(
        "chat_demo.html",
        {"request": request, "config": get_dynamic_config()}
    )