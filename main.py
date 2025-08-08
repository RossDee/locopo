#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Locopon - Swedish Retail Deals Intelligence System
Main application entry point

Features:
1. eReklamblad.se information extraction
2. DeepSeek AI analysis and categorization  
3. Telegram bot notifications
4. Automated scheduling and monitoring
"""

import sys
import signal
import argparse
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from locopon.config import ConfigManager
from locopon.scheduler import LocoponScheduler
from locopon.database import DatabaseManager
from locopon.scraper import EreklamkladScraper
from locopon.analyzer import DeepSeekAnalyzer  
from locopon.notifier import TelegramNotifierSync

logger = logging.getLogger(__name__)


class LocoponApp:
    """Main Locopon application"""
    
    def __init__(self, config_path: str = None):
        self.config = ConfigManager(config_path)
        self.scheduler = None
        self.running = False
        
        # Setup logging
        self.config.setup_logging()
    
    def run_daemon(self):
        """Run as daemon with scheduler"""
        logger.info("Starting Locopon daemon mode")
        
        try:
            # Initialize scheduler
            self.scheduler = LocoponScheduler(self.config.get_all())
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            # Start scheduler
            self.scheduler.start()
            self.running = True
            
            logger.info("Locopon daemon started. Press Ctrl+C to stop.")
            
            # Keep main thread alive
            while self.running:
                try:
                    signal.pause()  # Wait for signals
                except AttributeError:
                    # Windows doesn't have signal.pause()
                    import time
                    while self.running:
                        time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Daemon error: {e}")
            return 1
        finally:
            self._cleanup()
        
        return 0
    
    def run_once(self):
        """Run discovery once and exit"""
        logger.info("Running single discovery cycle")
        
        try:
            scheduler = LocoponScheduler(self.config.get_all())
            success = scheduler.run_once()
            
            if success:
                logger.info("Discovery completed successfully")
                return 0
            else:
                logger.error("Discovery failed")
                return 1
                
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            return 1
    
    def run_test(self):
        """Run system tests"""
        logger.info("Running system tests")
        
        errors = []
        
        try:
            # Test database
            logger.info("Testing database...")
            db = DatabaseManager(self.config.get('database_path'))
            stats = db.get_statistics()
            logger.info(f"Database OK: {stats['total_offers']} offers")
            
        except Exception as e:
            errors.append(f"Database test failed: {e}")
        
        try:
            # Test scraper
            logger.info("Testing scraper...")
            scraper = EreklamkladScraper()
            test_offers = scraper.discover_offers(max_attempts=5)
            logger.info(f"Scraper OK: found {len(test_offers)} test offer IDs")
            
        except Exception as e:
            errors.append(f"Scraper test failed: {e}")
        
        # Test AI analyzer
        if self.config.get('deepseek_api_key'):
            try:
                logger.info("Testing AI analyzer...")
                analyzer = DeepSeekAnalyzer(self.config.get('deepseek_api_key'))
                if analyzer.health_check():
                    logger.info("AI analyzer OK")
                else:
                    errors.append("AI analyzer health check failed")
                    
            except Exception as e:
                errors.append(f"AI analyzer test failed: {e}")
        else:
            logger.info("AI analyzer not configured (skipping test)")
        
        # Test Telegram notifier
        if self.config.get('telegram_bot_token') and self.config.get('telegram_chat_id'):
            try:
                logger.info("Testing Telegram notifier...")
                notifier = TelegramNotifierSync(
                    self.config.get('telegram_bot_token'),
                    self.config.get('telegram_chat_id')
                )
                
                if notifier.initialize():
                    notifier.send_system_status("Locopon test message")
                    logger.info("Telegram notifier OK")
                else:
                    errors.append("Telegram notifier initialization failed")
                    
            except Exception as e:
                errors.append(f"Telegram notifier test failed: {e}")
        else:
            logger.info("Telegram notifier not configured (skipping test)")
        
        # Report results
        if errors:
            logger.error("System tests failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return 1
        else:
            logger.info("All system tests passed!")
            return 0
    
    def show_status(self):
        """Show current system status"""
        logger.info("Checking system status")
        
        try:
            # Database stats
            db = DatabaseManager(self.config.get('database_path'))
            stats = db.get_statistics()
            
            print("=== Locopon System Status ===")
            print(f"Database: {stats['total_offers']} offers, {stats['active_offers']} active")
            print(f"Recent offers (24h): {stats['offers_24h']}")
            print(f"Total analyses: {stats['total_analyses']}")
            print(f"Database size: {stats['db_size_mb']:.1f} MB")
            print(f"Unique businesses: {stats['unique_businesses']}")
            
            if stats['top_businesses']:
                print("\nTop businesses:")
                for business, count in stats['top_businesses'].items():
                    print(f"  - {business}: {count} offers")
            
            # Configuration status
            print(f"\nConfiguration:")
            print(f"  - DeepSeek AI: {'✓' if self.config.get('deepseek_api_key') else '✗'}")
            print(f"  - Telegram: {'✓' if self.config.get('telegram_bot_token') else '✗'}")
            print(f"  - Target publications: {len(self.config.get('target_publications', []))}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return 1
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.running = False
        self._cleanup()
    
    def _cleanup(self):
        """Cleanup resources"""
        if self.scheduler:
            self.scheduler.stop()
            self.scheduler = None
        
        logger.info("Cleanup completed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Locopon - Swedish Retail Deals Intelligence")
    
    parser.add_argument('command', nargs='?', default='daemon',
                       choices=['daemon', 'once', 'test', 'status'],
                       help='Command to run (default: daemon)')
    
    parser.add_argument('--config', '-c', 
                       help='Path to configuration file')
    
    parser.add_argument('--log-level', '-l',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Override log level')
    
    args = parser.parse_args()
    
    # Create app with configuration
    app = LocoponApp(args.config)
    
    # Override log level if specified
    if args.log_level:
        app.config.set('logging', {**app.config.get('logging', {}), 'level': args.log_level})
        app.config.setup_logging()
    
    # Log startup info
    logger.info("=" * 50)
    logger.info("Locopon - Swedish Retail Deals Intelligence")
    logger.info(f"Command: {args.command}")
    logger.info(f"Config: {app.config.config_path}")
    logger.info("=" * 50)
    
    # Create and run app
    try:
        if args.command == 'daemon':
            exit_code = app.run_daemon()
        elif args.command == 'once':
            exit_code = app.run_once()
        elif args.command == 'test':
            exit_code = app.run_test()
        elif args.command == 'status':
            exit_code = app.show_status()
        else:
            logger.error(f"Unknown command: {args.command}")
            exit_code = 1
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        exit_code = 0
    except Exception as e:
        logger.error(f"Application error: {e}")
        exit_code = 1
    
    logger.info(f"Locopon exiting with code {exit_code}")
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
