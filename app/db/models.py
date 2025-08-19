from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, create_engine
from app.settings import settings


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    channel: str
    user_id: str
    text: str
    intent: Optional[str] = None
    source: Optional[str] = None  # faq/menu/rag/llm/fallback
    response: Optional[str] = None
    trace_data: Optional[str] = None  # JSON string with debug info
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FAQ(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question: str
    answer: str
    tags: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float
    description: Optional[str] = None
    available: bool = True
    category: Optional[str] = None
    tags: Optional[str] = None
    featured: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    items_json: str  # JSON: [{"product_id": 1, "name": "Pizza", "qty": 2, "price": 15.0}]
    total: float = 0.0
    status: str = "new"  # new|confirmed|cancelled|fulfilled
    channel: str
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class Doc(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    file_path: str
    file_type: str  # pdf/txt/md/csv
    content_preview: Optional[str] = None
    indexed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Setting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True)
    value: Optional[str] = None
    category: str = "general"  # business, ai, channels, etc.
    is_secret: bool = False  # Para API keys y passwords
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


def create_db_and_tables():
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
    )
    SQLModel.metadata.create_all(engine)