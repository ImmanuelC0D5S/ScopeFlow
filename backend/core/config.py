from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ScopeFlow"
    database_url: str = "postgresql://neondb_owner:npg_0FpMmNGO4wgb@ep-wandering-mode-aotv7df7.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"


settings = Settings()
