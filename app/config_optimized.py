"""
Optimized configuration for Personal Health Record Manager
"""
# Import optimized configuration management
from .utils.config_manager import get_config


# For backwards compatibility, expose the get_config function
# This allows existing code to continue working while we transition
def get_config_class(config_name=None):
    """Get configuration class (backwards compatibility)"""
    return get_config(config_name)

# Maintain backwards compatibility for direct Config access
Config = get_config()
