"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    
    # API
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "VE SaaS Platform"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # User frontend
        "http://localhost:3001",  # Admin frontend
        "http://localhost:5173",  # Vite dev server
    ]
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Kubernetes
    K8S_API_URL: str = "https://localhost:6443"
    K8S_NAMESPACE_PREFIX: str = "customer-"
    
    # Agent Gateway
    AGENT_GATEWAY_URL: str = "http://172.23.0.7:8080"
    AGENT_GATEWAY_AUTH_TOKEN: str = "dev-token"
    
    # LLM Providers (API-agnostic)
    GOOGLE_API_KEY: str = ""  # For Gemini embeddings and LLM
    OPENAI_API_KEY: str = ""  # For OpenAI embeddings and LLM
    ANTHROPIC_API_KEY: str = ""  # For Claude LLM
    
    # Token Pricing (per 1K tokens)
    GPT4_INPUT_PRICE: float = 0.03
    GPT4_OUTPUT_PRICE: float = 0.06
    GPT35_INPUT_PRICE: float = 0.0015
    GPT35_OUTPUT_PRICE: float = 0.002
    
    # OpenTelemetry
    OTEL_ENABLED: bool = False
    OTEL_EXPORTER_ENDPOINT: str = "http://localhost:4317"  # Jaeger/Tempo OTLP endpoint
    
    # Webhooks
    WEBHOOK_SECRET: str = "change-me-in-production"
    
    class Config:
        env_file = [".env", "../.env"]
        case_sensitive = True
        extra = "ignore"

settings = Settings()
