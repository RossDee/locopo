#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database Manager for Locopon
SQLite-based data storage and management for Swedish retail offers
"""

import sqlite3
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
from pathlib import Path

from .models import Offer, OfferAnalysis, SystemStatus, PriceCategory

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite database manager for Locopon system"""
    
    def __init__(self, db_path: str = "data/locopon.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database schema"""
        logger.info(f"Initializing database: {self.db_path}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create offers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    current_price REAL,
                    original_price REAL,
                    currency TEXT DEFAULT 'SEK',
                    unit_price REAL,
                    base_unit TEXT,
                    unit_size_from REAL,
                    unit_size_to REAL,
                    unit_symbol TEXT,
                    business_name TEXT,
                    business_id TEXT,
                    publication_name TEXT,
                    url TEXT,
                    image_url TEXT,
                    valid_from TEXT,
                    valid_until TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    source_data TEXT,  -- JSON blob for raw data
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create offer_analyses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offer_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    offer_id TEXT NOT NULL,
                    category TEXT,
                    subcategory TEXT,
                    brand TEXT,
                    price_category TEXT,
                    value_score REAL,
                    deal_quality TEXT,
                    target_audience TEXT,
                    purchase_urgency TEXT,
                    seasonal_relevance TEXT,
                    recommendation TEXT,
                    pros TEXT,  -- JSON array
                    cons TEXT,  -- JSON array
                    analysis_model TEXT,
                    confidence_score REAL,
                    processed_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (offer_id) REFERENCES offers (id)
                )
            ''')
            
            # Create system_status table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    last_run TEXT,
                    next_run TEXT,
                    run_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Create scraping_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    total_offers INTEGER DEFAULT 0,
                    new_offers INTEGER DEFAULT 0,
                    updated_offers INTEGER DEFAULT 0,
                    failed_offers INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running',
                    error_message TEXT,
                    source_info TEXT  -- JSON blob
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_offers_business ON offers(business_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_offers_created ON offers(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_offers_active ON offers(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_offer ON offer_analyses(offer_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_category ON offer_analyses(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_started ON scraping_sessions(started_at)')
            
            conn.commit()
            logger.info("Database schema initialized successfully")
    
    def save_offer(self, offer: Offer) -> bool:
        """Save or update an offer"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if offer exists
                cursor.execute('SELECT id FROM offers WHERE id = ?', (offer.id,))
                exists = cursor.fetchone() is not None
                
                now = datetime.now().isoformat()
                
                if exists:
                    # Update existing offer
                    cursor.execute('''
                        UPDATE offers SET
                            name = ?, description = ?, current_price = ?, original_price = ?,
                            currency = ?, unit_price = ?, base_unit = ?, unit_size_from = ?,
                            unit_size_to = ?, unit_symbol = ?, business_name = ?, business_id = ?,
                            publication_name = ?, url = ?, image_url = ?, valid_from = ?,
                            valid_until = ?, updated_at = ?, source_data = ?
                        WHERE id = ?
                    ''', (
                        offer.name, offer.description, offer.current_price, offer.original_price,
                        offer.currency, offer.unit_price, offer.base_unit, offer.unit_size_from,
                        offer.unit_size_to, offer.unit_symbol, offer.business_name, offer.business_id,
                        offer.publication_name, offer.url, offer.image_url, offer.valid_from,
                        offer.valid_until, now, json.dumps(offer.source_data) if offer.source_data else None,
                        offer.id
                    ))
                    logger.debug(f"Updated offer: {offer.name}")
                else:
                    # Insert new offer
                    cursor.execute('''
                        INSERT INTO offers (
                            id, name, description, current_price, original_price, currency,
                            unit_price, base_unit, unit_size_from, unit_size_to, unit_symbol,
                            business_name, business_id, publication_name, url, image_url,
                            valid_from, valid_until, created_at, updated_at, source_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        offer.id, offer.name, offer.description, offer.current_price, offer.original_price,
                        offer.currency, offer.unit_price, offer.base_unit, offer.unit_size_from,
                        offer.unit_size_to, offer.unit_symbol, offer.business_name, offer.business_id,
                        offer.publication_name, offer.url, offer.image_url, offer.valid_from,
                        offer.valid_until, now, now, json.dumps(offer.source_data) if offer.source_data else None
                    ))
                    logger.debug(f"Inserted new offer: {offer.name}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving offer {offer.id}: {e}")
            return False
    
    def save_offers_batch(self, offers: List[Offer]) -> int:
        """Save multiple offers efficiently"""
        saved_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                for offer in offers:
                    try:
                        # Check existence
                        cursor.execute('SELECT id FROM offers WHERE id = ?', (offer.id,))
                        exists = cursor.fetchone() is not None
                        
                        if exists:
                            cursor.execute('''
                                UPDATE offers SET
                                    name = ?, description = ?, current_price = ?, original_price = ?,
                                    currency = ?, unit_price = ?, base_unit = ?, unit_size_from = ?,
                                    unit_size_to = ?, unit_symbol = ?, business_name = ?, business_id = ?,
                                    publication_name = ?, url = ?, image_url = ?, valid_from = ?,
                                    valid_until = ?, updated_at = ?, source_data = ?
                                WHERE id = ?
                            ''', (
                                offer.name, offer.description, offer.current_price, offer.original_price,
                                offer.currency, offer.unit_price, offer.base_unit, offer.unit_size_from,
                                offer.unit_size_to, offer.unit_symbol, offer.business_name, offer.business_id,
                                offer.publication_name, offer.url, offer.image_url, offer.valid_from,
                                offer.valid_until, now, json.dumps(offer.source_data) if offer.source_data else None,
                                offer.id
                            ))
                        else:
                            cursor.execute('''
                                INSERT INTO offers (
                                    id, name, description, current_price, original_price, currency,
                                    unit_price, base_unit, unit_size_from, unit_size_to, unit_symbol,
                                    business_name, business_id, publication_name, url, image_url,
                                    valid_from, valid_until, created_at, updated_at, source_data
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                offer.id, offer.name, offer.description, offer.current_price, offer.original_price,
                                offer.currency, offer.unit_price, offer.base_unit, offer.unit_size_from,
                                offer.unit_size_to, offer.unit_symbol, offer.business_name, offer.business_id,
                                offer.publication_name, offer.url, offer.image_url, offer.valid_from,
                                offer.valid_until, now, now, json.dumps(offer.source_data) if offer.source_data else None
                            ))
                        
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error saving individual offer {offer.id}: {e}")
                
                conn.commit()
                logger.info(f"Batch saved {saved_count}/{len(offers)} offers")
                
        except Exception as e:
            logger.error(f"Error in batch save: {e}")
        
        return saved_count
    
    def save_analysis(self, analysis: OfferAnalysis) -> bool:
        """Save offer analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO offer_analyses (
                        offer_id, category, subcategory, brand, price_category, value_score,
                        deal_quality, target_audience, purchase_urgency, seasonal_relevance,
                        recommendation, pros, cons, analysis_model, confidence_score,
                        processed_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis.offer_id, analysis.category, analysis.subcategory, analysis.brand,
                    analysis.price_category.value if analysis.price_category else None,
                    analysis.value_score, analysis.deal_quality, analysis.target_audience,
                    analysis.purchase_urgency, analysis.seasonal_relevance, analysis.recommendation,
                    json.dumps(analysis.pros) if analysis.pros else None,
                    json.dumps(analysis.cons) if analysis.cons else None,
                    analysis.analysis_model, analysis.confidence_score,
                    analysis.processed_at.isoformat(), datetime.now().isoformat()
                ))
                
                conn.commit()
                logger.debug(f"Saved analysis for offer: {analysis.offer_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving analysis for {analysis.offer_id}: {e}")
            return False
    
    def get_offer(self, offer_id: str) -> Optional[Offer]:
        """Get offer by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM offers WHERE id = ?', (offer_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_offer(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting offer {offer_id}: {e}")
            return None
    
    def get_offers(self, limit: int = 100, business_name: str = None, 
                   active_only: bool = True) -> List[Offer]:
        """Get offers with optional filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM offers"
                params = []
                
                conditions = []
                if active_only:
                    conditions.append("is_active = 1")
                if business_name:
                    conditions.append("business_name = ?")
                    params.append(business_name)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_offer(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting offers: {e}")
            return []
    
    def get_recent_offers(self, hours: int = 24) -> List[Offer]:
        """Get offers created in the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM offers 
                    WHERE created_at >= ? AND is_active = 1
                    ORDER BY created_at DESC
                ''', (cutoff_time.isoformat(),))
                
                rows = cursor.fetchall()
                return [self._row_to_offer(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting recent offers: {e}")
            return []
    
    def get_offer_analysis(self, offer_id: str) -> Optional[OfferAnalysis]:
        """Get latest analysis for an offer"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM offer_analyses 
                    WHERE offer_id = ? 
                    ORDER BY processed_at DESC 
                    LIMIT 1
                ''', (offer_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_analysis(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting analysis for {offer_id}: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Offer counts
                cursor.execute('SELECT COUNT(*) FROM offers')
                stats['total_offers'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM offers WHERE is_active = 1')
                stats['active_offers'] = cursor.fetchone()[0]
                
                # Recent offers (24h)
                cutoff = datetime.now() - timedelta(hours=24)
                cursor.execute('SELECT COUNT(*) FROM offers WHERE created_at >= ?', (cutoff.isoformat(),))
                stats['offers_24h'] = cursor.fetchone()[0]
                
                # Business counts
                cursor.execute('SELECT COUNT(DISTINCT business_name) FROM offers WHERE business_name IS NOT NULL')
                stats['unique_businesses'] = cursor.fetchone()[0]
                
                # Analysis counts
                cursor.execute('SELECT COUNT(*) FROM offer_analyses')
                stats['total_analyses'] = cursor.fetchone()[0]
                
                # Top businesses
                cursor.execute('''
                    SELECT business_name, COUNT(*) as count 
                    FROM offers 
                    WHERE business_name IS NOT NULL AND is_active = 1
                    GROUP BY business_name 
                    ORDER BY count DESC 
                    LIMIT 5
                ''')
                stats['top_businesses'] = dict(cursor.fetchall())
                
                # Database size
                stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
        
        return stats
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """Remove old inactive offers and analyses"""
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Remove old analyses first (FK constraint)
                cursor.execute('''
                    DELETE FROM offer_analyses 
                    WHERE offer_id IN (
                        SELECT id FROM offers 
                        WHERE is_active = 0 AND updated_at < ?
                    )
                ''', (cutoff_date.isoformat(),))
                
                analyses_removed = cursor.rowcount
                
                # Remove old inactive offers
                cursor.execute('''
                    DELETE FROM offers 
                    WHERE is_active = 0 AND updated_at < ?
                ''', (cutoff_date.isoformat(),))
                
                offers_removed = cursor.rowcount
                removed_count = offers_removed
                
                # Remove old scraping sessions
                cursor.execute('''
                    DELETE FROM scraping_sessions 
                    WHERE completed_at < ?
                ''', (cutoff_date.isoformat(),))
                
                sessions_removed = cursor.rowcount
                
                conn.commit()
                
                logger.info(f"Cleanup completed: {offers_removed} offers, {analyses_removed} analyses, {sessions_removed} sessions removed")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        return removed_count
    
    def _row_to_offer(self, row: sqlite3.Row) -> Offer:
        """Convert database row to Offer object"""
        source_data = None
        if row['source_data']:
            try:
                source_data = json.loads(row['source_data'])
            except:
                pass
        
        return Offer(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            current_price=row['current_price'],
            original_price=row['original_price'],
            currency=row['currency'],
            unit_price=row['unit_price'],
            base_unit=row['base_unit'],
            unit_size_from=row['unit_size_from'],
            unit_size_to=row['unit_size_to'],
            unit_symbol=row['unit_symbol'],
            business_name=row['business_name'],
            business_id=row['business_id'],
            publication_name=row['publication_name'],
            url=row['url'],
            image_url=row['image_url'],
            valid_from=row['valid_from'],
            valid_until=row['valid_until'],
            source_data=source_data
        )
    
    def _row_to_analysis(self, row: sqlite3.Row) -> OfferAnalysis:
        """Convert database row to OfferAnalysis object"""
        pros = []
        cons = []
        
        if row['pros']:
            try:
                pros = json.loads(row['pros'])
            except:
                pass
        
        if row['cons']:
            try:
                cons = json.loads(row['cons'])
            except:
                pass
        
        price_category = None
        if row['price_category']:
            try:
                price_category = PriceCategory(row['price_category'])
            except:
                pass
        
        return OfferAnalysis(
            offer_id=row['offer_id'],
            category=row['category'],
            subcategory=row['subcategory'],
            brand=row['brand'],
            price_category=price_category,
            value_score=row['value_score'],
            deal_quality=row['deal_quality'],
            target_audience=row['target_audience'],
            purchase_urgency=row['purchase_urgency'],
            seasonal_relevance=row['seasonal_relevance'],
            recommendation=row['recommendation'],
            pros=pros,
            cons=cons,
            analysis_model=row['analysis_model'],
            confidence_score=row['confidence_score'],
            processed_at=datetime.fromisoformat(row['processed_at'])
        )
    
    def close(self):
        """Close database connection (not needed for sqlite3 context managers)"""
        pass
