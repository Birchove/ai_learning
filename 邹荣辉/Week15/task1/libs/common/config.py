"""统一配置 — README 锁定值作为默认值，可被环境变量覆盖。"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # 模型路径
    mineru_model_path: str = ""
    bge_model_path: str = ""
    clip_model_path: str = ""
    reranker_model_path: str = ""
    qwen_vl_model_path: str = ""
    torch_device: str = "cuda:0"
    qwen_vl_dtype: str = "bfloat16"

    # 中间件
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_parse_topic: str = "doc_parse"
    kafka_consumer_group: str = "parse-worker"
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_text_collection: str = "text_chunks"
    milvus_image_collection: str = "image_chunks"
    sqlite_path: str = "./data/app.db"

    # 存储
    data_dir: str = "./data"
    pdf_dir: str = "./data/pdfs"
    parsed_dir: str = "./data/parsed"
    static_url_prefix: str = "/static"

    # 检索（README 锁定值）
    chunk_size: int = 500
    chunk_overlap: int = 50
    bm25_top_k: int = 100
    bge_top_k: int = 100
    clip_top_k: int = 50
    rerank_top_k: int = 10

    # 生成
    qwen_vl_max_input_tokens: int = 4000
    qwen_vl_max_output_tokens: int = 1000
    qwen_vl_max_images: int = 3

    upload_api_port: int = 8001
    chat_api_port: int = 8002
    log_level: str = "INFO"
