#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration Management for Locopon
Centralized configuration loading and validation
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file
except ImportError:
    # dotenv not available, continue without it
    pass

logger = logging.getLogger(__name__)


class ConfigManager:
    """Configuration manager for Locopon system"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "config/config.json"
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file and environment variables"""
        logger.info(f"Loading configuration from {self.config_path}")
        
        # Load default configuration
        self.config = self._get_default_config()
        
        # Load from file if exists
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                    logger.info("Configuration loaded from file")
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
        
        # Override with environment variables
        self._load_from_environment()
        
        # Validate configuration
        self._validate_config()
        
        logger.info("Configuration loaded successfully")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            # Database settings
            'database_path': 'data/locopon.db',
            
            # Scraping settings
            'scraping': {
                'request_delay': 1.0,
                'max_retries': 3,
                'timeout': 30,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            
            # DeepSeek AI settings
            'deepseek_api_key': None,
            'deepseek_base_url': 'https://api.deepseek.com',
            'max_analysis_per_run': 20,
            
            # Telegram settings
            'telegram_bot_token': None,
            'telegram_chat_id': None,
            
            # Scheduling settings
            'schedule': {
                'scrape_interval_hours': 2,
                'quick_check_minutes': 30,
                'daily_summary_time': '20:00',
                'cleanup_time': '02:00',
                'health_check_minutes': 60
            },
            
            # Target publications
            'target_publications': [
                "https://ereklamblad.se/ICA-Maxi-Stormarknad?publication=5X0fxUgs",
                "https://ereklamblad.se/Coop?publication=4zFUKNKp",
                "https://ereklamblad.se/Willys?publication=JlTbj6jx"
            ],
            
            # Data retention settings
            'cleanup_days': 30,
            
            # Logging settings
            'logging': {
                'level': 'INFO',
                'file': 'logs/locopon.log',
                'max_size_mb': 10,
                'backup_count': 5
            }
        }
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'LOCOPON_DB_PATH': ['database_path'],
            'DEEPSEEK_API_KEY': ['deepseek_api_key'],
            'DEEPSEEK_BASE_URL': ['deepseek_base_url'],
            'TELEGRAM_BOT_TOKEN': ['telegram_bot_token'],
            'TELEGRAM_CHAT_ID': ['telegram_chat_id'],
            'LOCOPON_LOG_LEVEL': ['logging', 'level'],
            'LOCOPON_SCRAPE_INTERVAL': ['schedule', 'scrape_interval_hours'],
            'LOCOPON_QUICK_CHECK': ['schedule', 'quick_check_minutes'],
            'LOCOPON_SUMMARY_TIME': ['schedule', 'daily_summary_time'],
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_config(config_path, value)
                logger.debug(f"Set {'.'.join(config_path)} from environment")
    
    def _set_nested_config(self, path: list, value: str):
        """Set nested configuration value"""
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Try to convert value to appropriate type
        final_key = path[-1]
        if final_key.endswith('_hours') or final_key.endswith('_minutes'):
            try:
                current[final_key] = int(value)
            except ValueError:
                current[final_key] = value
        else:
            current[final_key] = value
    
    def _validate_config(self):
        """Validate configuration"""
        errors = []
        
        # Check required paths exist
        paths_to_create = [
            Path(self.config['database_path']).parent,
            Path(self.config['logging']['file']).parent
        ]
        
        for path in paths_to_create:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {path}: {e}")
        
        # Validate AI configuration
        if self.config.get('deepseek_api_key'):
            if not isinstance(self.config['deepseek_api_key'], str) or len(self.config['deepseek_api_key']) < 10:
                errors.append("Invalid DeepSeek API key")
        
        # Validate Telegram configuration
        if self.config.get('telegram_bot_token'):
            if not self.config.get('telegram_chat_id'):
                errors.append("Telegram bot token provided but chat ID missing")
        
        # Validate schedule times
        schedule_config = self.config.get('schedule', {})
        time_fields = ['daily_summary_time', 'cleanup_time']
        for field in time_fields:
            time_value = schedule_config.get(field)
            if time_value and not self._is_valid_time(time_value):
                errors.append(f"Invalid time format for {field}: {time_value}")
        
        if errors:
            logger.error("Configuration validation errors:")
            for error in errors:
                logger.error(f"  - {error}")
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def _is_valid_time(self, time_str: str) -> bool:
        """Validate time format (HH:MM)"""
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            
            hour, minute = int(parts[0]), int(parts[1])
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def get_nested(self, *keys, default: Any = None) -> Any:
        """Get nested configuration value"""
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
    
    def save_config(self, path: str = None):
        """Save current configuration to file"""
        save_path = path or self.config_path
        
        try:
            config_file = Path(save_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self.config.copy()
    
    def setup_logging(self):
        """Setup logging based on configuration"""
        log_config = self.config.get('logging', {})
        
        # Create logs directory
        log_file = Path(log_config.get('file', 'logs/locopon.log'))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add file handler with rotation
        try:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=log_config.get('max_size_mb', 10) * 1024 * 1024,
                backupCount=log_config.get('backup_count', 5)
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to basic file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
            logger.warning(f"Could not setup rotating file handler: {e}")
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        logger.info(f"Logging configured: level={log_level}, file={log_file}")


# Global config instance
config = ConfigManager()
