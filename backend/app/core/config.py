import configparser
import os
import sys
import json
from functools import lru_cache

class Settings:
    def __init__(self):
        self.config = configparser.ConfigParser()
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(base_dir, "config.ini")
        json_config_path = os.path.join(base_dir, "llm_config.json")
        secret_config_path = "/secrets/llm_config.json"
        
        if os.path.exists(config_path):
            self.config.read(config_path)
        elif os.path.exists(secret_config_path):
            self._load_json_config(secret_config_path)
        elif os.path.exists(json_config_path):
            self._load_json_config(json_config_path)
        else:
            print(f"Error: Secure configuration required. Please mount 'config.ini' or 'llm_config.json' to {base_dir} or {secret_config_path}.")
            sys.exit(1)

    def _load_json_config(self, path):
        try:
            with open(path, 'r') as f:
                file_content = f.read().strip()
            
            try:
                data = json.loads(file_content)
                # Map JSON keys to ConfigParser structure
                config_data = {
                    'api_key': data.get('api_key', ''),
                    'provider': data.get('provider', 'google'),
                    'model_name': data.get('model', 'gemini-1.5-pro'),
                    'base_url': data.get('base_url', '')
                }
                self.config.read_dict({'AI': config_data})
                print(f"Info: Loaded configuration from {path} (JSON)")
            except json.JSONDecodeError:
                # Fallback: Assume the file contains just the API Key string
                print(f"Warning: {path} is not valid JSON. Treating as raw API Key.")
                if file_content:
                    self.config.read_dict({'AI': {'api_key': file_content, 'provider': 'google', 'model_name': 'gemini-1.5-pro'}})
                else:
                    print(f"Error: {path} is empty.")
                    sys.exit(1)
        except Exception as e:
            print(f"Error reading {path}: {e}")
            sys.exit(1)

    @property
    def ai_provider(self):
        return os.getenv("AI_PROVIDER") or self.config.get('AI', 'provider', fallback='google')

    @property
    def ai_model(self):
        return os.getenv("AI_MODEL") or self.config.get('AI', 'model_name', fallback='gemini-1.5-pro')

    @property
    def ai_api_key(self):
        # Strict file-based config only
        key = self.config.get('AI', 'api_key', fallback='')
        if not key:
            raise ValueError("Secure configuration error: 'api_key' is missing in config.ini")
        return key.strip().strip('"').strip("'")

    @property
    def ai_base_url(self):
        return os.getenv("AI_BASE_URL") or self.config.get('AI', 'base_url', fallback='')

@lru_cache()
def get_settings():
    return Settings()
