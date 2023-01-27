from dataclasses import dataclass
from typing import Optional
from src.dargparser import dargparse, dArg, Choice





@dataclass
class Args:
    pretrained_model: str = dArg(default="xlm-roberta-base", help="Pretrained model to use")
    target_tokenizer: str = dArg(default=None)
    extend_tokenizer: str = dArg(default=None, aliases="--extend")
    target_fasttext_data: str = dArg(default=None)
    fasttext_dim: int = dArg(default=300)
    fasttext_epochs: int = dArg(default=1)
    processes: int = dArg(default=4)
    fuzzy_search: bool = dArg(default=True)
    language_identifier: Optional[str] = dArg(default=None)
    bois: list[int] = dArg(default_factory=list)
    qq: Choice[42, "wer"] = dArg(default=42)
    boiq: bool | None = dArg(default=True)
    eor: str | None = dArg(default=None)
    inti: int | None = dArg(default=None)
    qdq: Choice[42, "wer", None] = dArg(default=42)
    hackyl: list[int] = dArg(default=[2,3])
    listw: list[Choice["mnist", "cifar10", "imagenet"]] = dArg(default=["mnist", "cifar10"])




def main(args: Args):
    print("fasttext", args)


if __name__ == "__main__":
    args = dargparse(dataclasses=Args)
    main(args)
