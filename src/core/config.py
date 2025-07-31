from pathlib import Path

from pydantic import BaseModel

from core.pipeline.steps.data_loading_step.config import DataLoadingConfig
from core.pipeline.steps.data_parsing_step.config import DataParsingConfig


class StepsConfig(BaseModel):
    data_loading: DataLoadingConfig
    data_parsing: DataParsingConfig
    filtering: FilteringConfig
    signals_extraction: SignalsExtractionConfig
    signals_interpretation: SignalsInterpretationConfig


class PipelineBaseConfig(BaseModel):
    checkpoint_dir: Path
    environment: str = "dev"


class FullPipelineConfig(BaseModel):
    pipeline: PipelineBaseConfig
    steps: StepsConfig
