#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Application Entry Point for Locopon
Swedish Deals Intelligence System
"""

import sys
import signal
import logging
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from locopon.config import ConfigManager
from locopon.scheduler import LocoponScheduler
from locopon.scraper import EreklamkladScraper
from locopon.database import DatabaseManager

logger = logging.getLogger(__name__)


def setup_signal_handlers(scheduler: LocoponScheduler):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        scheduler.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def run_scheduler(config_path: str = None):
    """Run the main scheduler"""
    try:
        # Load configuration
        config_manager = ConfigManager(config_path)
        config_manager.setup_logging()
        
        logger.info("Starting Locopon Swedish Deals Intelligence System")
        logger.info(f"Configuration loaded from: {config_manager.config_path}")
        
        # Initialize scheduler
        scheduler = LocoponScheduler(config_manager.get_all())
        
        # Setup signal handlers
        setup_signal_handlers(scheduler)
        
        # Start scheduler
        scheduler.start()
        
        logger.info("Scheduler started successfully")
        logger.info("Press Ctrl+C to stop")
        
        # Keep main thread alive
        try:
            while scheduler.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        sys.exit(1)


def run_single_discovery(config_path: str = None, publication_url: str = None):
    """Run a single discovery cycle"""
    try:
        # Load configuration
        config_manager = ConfigManager(config_path)
        config_manager.setup_logging()
        
        logger.info("Starting single discovery cycle")
        
        # Initialize components
        config = config_manager.get_all()
        scheduler = LocoponScheduler(config)
        
        # Run discovery
        success = scheduler.run_once()
        
        if success:
            logger.info("Discovery completed successfully")
            
            # Show results
            db = DatabaseManager(config.get('database_path'))
            stats = db.get_statistics()
            
            print(f"\n=== Discovery Results ===")
            print(f"Total offers in database: {stats['total_offers']}")
            print(f"Active offers: {stats['active_offers']}")
            print(f"New offers (24h): {stats['offers_24h']}")
            print(f"Unique businesses: {stats['unique_businesses']}")
            print(f"Total analyses: {stats['total_analyses']}")
            
        else:
            logger.error("Discovery failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        sys.exit(1)


def test_scraper(publication_url: str):
    """Test the scraper with a specific publication"""
    try:
        # Setup basic logging
        logging.basicConfig(level=logging.INFO)
        
        logger.info(f"Testing scraper with: {publication_url}")
        
        # Initialize scraper
        scraper = EreklamkladScraper()
        
        # Discover offers
        offers = scraper.discover_publication_offers(publication_url)
        
        print(f"\n=== Scraper Test Results ===")
        print(f"Found {len(offers)} offers")
        
        for i, offer in enumerate(offers[:5], 1):
            print(f"\n{i}. {offer.name}")
            print(f"   Price: {offer.get_display_price()}")
            print(f"   Business: {offer.business_name}")
            print(f"   URL: {offer.url}")
        
        if len(offers) > 5:
            print(f"\n... and {len(offers) - 5} more offers")
            
    except Exception as e:
        logger.error(f"Scraper test failed: {e}")
        sys.exit(1)


def show_status(config_path: str = None):
    """Show system status"""
    try:
        config_manager = ConfigManager(config_path)
        config = config_manager.get_all()
        
        # Get database statistics
        db = DatabaseManager(config.get('database_path'))
        stats = db.get_statistics()
        
        print("=== Locopon System Status ===")
        print(f"Database: {config.get('database_path')}")
        print(f"Database size: {stats['db_size_mb']:.1f} MB")
        print()
        print("=== Offers Statistics ===")
        print(f"Total offers: {stats['total_offers']}")
        print(f"Active offers: {stats['active_offers']}")
        print(f"New offers (24h): {stats['offers_24h']}")
        print(f"Unique businesses: {stats['unique_businesses']}")
        print(f"Total analyses: {stats['total_analyses']}")
        print()
        print("=== Top Businesses ===")
        for business, count in stats.get('top_businesses', {}).items():
            print(f"  {business}: {count} offers")
        
        # Test component connectivity
        print("\n=== Component Status ===")
        
        # Test AI
        if config.get('deepseek_api_key'):
            try:
                from locopon.analyzer import DeepSeekAnalyzer
                analyzer = DeepSeekAnalyzer(config['deepseek_api_key'])
                ai_status = "✅ Connected" if analyzer.health_check() else "❌ Failed"
            except Exception as e:
                ai_status = f"❌ Error: {e}"
        else:
            ai_status = "⚠️ Not configured"
        print(f"DeepSeek AI: {ai_status}")
        
        # Test Telegram
        if config.get('telegram_bot_token'):
            try:
                from locopon.notifier import TelegramNotifierSync
                notifier = TelegramNotifierSync(
                    config['telegram_bot_token'], 
                    config['telegram_chat_id']
                )
                tg_status = "✅ Connected" if notifier.initialize() else "❌ Failed"
            except Exception as e:
                tg_status = f"❌ Error: {e}"
        else:
            tg_status = "⚠️ Not configured"
        print(f"Telegram Bot: {tg_status}")
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        sys.exit(1)


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="Locopon - Swedish Deals Intelligence System"
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config/config.json',
        help='Configuration file path (default: config/config.json)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser(
        'run', 
        help='Start the main scheduler (continuous monitoring)'
    )
    
    # Single discovery command
    discovery_parser = subparsers.add_parser(
        'discover',
        help='Run a single discovery cycle'
    )
    discovery_parser.add_argument(
        '--url',
        help='Specific publication URL to scrape'
    )
    
    # Test scraper command
    test_parser = subparsers.add_parser(
        'test',
        help='Test the scraper with a specific publication'
    )
    test_parser.add_argument(
        'url',
        help='Publication URL to test'
    )
    
    # Status command
    status_parser = subparsers.add_parser(
        'status',
        help='Show system status and statistics'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'run':
            run_scheduler(args.config)
        elif args.command == 'discover':
            run_single_discovery(args.config, args.url)
        elif args.command == 'test':
            test_scraper(args.url)
        elif args.command == 'status':
            show_status(args.config)
        else:
            parser.print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
