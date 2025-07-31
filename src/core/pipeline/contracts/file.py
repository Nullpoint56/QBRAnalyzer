from pathlib import Path

from pydantic import BaseModel

from core.pipeline.contracts.base import StepOutputBase


class RawFile(BaseModel):
    file_id: str
    path: Path
    content: str


class RawFileBatch(StepOutputBase[list[RawFile]]):
    pass
