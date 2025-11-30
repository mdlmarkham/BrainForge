"""Production configuration management for BrainForge."""

import os
from typing import Dict, Optional


class ProductionConfig:
    """Production configuration with environment-specific settings."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        
        # Security settings
        self.secret_key = self._get_required_env("SECRET_KEY")
        self.encryption_key = self._get_required_env("ENCRYPTION_KEY")
        self.jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
        
        # Database settings
        self.database_url = self._get_required_env("DATABASE_URL")
        self.database_pool_size = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        self.database_max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        
        # Redis settings for caching
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_timeout = int(os.getenv("REDIS_TIMEOUT", "5"))
        
        # Logging settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "json")
        
        # Monitoring settings
        self.metrics_enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        self.health_check_interval = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
        
        # Performance settings
        self.max_request_size = int(os.getenv("MAX_REQUEST_SIZE", "100000000"))  # 100MB
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        
        # Rate limiting settings
        self.rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.default_rate_limit = int(os.getenv("DEFAULT_RATE_LIMIT", "100"))
        
        # Backup settings
        self.backup_enabled = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
        self.backup_retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
        
        # CORS settings
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        if not self.allowed_origins or self.allowed_origins == [""]:
            self.allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error.
        
        Args:
            key: Environment variable name
            
        Returns:
            Environment variable value
            
        Raises:
            ValueError: If environment variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def get_database_config(self) -> Dict[str, any]:
        """Get database configuration for SQLAlchemy."""
        return {
            "url": self.database_url,
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow,
            "pool_pre_ping": True,
            "echo": self.debug_mode,
        }
    
    def get_redis_config(self) -> Dict[str, any]:
        """Get Redis configuration."""
        return {
            "url": self.redis_url,
            "encoding": "utf-8",
            "decode_responses": True,
            "socket_timeout": self.redis_timeout,
            "retry_on_timeout": True,
        }
    
    def get_security_config(self) -> Dict[str, any]:
        """Get security configuration."""
        return {
            "secret_key": self.secret_key,
            "encryption_key": self.encryption_key,
            "jwt_expire_minutes": self.jwt_expire_minutes,
            "algorithm": "HS256",
        }
    
    def get_logging_config(self) -> Dict[str, any]:
        """Get logging configuration."""
        return {
            "level": self.log_level,
            "format": self.log_format,
            "handlers": ["console", "file"] if self.environment == "production" else ["console"],
        }
    
    def get_monitoring_config(self) -> Dict[str, any]:
        """Get monitoring configuration."""
        return {
            "metrics_enabled": self.metrics_enabled,
            "health_check_interval": self.health_check_interval,
            "performance_monitoring": True,
            "error_tracking": True,
        }
    
    def get_performance_config(self) -> Dict[str, any]:
        """Get performance configuration."""
        return {
            "max_request_size": self.max_request_size,
            "request_timeout": self.request_timeout,
            "caching_enabled": True,
            "compression_enabled": True,
        }
    
    def validate_config(self) -> bool:
        """Validate production configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check required environment variables
            self._get_required_env("SECRET_KEY")
            self._get_required_env("ENCRYPTION_KEY")
            self._get_required_env("DATABASE_URL")
            
            # Validate numeric values
            if self.database_pool_size <= 0:
                raise ValueError("DATABASE_POOL_SIZE must be positive")
            if self.database_max_overflow < 0:
                raise ValueError("DATABASE_MAX_OVERFLOW cannot be negative")
            if self.jwt_expire_minutes <= 0:
                raise ValueError("JWT_EXPIRE_MINUTES must be positive")
            if self.backup_retention_days <= 0:
                raise ValueError("BACKUP_RETENTION_DAYS must be positive")
            
            return True
            
        except ValueError as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, any]:
        """Get configuration summary (safe for logging, excludes secrets)."""
        return {
            "environment": self.environment,
            "debug_mode": self.debug_mode,
            "database_pool_size": self.database_pool_size,
            "database_max_overflow": self.database_max_overflow,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "metrics_enabled": self.metrics_enabled,
            "rate_limit_enabled": self.rate_limit_enabled,
            "backup_enabled": self.backup_enabled,
            "backup_retention_days": self.backup_retention_days,
            "allowed_origins_count": len(self.allowed_origins),
        }


# Global production configuration instance
production_config = ProductionConfig()


def get_production_config() -> ProductionConfig:
    """Get production configuration dependency."""
    return production_config


def setup_production_environment():
    """Setup production environment configuration."""
    if not production_config.validate_config():
        raise RuntimeError("Production configuration validation failed")
    
    # Set up logging based on configuration
    import logging
    logging.basicConfig(
        level=getattr(logging, production_config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Log configuration summary (excluding secrets)
    logger = logging.getLogger(__name__)
    config_summary = production_config.get_config_summary()
    logger.info(f"Production configuration loaded: {config_summary}")
    
    return production_config