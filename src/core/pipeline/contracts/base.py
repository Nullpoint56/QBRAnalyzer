from pathlib import Path
from typing import TypeVar, Optional, Generic

from pydantic import BaseModel

T = TypeVar("T")


class OriginMetadata(BaseModel):
    chunk_id: Optional[int] = None
    email_index: Optional[int] = None
    signal_index: Optional[int] = None
    step: Optional[str] = None


class SourceTrace(BaseModel):
    file_id: str
    file_path: Path
    origin: OriginMetadata


class StepOutputBase(BaseModel, Generic[T]):
    source: SourceTrace
    data: T
