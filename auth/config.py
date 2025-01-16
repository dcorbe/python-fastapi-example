from pydantic import BaseModel, Field
import os


class JWTConfig(BaseModel):
    """Centralized JWT configuration"""

    secret_key: str = Field(...)
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    @classmethod
    def from_env(cls) -> "JWTConfig":
        secret_key = os.getenv("JWT_SECRET", "")
        if not secret_key:
            raise ValueError("JWT_SECRET environment variable must be set")

        return cls(
            secret_key=secret_key,
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
            ),
        )


# Global instance - initialized at startup
jwt_config: JWTConfig | None = None


def get_jwt_config() -> JWTConfig:
    if jwt_config is None:
        raise RuntimeError(
            "JWT config not initialized. Call initialize_jwt_config() first."
        )
    return jwt_config


def initialize_jwt_config() -> None:
    global jwt_config
    jwt_config = JWTConfig.from_env()
