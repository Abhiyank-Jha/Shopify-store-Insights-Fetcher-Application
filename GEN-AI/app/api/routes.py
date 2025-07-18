from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import logging
from typing import List

from app.models.schemas import (
    StoreInsightsRequest, StoreInsightsResponse, CompetitorAnalysisRequest,
    CompetitorAnalysisResponse, ErrorCode, BrandContext
)
from app.services.shopify_scraper import ShopifyScraper
from app.services.competitor_analyzer import CompetitorAnalyzer
from app.repositories.store_repository import StoreRepository
from app.database.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/store-insights", response_model=StoreInsightsResponse)
async def get_store_insights(
    request: StoreInsightsRequest,
    db: Session = Depends(get_db)
):
    try:
        repository = StoreRepository(db)
        existing_insight = repository.get_store_insight(str(request.website_url))
        
        if existing_insight:
            return StoreInsightsResponse(
                success=True,
                data=existing_insight,
                message="Store insights retrieved from cache"
            )
        
        async with ShopifyScraper() as scraper:
            brand_context = await scraper.fetch_store_insights(str(request.website_url))
            
            saved_insight = repository.save_store_insight(brand_context)
            
            message = "Store insights successfully extracted"
            if saved_insight is None:
                message += " (not cached - database not available)"
            
            return StoreInsightsResponse(
                success=True,
                data=brand_context,
                message=message
            )
            
    except Exception as e:
        logger.error(f"Error fetching store insights: {str(e)}")
        
        error_code = ErrorCode.INTERNAL_ERROR
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        if "404" in str(e) or "not found" in str(e).lower():
            error_code = ErrorCode.WEBSITE_NOT_FOUND
            status_code = status.HTTP_404_NOT_FOUND
        elif "timeout" in str(e).lower():
            error_code = ErrorCode.TIMEOUT_ERROR
            status_code = status.HTTP_408_REQUEST_TIMEOUT
        elif "invalid" in str(e).lower():
            error_code = ErrorCode.INVALID_URL
            status_code = status.HTTP_400_BAD_REQUEST
        
        raise HTTPException(
            status_code=status_code,
            detail=StoreInsightsResponse(
                success=False,
                error=str(e),
                error_code=error_code,
                message="Failed to extract store insights"
            ).dict()
        )


@router.post("/competitor-analysis", response_model=CompetitorAnalysisResponse)
async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    db: Session = Depends(get_db)
):
    try:
        repository = StoreRepository(db)
        
        main_brand = repository.get_store_insight(str(request.website_url))
        if not main_brand:
            async with ShopifyScraper() as scraper:
                main_brand = await scraper.fetch_store_insights(str(request.website_url))
                repository.save_store_insight(main_brand)
        
        async with CompetitorAnalyzer() as analyzer:
            competitor_urls = await analyzer.find_competitors(
                str(request.website_url), 
                request.max_competitors
            )
            
            competitors = await analyzer.analyze_competitors(main_brand, competitor_urls)
            analysis_summary = await analyzer.generate_analysis_summary(main_brand, competitors)
        
        for competitor in competitors:
            repository.save_store_insight(competitor)
        
        return CompetitorAnalysisResponse(
            main_brand=main_brand,
            competitors=competitors,
            analysis_summary=analysis_summary
        )
        
    except Exception as e:
        logger.error(f"Error analyzing competitors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze competitors: {str(e)}"
        )


@router.get("/store-insights/{store_url:path}", response_model=StoreInsightsResponse)
async def get_cached_store_insights(
    store_url: str,
    db: Session = Depends(get_db)
):
    try:
        repository = StoreRepository(db)
        insight = repository.get_store_insight(store_url)
        
        if not insight:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store insights not found in cache"
            )
        
        return StoreInsightsResponse(
            success=True,
            data=insight,
            message="Store insights retrieved from cache"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving cached store insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cached store insights: {str(e)}"
        )


@router.get("/store-insights", response_model=List[BrandContext])
async def get_all_store_insights(db: Session = Depends(get_db)):
    try:
        repository = StoreRepository(db)
        insights = repository.get_all_store_insights()
        return insights
        
    except Exception as e:
        logger.error(f"Error retrieving all store insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve store insights: {str(e)}"
        )


@router.delete("/store-insights/{store_url:path}")
async def delete_store_insights(
    store_url: str,
    db: Session = Depends(get_db)
):
    try:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Delete functionality not implemented yet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting store insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete store insights: {str(e)}"
        ) 