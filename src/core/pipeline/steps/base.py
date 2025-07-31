from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, Generic

from pydantic import BaseModel

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)


class PipelineStep(ABC, Generic[TInput, TOutput]):
    name: str

    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_path = checkpoint_dir / self.name / "output.json"
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    def has_checkpoint(self) -> bool:
        return self.checkpoint_path.exists()

    def load_checkpoint(self) -> TOutput:
        return self.output_model.parse_raw(self.checkpoint_path.read_text())

    def save_checkpoint(self, output: TOutput):
        self.checkpoint_path.write_text(output.json(indent=2))

    def execute(self, input: TInput) -> TOutput:
        if self.has_checkpoint():
            print(f"[{self.name}] Resuming from checkpoint")
            return self.load_checkpoint()
        result = self.run(input)
        self.save_checkpoint(result)
        return result

    @property
    @abstractmethod
    def output_model(self) -> type:
        ...

    @abstractmethod
    def run(self, input: TInput) -> TOutput:
        ...
