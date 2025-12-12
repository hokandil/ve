"""
Feature flags configuration for gradual rollout of new features
"""
import os
from typing import Dict, Any


class FeatureFlags:
    """
    Feature flags for controlling experimental features.
    Supports environment variables and runtime overrides.
    """
    
    def __init__(self):
        self._flags: Dict[str, bool] = {}
        self._load_from_env()
    
    def _load_from_env(self):
        """Load feature flags from environment variables"""
        # DSPy delegation optimization
        self._flags['use_dspy_delegation'] = os.getenv(
            'USE_DSPY_DELEGATION', 
            'false'
        ).lower() == 'true'
        
        # A/B testing percentage for DSPy (0-100)
        self._flags['dspy_rollout_percentage'] = int(os.getenv(
            'DSPY_ROLLOUT_PERCENTAGE',
            '0'  # Start at 0%, gradually increase
        ))
        
        # Enable DSPy optimization training
        self._flags['enable_dspy_training'] = os.getenv(
            'ENABLE_DSPY_TRAINING',
            'false'
        ).lower() == 'true'
        
        # Use optimized vs base DSPy module
        self._flags['use_optimized_dspy'] = os.getenv(
            'USE_OPTIMIZED_DSPY',
            'true'
        ).lower() == 'true'
        
        # Log delegation decisions for training
        self._flags['log_delegation_decisions'] = os.getenv(
            'LOG_DELEGATION_DECISIONS',
            'true'
        ).lower() == 'true'
    
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self._flags.get(flag_name, False)
    
    def get_value(self, flag_name: str, default: Any = None) -> Any:
        """Get feature flag value"""
        return self._flags.get(flag_name, default)
    
    def set_flag(self, flag_name: str, value: Any):
        """Set a feature flag at runtime (for testing)"""
        self._flags[flag_name] = value
    
    def get_all_flags(self) -> Dict[str, Any]:
        """Get all feature flags"""
        return self._flags.copy()


# Global feature flags instance
_feature_flags = FeatureFlags()


def get_feature_flags() -> FeatureFlags:
    """Get the global feature flags instance"""
    return _feature_flags


def is_feature_enabled(flag_name: str) -> bool:
    """Quick check if a feature is enabled"""
    return _feature_flags.is_enabled(flag_name)


def should_use_dspy_delegation() -> bool:
    """
    Determine if DSPy delegation should be used.
    Supports gradual rollout via percentage.
    """
    import random
    
    # Check if DSPy is globally enabled
    if not is_feature_enabled('use_dspy_delegation'):
        return False
    
    # Check rollout percentage
    rollout_pct = _feature_flags.get_value('dspy_rollout_percentage', 0)
    
    if rollout_pct >= 100:
        return True
    elif rollout_pct <= 0:
        return False
    else:
        # Random selection based on percentage
        return random.random() * 100 < rollout_pct
