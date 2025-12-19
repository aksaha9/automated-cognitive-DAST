import configparser
import os
from functools import lru_cache

class Settings:
    def __init__(self):
        self.config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.ini")
        
        if os.path.exists(config_path):
            self.config.read(config_path)
        else:
            # Fallback or default values if config.ini is missing
            self.config['AI'] = {
                'provider': 'google',
                'model_name': 'gemini-1.5-pro',
                'api_key': '',
                'base_url': ''
            }
            print(f"Warning: Config file not found at {config_path}. Using defaults.")

    @property
    def ai_provider(self):
        return self.config.get('AI', 'provider', fallback='google')

    @property
    def ai_model(self):
        return self.config.get('AI', 'model_name', fallback='gemini-1.5-pro')

    @property
    def ai_api_key(self):
        key = self.config.get('AI', 'api_key', fallback='')
        return key.strip().strip('"').strip("'")

    @property
    def ai_base_url(self):
        return self.config.get('AI', 'base_url', fallback='')

@lru_cache()
def get_settings():
    return Settings()
