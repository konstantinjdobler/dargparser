# dargparser - the typed argparser with dataclasses

---

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
    learning_rate: float = dArg(help="Required argument (no default).")
    data_path: str = dArg(default="./data/", aliases=["--data", "-d"])
    extra_data: str | None = dArg(default=None)
    epochs: int = dArg(default=42)
    cuda: bool = dArg(default=True, help="We automatically create a `--no_<arg>` flag for bools.")
    precision: Choice[32, 16, 8, "bf16", "tf32"] = dArg(default=32, help="Choices with mixed types are supported.")

args = dargparse(Args)
args.<...>  # <-- this now has typehints and contains the values passed in via the command line
```

Everything can be defined in a single place and you get strong typing of your arguments for free!

<details> 
<summary><b>Advanced Usage</b></summary>
<p>


**List args**
You can easily specify `list` arguments as follows (behavior is similar to `argparse`'s `nargs="+"`). To specifiy default values, use the `default_factory` argument instead of `default`.

```python
@dataclass
class Args:
    required_list: list[int] = dArg(help="Required.")
    empty_default_list: list[int] = dArg(default_factory=list, help="Empty list as default.")
    custom_default_list: list[int] = dArg(default_factory=lambda: [1, 2, 3])
```

**Config files**
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
**Multiple dataclasses**
To seperate concerns, you can split your arguments into multiple `dataclasses`, e.g. `TrainingArgs`, `ModelArgs`, and `LoggingArgs`.

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

This project is a fork of the `HfArgparser` from the HuggingFace `transformers` repository, with added features such as:

- Supporting aliases for command line flags
- Supporting reading of arguments from a config file specified via the command line 
- Easy specfiication of choices via `Literal` and `Choice`
- Supporting mixed types for `Literal` and `Enum` arguments
- Enriching the help message with type information and more
- Supporting modern typing patterns such as builtin types (`list[int]` vs. `typing.List[int]`) and Optional (`str | None` vs. `typing.Optional[str]`)
- Fixing some type hint issues for VSCode

Some of these change shave already been contributed back upstream.

This code is distributed under the Apache 2.0 license, without restricting any rights by the HuggingFace team.


