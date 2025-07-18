from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.database.models import (
    StoreInsight, Product, HeroProduct, Policy, FAQ, 
    SocialHandle, ContactInfo, ImportantLink, CompetitorAnalysis
)
from app.models.schemas import BrandContext, Product as ProductSchema, Policy as PolicySchema
from app.models.schemas import FAQ as FAQSchema, SocialHandle as SocialHandleSchema
from app.models.schemas import ContactInfo as ContactInfoSchema, ImportantLink as ImportantLinkSchema

logger = logging.getLogger(__name__)


class StoreRepository:
    def __init__(self, db: Session):
        self.db = db
        self.is_mock = hasattr(db, '__class__') and 'MockSession' in str(db.__class__)
    
    def save_store_insight(self, brand_context: BrandContext) -> Optional[StoreInsight]:
        if self.is_mock:
            logger.info("Database not available - skipping save operation")
            return None
            
        try:
            existing_insight = self.db.query(StoreInsight).filter(
                StoreInsight.store_url == brand_context.store_url
            ).first()
            
            if existing_insight:
                existing_insight.brand_name = brand_context.brand_name
                existing_insight.brand_description = brand_context.brand_description
                existing_insight.extracted_at = brand_context.extracted_at
                existing_insight.meta_data = brand_context.metadata
                
                self.db.query(Product).filter(Product.store_insight_id == existing_insight.id).delete()
                self.db.query(HeroProduct).filter(HeroProduct.store_insight_id == existing_insight.id).delete()
                self.db.query(Policy).filter(Policy.store_insight_id == existing_insight.id).delete()
                self.db.query(FAQ).filter(FAQ.store_insight_id == existing_insight.id).delete()
                self.db.query(SocialHandle).filter(SocialHandle.store_insight_id == existing_insight.id).delete()
                self.db.query(ContactInfo).filter(ContactInfo.store_insight_id == existing_insight.id).delete()
                self.db.query(ImportantLink).filter(ImportantLink.store_insight_id == existing_insight.id).delete()
                
                store_insight = existing_insight
            else:
                store_insight = StoreInsight(
                    store_url=brand_context.store_url,
                    brand_name=brand_context.brand_name,
                    brand_description=brand_context.brand_description,
                    extracted_at=brand_context.extracted_at,
                    meta_data=brand_context.metadata
                )
                self.db.add(store_insight)
                self.db.flush()
            
            for product in brand_context.product_catalog:
                db_product = Product(
                    store_insight_id=store_insight.id,
                    product_id=product.id,
                    title=product.title,
                    description=product.description,
                    price=product.price,
                    currency=product.currency,
                    images=product.images,
                    url=product.url,
                    available=product.available,
                    tags=product.tags,
                    category=product.category
                )
                self.db.add(db_product)
            
            for product in brand_context.hero_products:
                db_hero_product = HeroProduct(
                    store_insight_id=store_insight.id,
                    product_id=product.id,
                    title=product.title,
                    description=product.description,
                    price=product.price,
                    currency=product.currency,
                    images=product.images,
                    url=product.url,
                    available=product.available,
                    tags=product.tags,
                    category=product.category
                )
                self.db.add(db_hero_product)
            
            if brand_context.privacy_policy:
                db_policy = Policy(
                    store_insight_id=store_insight.id,
                    title=brand_context.privacy_policy.title,
                    content=brand_context.privacy_policy.content,
                    url=brand_context.privacy_policy.url,
                    policy_type='privacy'
                )
                self.db.add(db_policy)
            
            if brand_context.return_policy:
                db_policy = Policy(
                    store_insight_id=store_insight.id,
                    title=brand_context.return_policy.title,
                    content=brand_context.return_policy.content,
                    url=brand_context.return_policy.url,
                    policy_type='return'
                )
                self.db.add(db_policy)
            
            if brand_context.refund_policy:
                db_policy = Policy(
                    store_insight_id=store_insight.id,
                    title=brand_context.refund_policy.title,
                    content=brand_context.refund_policy.content,
                    url=brand_context.refund_policy.url,
                    policy_type='refund'
                )
                self.db.add(db_policy)
            
            for faq in brand_context.faqs:
                db_faq = FAQ(
                    store_insight_id=store_insight.id,
                    question=faq.question,
                    answer=faq.answer
                )
                self.db.add(db_faq)
            
            for social in brand_context.social_handles:
                db_social = SocialHandle(
                    store_insight_id=store_insight.id,
                    platform=social.platform,
                    url=social.url,
                    handle=social.handle
                )
                self.db.add(db_social)
            
            if brand_context.contact_info:
                db_contact = ContactInfo(
                    store_insight_id=store_insight.id,
                    email=brand_context.contact_info.email,
                    phone=brand_context.contact_info.phone,
                    address=brand_context.contact_info.address
                )
                self.db.add(db_contact)
            
            for link in brand_context.important_links:
                db_link = ImportantLink(
                    store_insight_id=store_insight.id,
                    title=link.title,
                    url=link.url,
                    description=link.description
                )
                self.db.add(db_link)
            
            self.db.commit()
            return store_insight
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving store insight: {str(e)}")
            raise e
    
    def get_store_insight(self, store_url: str) -> Optional[BrandContext]:
        if self.is_mock:
            logger.info("Database not available - no cached data available")
            return None
            
        try:
            store_insight = self.db.query(StoreInsight).filter(
                StoreInsight.store_url == store_url
            ).first()
            
            if not store_insight:
                return None
            
            return self._map_to_brand_context(store_insight)
            
        except Exception as e:
            logger.error(f"Error getting store insight: {str(e)}")
            raise e
    
    def get_all_store_insights(self) -> List[BrandContext]:
        if self.is_mock:
            logger.info("Database not available - no cached data available")
            return []
            
        try:
            store_insights = self.db.query(StoreInsight).all()
            return [self._map_to_brand_context(insight) for insight in store_insights]
            
        except Exception as e:
            logger.error(f"Error getting all store insights: {str(e)}")
            raise e
    
    def save_competitor_analysis(self, main_brand_id: int, competitor_id: int, analysis_summary: str) -> Optional[CompetitorAnalysis]:
        if self.is_mock:
            logger.info("Database not available - skipping competitor analysis save")
            return None
            
        try:
            competitor_analysis = CompetitorAnalysis(
                main_brand_id=main_brand_id,
                competitor_id=competitor_id,
                analysis_summary=analysis_summary
            )
            self.db.add(competitor_analysis)
            self.db.commit()
            return competitor_analysis
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving competitor analysis: {str(e)}")
            raise e
    
    def _map_to_brand_context(self, store_insight: StoreInsight) -> BrandContext:
        products = []
        for product in store_insight.products:
            products.append(ProductSchema(
                id=product.product_id,
                title=product.title,
                description=product.description,
                price=product.price,
                currency=product.currency,
                images=product.images or [],
                url=product.url,
                available=product.available,
                tags=product.tags or [],
                category=product.category
            ))
        
        hero_products = []
        for product in store_insight.hero_products:
            hero_products.append(ProductSchema(
                id=product.product_id,
                title=product.title,
                description=product.description,
                price=product.price,
                currency=product.currency,
                images=product.images or [],
                url=product.url,
                available=product.available,
                tags=product.tags or [],
                category=product.category
            ))
        
        privacy_policy = None
        return_policy = None
        refund_policy = None
        
        for policy in store_insight.policies:
            policy_schema = PolicySchema(
                title=policy.title,
                content=policy.content,
                url=policy.url
            )
            
            if policy.policy_type == 'privacy':
                privacy_policy = policy_schema
            elif policy.policy_type == 'return':
                return_policy = policy_schema
            elif policy.policy_type == 'refund':
                refund_policy = policy_schema
        
        faqs = []
        for faq in store_insight.faqs:
            faqs.append(FAQSchema(
                question=faq.question,
                answer=faq.answer
            ))
        
        social_handles = []
        for social in store_insight.social_handles:
            social_handles.append(SocialHandleSchema(
                platform=social.platform,
                url=social.url,
                handle=social.handle
            ))
        
        contact_info = ContactInfoSchema()
        if store_insight.contact_info:
            contact_info = ContactInfoSchema(
                email=store_insight.contact_info.email,
                phone=store_insight.contact_info.phone,
                address=store_insight.contact_info.address
            )
        
        important_links = []
        for link in store_insight.important_links:
            important_links.append(ImportantLinkSchema(
                title=link.title,
                url=link.url,
                description=link.description
            ))
        
        return BrandContext(
            store_url=store_insight.store_url,
            brand_name=store_insight.brand_name,
            brand_description=store_insight.brand_description,
            hero_products=hero_products,
            product_catalog=products,
            privacy_policy=privacy_policy,
            return_policy=return_policy,
            refund_policy=refund_policy,
            faqs=faqs,
            social_handles=social_handles,
            contact_info=contact_info,
            important_links=important_links,
            extracted_at=store_insight.extracted_at,
            metadata=store_insight.meta_data or {}
        ) 