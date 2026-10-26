from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    app_mode: str = "DEMO"
    database_url: str = ""
    external_requests_enabled: bool = False
    live_enabled: bool = False
    demo_owner_password: str = "local-demo-owner"
    demo_partner_password: str = "local-demo-partner"
    max_order_eur: int = Field(default=500, ge=1, le=500)
    max_position_eur: int = Field(default=1000, ge=1, le=1000)
    approval_ttl_seconds: int = Field(default=120, ge=1, le=600)

    def validate_mode(self):
        if self.app_mode != "DEMO" or self.live_enabled:
            raise ValueError("This preview supports DEMO only. External execution is not implemented.")


settings = Settings()
