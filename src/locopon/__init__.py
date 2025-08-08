#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Locopon - Swedish Deals Intelligence System

A comprehensive system for:
1. Extracting offers from eReklamblad.se
2. AI-powered analysis using DeepSeek
3. Intelligent notifications via Telegram

Author: Locopon Team
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Locopon Team"

# Import core components (avoiding circular imports)
# from .models import Offer, OfferAnalysis, SystemStatus
# from .scraper import EreklamkladScraper
# from .analyzer import DeepSeekAnalyzer
# from .notifier import TelegramNotifier, TelegramNotifierSync
# from .database import DatabaseManager
# from .scheduler import LocoponScheduler

__all__ = [
    "Offer",
    "OfferAnalysis", 
    "SystemStatus",
    "EreklamkladScraper",
    "DeepSeekAnalyzer",
    "TelegramNotifier",
    "TelegramNotifierSync",
    "DatabaseManager",
    "LocoponScheduler",
]
