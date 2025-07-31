from pathlib import Path

from langchain.output_parsers import StructuredOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.pipeline.contracts.email import ParsedEmailsBatch, ParsedEmail
from core.pipeline.contracts.file import RawFile
from core.pipeline.steps.base import PipelineStep
from core.pipeline.steps.data_parsing_step.config import DataParsingConfig


class DataParsingStep(PipelineStep[RawFile, ParsedEmailsBatch]):
    name = "parse_data"

    def __init__(self, checkpoint_dir: Path, config: DataParsingConfig):
        super().__init__(checkpoint_dir)
        self.config = config

    @property
    def output_model(self):
        return ParsedEmailsBatch

    def run(self, input: RawFile) -> ParsedEmailsBatch:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.max_tokens,
            chunk_overlap=self.config.chunk_overlap,
        )

        chunks = splitter.split_text(input.content)
        parser = StructuredOutputParser.from_orm_model(ParsedEmailsBatch)

        prompt = PromptTemplate(
            template=self.config.system_prompt,
            input_variables=["input"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        llm = Ollama(model=self.config.model)
        chain = prompt | llm | parser

        all_emails: list[ParsedEmail] = []
        for chunk in chunks:
            parsed = chain.invoke({"input": chunk})
            all_emails.extend(parsed.messages)

        return ParsedEmailsBatch(file_id=input.file_id, messages=all_emails)