from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import structlog

from app.services.responder import response_orchestrator

logger = structlog.get_logger()
router = APIRouter()


class WebChatMessage(BaseModel):
    text: str
    user_id: str
    session_id: Optional[str] = None


@router.post("/web")
async def web_chat_webhook(message: WebChatMessage):
    """Webhook for web chat widget"""
    try:
        result = await response_orchestrator.process_message(
            text=message.text,
            user_id=message.user_id,
            channel="web",
            meta={"session_id": message.session_id}
        )
        
        return {
            "message": result["reply"],
            "quick_replies": result.get("quick_replies", []),
            "flow_active": result.get("flow_active", False)
        }
    
    except Exception as e:
        logger.error(f"Error in web chat webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")