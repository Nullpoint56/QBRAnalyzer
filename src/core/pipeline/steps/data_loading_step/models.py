from pydantic import BaseModel


class RawTextInput(BaseModel):
    content: str

class ParsedEmail(BaseModel):
    from_: str
    to: list[str]
    date: str
    subject: str
    body: str

class EmailExtractionOutput(BaseModel):
    emails: list[ParsedEmail]