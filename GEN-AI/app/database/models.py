from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class StoreInsight(Base):
    """Main table for storing store insights"""
    __tablename__ = "store_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    store_url = Column(String(500), nullable=False, index=True)
    brand_name = Column(String(255))
    brand_description = Column(Text)
    extracted_at = Column(DateTime, default=datetime.utcnow)
    meta_data = Column(JSON)  # Changed from 'metadata' to 'meta_data'
    
    # Relationships
    products = relationship("Product", back_populates="store_insight", cascade="all, delete-orphan")
    hero_products = relationship("HeroProduct", back_populates="store_insight", cascade="all, delete-orphan")
    policies = relationship("Policy", back_populates="store_insight", cascade="all, delete-orphan")
    faqs = relationship("FAQ", back_populates="store_insight", cascade="all, delete-orphan")
    social_handles = relationship("SocialHandle", back_populates="store_insight", cascade="all, delete-orphan")
    contact_info = relationship("ContactInfo", back_populates="store_insight", uselist=False, cascade="all, delete-orphan")
    important_links = relationship("ImportantLink", back_populates="store_insight", cascade="all, delete-orphan")


class Product(Base):
    """Products table"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    store_insight_id = Column(Integer, ForeignKey("store_insights.id"), nullable=False)
    product_id = Column(String(100))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    price = Column(String(50))
    currency = Column(String(10))
    images = Column(JSON)  # List of image URLs
    url = Column(String(500))
    available = Column(Boolean, default=True)
    tags = Column(JSON)  # List of tags
    category = Column(String(255))
    
    store_insight = relationship("StoreInsight", back_populates="products")


class HeroProduct(Base):
    """Hero products table"""
    __tablename__ = "hero_products"
    
    id = Column(Integer, primary_key=True, index=True)
    store_insight_id = Column(Integer, ForeignKey("store_insights.id"), nullable=False)
    product_id = Column(String(100))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    price = Column(String(50))
    currency = Column(String(10))
    images = Column(JSON)  # List of image URLs
    url = Column(String(500))
    available = Column(Boolean, default=True)
    tags = Column(JSON)  # List of tags
    category = Column(String(255))
    
    store_insight = relationship("StoreInsight", back_populates="hero_products")


class Policy(Base):
    """Policies table"""
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    store_insight_id = Column(Integer, ForeignKey("store_insights.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(500))
    policy_type = Column(String(50))  # privacy, return, refund
    
    store_insight = relationship("StoreInsight", back_populates="policies")


class FAQ(Base):
    """FAQs table"""
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    store_insight_id = Column(Integer, ForeignKey("store_insights.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    
    store_insight = relationship("StoreInsight", back_populates="faqs")


class SocialHandle(Base):
    """Social handles table"""
    __tablename__ = "social_handles"
    
    id = Column(Integer, primary_key=True, index=True)
    store_insight_id = Column(Integer, ForeignKey("store_insights.id"), nullable=False)
    platform = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    handle = Column(String(255))
    
    store_insight = relationship("StoreInsight", back_populates="social_handles")


class ContactInfo(Base):
    """Contact information table"""
    __tablename__ = "contact_info"
    
    id = Column(Integer, primary_key=True, index=True)
    store_insight_id = Column(Integer, ForeignKey("store_insights.id"), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    
    store_insight = relationship("StoreInsight", back_populates="contact_info")


class ImportantLink(Base):
    """Important links table"""
    __tablename__ = "important_links"
    
    id = Column(Integer, primary_key=True, index=True)
    store_insight_id = Column(Integer, ForeignKey("store_insights.id"), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text)
    
    store_insight = relationship("StoreInsight", back_populates="important_links")


class CompetitorAnalysis(Base):
    """Competitor analysis table"""
    __tablename__ = "competitor_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    main_brand_id = Column(Integer, ForeignKey("store_insights.id"), nullable=False)
    competitor_id = Column(Integer, ForeignKey("store_insights.id"), nullable=False)
    analysis_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    main_brand = relationship("StoreInsight", foreign_keys=[main_brand_id])
    competitor = relationship("StoreInsight", foreign_keys=[competitor_id]) 