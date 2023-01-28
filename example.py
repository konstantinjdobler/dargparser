from dataclasses import dataclass
from typing import Literal

from dargparser import Choice, dArg, dargparse

# flake8 doesn't like Choice with strings, you can use Literal instead.
# flake8: noqa


@dataclass
class Args:
    epochs: int
    learning_rate: float = dArg(aliases="--lr", help="Required argument (no default).")
    data_path: str = dArg(default="./data/", aliases=["--data", "-d"])
    # str | None syntax is only available in Python >=3.10. Use Optional[str] for older versions.
    extra_data: str | None = dArg(default=None)
    cuda: bool = dArg(default=True, help="We automatically create a `--no_<arg>` flag for bools.")
    precision: Choice[32, 16, 8, "bf16", "tf32"] = dArg(default=32, help="Choices with mixed types are supported.")
    some_list_arg: list[int] = dArg(default=[1, 2, 3])
    evaluation_datasets: list[Choice["xnli", "tydiqa", "wikiann", "squad"]] = dArg(
        default=["xnli", "wikiann"], help="Select arbitrary number of datasets to evaluate on."
    )


@dataclass
class LoggingArgs:
    log_dir: str | None = dArg(default=None)
    log_backends: list[Choice["wandb", "tensorboard", "neptune"]] = dArg(default=["wandb"])
    # Choice is just an alias for Literal to be more descriptive.
    log_level: Literal["debug", "info", "warning", "error", "critical"] = dArg(default="info")


def main(args: Args, logging_args: LoggingArgs):
    print("Arguments:", args)
    print("Logging arguments:", logging_args)


if __name__ == "__main__":
    args, logging_args = dargparse(dataclasses=(Args, LoggingArgs))
    main(args, logging_args)
