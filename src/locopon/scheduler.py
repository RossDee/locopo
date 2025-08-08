#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scheduler for Locopon
Automated scheduling and monitoring for Swedish retail deals discovery
"""

import time
import logging
import threading
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import schedule

from .scraper import EreklamkladScraper
from .analyzer import DeepSeekAnalyzer
from .notifier import TelegramNotifierSync
from .database import DatabaseManager
from .models import SystemStatus

logger = logging.getLogger(__name__)


class LocoponScheduler:
    """Main scheduler for automated deal discovery and analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.scheduler_thread = None
        
        # Initialize components
        self.db = DatabaseManager(config.get('database_path', 'data/locopon.db'))
        self.scraper = EreklamkladScraper()
        
        # Initialize AI analyzer if configured
        self.analyzer = None
        if config.get('deepseek_api_key'):
            self.analyzer = DeepSeekAnalyzer(
                api_key=config['deepseek_api_key'],
                base_url=config.get('deepseek_base_url', 'https://api.deepseek.com')
            )
        
        # Initialize Telegram notifier if configured
        self.notifier = None
        if config.get('telegram_bot_token') and config.get('telegram_chat_id'):
            self.notifier = TelegramNotifierSync(
                bot_token=config['telegram_bot_token'],
                chat_id=config['telegram_chat_id']
            )
        
        # Scheduling configuration
        self.schedule_config = config.get('schedule', {})
        self.setup_default_schedules()
    
    def setup_default_schedules(self):
        """Setup default scheduled tasks"""
        
        # Main scraping schedule - default every 2 hours
        scrape_interval = self.schedule_config.get('scrape_interval_hours', 2)
        schedule.every(scrape_interval).hours.do(self._run_full_discovery)
        
        # Quick check schedule - default every 30 minutes for urgent deals
        quick_interval = self.schedule_config.get('quick_check_minutes', 30)
        schedule.every(quick_interval).minutes.do(self._run_quick_check)
        
        # Daily summary - default at 20:00
        summary_time = self.schedule_config.get('daily_summary_time', '20:00')
        schedule.every().day.at(summary_time).do(self._send_daily_summary)
        
        # Weekly cleanup - default Sunday at 02:00  
        cleanup_time = self.schedule_config.get('cleanup_time', '02:00')
        schedule.every().sunday.at(cleanup_time).do(self._run_cleanup)
        
        # Health check - default every hour
        health_interval = self.schedule_config.get('health_check_minutes', 60)
        schedule.every(health_interval).minutes.do(self._run_health_check)
        
        logger.info("Scheduled tasks configured:")
        logger.info(f"  - Full discovery: every {scrape_interval} hours")
        logger.info(f"  - Quick check: every {quick_interval} minutes")
        logger.info(f"  - Daily summary: {summary_time}")
        logger.info(f"  - Weekly cleanup: Sunday {cleanup_time}")
        logger.info(f"  - Health check: every {health_interval} minutes")
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        logger.info("Starting Locopon scheduler")
        self.running = True
        
        # Initialize components
        self._initialize_components()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # Send startup notification
        if self.notifier:
            self.notifier.send_system_status("Locopon scheduler started successfully")
        
        logger.info("Scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            logger.warning("Scheduler not running")
            return
        
        logger.info("Stopping Locopon scheduler")
        self.running = False
        
        # Wait for scheduler thread to finish
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        # Send shutdown notification
        if self.notifier:
            self.notifier.send_system_status("Locopon scheduler stopped")
        
        logger.info("Scheduler stopped")
    
    def run_once(self) -> bool:
        """Run full discovery cycle once"""
        logger.info("Running manual discovery cycle")
        return self._run_full_discovery()
    
    def _initialize_components(self):
        """Initialize all system components"""
        logger.info("Initializing system components")
        
        # Test database
        try:
            stats = self.db.get_statistics()
            logger.info(f"Database connected: {stats['total_offers']} offers, {stats['total_analyses']} analyses")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False
        
        # Test AI analyzer
        if self.analyzer:
            try:
                if self.analyzer.health_check():
                    logger.info("DeepSeek AI analyzer connected")
                else:
                    logger.warning("DeepSeek AI analyzer health check failed")
            except Exception as e:
                logger.error(f"AI analyzer initialization failed: {e}")
        
        # Test Telegram notifier
        if self.notifier:
            try:
                if self.notifier.initialize():
                    logger.info("Telegram notifier initialized")
                else:
                    logger.warning("Telegram notifier initialization failed")
            except Exception as e:
                logger.error(f"Telegram notifier initialization failed: {e}")
        
        return True
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("Scheduler loop started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait longer on error
        
        logger.info("Scheduler loop stopped")
    
    def _run_full_discovery(self) -> bool:
        """Run full offer discovery and analysis"""
        start_time = datetime.now()
        logger.info("Starting full discovery cycle")
        
        try:
            # Scrape new offers
            logger.info("Discovering new offers...")
            publications = self.config.get('target_publications', [])
            
            if not publications:
                # Use default popular publications
                publications = [
                    "https://ereklamblad.se/ICA-Maxi-Stormarknad?publication=5X0fxUgs",
                    "https://ereklamblad.se/Coop?publication=4zFUKNKp", 
                    "https://ereklamblad.se/Willys?publication=JlTbj6jx"
                ]
            
            all_offers = []
            
            # Use the scraper's discovery method
            try:
                logger.info("Discovering offers using intelligent pattern generation...")
                offer_ids = self.scraper.discover_offers(max_attempts=50)
                
                if offer_ids:
                    logger.info(f"Found {len(offer_ids)} offer IDs, extracting data...")
                    
                    # Extract data for each offer ID
                    for offer_id in offer_ids:
                        try:
                            offer_data = self.scraper.extract_offer_data(offer_id)
                            if offer_data:
                                all_offers.append(offer_data)
                                logger.debug(f"Extracted data for offer: {offer_id}")
                        except Exception as e:
                            logger.warning(f"Failed to extract data for offer {offer_id}: {e}")
                    
                    logger.info(f"Successfully extracted {len(all_offers)} complete offers")
                else:
                    logger.warning("No offer IDs discovered")
                    
            except Exception as e:
                logger.error(f"Error during offer discovery: {e}")
                return False
            
            if not all_offers:
                logger.warning("No offers discovered")
                return False
            
            # Save offers to database
            logger.info(f"Saving {len(all_offers)} offers to database")
            saved_count = self.db.save_offers_batch(all_offers)
            
            # Filter new offers (created in last hour)
            new_offers = self.db.get_recent_offers(hours=1)
            logger.info(f"Found {len(new_offers)} new offers")
            
            # Analyze offers with AI
            analyses = []
            if self.analyzer and new_offers:
                logger.info("Starting AI analysis of new offers")
                
                # Limit analysis to prevent API overuse
                max_analysis = self.config.get('max_analysis_per_run', 20)
                offers_to_analyze = new_offers[:max_analysis]
                
                analyses = self.analyzer.analyze_batch(offers_to_analyze)
                
                # Save analyses
                for analysis in analyses:
                    self.db.save_analysis(analysis)
                
                logger.info(f"Completed {len(analyses)} AI analyses")
            
            # Send notifications
            if self.notifier and new_offers:
                logger.info("Sending notifications")
                
                # Send batch notification for new offers
                self.notifier.send_batch_notification(new_offers, analyses)
                
                # Generate and send summary if we have analyses
                if analyses and self.analyzer:
                    summary = self.analyzer.generate_summary(new_offers, analyses)
                    self.notifier.send_summary(summary, len(new_offers))
            
            # Update system status
            duration = datetime.now() - start_time
            status_message = f"Discovery completed: {len(all_offers)} total offers, {len(new_offers)} new, {len(analyses)} analyzed (took {duration.total_seconds():.1f}s)"
            
            logger.info(status_message)
            
            if self.notifier:
                self.notifier.send_system_status(status_message)
            
            return True
            
        except Exception as e:
            error_message = f"Full discovery failed: {e}"
            logger.error(error_message)
            
            if self.notifier:
                self.notifier.send_system_status(error_message, is_error=True)
            
            return False
    
    def _run_quick_check(self) -> bool:
        """Run quick check for urgent deals"""
        logger.debug("Running quick check")
        
        try:
            # Quick check for excellent deals only
            recent_offers = self.db.get_recent_offers(hours=1)
            
            if not recent_offers:
                return True
            
            # If analyzer available, check for excellent deals
            if self.analyzer:
                urgent_offers = []
                
                for offer in recent_offers:
                    analysis = self.db.get_offer_analysis(offer.id)
                    if analysis and analysis.price_category and analysis.price_category.value == 'excellent':
                        urgent_offers.append(offer)
                
                # Send urgent notifications
                if urgent_offers and self.notifier:
                    for offer in urgent_offers:
                        analysis = self.db.get_offer_analysis(offer.id)
                        self.notifier.send_offer_notification(offer, analysis)
                    
                    logger.info(f"Sent {len(urgent_offers)} urgent deal notifications")
            
            return True
            
        except Exception as e:
            logger.error(f"Quick check failed: {e}")
            return False
    
    def _send_daily_summary(self) -> bool:
        """Send daily summary"""
        logger.info("Generating daily summary")
        
        try:
            # Get today's offers
            today_offers = self.db.get_recent_offers(hours=24)
            
            if not today_offers:
                if self.notifier:
                    self.notifier.send_summary("No new offers discovered today.", 0)
                return True
            
            # Get analyses for today's offers
            analyses = []
            for offer in today_offers:
                analysis = self.db.get_offer_analysis(offer.id)
                if analysis:
                    analyses.append(analysis)
            
            # Generate intelligent summary
            if self.analyzer and analyses:
                summary = self.analyzer.generate_summary(today_offers, analyses)
            else:
                summary = f"Discovered {len(today_offers)} offers today across various Swedish retailers."
            
            # Send summary
            if self.notifier:
                self.notifier.send_summary(summary, len(today_offers))
            
            logger.info(f"Daily summary sent: {len(today_offers)} offers")
            return True
            
        except Exception as e:
            logger.error(f"Daily summary failed: {e}")
            return False
    
    def _run_cleanup(self) -> bool:
        """Run weekly cleanup"""
        logger.info("Running weekly cleanup")
        
        try:
            # Clean old data
            cleanup_days = self.config.get('cleanup_days', 30)
            removed_count = self.db.cleanup_old_data(cleanup_days)
            
            # Get updated statistics
            stats = self.db.get_statistics()
            
            cleanup_message = f"Weekly cleanup completed: {removed_count} old records removed. Database now has {stats['active_offers']} active offers ({stats['db_size_mb']:.1f}MB)"
            
            logger.info(cleanup_message)
            
            if self.notifier:
                self.notifier.send_system_status(cleanup_message)
            
            return True
            
        except Exception as e:
            error_message = f"Cleanup failed: {e}"
            logger.error(error_message)
            
            if self.notifier:
                self.notifier.send_system_status(error_message, is_error=True)
            
            return False
    
    def _run_health_check(self) -> bool:
        """Run system health check"""
        logger.debug("Running health check")
        
        issues = []
        
        try:
            # Check database
            stats = self.db.get_statistics()
            if stats['db_size_mb'] > 1000:  # 1GB limit
                issues.append("Database size exceeds 1GB")
            
            # Check AI analyzer
            if self.analyzer and not self.analyzer.health_check():
                issues.append("DeepSeek AI analyzer unavailable")
            
            # Check Telegram notifier
            if self.notifier and not self.notifier.health_check():
                issues.append("Telegram notifier unavailable")
            
            # Report issues if any
            if issues:
                issue_message = f"Health check found issues: {'; '.join(issues)}"
                logger.warning(issue_message)
                
                if self.notifier:
                    self.notifier.send_system_status(issue_message, is_error=True)
                
                return False
            else:
                logger.debug("Health check passed")
                return True
            
        except Exception as e:
            error_message = f"Health check failed: {e}"
            logger.error(error_message)
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            'running': self.running,
            'next_runs': {
                'full_discovery': self._get_next_run_time('_run_full_discovery'),
                'quick_check': self._get_next_run_time('_run_quick_check'),
                'daily_summary': self._get_next_run_time('_send_daily_summary'),
                'cleanup': self._get_next_run_time('_run_cleanup'),
            },
            'components': {
                'database': self.db is not None,
                'scraper': self.scraper is not None,
                'analyzer': self.analyzer is not None,
                'notifier': self.notifier is not None,
            },
            'database_stats': self.db.get_statistics() if self.db else {}
        }
    
    def _get_next_run_time(self, job_func_name: str) -> Optional[str]:
        """Get next run time for a scheduled job"""
        for job in schedule.jobs:
            if hasattr(job.job_func, '__name__') and job.job_func.__name__ == job_func_name:
                return str(job.next_run)
        return None
