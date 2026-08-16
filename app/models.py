from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.sql import func
from .database import Base


class Trader(Base):
    __tablename__ = "traders"

    id = Column(Integer, primary_key=True, index=True)
    trader_code = Column(String(20), unique=True, index=True, nullable=False)

    business_name = Column(String(255), nullable=False, index=True)
    owner_name = Column(String(255), nullable=False, index=True)
    mobile = Column(String(20), index=True)
    ward_no = Column(Integer, index=True)
    building_no = Column(String(50), index=True)
    address = Column(Text)
    trade_type = Column(String(255))

    has_licence = Column(String(20))  # "Yes" / "No" / "Don't Know"
    licence_number = Column(String(100), index=True)
    licence_issue_date = Column(Date, nullable=True)
    licence_expiry_date = Column(Date, nullable=True)
    no_licence_reason = Column(String(100))

    remarks = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
