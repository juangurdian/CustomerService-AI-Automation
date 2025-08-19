from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import structlog

from app.services.responder import response_orchestrator
from app.settings import settings

logger = structlog.get_logger()
router = APIRouter()


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None


class TelegramMessage(BaseModel):
    message_id: int
    from_user: Dict[str, Any]
    chat: Dict[str, Any]
    date: int
    text: Optional[str] = None


@router.post("/telegram")
async def telegram_webhook(update: TelegramUpdate):
    """Webhook for Telegram bot messages"""
    try:
        if not update.message:
            return {"ok": True}  # Ignore non-message updates for now
        
        message = update.message
        user_id = str(message["from"]["id"])
        chat_id = str(message["chat"]["id"])
        text = message.get("text", "")
        
        if not text:
            return {"ok": True}  # Ignore non-text messages for now
        
        # Process message
        result = await response_orchestrator.process_message(
            text=text,
            user_id=user_id,
            channel="telegram",
            meta={
                "chat_id": chat_id,
                "message_id": message["message_id"],
                "username": message["from"].get("username"),
                "first_name": message["from"].get("first_name")
            }
        )
        
        # Send response back to Telegram
        await send_telegram_message(chat_id, result["reply"], result.get("quick_replies", []))
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"Error in Telegram webhook: {e}")
        return {"ok": False, "error": str(e)}


async def send_telegram_message(chat_id: str, text: str, quick_replies: List[str] = None):
    """Send message to Telegram chat"""
    if not settings.telegram_bot_token:
        logger.warning("Telegram bot token not configured")
        return
    
    import httpx
    
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    # Add quick replies as inline keyboard
    if quick_replies:
        keyboard = []
        for reply in quick_replies[:6]:  # Limit to 6 quick replies
            keyboard.append([{"text": reply, "callback_data": f"quick_{reply}"}])
        
        payload["reply_markup"] = {
            "inline_keyboard": keyboard
        }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                logger.error(f"Telegram API error: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")


@router.post("/telegram/set-webhook")
async def set_telegram_webhook(webhook_url: str):
    """Set Telegram webhook URL"""
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=400, detail="Telegram bot token not configured")
    
    import httpx
    
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={"url": webhook_url})
            result = response.json()
            
            if result.get("ok"):
                return {"success": True, "description": result.get("description")}
            else:
                raise HTTPException(status_code=400, detail=result.get("description"))
    
    except Exception as e:
        logger.error(f"Error setting Telegram webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))