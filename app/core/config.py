import os


class Settings:
    def __init__(self) -> None:
        self.database_host = os.getenv("DATABASE_HOST", "localhost")
        self.database_port = int(os.getenv("DATABASE_PORT", "5432"))
        self.database_name = os.getenv("DATABASE_NAME", "forumx")
        self.database_user = os.getenv("DATABASE_USER", "forumx")
        self.database_password = os.getenv("DATABASE_PASSWORD", "")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
        self.access_token_expire_minutes = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )


settings = Settings()
