#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data Models for Locopon System
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json


class OfferStatus(Enum):
    """Offer processing status"""
    NEW = "new"
    PROCESSED = "processed"
    ANALYZED = "analyzed"
    NOTIFIED = "notified"
    EXPIRED = "expired"


class PriceCategory(Enum):
    """Price category classification"""
    EXCELLENT = "excellent"  # 超值优惠
    GOOD = "good"           # 很好的价格
    AVERAGE = "average"      # 平均价格
    POOR = "poor"           # 价格偏高


@dataclass
class Offer:
    """Swedish retail offer data model"""
    
    # Core identification
    id: str
    publication_id: str
    business_id: str
    
    # Product information
    name: str
    description: Optional[str] = None
    
    # Pricing
    price: Optional[float] = None
    currency: str = "SEK"
    membership_price: Optional[float] = None
    original_price: Optional[float] = None
    unit_price: Optional[float] = None
    base_unit: Optional[str] = None
    
    # Images
    image_url: Optional[str] = None
    image_large_url: Optional[str] = None
    
    # Validity
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    
    # Product details
    unit_size_from: Optional[int] = None
    unit_size_to: Optional[int] = None
    unit_symbol: Optional[str] = None
    
    # Business information
    business_name: Optional[str] = None
    business_logo: Optional[str] = None
    
    # System fields
    discovered_at: datetime = field(default_factory=datetime.now)
    status: OfferStatus = OfferStatus.NEW
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "publication_id": self.publication_id,
            "business_id": self.business_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "currency": self.currency,
            "membership_price": self.membership_price,
            "original_price": self.original_price,
            "unit_price": self.unit_price,
            "base_unit": self.base_unit,
            "image_url": self.image_url,
            "image_large_url": self.image_large_url,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "unit_size_from": self.unit_size_from,
            "unit_size_to": self.unit_size_to,
            "unit_symbol": self.unit_symbol,
            "business_name": self.business_name,
            "business_logo": self.business_logo,
            "discovered_at": self.discovered_at.isoformat(),
            "status": self.status.value,
        }
    
    @classmethod
    def from_ereklamblad_data(cls, data: Dict[str, Any]) -> "Offer":
        """Create Offer from eReklamblad API data"""
        return cls(
            id=data.get("publicId", ""),
            publication_id=data.get("publicationPublicId", ""),
            business_id=data.get("businessPublicId", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            price=data.get("price"),
            currency=data.get("currencyCode", "SEK"),
            membership_price=data.get("membershipPrice"),
            unit_price=data.get("unitPrice"),
            base_unit=data.get("baseUnit"),
            image_url=data.get("image"),
            image_large_url=data.get("imageLarge"),
            valid_from=datetime.fromisoformat(data["validFrom"].replace("Z", "+00:00")) if data.get("validFrom") else None,
            valid_until=datetime.fromisoformat(data["validUntil"].replace("Z", "+00:00")) if data.get("validUntil") else None,
            unit_size_from=data.get("unitSizeFrom"),
            unit_size_to=data.get("unitSizeTo"),
            unit_symbol=data.get("unitSymbol"),
            business_name=data.get("business", {}).get("name"),
            business_logo=data.get("business", {}).get("positiveLogoImage"),
        )
    
    def get_display_price(self) -> float:
        """Get the most relevant price for display"""
        return self.membership_price or self.price or 0.0
    
    def is_valid(self) -> bool:
        """Check if offer is currently valid"""
        now = datetime.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        return True


@dataclass  
class OfferAnalysis:
    """AI analysis results for an offer"""
    
    offer_id: str
    
    # AI Analysis Results
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    
    # Value Assessment
    price_category: Optional[PriceCategory] = None
    value_score: Optional[float] = None  # 0-10 scale
    deal_quality: Optional[str] = None
    
    # Consumer Insights
    target_audience: Optional[str] = None
    purchase_urgency: Optional[str] = None  # low, medium, high
    seasonal_relevance: Optional[str] = None
    
    # Recommendations
    recommendation: Optional[str] = None
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    
    # AI Processing
    analysis_model: str = "deepseek-chat"
    confidence_score: Optional[float] = None
    processed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "offer_id": self.offer_id,
            "category": self.category,
            "subcategory": self.subcategory,
            "brand": self.brand,
            "price_category": self.price_category.value if self.price_category else None,
            "value_score": self.value_score,
            "deal_quality": self.deal_quality,
            "target_audience": self.target_audience,
            "purchase_urgency": self.purchase_urgency,
            "seasonal_relevance": self.seasonal_relevance,
            "recommendation": self.recommendation,
            "pros": self.pros,
            "cons": self.cons,
            "analysis_model": self.analysis_model,
            "confidence_score": self.confidence_score,
            "processed_at": self.processed_at.isoformat(),
        }


@dataclass
class SystemStatus:
    """System health and performance metrics"""
    
    # Basic Status
    is_running: bool = False
    last_scan: Optional[datetime] = None
    next_scan: Optional[datetime] = None
    
    # Performance Metrics
    total_offers_discovered: int = 0
    offers_this_session: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    
    # AI Analysis Stats
    offers_analyzed: int = 0
    analysis_success_rate: float = 0.0
    
    # Notification Stats
    notifications_sent: int = 0
    last_notification: Optional[datetime] = None
    
    # Error Tracking
    last_error: Optional[str] = None
    error_count: int = 0
    
    # System Resources
    memory_usage_mb: Optional[float] = None
    disk_usage_mb: Optional[float] = None
    
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_offers_discovered == 0:
            return 0.0
        return (self.successful_extractions / self.total_offers_discovered) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_running": self.is_running,
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "next_scan": self.next_scan.isoformat() if self.next_scan else None,
            "total_offers_discovered": self.total_offers_discovered,
            "offers_this_session": self.offers_this_session,
            "successful_extractions": self.successful_extractions,
            "failed_extractions": self.failed_extractions,
            "offers_analyzed": self.offers_analyzed,
            "analysis_success_rate": self.analysis_success_rate,
            "notifications_sent": self.notifications_sent,
            "last_notification": self.last_notification.isoformat() if self.last_notification else None,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "memory_usage_mb": self.memory_usage_mb,
            "disk_usage_mb": self.disk_usage_mb,
            "updated_at": self.updated_at.isoformat(),
            "success_rate": self.get_success_rate(),
        }


@dataclass
class NotificationMessage:
    """Telegram notification message structure"""
    
    title: str
    content: str
    offers: List[Offer] = field(default_factory=list)
    analysis: Optional[List[OfferAnalysis]] = None
    message_type: str = "summary"  # summary, alert, status
    priority: str = "normal"  # low, normal, high
    
    def format_telegram_message(self) -> str:
        """Format message for Telegram"""
        message_parts = [
            f"🎯 *{self.title}*",
            "",
            self.content
        ]
        
        if self.offers:
            message_parts.extend([
                "",
                "📦 *发现的优惠:*"
            ])
            
            for offer in self.offers[:5]:  # Limit to 5 offers
                price_text = f"{offer.get_display_price():.1f} {offer.currency}"
                message_parts.append(
                    f"• {offer.name} - {price_text}"
                )
            
            if len(self.offers) > 5:
                message_parts.append(f"...还有 {len(self.offers) - 5} 个优惠")
        
        return "\n".join(message_parts)
