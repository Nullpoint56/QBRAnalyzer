from pydantic import BaseModel

from core.pipeline.contracts.base import StepOutputBase


class ParsedEmail(BaseModel):
    file_id: str
    from_: str
    to: list[str]
    date: str
    subject: str
    body: str


class RawFileBatch(StepOutputBase[list[ParsedEmail]]):
    pass

