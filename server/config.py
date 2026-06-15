import boto3
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_default_region: str = "us-east-1"
    openai_api_key: str
    pinecone_api_key: str
    pinecone_index_name: str = "aws-intelligence"
    langchain_api_key: str
    langchain_project: str = "aws-intelligence-server"
    mcp_server_name: str = "aws-intelligence"
    mcp_server_version: str = "0.1.0"
    rag_top_k: int = 5
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


def get_client(service: str, region_name: str | None = None):
    return boto3.client(
        service,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=region_name or settings.aws_default_region,
    )
