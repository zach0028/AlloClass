from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    openai_api_key: str

    agent_model: str = "gpt-5.1"
    classifier_model: str = "gpt-5-nano"
    challenger_model: str = "gpt-5.1"
    evaluator_model: str = "gpt-5.1"
    generator_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"

    challenger_threshold: float = 0.75
    few_shot_top_k: int = 5
    self_consistency_enabled: bool = True
    self_consistency_n: int = 3

    drip_feed_default_interval: int = 10

    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env"}


settings = Settings()
