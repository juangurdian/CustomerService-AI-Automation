from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from pathlib import Path

from app.settings import settings, config
from app.db.models import create_db_and_tables
from app.routes import ui, api, webhook_web, webhook_twilio, webhook_telegram


# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Customer Service AI Agent Dashboard")
    create_db_and_tables()
    yield
    # Shutdown
    logger.info("Shutting down")


app = FastAPI(
    title="Customer Service AI Agent Dashboard",
    description="AI-powered customer service for small businesses",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/widget", StaticFiles(directory="web_widget"), name="widget")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Routes
app.include_router(ui.router)
app.include_router(api.router, prefix="/api")
app.include_router(webhook_web.router, prefix="/webhook")
app.include_router(webhook_twilio.router, prefix="/webhook")
app.include_router(webhook_telegram.router, prefix="/webhook")


@app.get("/healthz")
async def health_check():
    return {"status": "ok", "business": config["business"]["name"]}


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "business": config["business"]}
    )