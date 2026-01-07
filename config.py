import json
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

class Config(BaseSettings):
    url: str
    search_texts: List[str]
    check_interval: int = 10
    bot_token: str
    chat_id: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Allow extra fields in env/json
    )

def load_config() -> Config:
    # 1. Try loading from config.json first to seed values
    # 2. Environment variables will override these automatically due to pydantic-settings priority
    #    IF we configure it correctly. However, BaseSettings default priority is Env > Secrets > Config file.
    #    But we have a custom JSON file.
    
    file_data = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                file_data = json.load(f)
        except json.JSONDecodeError:
            pass

    # We instantiate Config passing the file data as kwargs. 
    # Environment variables will still take precedence over these kwargs if set.
    return Config(**file_data)
