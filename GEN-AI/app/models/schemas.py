from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ErrorCode(str, Enum):
    WEBSITE_NOT_FOUND = "WEBSITE_NOT_FOUND"
    INVALID_URL = "INVALID_URL"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    PARSE_ERROR = "PARSE_ERROR"


class SocialHandle(BaseModel):
    platform: str
    url: str
    handle: Optional[str] = None


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class FAQ(BaseModel):
    question: str
    answer: str


class Product(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    images: List[str] = []
    url: Optional[str] = None
    available: bool = True
    tags: List[str] = []
    category: Optional[str] = None


class Policy(BaseModel):
    title: str
    content: str
    url: Optional[str] = None


class ImportantLink(BaseModel):
    title: str
    url: str
    description: Optional[str] = None


class BrandContext(BaseModel):
    store_url: str
    brand_name: Optional[str] = None
    brand_description: Optional[str] = None
    hero_products: List[Product] = []
    product_catalog: List[Product] = []
    privacy_policy: Optional[Policy] = None
    return_policy: Optional[Policy] = None
    refund_policy: Optional[Policy] = None
    faqs: List[FAQ] = []
    social_handles: List[SocialHandle] = []
    contact_info: ContactInfo = ContactInfo()
    important_links: List[ImportantLink] = []
    extracted_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}


class StoreInsightsRequest(BaseModel):
    website_url: HttpUrl = Field(..., description="The Shopify store URL to analyze")


class StoreInsightsResponse(BaseModel):
    success: bool
    data: Optional[BrandContext] = None
    error: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    message: str


class CompetitorAnalysisRequest(BaseModel):
    website_url: HttpUrl = Field(..., description="The main brand's Shopify store URL")
    max_competitors: int = Field(default=5, ge=1, le=10, description="Maximum number of competitors to analyze")


class CompetitorAnalysisResponse(BaseModel):
    main_brand: BrandContext
    competitors: List[BrandContext] = []
    analysis_summary: Optional[str] = None 