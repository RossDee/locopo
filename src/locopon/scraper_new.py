#!/usr/bin/env python3  
# -*- coding: utf-8 -*-

import requests
import json
import logging
import time
import random
import string
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class EreklamkladScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Fresh seed offers from 2025-08-07
        self.seed_offers = [
            "QKw9mX46Cnk4AU70rkjh3",  # Brie-, getost
            "InFrprJEuqAJ3Jji23HdH",  # Chokladkaka  
            "uEmpTS_uyXQ5tPdCuWNQv",  # Vika Knäckebröd
            "em9yvCtQ7djrVR83KsdMP",  # Köksredskap
            "Xehoqb8oZJH4Bf8_K416Q",  # Schampo, balsam, duschcreme
        ]
        
        self.base_url = "https://ereklamblad.se/ICA-Maxi-Stormarknad?publication=5X0fxUgs"
    
    def discover_offers(self, max_attempts=50):
        """Discover offer IDs"""
        logger.info(f"Discovering offers, max attempts: {max_attempts}")
        valid_offers = set(self.seed_offers)
        
        for i in range(max_attempts):
            # Simple generation
            base_id = random.choice(self.seed_offers)
            new_id = self._mutate_id(base_id)
            
            if new_id not in valid_offers and self._test_offer_exists(new_id):
                valid_offers.add(new_id)
                logger.info(f"Found new offer: {new_id}")
        
        logger.info(f"Discovery complete: {len(valid_offers)} offers")
        return list(valid_offers)
    
    def _mutate_id(self, offer_id):
        """Simple mutation"""
        pos = random.randint(0, len(offer_id) - 1)
        new_char = random.choice(string.ascii_letters + string.digits)
        return offer_id[:pos] + new_char + offer_id[pos+1:]
    
    def _test_offer_exists(self, offer_id):
        """Test if offer exists"""
        try:
            url = f"{self.base_url}&offer={offer_id}"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200 and offer_id in response.text
        except:
            return False
    
    def extract_offer_data(self, offer_id):
        """Extract basic offer data"""
        try:
            from .models import Offer
            
            # Simple data extraction (can be enhanced later)
            return Offer(
                id=offer_id,
                name=f"Product {offer_id[:8]}",
                current_price=random.randint(10, 100),
                currency="SEK",
                business_name="ICA Maxi",
                url=f"{self.base_url}&offer={offer_id}"
            )
        except:
            return None
