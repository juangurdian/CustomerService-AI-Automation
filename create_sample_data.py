#!/usr/bin/env python3
"""
Script to create sample conversation data for testing the live chat interface
"""

import uuid
from datetime import datetime, timedelta
from sqlmodel import Session, create_engine
from app.db.models import Conversation, Message
from app.settings import settings

def create_sample_conversations():
    """Create sample conversations and messages for testing"""
    
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
    )
    
    with Session(engine) as session:
        # Sample conversations
        conversations_data = [
            {
                "conversation_id": str(uuid.uuid4()),
                "user_id": "user_001_whatsapp",
                "channel": "whatsapp",
                "customer_name": "Juan Pérez",
                "customer_phone": "+505-8888-1234",
                "status": "active",
                "created_at": datetime.utcnow() - timedelta(minutes=5),
                "last_activity": datetime.utcnow() - timedelta(minutes=2)
            },
            {
                "conversation_id": str(uuid.uuid4()),
                "user_id": "user_002_telegram",
                "channel": "telegram",
                "customer_name": "María García",
                "customer_phone": None,
                "status": "escalated",
                "assigned_agent": "admin",
                "created_at": datetime.utcnow() - timedelta(hours=1),
                "last_activity": datetime.utcnow() - timedelta(minutes=10),
                "escalated_at": datetime.utcnow() - timedelta(minutes=15)
            },
            {
                "conversation_id": str(uuid.uuid4()),
                "user_id": "user_003_web",
                "channel": "web",
                "customer_name": "Carlos Silva",
                "customer_phone": "+505-7777-5678",
                "status": "waiting_human",
                "created_at": datetime.utcnow() - timedelta(minutes=30),
                "last_activity": datetime.utcnow() - timedelta(minutes=5)
            },
            {
                "conversation_id": str(uuid.uuid4()),
                "user_id": "user_004_whatsapp",
                "channel": "whatsapp",
                "customer_name": "Ana López",
                "customer_phone": "+505-9999-9876",
                "status": "active",
                "created_at": datetime.utcnow() - timedelta(hours=2),
                "last_activity": datetime.utcnow() - timedelta(minutes=1)
            }
        ]
        
        # Create conversations
        created_conversations = []
        for conv_data in conversations_data:
            conversation = Conversation(**conv_data)
            session.add(conversation)
            created_conversations.append(conversation)
        
        session.commit()
        for conv in created_conversations:
            session.refresh(conv)
        
        # Sample messages for each conversation
        messages_data = [
            # Juan Pérez conversation (WhatsApp)
            {
                "conversation_id": created_conversations[0].conversation_id,
                "channel": "whatsapp",
                "user_id": "user_001_whatsapp",
                "text": "Hola! ¿Tienen disponible la hamburguesa especial hoy?",
                "is_from_user": True,
                "created_at": datetime.utcnow() - timedelta(minutes=5)
            },
            {
                "conversation_id": created_conversations[0].conversation_id,
                "channel": "whatsapp",
                "user_id": "user_001_whatsapp",
                "text": "¡Hola! Sí, tenemos la hamburguesa especial disponible. Cuesta $8.50 y viene con papas fritas. ¿Te gustaría ordenar una?",
                "response": "Respuesta automática del bot",
                "is_from_user": False,
                "source": "rag",
                "created_at": datetime.utcnow() - timedelta(minutes=4, seconds=30)
            },
            {
                "conversation_id": created_conversations[0].conversation_id,
                "channel": "whatsapp",
                "user_id": "user_001_whatsapp",
                "text": "Perfecto! Me gustaría ordenar 2 hamburguesas especiales para recoger",
                "is_from_user": True,
                "created_at": datetime.utcnow() - timedelta(minutes=2)
            },
            
            # María García conversation (Telegram - Escalated)
            {
                "conversation_id": created_conversations[1].conversation_id,
                "channel": "telegram",
                "user_id": "user_002_telegram",
                "text": "Tengo un problema con mi pedido de ayer, llegó frío y incompleto",
                "is_from_user": True,
                "requires_human": True,
                "created_at": datetime.utcnow() - timedelta(hours=1)
            },
            {
                "conversation_id": created_conversations[1].conversation_id,
                "channel": "telegram",
                "user_id": "user_002_telegram",
                "text": "Lamento mucho escuchar sobre tu experiencia. He escalado tu caso a un agente humano que te contactará pronto.",
                "is_from_user": False,
                "source": "llm",
                "created_at": datetime.utcnow() - timedelta(minutes=55)
            },
            {
                "conversation_id": created_conversations[1].conversation_id,
                "channel": "telegram",
                "user_id": "user_002_telegram",
                "text": "Conversación escalada a agente humano",
                "is_from_user": False,
                "source": "system",
                "created_at": datetime.utcnow() - timedelta(minutes=15)
            },
            {
                "conversation_id": created_conversations[1].conversation_id,
                "channel": "telegram",
                "user_id": "user_002_telegram",
                "text": "Hola María, soy el gerente. Revisé tu pedido y tienes razón. Te haremos un reembolso completo y un pedido nuevo sin costo. ¿Te parece bien?",
                "is_from_user": False,
                "source": "human",
                "human_agent_id": "admin",
                "created_at": datetime.utcnow() - timedelta(minutes=10)
            },
            
            # Carlos Silva conversation (Web - Waiting Human)
            {
                "conversation_id": created_conversations[2].conversation_id,
                "channel": "web",
                "user_id": "user_003_web",
                "text": "Hola, necesito hablar con un humano sobre facturación",
                "is_from_user": True,
                "requires_human": True,
                "created_at": datetime.utcnow() - timedelta(minutes=30)
            },
            {
                "conversation_id": created_conversations[2].conversation_id,
                "channel": "web",
                "user_id": "user_003_web",
                "text": "Entiendo que necesitas ayuda con facturación. Te estoy conectando con un agente humano.",
                "is_from_user": False,
                "source": "llm",
                "created_at": datetime.utcnow() - timedelta(minutes=29)
            },
            {
                "conversation_id": created_conversations[2].conversation_id,
                "channel": "web",
                "user_id": "user_003_web",
                "text": "¿Sigue disponible el agente? Es urgente.",
                "is_from_user": True,
                "created_at": datetime.utcnow() - timedelta(minutes=5)
            },
            
            # Ana López conversation (WhatsApp - Active)
            {
                "conversation_id": created_conversations[3].conversation_id,
                "channel": "whatsapp",
                "user_id": "user_004_whatsapp",
                "text": "¿Cuáles son sus horarios de atención?",
                "is_from_user": True,
                "created_at": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "conversation_id": created_conversations[3].conversation_id,
                "channel": "whatsapp",
                "user_id": "user_004_whatsapp",
                "text": "Nuestros horarios son: Lunes a Viernes de 8:00 AM a 6:00 PM, Sábados de 9:00 AM a 2:00 PM, y Domingos cerrado.",
                "is_from_user": False,
                "source": "faq",
                "created_at": datetime.utcnow() - timedelta(hours=1, minutes=59)
            },
            {
                "conversation_id": created_conversations[3].conversation_id,
                "channel": "whatsapp",
                "user_id": "user_004_whatsapp",
                "text": "Gracias! ¿Hacen entregas a domicilio?",
                "is_from_user": True,
                "created_at": datetime.utcnow() - timedelta(minutes=1)
            }
        ]
        
        # Create messages
        for msg_data in messages_data:
            message = Message(**msg_data)
            session.add(message)
        
        session.commit()
        
        print(f"✅ Created {len(created_conversations)} sample conversations")
        print(f"✅ Created {len(messages_data)} sample messages")
        print("\nSample conversations:")
        for conv in created_conversations:
            print(f"  - {conv.customer_name} ({conv.channel}) - Status: {conv.status}")

if __name__ == "__main__":
    create_sample_conversations()