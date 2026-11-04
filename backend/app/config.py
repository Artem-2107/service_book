from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "ServiceBook API"
    DEBUG: bool = True
    
    DATABASE_URL: str = "postgresql+asyncpg://postgres:1111@localhost:5432/service_book"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:1111@localhost:5432/service_book"
    
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_super_secret_key_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()