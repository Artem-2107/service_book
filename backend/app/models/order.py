from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime
import random
import string


def generate_order_number() -> str:
    """Генерирует уникальный номер заказа в формате: YYMMDD-XXXX"""
    now = datetime.now()
    date_part = now.strftime("%y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{date_part}-{random_part}"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(20), unique=True, nullable=False, default=generate_order_number)
    car_id = Column(Integer, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="new")
    works_description = Column(Text, nullable=False)
    amount = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Связи
    car = relationship("Car", back_populates="orders")

    def __repr__(self):
        return f"<Order {self.order_number}>"