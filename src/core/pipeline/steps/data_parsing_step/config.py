from pydantic import BaseModel


class DataParsingConfig(BaseModel):
    model: str = "mistral"
    system_prompt: str = (
        "You are an email parser. Extract all the messages from the raw email thread below.\n"
        "Return them in the following format:\n\n{format_instructions}\n\nEMAIL THREAD:\n{input}"
    )
    max_tokens: int = 2048
    chunk_overlap: int = 200
