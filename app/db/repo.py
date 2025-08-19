from typing import List, Optional
from sqlmodel import Session, select
from datetime import datetime
import json

from app.db.models import Message, FAQ, Product, Order, Doc


class MessageRepo:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, message: Message) -> Message:
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message
    
    def get_by_user(self, user_id: str, channel: str, limit: int = 50) -> List[Message]:
        statement = select(Message).where(
            Message.user_id == user_id,
            Message.channel == channel
        ).order_by(Message.created_at.desc()).limit(limit)
        return self.session.exec(statement).all()
    
    def get_all(self, limit: int = 100) -> List[Message]:
        statement = select(Message).order_by(Message.created_at.desc()).limit(limit)
        return self.session.exec(statement).all()


class FAQRepo:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, faq: FAQ) -> FAQ:
        self.session.add(faq)
        self.session.commit()
        self.session.refresh(faq)
        return faq
    
    def get_all(self, active_only: bool = True) -> List[FAQ]:
        statement = select(FAQ)
        if active_only:
            statement = statement.where(FAQ.active == True)
        return self.session.exec(statement).all()
    
    def update(self, faq_id: int, **kwargs) -> Optional[FAQ]:
        faq = self.session.get(FAQ, faq_id)
        if faq:
            for key, value in kwargs.items():
                setattr(faq, key, value)
            self.session.commit()
            self.session.refresh(faq)
        return faq
    
    def delete(self, faq_id: int) -> bool:
        faq = self.session.get(FAQ, faq_id)
        if faq:
            self.session.delete(faq)
            self.session.commit()
            return True
        return False


class ProductRepo:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, product: Product) -> Product:
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product
    
    def get_all(self, available_only: bool = True) -> List[Product]:
        statement = select(Product)
        if available_only:
            statement = statement.where(Product.available == True)
        return self.session.exec(statement).all()
    
    def get_by_category(self, category: str) -> List[Product]:
        statement = select(Product).where(
            Product.category == category,
            Product.available == True
        )
        return self.session.exec(statement).all()
    
    def update(self, product_id: int, **kwargs) -> Optional[Product]:
        product = self.session.get(Product, product_id)
        if product:
            for key, value in kwargs.items():
                setattr(product, key, value)
            self.session.commit()
            self.session.refresh(product)
        return product
    
    def delete(self, product_id: int) -> bool:
        product = self.session.get(Product, product_id)
        if product:
            self.session.delete(product)
            self.session.commit()
            return True
        return False


class OrderRepo:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, order: Order) -> Order:
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return order
    
    def get_all(self, status: Optional[str] = None) -> List[Order]:
        statement = select(Order)
        if status:
            statement = statement.where(Order.status == status)
        return self.session.exec(statement.order_by(Order.created_at.desc())).all()
    
    def update_status(self, order_id: int, status: str) -> Optional[Order]:
        order = self.session.get(Order, order_id)
        if order:
            order.status = status
            order.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(order)
        return order
    
    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self.session.get(Order, order_id)


class ProductRepo:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, product: Product) -> Product:
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product
    
    def get_all(self, available_only: bool = True) -> List[Product]:
        statement = select(Product)
        if available_only:
            statement = statement.where(Product.available == True)
        return self.session.exec(statement).all()
    
    def get_by_category(self, category: str) -> List[Product]:
        statement = select(Product).where(
            Product.category == category,
            Product.available == True
        )
        return self.session.exec(statement).all()
    
    def update(self, product_id: int, **kwargs) -> Optional[Product]:
        product = self.session.get(Product, product_id)
        if product:
            for key, value in kwargs.items():
                setattr(product, key, value)
            self.session.commit()
            self.session.refresh(product)
        return product
    
    def delete(self, product_id: int) -> bool:
        product = self.session.get(Product, product_id)
        if product:
            self.session.delete(product)
            self.session.commit()
            return True
        return False


class DocRepo:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, doc: Doc) -> Doc:
        self.session.add(doc)
        self.session.commit()
        self.session.refresh(doc)
        return doc
    
    def get_all(self) -> List[Doc]:
        statement = select(Doc).order_by(Doc.created_at.desc())
        return self.session.exec(statement).all()
    
    def mark_indexed(self, doc_id: int) -> Optional[Doc]:
        doc = self.session.get(Doc, doc_id)
        if doc:
            doc.indexed = True
            self.session.commit()
            self.session.refresh(doc)
        return doc
    
    def delete(self, doc_id: int) -> bool:
        doc = self.session.get(Doc, doc_id)
        if doc:
            self.session.delete(doc)
            self.session.commit()
            return True
        return False