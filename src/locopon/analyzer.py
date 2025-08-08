#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DeepSeek AI Analyzer for Locopon
Intelligent analysis of Swedish retail offers
"""

import json
import logging
from typing import List, Optional
import openai
from datetime import datetime

from .models import Offer, OfferAnalysis, PriceCategory

logger = logging.getLogger(__name__)


class DeepSeekAnalyzer:
    """DeepSeek AI-powered offer analysis system"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = "deepseek-chat"
        
    def analyze_offer(self, offer: Offer) -> Optional[OfferAnalysis]:
        """Analyze a single offer using DeepSeek AI"""
        logger.info(f"Analyzing offer: {offer.name} ({offer.id})")
        
        try:
            # Prepare offer context
            offer_context = self._prepare_offer_context(offer)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(offer_context)
            
            # Get AI analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Swedish retail analyst specializing in grocery and consumer goods pricing, trends, and consumer behavior. Provide detailed, accurate analysis in JSON format."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse response
            analysis_data = self._parse_ai_response(response.choices[0].message.content)
            
            if analysis_data:
                return self._create_offer_analysis(offer.id, analysis_data)
            else:
                logger.warning(f"Failed to parse AI response for offer: {offer.id}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing offer {offer.id}: {e}")
            return None
    
    def analyze_batch(self, offers: List[Offer], max_batch_size: int = 10) -> List[OfferAnalysis]:
        """Analyze multiple offers in batches"""
        logger.info(f"Starting batch analysis of {len(offers)} offers")
        
        analyses = []
        
        # Process in batches to avoid rate limits
        for i in range(0, len(offers), max_batch_size):
            batch = offers[i:i + max_batch_size]
            logger.info(f"Analyzing batch {i//max_batch_size + 1}: {len(batch)} offers")
            
            for offer in batch:
                analysis = self.analyze_offer(offer)
                if analysis:
                    analyses.append(analysis)
                    logger.debug(f"Analysis completed: {offer.name}")
                else:
                    logger.warning(f"Analysis failed: {offer.name}")
        
        logger.info(f"Batch analysis complete: {len(analyses)} successful analyses")
        return analyses
    
    def _prepare_offer_context(self, offer: Offer) -> dict:
        """Prepare offer data for AI analysis"""
        context = {
            "name": offer.name,
            "description": offer.description,
            "price": offer.get_display_price(),
            "currency": offer.currency,
            "original_price": offer.original_price,
            "unit_price": offer.unit_price,
            "base_unit": offer.base_unit,
            "unit_size": f"{offer.unit_size_from}-{offer.unit_size_to} {offer.unit_symbol}" if offer.unit_size_from and offer.unit_size_to else None,
            "business": offer.business_name,
            "valid_period": f"{offer.valid_from} to {offer.valid_until}" if offer.valid_from and offer.valid_until else None,
        }
        
        # Remove None values
        return {k: v for k, v in context.items() if v is not None}
    
    def _create_analysis_prompt(self, offer_context: dict) -> str:
        """Create analysis prompt for DeepSeek AI"""
        
        prompt = f"""
Analyze this Swedish retail offer and provide a comprehensive assessment:

OFFER DETAILS:
{json.dumps(offer_context, ensure_ascii=False, indent=2)}

Please provide analysis in the following JSON format:
{{
    "category": "主要产品类别 (如: 食品, 日用品, 个护等)",
    "subcategory": "具体子类别 (如: 乳制品, 清洁用品等)", 
    "brand": "品牌名称 (如能识别)",
    "price_category": "excellent|good|average|poor",
    "value_score": "0-10评分 (10为最优价值)",
    "deal_quality": "简短评价优惠质量",
    "target_audience": "目标消费群体",
    "purchase_urgency": "low|medium|high",
    "seasonal_relevance": "季节性相关性描述",
    "recommendation": "购买建议 (1-2句话)",
    "pros": ["优势1", "优势2", "优势3"],
    "cons": ["劣势1", "劣势2"],
    "confidence_score": "0-1 (分析置信度)"
}}

Analysis Guidelines:
- Consider Swedish market context and pricing
- Evaluate value proposition objectively  
- Factor in unit pricing when available
- Consider typical Swedish consumer preferences
- Use Swedish/English mixed terminology as appropriate
- Be concise but informative

Respond with ONLY the JSON object, no additional text.
"""
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> Optional[dict]:
        """Parse AI response and extract analysis data"""
        try:
            # Clean response text
            response_text = response_text.strip()
            
            # Find JSON content
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                return json.loads(json_text)
            else:
                logger.warning("No JSON found in AI response")
                return None
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            return None
    
    def _create_offer_analysis(self, offer_id: str, analysis_data: dict) -> OfferAnalysis:
        """Create OfferAnalysis object from parsed AI data"""
        
        # Map price category string to enum
        price_category_map = {
            "excellent": PriceCategory.EXCELLENT,
            "good": PriceCategory.GOOD,
            "average": PriceCategory.AVERAGE,
            "poor": PriceCategory.POOR,
        }
        
        return OfferAnalysis(
            offer_id=offer_id,
            category=analysis_data.get("category"),
            subcategory=analysis_data.get("subcategory"),
            brand=analysis_data.get("brand"),
            price_category=price_category_map.get(analysis_data.get("price_category")),
            value_score=analysis_data.get("value_score"),
            deal_quality=analysis_data.get("deal_quality"),
            target_audience=analysis_data.get("target_audience"),
            purchase_urgency=analysis_data.get("purchase_urgency"),
            seasonal_relevance=analysis_data.get("seasonal_relevance"),
            recommendation=analysis_data.get("recommendation"),
            pros=analysis_data.get("pros", []),
            cons=analysis_data.get("cons", []),
            analysis_model=self.model,
            confidence_score=analysis_data.get("confidence_score"),
            processed_at=datetime.now(),
        )
    
    def generate_summary(self, offers: List[Offer], analyses: List[OfferAnalysis]) -> str:
        """Generate intelligent summary of all offers"""
        logger.info(f"Generating summary for {len(offers)} offers and {len(analyses)} analyses")
        
        try:
            # Prepare summary context
            summary_context = self._prepare_summary_context(offers, analyses)
            
            # Create summary prompt
            prompt = f"""
Based on the following Swedish retail offers and analyses, generate an intelligent summary:

OFFERS DATA:
{json.dumps(summary_context, ensure_ascii=False, indent=2)}

Please provide a comprehensive summary covering:
1. Overall deal quality and highlights
2. Best value offers (top 3-5)
3. Category distribution 
4. Price trends and insights
5. Shopping recommendations

Format the response as a well-structured, engaging summary suitable for Swedish consumers.
Use a mix of Swedish and English terms as appropriate.
Keep it concise but informative (max 500 words).
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Swedish retail expert providing consumer insights and shopping advice."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"发现 {len(offers)} 个优惠，其中 {len(analyses)} 个已完成分析。"
    
    def _prepare_summary_context(self, offers: List[Offer], analyses: List[OfferAnalysis]) -> dict:
        """Prepare context for summary generation"""
        
        # Create analysis lookup
        analysis_map = {a.offer_id: a for a in analyses}
        
        offers_with_analysis = []
        for offer in offers:
            analysis = analysis_map.get(offer.id)
            offer_data = {
                "name": offer.name,
                "price": offer.get_display_price(),
                "business": offer.business_name,
            }
            
            if analysis:
                offer_data.update({
                    "category": analysis.category,
                    "value_score": analysis.value_score,
                    "price_category": analysis.price_category.value if analysis.price_category else None,
                    "recommendation": analysis.recommendation,
                })
            
            offers_with_analysis.append(offer_data)
        
        return {
            "total_offers": len(offers),
            "analyzed_offers": len(analyses),
            "offers": offers_with_analysis[:20],  # Limit for context size
        }
    
    def health_check(self) -> bool:
        """Test DeepSeek API connectivity"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.error(f"DeepSeek health check failed: {e}")
            return False
