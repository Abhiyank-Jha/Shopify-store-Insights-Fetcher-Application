import asyncio
import aiohttp
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from fake_useragent import UserAgent

from app.models.schemas import BrandContext
from app.services.shopify_scraper import ShopifyScraper

logger = logging.getLogger(__name__)


class CompetitorAnalyzer:
    """Service for analyzing competitors of a given brand"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': self.ua.random},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def find_competitors(self, website_url: str, max_competitors: int = 5) -> List[str]:
        """Find competitors for a given brand website"""
        try:
            competitors = []
            
            # Extract brand name from URL
            brand_name = self._extract_brand_name_from_url(website_url)
            if not brand_name:
                return competitors
            
            # Search for competitors using various strategies
            search_queries = [
                f"{brand_name} competitors",
                f"similar brands to {brand_name}",
                f"alternative to {brand_name}",
                f"brands like {brand_name}"
            ]
            
            for query in search_queries:
                if len(competitors) >= max_competitors:
                    break
                    
                search_results = await self._search_web(query)
                shopify_urls = self._extract_shopify_urls(search_results)
                
                for url in shopify_urls:
                    if url not in competitors and url != website_url:
                        competitors.append(url)
                        if len(competitors) >= max_competitors:
                            break
            
            return competitors[:max_competitors]
            
        except Exception as e:
            logger.error(f"Error finding competitors: {str(e)}")
            return []
    
    async def analyze_competitors(self, main_brand: BrandContext, competitor_urls: List[str]) -> List[BrandContext]:
        """Analyze competitor stores and return their insights"""
        competitor_insights = []
        
        try:
            # Use the ShopifyScraper to get insights for each competitor
            async with ShopifyScraper() as scraper:
                for url in competitor_urls:
                    try:
                        competitor_insight = await scraper.fetch_store_insights(url)
                        competitor_insights.append(competitor_insight)
                    except Exception as e:
                        logger.warning(f"Error analyzing competitor {url}: {str(e)}")
                        continue
            
            return competitor_insights
            
        except Exception as e:
            logger.error(f"Error analyzing competitors: {str(e)}")
            return competitor_insights
    
    def _extract_brand_name_from_url(self, url: str) -> Optional[str]:
        """Extract brand name from website URL"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Remove common domain suffixes
            domain = re.sub(r'\.(com|co\.in|in|org|net)$', '', domain)
            
            # Remove www prefix
            domain = re.sub(r'^www\.', '', domain)
            
            return domain
            
        except Exception:
            return None
    
    async def _search_web(self, query: str) -> List[str]:
        """Simulate web search results (in a real implementation, you'd use a search API)"""
        # This is a simplified implementation
        # In production, you'd integrate with Google Search API, Bing API, or similar
        
        # For demo purposes, return some common competitor patterns
        search_results = []
        
        try:
            # Simulate search by looking for common competitor patterns
            competitor_patterns = [
                "competitor1.com",
                "competitor2.com", 
                "competitor3.com",
                "similar-brand.com",
                "alternative-store.com"
            ]
            
            # In a real implementation, you'd make actual search API calls
            # For now, return mock results
            search_results = competitor_patterns
            
        except Exception as e:
            logger.warning(f"Error in web search: {str(e)}")
        
        return search_results
    
    def _extract_shopify_urls(self, search_results: List[str]) -> List[str]:
        """Extract Shopify URLs from search results"""
        shopify_urls = []
        
        for result in search_results:
            # Check if it looks like a Shopify store
            if self._is_likely_shopify_store(result):
                shopify_urls.append(result)
        
        return shopify_urls
    
    def _is_likely_shopify_store(self, url: str) -> bool:
        """Check if a URL is likely a Shopify store"""
        try:
            # Common Shopify indicators
            shopify_indicators = [
                '.myshopify.com',
                'shopify',
                'cart',
                'products'
            ]
            
            url_lower = url.lower()
            
            # Check for Shopify-specific patterns
            for indicator in shopify_indicators:
                if indicator in url_lower:
                    return True
            
            # Additional checks could be added here
            # For example, checking for common Shopify page structures
            
            return False
            
        except Exception:
            return False
    
    async def generate_analysis_summary(self, main_brand: BrandContext, competitors: List[BrandContext]) -> str:
        """Generate a summary analysis comparing the main brand with competitors"""
        try:
            summary_parts = []
            
            # Basic comparison
            summary_parts.append(f"Analysis Summary for {main_brand.brand_name or 'Main Brand'}")
            summary_parts.append(f"Total competitors analyzed: {len(competitors)}")
            
            # Product catalog comparison
            main_product_count = len(main_brand.product_catalog)
            competitor_avg_products = sum(len(c.product_catalog) for c in competitors) / max(len(competitors), 1)
            
            summary_parts.append(f"\nProduct Catalog:")
            summary_parts.append(f"- Main brand products: {main_product_count}")
            summary_parts.append(f"- Average competitor products: {competitor_avg_products:.1f}")
            
            # Social media presence comparison
            main_social_count = len(main_brand.social_handles)
            competitor_avg_social = sum(len(c.social_handles) for c in competitors) / max(len(competitors), 1)
            
            summary_parts.append(f"\nSocial Media Presence:")
            summary_parts.append(f"- Main brand social handles: {main_social_count}")
            summary_parts.append(f"- Average competitor social handles: {competitor_avg_social:.1f}")
            
            # FAQ comparison
            main_faq_count = len(main_brand.faqs)
            competitor_avg_faqs = sum(len(c.faqs) for c in competitors) / max(len(competitors), 1)
            
            summary_parts.append(f"\nCustomer Support (FAQs):")
            summary_parts.append(f"- Main brand FAQs: {main_faq_count}")
            summary_parts.append(f"- Average competitor FAQs: {competitor_avg_faqs:.1f}")
            
            # Policy completeness
            main_policies = sum(1 for p in [main_brand.privacy_policy, main_brand.return_policy, main_brand.refund_policy] if p)
            competitor_avg_policies = sum(
                sum(1 for p in [c.privacy_policy, c.return_policy, c.refund_policy] if p)
                for c in competitors
            ) / max(len(competitors), 1)
            
            summary_parts.append(f"\nPolicy Completeness:")
            summary_parts.append(f"- Main brand policies: {main_policies}/3")
            summary_parts.append(f"- Average competitor policies: {competitor_avg_policies:.1f}/3")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {str(e)}")
            return "Unable to generate analysis summary due to an error." 