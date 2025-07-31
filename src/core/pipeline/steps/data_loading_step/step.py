from pathlib import Path
from uuid import uuid4

from core.pipeline.contracts.base import SourceTrace
from core.pipeline.contracts.file import RawFileBatch, RawFile
from core.pipeline.steps.base import PipelineStep
from core.pipeline.steps.data_loading_step.config import DataLoadingConfig


class DataLoadingStep(PipelineStep[None, RawFileBatch]):
    name = "load_files"

    def __init__(self, checkpoint_dir: Path, config: DataLoadingConfig):
        super().__init__(checkpoint_dir)
        self.config = config

    @property
    def output_model(self):
        return RawFileBatch

    def run(self, input: None) -> RawFileBatch:
        files = []
        for file_path in self.config.input_dir.glob("*.txt"):
            text = file_path.read_text(encoding="utf-8")
            files.append(RawFile(file_id=str(uuid4()), path=file_path, content=text))

        # Example usage in a step:
        new_trace = self.enrich_trace(prev_trace, email_index=2, step="ParsingStep")

        return RawFileBatch(files=files)

    def enrich_trace(self, base: SourceTrace, **kwargs) -> SourceTrace:
        return SourceTrace(
            file_id=base.file_id,
            file_path=base.file_path,
            origin=base.origin.model_copy(update=kwargs),
        )