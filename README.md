# > Customer Service AI Agent Dashboard

Un asistente virtual completo para pequeños negocios (food trucks, tienditas, restaurantes) que permite manejar consultas, mostrar menús y tomar pedidos automáticamente a través de múltiples canales.

## ( Características

- >à **AI Inteligente**: Respuestas automáticas basadas en RAG (Retrieval Augmented Generation)
- =ñ **Multi-Canal**: Web chat, WhatsApp (Twilio/Cloud API), Telegram  
- =Ë **Gestión de Pedidos**: Flujo guiado para tomar pedidos paso a paso
- =Ê **Panel Admin**: Interface web completa para gestionar todo
- =' **Fácil Setup**: Configuración en minutos, sin conocimientos técnicos avanzados
- =¾ **Datos Locales**: Todo se guarda en SQLite, privacidad garantizada
- <¯ **Plug & Play**: Clona, configura y corre

## =€ Instalación Rápida

### 1. Prerequisitos
- Python 3.11 o superior
- Git

### 2. Configurar Entorno
```bash
# Copiar archivos de configuración
cp .env.example .env
cp config_example.yaml config.yaml

# Instalar dependencias de Python
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno
Edita el archivo `.env` con tus API keys (opcionales):

```bash
# LLM APIs (opcional - elige uno o usa modo rag_only)
OPENAI_API_KEY=tu-key-aqui
GROQ_API_KEY=tu-key-aqui
GEMINI_API_KEY=tu-key-aqui

# WhatsApp Twilio (recomendado para principiantes)
TWILIO_ACCOUNT_SID=tu-sid
TWILIO_AUTH_TOKEN=tu-token
TWILIO_WHATSAPP_FROM=whatsapp:+1234567890

# Telegram
TELEGRAM_BOT_TOKEN=tu-bot-token
```

### 4. Personalizar tu Negocio
Edita `config.yaml` con la información de tu negocio:

```yaml
business:
  name: "Tu Negocio"
  address: "Tu dirección"
  phone: "+505-xxxx-xxxx"
  hours:
    mon_fri: "8:00-18:00"
    sat: "9:00-14:00"
    sun: "cerrado"
```

### 5. Ejecutar
```bash
uvicorn app.main:app --reload --port 8000
```

¡Listo! Visita:
- **Panel Admin**: http://localhost:8000/admin
- **Chat Demo**: http://localhost:8000/demo

## =3 Instalación con Docker

```bash
# Configurar archivos .env y config.yaml como arriba, luego:
docker compose up -d --build
```

## =ñ Configuración de Canales

### Web Chat
-  **Incluido**: Funciona inmediatamente
- = **Integración**: Copia el código del panel admin

### WhatsApp (Twilio - Recomendado)
1. Crea cuenta en [Twilio.com](https://twilio.com)
2. Ve a WhatsApp Sandbox  
3. Obtén Account SID y Auth Token
4. Configura webhook: `https://tu-dominio.com/webhook/twilio`
5. Agrega variables a `.env`

### Telegram
1. Habla con @BotFather en Telegram
2. Crea bot con `/newbot`
3. Agrega token a `.env`
4. El sistema configurará el webhook automáticamente

## <¯ Guía de Uso

1. **Ve a** http://localhost:8000/admin/onboarding
2. **Sigue la checklist** de configuración inicial
3. **Carga tus FAQs y menú** usando los archivos CSV
4. **Construye el índice** de búsqueda
5. **Prueba el bot** en el playground
6. **Integra el widget** en tu sitio web

## =' Formato de Datos

**FAQs (data/faqs.csv)**:
```csv
question,answer,tags
"¿Cuáles son sus horarios?","Lunes a Viernes 8am-6pm","horarios"
"¿Dónde están ubicados?","Calle Principal #123","ubicacion"
```

**Menú (data/menu.csv)**:
```csv
name,price,description,category,available,featured
"Pizza Margherita",12.99,"Pizza clásica con mozzarella","pizza",true,true
"Coca Cola",2.00,"Refresco 350ml","bebida",true,false
```

## =à APIs Principales

- `POST /api/chat` - Endpoint principal del bot
- `GET /api/search` - Búsqueda en base de conocimiento  
- `POST /admin/rebuild-index` - Reconstruir índice
- `GET /admin/*` - Panel administrativo

## =Þ Problemas Comunes

**"No responde correctamente"**
-  Ve a `/admin/onboarding` y completa todos los pasos
-  Verifica que el índice esté construido en `/admin/knowledge`
-  Usa el playground para debug

**"Error al instalar dependencias"**
-  Verifica Python 3.11+: `python --version`
-  Actualiza pip: `pip install --upgrade pip`
-  Instala en entorno virtual

**"WhatsApp no funciona"**
-  Verifica credenciales en `.env`
-  Confirma webhook en Twilio/Meta
-  Usa HTTPS en producción

## =È Próximas Funcionalidades

- [ ] Multi-sucursal (varios perfiles)
- [ ] Inventario y stock
- [ ] Integración con pagos
- [ ] Analítica avanzada
- [ ] App móvil para administradores

---

**¿Necesitas ayuda?** Abre un issue en GitHub o contacta al equipo de desarrollo.