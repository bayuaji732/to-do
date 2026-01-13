"""
Configuration management for the multi-agent chatbot system.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    openai_api_key: str
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Model Configuration
    llm_model: str = "gpt-5-nano"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 4000
    
    # Data Configuration
    dataset_path: str = "./data/sp500_companies.csv"
    duckdb_path: str = "./data/sp500.duckdb"
    
    # Agent Configuration
    max_agent_iterations: int = 5
    agent_timeout_seconds: int = 30
    
    # Evaluation Configuration
    eval_dataset_path: str = "./data/eval_queries.json"
    eval_results_path: str = "./data/eval_results.json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()