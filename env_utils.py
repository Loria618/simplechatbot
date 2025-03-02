import os
from dotenv import load_dotenv

def is_production():
    """
    Determine if the application is running in production environment.
    
    Returns:
        bool: True if running in production, False otherwise
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Check if running on Render
    is_render = os.environ.get('RENDER', '').lower() == 'true'
    
    # Check explicit environment setting
    env_setting = os.environ.get('ENVIRONMENT', 'local').lower()
    is_prod_env = env_setting in ['production', 'prod']
    
    return is_render or is_prod_env

def get_port():
    """
    Get the port to run the server on.
    
    Returns:
        int: Port number
    """
    # Render sets PORT environment variable
    port = os.environ.get('PORT')
    if port:
        return int(port)
    
    # Default local port
    return 8000

def configure_for_environment():
    """
    Configure application settings based on the environment.
    
    Returns:
        dict: Configuration settings
    """
    # Load environment variables
    load_dotenv()
    
    # Check environment
    production = is_production()
    
    # Base configuration
    config = {
        'production': production,
        'port': get_port(),
        'host': '0.0.0.0',  # Bind to all interfaces
    }
    
    # If in production, use HuggingFace API
    if production:
        # Update config to use HuggingFace API
        config['use_huggingface_api'] = True
        config['huggingface_api_key'] = os.environ.get('HUGGINGFACE_API_KEY', '')
    
    return config
