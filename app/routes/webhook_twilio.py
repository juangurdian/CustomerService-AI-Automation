from fastapi import APIRouter, Form, HTTPException
from typing import Optional
import structlog
from twilio.twiml.messaging_response import MessagingResponse

from app.services.responder import response_orchestrator
from app.settings import settings

logger = structlog.get_logger()
router = APIRouter()


@router.post("/twilio")
async def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    AccountSid: str = Form(...),
    To: Optional[str] = Form(None)
):
    """Webhook for Twilio WhatsApp messages"""
    try:
        # Verify this is from our Twilio account
        if AccountSid != settings.twilio_account_sid:
            raise HTTPException(status_code=403, detail="Invalid AccountSid")
        
        # Clean phone number (remove whatsapp: prefix)
        user_id = From.replace("whatsapp:", "")
        
        # Process message
        result = await response_orchestrator.process_message(
            text=Body,
            user_id=user_id,
            channel="whatsapp",
            meta={"message_sid": MessageSid, "to": To}
        )
        
        # Create Twilio response
        twiml_response = MessagingResponse()
        message = twiml_response.message()
        message.body(result["reply"])
        
        # Add quick replies as numbered options if available
        quick_replies = result.get("quick_replies", [])
        if quick_replies:
            options_text = "\n\nOpciones rápidas:\n"
            for i, option in enumerate(quick_replies[:4], 1):
                options_text += f"{i}. {option}\n"
            message.body(result["reply"] + options_text)
        
        return str(twiml_response)
    
    except Exception as e:
        logger.error(f"Error in Twilio webhook: {e}")
        # Return a basic error response
        twiml_response = MessagingResponse()
        twiml_response.message("Lo siento, hubo un error procesando tu mensaje. Intenta de nuevo.")
        return str(twiml_response)