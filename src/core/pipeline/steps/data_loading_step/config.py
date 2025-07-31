from pathlib import Path

from pydantic import BaseModel


class DataLoadingConfig(BaseModel):
    input_dir: Path
    max_tokens_per_chunk: int = 2048
    chunk_overlap: int = 200