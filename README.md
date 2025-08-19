# > Customer Service AI Agent Dashboard

Un asistente virtual completo para peque�os negocios (food trucks, tienditas, restaurantes) que permite manejar consultas, mostrar men�s y tomar pedidos autom�ticamente a trav�s de m�ltiples canales.

## ( Caracter�sticas

- >� **AI Inteligente**: Respuestas autom�ticas basadas en RAG (Retrieval Augmented Generation)
- =� **Multi-Canal**: Web chat, WhatsApp (Twilio/Cloud API), Telegram  
- =� **Gesti�n de Pedidos**: Flujo guiado para tomar pedidos paso a paso
- =� **Panel Admin**: Interface web completa para gestionar todo
- =' **F�cil Setup**: Configuraci�n en minutos, sin conocimientos t�cnicos avanzados
- =� **Datos Locales**: Todo se guarda en SQLite, privacidad garantizada
- <� **Plug & Play**: Clona, configura y corre

## =� Instalaci�n R�pida

### 1. Prerequisitos
- Python 3.11 o superior
- Git

### 2. Configurar Entorno
```bash
# Copiar archivos de configuraci�n
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
Edita `config.yaml` con la informaci�n de tu negocio:

```yaml
business:
  name: "Tu Negocio"
  address: "Tu direcci�n"
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

�Listo! Visita:
- **Panel Admin**: http://localhost:8000/admin
- **Chat Demo**: http://localhost:8000/demo

## =3 Instalaci�n con Docker

```bash
# Configurar archivos .env y config.yaml como arriba, luego:
docker compose up -d --build
```

## =� Configuraci�n de Canales

### Web Chat
-  **Incluido**: Funciona inmediatamente
- = **Integraci�n**: Copia el c�digo del panel admin

### WhatsApp (Twilio - Recomendado)
1. Crea cuenta en [Twilio.com](https://twilio.com)
2. Ve a WhatsApp Sandbox  
3. Obt�n Account SID y Auth Token
4. Configura webhook: `https://tu-dominio.com/webhook/twilio`
5. Agrega variables a `.env`

### Telegram
1. Habla con @BotFather en Telegram
2. Crea bot con `/newbot`
3. Agrega token a `.env`
4. El sistema configurar� el webhook autom�ticamente

## <� Gu�a de Uso

1. **Ve a** http://localhost:8000/admin/onboarding
2. **Sigue la checklist** de configuraci�n inicial
3. **Carga tus FAQs y men�** usando los archivos CSV
4. **Construye el �ndice** de b�squeda
5. **Prueba el bot** en el playground
6. **Integra el widget** en tu sitio web

## =' Formato de Datos

**FAQs (data/faqs.csv)**:
```csv
question,answer,tags
"�Cu�les son sus horarios?","Lunes a Viernes 8am-6pm","horarios"
"�D�nde est�n ubicados?","Calle Principal #123","ubicacion"
```

**Men� (data/menu.csv)**:
```csv
name,price,description,category,available,featured
"Pizza Margherita",12.99,"Pizza cl�sica con mozzarella","pizza",true,true
"Coca Cola",2.00,"Refresco 350ml","bebida",true,false
```

## =� APIs Principales

- `POST /api/chat` - Endpoint principal del bot
- `GET /api/search` - B�squeda en base de conocimiento  
- `POST /admin/rebuild-index` - Reconstruir �ndice
- `GET /admin/*` - Panel administrativo

## =� Problemas Comunes

**"No responde correctamente"**
-  Ve a `/admin/onboarding` y completa todos los pasos
-  Verifica que el �ndice est� construido en `/admin/knowledge`
-  Usa el playground para debug

**"Error al instalar dependencias"**
-  Verifica Python 3.11+: `python --version`
-  Actualiza pip: `pip install --upgrade pip`
-  Instala en entorno virtual

**"WhatsApp no funciona"**
-  Verifica credenciales en `.env`
-  Confirma webhook en Twilio/Meta
-  Usa HTTPS en producci�n

## =� Pr�ximas Funcionalidades

- [ ] Multi-sucursal (varios perfiles)
- [ ] Inventario y stock
- [ ] Integraci�n con pagos
- [ ] Anal�tica avanzada
- [ ] App m�vil para administradores

---

**�Necesitas ayuda?** Abre un issue en GitHub o contacta al equipo de desarrollo.