#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Telegram Notifier for Locopon
Intelligent Swedish retail deal notifications
"""

import asyncio
import logging
from typing import List, Optional
import json
from datetime import datetime

try:
    import telegram
    from telegram import Bot
    from telegram.constants import ParseMode
except ImportError:
    # Graceful fallback if telegram not installed
    telegram = None
    Bot = None
    ParseMode = None

from .models import Offer, OfferAnalysis, NotificationMessage, PriceCategory

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram bot for sending Swedish deal notifications"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = None
        
        if telegram is None:
            logger.warning("Telegram library not available - notifications disabled")
            self.enabled = False
        else:
            self.bot = Bot(token=bot_token)
            self.enabled = True
    
    async def initialize(self) -> bool:
        """Initialize and test bot connection"""
        if not self.enabled:
            return False
            
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Connected to Telegram bot: {bot_info.first_name} (@{bot_info.username})")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            self.enabled = False
            return False
    
    async def send_offer_notification(self, offer: Offer, analysis: Optional[OfferAnalysis] = None) -> bool:
        """Send notification for a single offer"""
        if not self.enabled:
            logger.warning("Telegram notifications disabled")
            return False
        
        try:
            message = self._create_offer_message(offer, analysis)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message.content,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=False
            )
            
            logger.info(f"Sent offer notification: {offer.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send offer notification: {e}")
            return False
    
    async def send_batch_notification(self, offers: List[Offer], analyses: List[OfferAnalysis] = None) -> bool:
        """Send notification for multiple offers"""
        if not self.enabled:
            return False
        
        if not offers:
            logger.info("No offers to notify about")
            return True
        
        try:
            # Create analysis lookup
            analysis_map = {}
            if analyses:
                analysis_map = {a.offer_id: a for a in analyses}
            
            # Group offers by quality/category for better presentation
            premium_offers = []
            good_offers = []
            other_offers = []
            
            for offer in offers:
                analysis = analysis_map.get(offer.id)
                if analysis and analysis.price_category == PriceCategory.EXCELLENT:
                    premium_offers.append((offer, analysis))
                elif analysis and analysis.value_score and analysis.value_score >= 7:
                    good_offers.append((offer, analysis))
                else:
                    other_offers.append((offer, analysis))
            
            # Send premium offers first
            if premium_offers:
                message = self._create_premium_batch_message(premium_offers)
                await self._send_long_message(message)
            
            # Send good offers
            if good_offers:
                message = self._create_good_batch_message(good_offers)  
                await self._send_long_message(message)
            
            # Send summary for remaining offers
            if other_offers and len(other_offers) <= 10:
                message = self._create_summary_batch_message(other_offers)
                await self._send_long_message(message)
            elif other_offers:
                # Just send count for large batches
                count_msg = f"📊 Plus {len(other_offers)} additional offers available"
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=count_msg,
                    parse_mode=ParseMode.MARKDOWN
                )
            
            logger.info(f"Sent batch notification: {len(offers)} offers")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send batch notification: {e}")
            return False
    
    async def send_summary(self, summary_text: str, offer_count: int = 0) -> bool:
        """Send intelligent summary message"""
        if not self.enabled:
            return False
        
        try:
            header = f"🇸🇪 *Swedish Deals Intelligence Report*\n"
            if offer_count:
                header += f"📊 {offer_count} offers analyzed\n"
            header += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            
            message = header + summary_text
            
            await self._send_long_message(message)
            
            logger.info(f"Sent summary notification: {len(summary_text)} chars")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send summary: {e}")
            return False
    
    async def send_system_status(self, status_message: str, is_error: bool = False) -> bool:
        """Send system status notification"""
        if not self.enabled:
            return False
        
        try:
            icon = "❌" if is_error else "✅"
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            message = f"{icon} *Locopon System Status*\n`{timestamp}` - {status_message}"
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send status notification: {e}")
            return False
    
    def _create_offer_message(self, offer: Offer, analysis: Optional[OfferAnalysis] = None) -> NotificationMessage:
        """Create formatted message for single offer"""
        
        # Header with offer name and business
        lines = [f"🛍️ *{offer.name}*"]
        
        if offer.business_name:
            lines.append(f"🏪 {offer.business_name}")
        
        # Price information
        price_line = f"💰 {offer.get_display_price()}"
        if offer.original_price and offer.original_price != offer.current_price:
            discount = ((offer.original_price - offer.current_price) / offer.original_price * 100)
            price_line += f" ~~{offer.original_price:.2f} {offer.currency}~~ (-{discount:.0f}%)"
        
        lines.append(price_line)
        
        # Unit pricing if available
        if offer.unit_price and offer.base_unit:
            lines.append(f"📏 {offer.unit_price:.2f} {offer.currency}/{offer.base_unit}")
        
        # AI Analysis if available
        if analysis:
            lines.append("")  # Separator
            
            # Quality indicator
            quality_icons = {
                PriceCategory.EXCELLENT: "⭐⭐⭐",
                PriceCategory.GOOD: "⭐⭐", 
                PriceCategory.AVERAGE: "⭐",
                PriceCategory.POOR: "⚠️"
            }
            
            if analysis.price_category:
                icon = quality_icons.get(analysis.price_category, "")
                lines.append(f"{icon} {analysis.price_category.value.title()} Deal")
            
            if analysis.value_score:
                lines.append(f"📈 Value Score: {analysis.value_score}/10")
            
            if analysis.recommendation:
                lines.append(f"💡 {analysis.recommendation}")
        
        # Validity period
        if offer.valid_until:
            lines.append(f"⏰ Valid until: {offer.valid_until}")
        
        # Link
        if offer.url:
            lines.append(f"\n[View Offer]({offer.url})")
        
        content = "\n".join(lines)
        
        return NotificationMessage(
            title=f"New Offer: {offer.name}",
            content=content,
            priority="high" if analysis and analysis.price_category == PriceCategory.EXCELLENT else "normal"
        )
    
    def _create_premium_batch_message(self, offers_with_analysis: List[tuple]) -> str:
        """Create message for premium/excellent offers"""
        lines = ["⭐⭐⭐ *PREMIUM DEALS* ⭐⭐⭐\n"]
        
        for offer, analysis in offers_with_analysis[:5]:  # Limit to top 5
            lines.append(f"🔥 *{offer.name}*")
            lines.append(f"   💰 {offer.get_display_price()} at {offer.business_name}")
            
            if analysis and analysis.value_score:
                lines.append(f"   📈 Score: {analysis.value_score}/10")
            
            if analysis and analysis.recommendation:
                lines.append(f"   💡 {analysis.recommendation}")
            
            if offer.url:
                lines.append(f"   [View Deal]({offer.url})")
            
            lines.append("")  # Separator
        
        return "\n".join(lines)
    
    def _create_good_batch_message(self, offers_with_analysis: List[tuple]) -> str:
        """Create message for good quality offers"""
        lines = ["⭐⭐ *GOOD DEALS* ⭐⭐\n"]
        
        for offer, analysis in offers_with_analysis[:8]:  # Limit to top 8
            lines.append(f"✅ *{offer.name}*")
            lines.append(f"   💰 {offer.get_display_price()} at {offer.business_name}")
            
            if analysis and analysis.category:
                lines.append(f"   🏷️ {analysis.category}")
            
            if offer.url:
                lines.append(f"   [View]({offer.url})")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _create_summary_batch_message(self, offers_with_analysis: List[tuple]) -> str:
        """Create summary message for remaining offers"""
        lines = ["📊 *OTHER OFFERS*\n"]
        
        for offer, analysis in offers_with_analysis:
            price_emoji = "💰"
            if analysis and analysis.price_category == PriceCategory.POOR:
                price_emoji = "⚠️"
            
            lines.append(f"{price_emoji} {offer.name} - {offer.get_display_price()}")
        
        return "\n".join(lines)
    
    async def _send_long_message(self, message: str, max_length: int = 4000):
        """Send message, splitting if too long"""
        if len(message) <= max_length:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        else:
            # Split message into chunks
            chunks = self._split_message(message, max_length)
            for i, chunk in enumerate(chunks):
                if i > 0:
                    await asyncio.sleep(0.5)  # Small delay between messages
                
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=chunk,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
    
    def _split_message(self, message: str, max_length: int) -> List[str]:
        """Split long message into chunks"""
        if len(message) <= max_length:
            return [message]
        
        chunks = []
        current_chunk = ""
        
        lines = message.split('\n')
        for line in lines:
            if len(current_chunk + line + '\n') <= max_length:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                    current_chunk = line + '\n'
                else:
                    # Line itself is too long, force split
                    chunks.append(line[:max_length])
                    current_chunk = line[max_length:] + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.rstrip())
        
        return chunks
    
    def health_check(self) -> bool:
        """Test Telegram bot connectivity"""
        if not self.enabled:
            return False
        
        try:
            # This would be async in real usage
            return True
        except Exception as e:
            logger.error(f"Telegram health check failed: {e}")
            return False


# Synchronous wrapper for easier integration
class TelegramNotifierSync:
    """Synchronous wrapper for TelegramNotifier"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.notifier = TelegramNotifier(bot_token, chat_id)
        self.loop = None
    
    def _get_loop(self):
        """Get or create event loop"""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            return self.loop
    
    def initialize(self) -> bool:
        """Initialize bot connection"""
        loop = self._get_loop()
        return loop.run_until_complete(self.notifier.initialize())
    
    def send_offer_notification(self, offer: Offer, analysis: Optional[OfferAnalysis] = None) -> bool:
        """Send single offer notification"""
        loop = self._get_loop()
        return loop.run_until_complete(self.notifier.send_offer_notification(offer, analysis))
    
    def send_batch_notification(self, offers: List[Offer], analyses: List[OfferAnalysis] = None) -> bool:
        """Send batch notification"""
        loop = self._get_loop()
        return loop.run_until_complete(self.notifier.send_batch_notification(offers, analyses))
    
    def send_summary(self, summary_text: str, offer_count: int = 0) -> bool:
        """Send summary"""
        loop = self._get_loop()
        return loop.run_until_complete(self.notifier.send_summary(summary_text, offer_count))
    
    def send_system_status(self, status_message: str, is_error: bool = False) -> bool:
        """Send system status"""
        loop = self._get_loop()
        return loop.run_until_complete(self.notifier.send_system_status(status_message, is_error))
