import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import re
from typing import List, Optional, Dict, Any
from fake_useragent import UserAgent
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from app.models.schemas import (
    BrandContext, Product, Policy, FAQ, SocialHandle, 
    ContactInfo, ImportantLink, ErrorCode
)

logger = logging.getLogger(__name__)


class ShopifyScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = None
        self.driver = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': self.ua.random},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()
    
    def _setup_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-agent={self.ua.random}")
        
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=chrome_options
        )
    
    async def fetch_store_insights(self, website_url: str) -> BrandContext:
        try:
            if not website_url.startswith(('http://', 'https://')):
                website_url = f"https://{website_url}"
            
            brand_context = BrandContext(store_url=website_url)
            
            await self._extract_basic_info(website_url, brand_context)
            await self._extract_product_catalog(website_url, brand_context)
            await self._extract_hero_products(website_url, brand_context)
            await self._extract_policies(website_url, brand_context)
            await self._extract_faqs(website_url, brand_context)
            await self._extract_social_handles(website_url, brand_context)
            await self._extract_contact_info(website_url, brand_context)
            await self._extract_important_links(website_url, brand_context)
            
            return brand_context
            
        except Exception as e:
            logger.error(f"Error fetching store insights: {str(e)}")
            raise
    
    async def _extract_basic_info(self, website_url: str, brand_context: BrandContext):
        try:
            async with self.session.get(website_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    brand_name = self._extract_brand_name(soup)
                    if brand_name:
                        brand_context.brand_name = brand_name
                    
                    brand_description = self._extract_brand_description(soup)
                    if brand_description:
                        brand_context.brand_description = brand_description
                        
        except Exception as e:
            logger.warning(f"Error extracting basic info: {str(e)}")
    
    async def _extract_product_catalog(self, website_url: str, brand_context: BrandContext):
        try:
            products_url = urljoin(website_url, '/products.json')
            async with self.session.get(products_url) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get('products', [])
                    
                    for product_data in products:
                        product = self._parse_product_data(product_data, website_url)
                        if product:
                            brand_context.product_catalog.append(product)
                            
        except Exception as e:
            logger.warning(f"Error extracting product catalog: {str(e)}")
    
    async def _extract_hero_products(self, website_url: str, brand_context: BrandContext):
        try:
            async with self.session.get(website_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    hero_selectors = [
                        '.hero-product',
                        '.featured-product',
                        '.product-hero',
                        '.main-product',
                        '[data-product-id]',
                        '.product-card',
                        '.product-item'
                    ]
                    
                    for selector in hero_selectors:
                        products = soup.select(selector)
                        for product_elem in products[:5]:
                            product = self._parse_product_element(product_elem, website_url)
                            if product and product not in brand_context.hero_products:
                                brand_context.hero_products.append(product)
                                
        except Exception as e:
            logger.warning(f"Error extracting hero products: {str(e)}")
    
    async def _extract_policies(self, website_url: str, brand_context: BrandContext):
        policy_urls = {
            'privacy': ['/pages/privacy-policy', '/pages/privacy', '/privacy-policy', '/privacy'],
            'return': ['/pages/return-policy', '/pages/returns', '/return-policy', '/returns'],
            'refund': ['/pages/refund-policy', '/pages/refunds', '/refund-policy', '/refunds']
        }
        
        for policy_type, urls in policy_urls.items():
            for url_path in urls:
                try:
                    policy_url = urljoin(website_url, url_path)
                    async with self.session.get(policy_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            policy = self._parse_policy_page(soup, policy_url, policy_type)
                            if policy:
                                if policy_type == 'privacy':
                                    brand_context.privacy_policy = policy
                                elif policy_type == 'return':
                                    brand_context.return_policy = policy
                                elif policy_type == 'refund':
                                    brand_context.refund_policy = policy
                                break
                                
                except Exception as e:
                    logger.warning(f"Error extracting {policy_type} policy: {str(e)}")
    
    async def _extract_faqs(self, website_url: str, brand_context: BrandContext):
        faq_urls = [
            '/pages/faq',
            '/pages/faqs',
            '/faq',
            '/faqs',
            '/help',
            '/support'
        ]
        
        for url_path in faq_urls:
            try:
                faq_url = urljoin(website_url, url_path)
                async with self.session.get(faq_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        faqs = self._parse_faq_page(soup)
                        if faqs:
                            brand_context.faqs.extend(faqs)
                            break
                            
            except Exception as e:
                logger.warning(f"Error extracting FAQs: {str(e)}")
    
    async def _extract_social_handles(self, website_url: str, brand_context: BrandContext):
        try:
            async with self.session.get(website_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    social_handles = self._parse_social_handles(soup)
                    brand_context.social_handles.extend(social_handles)
                    
        except Exception as e:
            logger.warning(f"Error extracting social handles: {str(e)}")
    
    async def _extract_contact_info(self, website_url: str, brand_context: BrandContext):
        contact_urls = [
            '/pages/contact',
            '/contact',
            '/pages/contact-us',
            '/contact-us'
        ]
        
        for url_path in contact_urls:
            try:
                contact_url = urljoin(website_url, url_path)
                async with self.session.get(contact_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        contact_info = self._parse_contact_page(soup)
                        if contact_info:
                            brand_context.contact_info = contact_info
                            break
                            
            except Exception as e:
                logger.warning(f"Error extracting contact info: {str(e)}")
    
    async def _extract_important_links(self, website_url: str, brand_context: BrandContext):
        try:
            async with self.session.get(website_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    important_links = self._parse_important_links(soup, website_url)
                    brand_context.important_links.extend(important_links)
                    
        except Exception as e:
            logger.warning(f"Error extracting important links: {str(e)}")
    
    def _extract_brand_name(self, soup: BeautifulSoup) -> Optional[str]:
        selectors = [
            'title',
            'h1',
            '.brand-name',
            '.site-title',
            '.logo-text',
            '[data-brand-name]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text().strip():
                return element.get_text().strip()
        
        return None
    
    def _extract_brand_description(self, soup: BeautifulSoup) -> Optional[str]:
        selectors = [
            'meta[name="description"]',
            '.brand-description',
            '.site-description',
            '.hero-description',
            '.main-description'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if selector.startswith('meta'):
                    return element.get('content', '').strip()
                else:
                    return element.get_text().strip()
        
        return None
    
    def _parse_product_data(self, product_data: Dict, base_url: str) -> Optional[Product]:
        try:
            product_id = str(product_data.get('id', ''))
            title = product_data.get('title', '')
            description = product_data.get('body_html', '')
            
            variants = product_data.get('variants', [])
            price = '0'
            currency = 'USD'
            if variants:
                price = str(variants[0].get('price', '0'))
            
            images = []
            for image in product_data.get('images', []):
                if image.get('src'):
                    images.append(image['src'])
            
            url = urljoin(base_url, f"/products/{product_data.get('handle', '')}")
            
            return Product(
                id=product_id,
                title=title,
                description=description,
                price=price,
                currency=currency,
                images=images,
                url=url,
                available=product_data.get('available', True),
                tags=product_data.get('tags', []),
                category=product_data.get('product_type', '')
            )
        except Exception as e:
            logger.warning(f"Error parsing product data: {str(e)}")
            return None
    
    def _parse_product_element(self, element, base_url: str) -> Optional[Product]:
        try:
            title = element.get_text().strip()
            if not title:
                return None
            
            url = element.get('href') or element.find('a', href=True)
            if url:
                if isinstance(url, str):
                    product_url = urljoin(base_url, url)
                else:
                    product_url = urljoin(base_url, url.get('href', ''))
            else:
                product_url = ''
            
            return Product(
                id='',
                title=title,
                description='',
                price='0',
                currency='USD',
                images=[],
                url=product_url,
                available=True,
                tags=[],
                category=''
            )
        except Exception as e:
            logger.warning(f"Error parsing product element: {str(e)}")
            return None
    
    def _parse_policy_page(self, soup: BeautifulSoup, url: str, policy_type: str) -> Optional[Policy]:
        try:
            title = soup.find('h1') or soup.find('title')
            title_text = title.get_text().strip() if title else f"{policy_type.title()} Policy"
            
            content = soup.get_text()
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            return Policy(
                title=title_text,
                content=content,
                url=url
            )
        except Exception as e:
            logger.warning(f"Error parsing policy page: {str(e)}")
            return None
    
    def _parse_faq_page(self, soup: BeautifulSoup) -> List[FAQ]:
        faqs = []
        
        faq_selectors = [
            '.faq-item',
            '.faq-question',
            '.accordion-item',
            '[data-faq]'
        ]
        
        for selector in faq_selectors:
            elements = soup.select(selector)
            for element in elements:
                question_elem = element.find(['h3', 'h4', 'h5', '.question', '.faq-question'])
                answer_elem = element.find(['p', 'div', '.answer', '.faq-answer'])
                
                if question_elem and answer_elem:
                    question = question_elem.get_text().strip()
                    answer = answer_elem.get_text().strip()
                    
                    if question and answer:
                        faqs.append(FAQ(question=question, answer=answer))
        
        return faqs
    
    def _parse_social_handles(self, soup: BeautifulSoup) -> List[SocialHandle]:
        social_handles = []
        
        social_patterns = {
            'instagram': r'instagram\.com/([^/\s]+)',
            'facebook': r'facebook\.com/([^/\s]+)',
            'twitter': r'twitter\.com/([^/\s]+)',
            'tiktok': r'tiktok\.com/@([^/\s]+)',
            'youtube': r'youtube\.com/([^/\s]+)',
            'linkedin': r'linkedin\.com/([^/\s]+)'
        }
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            
            for platform, pattern in social_patterns.items():
                match = re.search(pattern, href)
                if match:
                    handle = self._extract_handle_from_url(href, platform)
                    if handle:
                        social_handles.append(SocialHandle(
                            platform=platform,
                            url=href,
                            handle=handle
                        ))
        
        return social_handles
    
    def _extract_handle_from_url(self, url: str, platform: str) -> Optional[str]:
        patterns = {
            'instagram': r'instagram\.com/([^/\s?]+)',
            'facebook': r'facebook\.com/([^/\s?]+)',
            'twitter': r'twitter\.com/([^/\s?]+)',
            'tiktok': r'tiktok\.com/@([^/\s?]+)',
            'youtube': r'youtube\.com/([^/\s?]+)',
            'linkedin': r'linkedin\.com/([^/\s?]+)'
        }
        
        pattern = patterns.get(platform)
        if pattern:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_contact_page(self, soup: BeautifulSoup) -> Optional[ContactInfo]:
        try:
            email = None
            phone = None
            address = None
            
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            phone_pattern = r'[\+]?[1-9][\d]{0,15}'
            
            text = soup.get_text()
            
            email_match = re.search(email_pattern, text)
            if email_match:
                email = email_match.group(0)
            
            phone_match = re.search(phone_pattern, text)
            if phone_match:
                phone = phone_match.group(0)
            
            address_elem = soup.find(['address', '.address', '.contact-address'])
            if address_elem:
                address = address_elem.get_text().strip()
            
            if email or phone or address:
                return ContactInfo(
                    email=email,
                    phone=phone,
                    address=address
                )
            
        except Exception as e:
            logger.warning(f"Error parsing contact page: {str(e)}")
        
        return None
    
    def _parse_important_links(self, soup: BeautifulSoup, base_url: str) -> List[ImportantLink]:
        important_links = []
        
        important_keywords = [
            'track', 'order', 'shipping', 'delivery',
            'blog', 'news', 'about', 'story',
            'help', 'support', 'contact',
            'size', 'guide', 'measurement'
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            text = link.get_text().strip().lower()
            
            for keyword in important_keywords:
                if keyword in text or keyword in href.lower():
                    url = urljoin(base_url, href)
                    important_links.append(ImportantLink(
                        title=link.get_text().strip(),
                        url=url,
                        description=f"Important link: {keyword}"
                    ))
                    break
        
        return important_links 