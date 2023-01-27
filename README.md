# dargparser - the typed argparser with dataclasses

![Build Status](https://github.com/konstantinjdobler/dargparser/actions/workflows/test_publish.yml/badge.svg?branch=main) ![Python Versions](https://img.shields.io/badge/dynamic/json?query=info.requires_python&label=python&url=https%3A%2F%2Fpypi.org%2Fpypi%2Fdargparser%2Fjson) [![PyPI version](https://badge.fury.io/py/dargparser.svg)](https://badge.fury.io/py/dargparser) ![Code Style](https://img.shields.io/badge/code%20style-black-black)

A lean and hackable typed argument parser based on dataclasses. For deep learning research and everything else.

## Quickstart

Install `dargparser` with:

```sh
pip install dargparser
```

## Usage

Simply define a `dataclass` with your arguments and corresponding types. You can use the `dArg` utility to define default values, help texts or aliases. All information is additionally used to display a semantically rich help message with the `--help / -h` flag.

```python
from dataclasses import dataclass
from dargparser import dargparse, dArg, Choice

@dataclass
class Args:
    learning_rate: float = dArg(aliases="--lr", help="Required argument (no default).")
    data_path: str = dArg(default="./data/", aliases=["--data", "-d"])
    extra_data: str | None = dArg(default=None)
    epochs: int = dArg(default=42)
    cuda: bool = dArg(default=True, help="We automatically create a `--no_<arg>` flag for bools.")
    precision: Choice[32, 16, 8, "bf16", "tf32"] = dArg(default=32, help="Choices with mixed types are supported.")
    some_list_arg: list[int] = dArg(default=[1, 2, 3])

args = dargparse(Args)
args.<...>  # <-- this now has typehints and contains the values passed in via the command line
```

Everything can be defined in a single place and you get strong typing of your arguments for free! Using the example above:

```python
# Calling your script from the command line with these arguments...
example_cmd_args = "--lr 1e-4 -d ./special-data/ --epochs 1 --precision 16 --some_list_arg 0 1 42"

# ...would produce these values for `args`:
Args(learning_rate=0.0001, data_path='./special-data/', extra_data=None, epochs=1, cuda=True, precision=16, some_list_arg=[0, 1, 42])
```

<p>

<details>
<summary><b>Advanced Usage</b></summary>
<p>

**Required arguments** without a default value, alias or help text do not need `dArg`:

```python
@dataclass
class Args:
    learning_rate: float
    ...
```

**List args:**
You can easily specify arguments that take multiple values as follows (behavior is similar to `argparse`'s `nargs="+"`). Note that the default values should also be lists in this case.

```python
@dataclass
class Args:
    required_list: list[int] = dArg(help="Required.")
    empty_default_list: list[int] = dArg(default=[], help="Empty list as default.")
    custom_default_list: list[int] = dArg(default=[1, 2, 3])
```

**List + Choice combindation:**
You can combine `list` and `Choice` to allow the selection of an arbitrary number of values from a predefined set.

```python
@dataclass
class Args:
    datasets: list[Choice["mnist", "cifar10", "imagenet"]] = dArg(default=["mnist", "cifar10"])
```

**Config files:**
We support optionally reading arguments from a config file. By default, we read a config file specified in the CLI via the `"--cfg"` flag. The file is expected to contain lines of single flag-argument pairs, like you would specify them in the command line:

```txt
--argument value
--argument_two 42
--list_argument item1 item2 item3
```

If an argument is present in the config file and also specified via the CLI, we prefer the value in the CLI.

You can also use a different flag (e.g. `"--config"`) if you like.

```python
from dargparser import dargparse, dArg

@dataclass
class Args:
    lorem_arg: str = dArg(default="ipsum")

args = dargparse(Args, config_flag="--config")
```

**Multiple dataclasses:**
To seperate concerns, you can split your arguments into multiple `dataclasses`, e.g. `TrainingArgs`, `ModelArgs`, and `DataArgs`.

```python
@dataclass
class TrainingArgs:
    epochs: int = dArg(default=5)
    ...

@dataclass
class ModelArgs:
    model: Choice["roberta-base", "xlm-roberta-base"] = dArg(default="roberta-base")
    ...

@dataclass
class DataArgs:
    data_path: str = dArg(aliases="--data")
    ...

# the arguments parsed from the CLI are now split into the respective variables
training_args, model_args, data_args = dargparse(TrainingArgs, ModelArgs, DataArgs)
```

</details>

## Formalities

This project is a fork of the [`HfArgparser`](https://github.com/huggingface/transformers/blob/fd0ef8b66d957ac0fc94d715262dca1a6005a5ed/src/transformers/hf_argparser.py) from the HuggingFace `transformers` repository, with added features such as:

- Supporting aliases for command line flags
- Supporting reading of arguments from a config file specified via the command line
- Easy specification of choices via `Literal` and `Choice`
- Supporting mixed types for `Literal` and `Enum` arguments
- Supporting nested `list` and `Choice`
- Enriching the help message with type information and more
- Supporting modern typing patterns such as builtin types (`list[int]` vs. `typing.List[int]`) and Optional (`str | None` vs. `typing.Optional[str]`)
- Fixing some type hint issues for VSCode

Some of these changes have already been contributed back upstream.

This code is distributed under the Apache 2.0 license, without restricting any rights reserved by the HuggingFace team.
