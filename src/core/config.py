from pathlib import Path

from pydantic import BaseModel


class StepsConfig(BaseModel):
    data_loading_step: DataLoadingStepConfig
    filtering_step: FilteringStepConfig
    signals_extraction: SignalsExtractionConfig
    signals_interpretation: SignalsInterpretationConfig


class PipelineBaseConfig(BaseModel):
    checkpoint_dir: Path
    environment: str = "dev"


class FullPipelineConfig(BaseModel):
    pipeline: PipelineBaseConfig
    steps: StepsConfig
