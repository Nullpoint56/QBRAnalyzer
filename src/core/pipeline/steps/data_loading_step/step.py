from langchain.output_parsers import StructuredOutputParser
from langchain_core.prompts import PromptTemplate

from core.pipeline.steps.base import PipelineStep
from core.pipeline.steps.data_loading_step.models import RawTextInput, EmailExtractionOutput


class ExtractEmailsStep(PipelineStep[RawTextInput, EmailExtractionOutput]):
    name = "extract_emails"

    @property
    def output_model(self):
        return EmailExtractionOutput

    def run(self, input: RawTextInput) -> EmailExtractionOutput:
        parser = StructuredOutputParser.from_orm_model(EmailExtractionOutput)

        prompt = PromptTemplate(
            template=(
                "You are an email parser. Extract all the messages from the raw email thread below.\n"
                "Return them in the following format:\n\n{format_instructions}\n\nEMAIL THREAD:\n{input}"
            ),
            input_variables=["input"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        llm = Ollama(model="mistral")
        chain = prompt | llm | parser
        return chain.invoke({"input": input.content})