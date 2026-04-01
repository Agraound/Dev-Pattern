"""
AETHERYON Config Manager
Reusable module for encrypted config loading + env control

Features:
- Singleton pattern with thread-safe lazy loading
- Multi-environment support (demo, staging, production)
- Encrypted config via Fernet (AES)
- Dot notation access with caching
- Hot reload capability
- Graceful degradation with warnings
- Full type hints
- Comprehensive error handling
"""

import os
import base64
import json
import logging
from typing import Any, Dict, Optional, Union, List
from functools import lru_cache
from pathlib import Path

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    Fernet = None
    InvalidToken = None

# Configure logger
logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Base exception for configuration errors"""
    pass


class ConfigMissingError(ConfigError):
    """Raised when required config is missing"""
    pass


class ConfigDecryptionError(ConfigError):
    """Raised when config decryption fails"""
    pass


class ConfigManager:
    """
    Thread-safe configuration manager with encrypted config support
    
    Environment variables:
        MODE: demo | staging | production (default: demo)
        CORE_CONFIG: Base64-encoded encrypted JSON config
        CONFIG_SECRET: Fernet key (32 bytes base64)
    
    Example encrypted config structure:
    {
        "providers": {
            "llm": "groq",
            "api_key": "xxx"
        },
        "database": {
            "url": "postgresql://...",
            "pool_size": 10
        },
        "features": {
            "multiagent": true,
            "analytics": false
        }
    }
    """
    
    VALID_MODES = {"demo", "staging", "production"}
    DEFAULT_MODE = "demo"
    
    _instance: Optional['ConfigManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'ConfigManager':
        """Thread-safe singleton implementation"""
        if cls._instance is None:
            import threading
            cls._lock = threading.Lock()
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize config manager (only once)"""
        if self._initialized:
            return
        
        self._mode: str = os.getenv("MODE", self.DEFAULT_MODE).lower()
        self._validate_mode()
        
        self._raw_config: Optional[str] = os.getenv("CORE_CONFIG")
        self._secret: Optional[str] = os.getenv("CONFIG_SECRET")
        
        self._config: Dict[str, Any] = {}
        self._cache: Dict[str, Any] = {}
        self._warnings: List[str] = []
        
        self._load()
        self._initialized = True
    
    def _validate_mode(self) -> None:
        """Validate MODE environment variable"""
        if self._mode not in self.VALID_MODES:
            raise ConfigError(
                f"Invalid MODE: '{self._mode}'. "
                f"Must be one of: {', '.join(self.VALID_MODES)}"
            )
    
    def _check_cryptography(self) -> None:
        """Check if cryptography is installed"""
        if Fernet is None:
            raise ConfigError(
                "cryptography package is required for encrypted config. "
                "Install with: pip install cryptography"
            )
    
    def _decrypt_config(self) -> Dict[str, Any]:
        """Decrypt and parse CORE_CONFIG"""
        self._check_cryptography()
        
        if not self._raw_config:
            raise ConfigMissingError("CORE_CONFIG is not set")
        
        if not self._secret:
            raise ConfigMissingError("CONFIG_SECRET is not set")
        
        # Validate Fernet key format
        try:
            f = Fernet(self._secret.encode() if isinstance(self._secret, str) else self._secret)
        except (ValueError, TypeError) as e:
            raise ConfigError(f"Invalid CONFIG_SECRET format: {e}")
        
        # Decode base64 and decrypt
        try:
            decoded = base64.b64decode(self._raw_config)
            decrypted = f.decrypt(decoded)
            return json.loads(decrypted)
        except InvalidToken:
            raise ConfigDecryptionError("Invalid encryption key or corrupted config")
        except base64.binascii.Error:
            raise ConfigDecryptionError("CORE_CONFIG is not valid base64")
        except json.JSONDecodeError as e:
            raise ConfigDecryptionError(f"Decrypted config is not valid JSON: {e}")
        except Exception as e:
            raise ConfigDecryptionError(f"Decryption failed: {e}")
    
    def _load_from_env_prefix(self, prefix: str = "AETHERYON_") -> Dict[str, Any]:
        """
        Alternative: Load flat config from environment variables
        Example: AETHERYON_PROVIDERS_API_KEY=xxx becomes {"providers": {"api_key": "xxx"}}
        """
        config = {}
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            
            # Remove prefix and split by underscore
            path = key[len(prefix):].lower().split("_")
            current = config
            for i, part in enumerate(path):
                if i == len(path) - 1:
                    current[part] = value
                else:
                    current = current.setdefault(part, {})
        return config
    
    def _load(self) -> None:
        """Main loading logic with fallbacks"""
        config_loaded = False
        
        # Try encrypted config first
        if self._raw_config and self._secret:
            try:
                self._config = self._decrypt_config()
                config_loaded = True
                logger.info("Config loaded from encrypted CORE_CONFIG")
            except ConfigError as e:
                if self._mode == "production":
                    raise
                self._warnings.append(f"Encrypted config failed: {e}")
                logger.warning(f"Encrypted config failed: {e}")
        
        # Fallback to environment prefix config (non-production only)
        if not config_loaded and self._mode != "production":
            env_config = self._load_from_env_prefix()
            if env_config:
                self._config = env_config
                config_loaded = True
                logger.info("Config loaded from environment variables (AETHERYON_*)")
                self._warnings.append("Using environment variables config (less secure)")
        
        # Final fallback: demo mode defaults
        if not config_loaded:
            if self._mode == "production":
                raise ConfigMissingError(
                    "Production mode requires either:\n"
                    "  - CORE_CONFIG + CONFIG_SECRET (encrypted config), or\n"
                    "  - Individual AETHERYON_* environment variables"
                )
            
            self._config = {
                "mode": "demo",
                "features": {}
            }
            logger.info("Running in demo mode with default config")
    
    # ----------------------
    # Public API
    # ----------------------
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Access nested config via dot notation with caching
        
        Args:
            path: Dot-separated path (e.g., "providers.llm.api_key")
            default: Value to return if path not found
        
        Returns:
            Value at path or default
        
        Examples:
            >>> config.get("database.url")
            "postgresql://localhost/db"
            >>> config.get("nonexistent.key", "fallback")
            "fallback"
        """
        if not path:
            return self._config
        
        # Check cache
        if path in self._cache:
            return self._cache[path]
        
        # Navigate through config
        keys = path.split(".")
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                self._cache[path] = default
                return default
        
        self._cache[path] = value
        return value
    
    def require(self, path: str) -> Any:
        """
        Same as get() but raises ConfigMissingError if missing
        
        Args:
            path: Dot-separated path (e.g., "providers.llm.api_key")
        
        Returns:
            Value at path
        
        Raises:
            ConfigMissingError: If path not found
        """
        value = self.get(path)
        if value is None:
            raise ConfigMissingError(f"Required config missing: {path}")
        return value
    
    def get_list(self, path: str, default: Optional[List[Any]] = None) -> List[Any]:
        """
        Get value as list, returns empty list if not found
        
        Args:
            path: Dot-separated path
            default: Default list if path not found
        
        Returns:
            Value as list
        """
        value = self.get(path, default)
        if value is None:
            return []
        return value if isinstance(value, list) else [value]
    
    def get_dict(self, path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get value as dict, returns empty dict if not found
        
        Args:
            path: Dot-separated path
            default: Default dict if path not found
        
        Returns:
            Value as dict
        """
        value = self.get(path, default)
        if value is None:
            return {}
        return value if isinstance(value, dict) else {}
    
    def feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled
        
        Supports both:
        - Top-level: {"multiagent": true}
        - Nested: {"features": {"multiagent": true}}
        
        Args:
            feature: Feature name (e.g., "multiagent")
        
        Returns:
            True if feature enabled, False otherwise
        """
        # Check top-level first
        top_level = self.get(feature)
        if isinstance(top_level, bool):
            return top_level
        
        # Check nested in features
        return bool(self.get(f"features.{feature}", False))
    
    def is_demo(self) -> bool:
        """
        Returns True if running in demo mode
        Demo mode = MODE != production OR explicit mode: "demo" in config
        """
        if self._mode == "production":
            return False
        return self._config.get("mode", "demo") == "demo"
    
    def is_production(self) -> bool:
        """Returns True if running in production mode"""
        return self._mode == "production" and not self.is_demo()
    
    def get_mode(self) -> str:
        """Returns current mode (demo, staging, production)"""
        return self._mode
    
    def get_warnings(self) -> List[str]:
        """Returns list of warnings from config loading"""
        return self._warnings.copy()
    
    def reload(self) -> None:
        """
        Hot reload configuration
        Useful for dynamic updates without restart
        """
        self._cache.clear()
        self._warnings.clear()
        self._load()
        logger.info("Config reloaded")
    
    def has_feature(self, feature: str) -> bool:
        """Alias for feature_enabled"""
        return self.feature_enabled(feature)
    
    # ----------------------
    # Validation helpers
    # ----------------------
    
    def validate_required(self, paths: List[str]) -> List[str]:
        """
        Validate multiple required paths at once
        
        Args:
            paths: List of dot-separated paths
        
        Returns:
            List of missing paths (empty if all present)
        """
        missing = []
        for path in paths:
            try:
                self.require(path)
            except ConfigMissingError:
                missing.append(path)
        return missing
    
    def require_all(self, paths: List[str]) -> None:
        """
        Require multiple paths, raises error if any missing
        
        Args:
            paths: List of dot-separated paths
        
        Raises:
            ConfigMissingError: If any path is missing
        """
        missing = self.validate_required(paths)
        if missing:
            raise ConfigMissingError(f"Missing required configs: {', '.join(missing)}")
    
    # ----------------------
    # Diagnostic methods
    # ----------------------
    
    def get_status(self) -> Dict[str, Any]:
        """
        Returns diagnostic status (no sensitive data)
        """
        return {
            "mode": self._mode,
            "is_demo": self.is_demo(),
            "has_encrypted_config": bool(self._raw_config and self._secret),
            "warnings": self._warnings,
            "config_keys": list(self._config.keys()) if self._config else [],
            "features": {
                k: v for k, v in self._config.get("features", {}).items()
            } if isinstance(self._config.get("features"), dict) else {}
        }


# ----------------------
# Singleton instance
# ----------------------

config = ConfigManager()


# ----------------------
# Example usage
# ----------------------

if __name__ == "__main__":
    # Setup logging for demo
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 50)
    print("AETHERYON Config Manager - Demo")
    print("=" * 50)
    
    # Show status
    status = config.get_status()
    print(f"\n📊 Status:")
    print(f"  Mode: {status['mode']}")
    print(f"  Demo: {status['is_demo']}")
    print(f"  Encrypted config: {status['has_encrypted_config']}")
    
    if status['warnings']:
        print(f"\n⚠️ Warnings:")
        for warning in status['warnings']:
            print(f"  - {warning}")
    
    # Check features
    print(f"\n🚀 Features:")
    features = ["multiagent", "analytics", "monitoring"]
    for feature in features:
        enabled = config.feature_enabled(feature)
        print(f"  {feature}: {'✅' if enabled else '❌'}")
    
    # Safe access
    print(f"\n📦 Config access examples:")
    print(f"  get('database.url'): {config.get('database.url', 'not set')}")
    print(f"  get('nonexistent', 'default'): {config.get('nonexistent', 'default')}")
    
    # This would raise error in production:
    # api_key = config.require("providers.llm.api_key")
    
    # Validate multiple required fields
    required = ["providers.llm.api_key", "database.url"]
    missing = config.validate_required(required)
    if missing:
        print(f"\n⚠️ Missing required configs: {missing}")
    else:
        print(f"\n✅ All required configs present")
    
    print("\n" + "=" * 50)
    print("✅ Config Manager ready")