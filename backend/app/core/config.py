from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/traffic_violation?charset=utf8mb4"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "change-me-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    MEDIA_STORAGE_DIR: str = "./media"
    REPORT_STORAGE_DIR: str = "./reports"
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024
    ALLOWED_IMAGE_TYPES: tuple[str, ...] = ("image/jpeg", "image/png", "image/webp")
    # 邮件通知（杨翼-8）
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_SECURITY: str = "starttls"
    SMTP_TIMEOUT_SECONDS: float = 10.0
    EMAIL_CODE_TTL_SECONDS: int = 600
    EMAIL_CODE_RESEND_SECONDS: int = 60
    EMAIL_CODE_MAX_ATTEMPTS: int = 5
    # 随手拍奖励（杨翼-9）
    REWARD_DEFAULT_AMOUNT: int = 10
    AI_PROVIDER: str = "stub"  # stub | local
    LLM_PROVIDER: str = ""  # zhipu | openai_compatible
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    LLM_TEXT_MODEL: str = "glm-5.1"
    LLM_VISION_MODEL: str = "glm-5v-turbo"
    LLM_MODE: str = "text"  # text | vision
    LLM_TIMEOUT_SECONDS: float = 30


settings = Settings()
