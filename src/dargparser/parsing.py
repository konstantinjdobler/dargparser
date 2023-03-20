# Copyright of modifications Konstantin Dobler (original: https://github.com/huggingface/transformers/blob/fd0ef8b66d957ac0fc94d715262dca1a6005a5ed/src/transformers/hf_argparser.py).
#
# Copyright 2020 The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import dataclasses
import sys
from argparse import ArgumentParser
from copy import copy
from enum import Enum
from inspect import isclass
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    NewType,
    Optional,
    Tuple,
    TypeVar,
    Union,
    get_type_hints,
)

from .helpers import (
    ArgumentDefaultsLongHelpFormatter,
    make_choice_type_function,
    string_to_bool,
)

try:
    # For Python versions <3.8, Literal is not in typing: https://peps.python.org/pep-0586/
    from typing import Literal
except ImportError:
    # For Python 3.7
    from typing_extensions import Literal

try:
    from types import UnionType
except ImportError:
    # For Python <3.10, UnionType and the associated X | Y syntax are not supported
    # (https://docs.python.org/3/library/types.html#types.UnionType)
    UnionType = "NotImplemented"


Choice = Literal
DataClass = NewType("DataClass", Any)
DataClassType = NewType("DataClassType", Any)
DataclassOrDataclassTuple = TypeVar("DataclassOrDataclassTuple", bound=Union[DataClass, Tuple[DataClass, ...]])


def dargparse(dataclasses: DataclassOrDataclassTuple, config_flag: str = "--cfg") -> DataclassOrDataclassTuple:
    """Parse command line args into the given dataclass(es), optionally also reading from a config file.

    Args:
        dataclasses (Dataclass or tuple[Dataclass]): The dataclass(es) to parse the arguments into.

        config_flag (str, optional): Will look for a config file in the path specified via this flag. Example: `--random_arg 42 --cfg ./configs/train.txt --random_arg2 42`. The file is expected to contain one argument flag and value per line. Arguments specified via the CLI overwrite the config. Defaults to `"--cfg"`.

    Returns:
        The Dataclass or tuple[Dataclass] filled with the parsed arguments from the command line or config file.
    """
    parser = dArgParser(dataclasses)
    result = parser.parse_args_into_dataclasses(args_file_flag=config_flag)
    if len(result) == 1 and not isinstance(dataclasses, tuple):
        return result[0]
    else:
        return result


def dArg(
    *,
    default: Any = dataclasses.MISSING,
    aliases: Union[str, List[str]] = None,
    help: str = None,
    default_factory: Callable[[], Any] = dataclasses.MISSING,
    metadata: dict = None,
    **kwargs,
) -> dataclasses.Field:
    """
    Example using the `dArgParser` and `dArg`:
    ```
    from dargparse import dargparse, dArg

    @dataclass
    class Args:
        required_float_arg: float = dArg(help="You will need to specify this arg!")
        string_arg: str = dArg(default="nice", aliases=["--str", "-s"], help="What a nice syntax!")
        list_arg: list[int] = dArg(default_factory=list, aliases="-l", help="Empty list as default with default_factory.")
        choices_arg: Literal["dark", "light", 42, 78.0] = dArg(default="dark", help="Choices (mixed types are supported).")

    args = dargparse(Args)
    args.<...>  # <-- this now has typehints and contains the values passed in via the command line
    ```

    Args:
        default (Any, optional):
            Default value for the argument. If default and default_factory is not specified, the argument is required.
            Defaults to dataclasses.MISSING.
        aliases (Union[str, List[str]], optional):
            Single string or list of strings of aliases that can be used in the command line for this argument, e.g. `aliases=["--example", "-e"]`.
            Defaults to None.
        help (str, optional): Help string to pass on to argparse that can be displayed with --help. Defaults to None.
        default_factory (Callable[[], Any], optional):
            The default_factory is a 0-argument function called to initialize a field's value. It is useful to provide
            default values for mutable types, although lists can just be provided with the `default=` keyword argument.
            Mutually exclusive with `default=`.
            Defaults to dataclasses.MISSING.
        metadata (dict, optional): Further metadata to pass on to `dataclasses.field`. Defaults to None.

    Returns:
        Field: A `dataclasses.Field` with the desired properties.
    """
    if metadata is None:
        # Important, don't use as default param in function signature because dict is mutable and shared across function calls
        metadata = {}
    if aliases is not None:
        metadata["aliases"] = aliases
    if help is not None:
        metadata["help"] = help

    # Catch list default values here and redirect to default_factory
    if isinstance(default, list):
        default_copy = copy(default)
        default_factory = lambda: default_copy  # noqa: E731
        default = dataclasses.MISSING
    return dataclasses.field(metadata=metadata, default=default, default_factory=default_factory, **kwargs)


class dArgParser(ArgumentParser):
    """
    This subclass of `argparse.ArgumentParser` uses type hints on dataclasses to generate arguments.

    The class is designed to play well with the native argparse. In particular, you can add more (non-dataclass backed)
    arguments to the parser after initialization and you'll get the output back after parsing as an additional
    namespace. Optional: To create sub argument groups use the `_argument_group_name` attribute in the dataclass.
    """

    dataclass_types: Iterable[DataClassType]

    def __init__(self, dataclass_types: Union[DataClassType, Iterable[DataClassType]], **kwargs):
        """
        Args:
            dataclass_types:
                Dataclass type, or list of dataclass types for which we will "fill" instances with the parsed args.
            kwargs:
                (Optional) Passed to `argparse.ArgumentParser()` in the regular way.
        """
        # To make the default appear when using --help
        if "formatter_class" not in kwargs:
            kwargs["formatter_class"] = ArgumentDefaultsLongHelpFormatter
        super().__init__(**kwargs)
        if dataclasses.is_dataclass(dataclass_types):
            dataclass_types = [dataclass_types]
        self.dataclass_types = list(dataclass_types)
        for dtype in self.dataclass_types:
            self._add_dataclass_arguments(dtype)

    @staticmethod
    def _parse_dataclass_field(parser: ArgumentParser, field: dataclasses.Field, type_str: str):
        field_name = f"--{field.name}"
        kwargs = field.metadata.copy()
        # field.metadata is not used at all by Data Classes,
        # it is provided as a third-party extension mechanism.
        if isinstance(field.type, str):
            raise RuntimeError(
                "Unresolved type detected, which should have been done with the help of "
                "`typing.get_type_hints` method by default"
            )

        aliases = kwargs.pop("aliases", [])
        if isinstance(aliases, str):
            aliases = [aliases]

        origin_type = getattr(field.type, "__origin__", field.type)
        if origin_type is Union:
            if str not in field.type.__args__ and (len(field.type.__args__) != 2 or type(None) not in field.type.__args__):
                raise ValueError(
                    "Only `Union[X, NoneType]` (i.e., `Optional[X]`) is allowed for `Union` because"
                    " the argument parser only supports one type per argument."
                    f" Problem encountered in field '{field.name}'."
                )
            if type(None) not in field.type.__args__:
                # filter `str` in Union
                field.type = field.type.__args__[0] if field.type.__args__[1] == str else field.type.__args__[1]
                origin_type = getattr(field.type, "__origin__", field.type)
            elif bool not in field.type.__args__:
                # filter `NoneType` in Union (except for `Union[bool, NoneType]`)
                field.type = field.type.__args__[0] if isinstance(None, field.type.__args__[1]) else field.type.__args__[1]
                origin_type = getattr(field.type, "__origin__", field.type)
        elif field.type.__class__ is UnionType:
            # TODO: remove this hack and replace with native typing solution somehow
            individual_types = [t.strip() for t in str(field.type).split("|")]
            if len(individual_types) != 2 or not issubclass(type(None), field.type):
                raise ValueError(
                    "Only `X | None` (i.e., `Optional[X]`) is allowed for `Union` because"
                    " the argument parser only supports one type per argument (except for Literal / Enums)."
                    f" Problem encountered in field '{field.name}'."
                )
            accept_types = [str, int, float, bool]

            for t in accept_types:
                if issubclass(t, field.type):
                    field.type = t
                    origin_type = getattr(field.type, "__origin__", field.type)
                    break

        # A variable to store kwargs for a boolean field, if needed
        # so that we can init a `no_*` complement argument (see below)
        bool_kwargs = {}
        if origin_type is Literal or (isinstance(field.type, type) and issubclass(field.type, Enum)):
            if origin_type is Literal:
                kwargs["choices"] = field.type.__args__
            else:
                kwargs["choices"] = [x.value for x in field.type]

            kwargs["type"] = make_choice_type_function(kwargs["choices"])
            type_str = str(set(kwargs["choices"]))

            if field.default is not dataclasses.MISSING:
                kwargs["default"] = field.default
            else:
                kwargs["required"] = True
        elif field.type is bool or field.type == Optional[bool]:
            # Copy the currect kwargs to use to instantiate a `no_*` complement argument below.
            # We do not initialize it here because the `no_*` alternative must be instantiated after the real argument
            bool_kwargs = copy(kwargs)

            # Hack because type=bool in argparse does not behave as we want.
            kwargs["type"] = string_to_bool

            type_str = "BOOL"
            if field.type is bool or (field.default is not None and field.default is not dataclasses.MISSING):
                # Default value is False if we have no default when of type bool.
                default = False if field.default is dataclasses.MISSING else field.default
                # This is the value that will get picked if we don't include --field_name in any way
                kwargs["default"] = default
                # This tells argparse we accept 0 or 1 value after --field_name
                kwargs["nargs"] = "?"
                # This is the value that will get picked if we do --field_name (without value)
                kwargs["const"] = True
        elif isclass(origin_type) and issubclass(origin_type, list):
            kwargs["type"] = field.type.__args__[0]
            type_str = kwargs["type"].__name__.upper()

            kwargs["nargs"] = "+"
            if field.default_factory is not dataclasses.MISSING:
                kwargs["default"] = field.default_factory()
            elif field.default is dataclasses.MISSING:
                kwargs["required"] = True

            # Support nested Choice/Literal in list
            if getattr(kwargs["type"], "__origin__", kwargs["type"]) is Literal:
                kwargs["choices"] = kwargs["type"].__args__
                kwargs["type"] = make_choice_type_function(kwargs["choices"])
                type_str = str(set(kwargs["choices"]))

        else:
            kwargs["type"] = field.type
            if field.default is not dataclasses.MISSING:
                kwargs["default"] = field.default
            elif field.default_factory is not dataclasses.MISSING:
                kwargs["default"] = field.default_factory()
            else:
                kwargs["required"] = True
            type_str = field.type.__name__.upper()

        parser.add_argument(field_name, *aliases, **kwargs, metavar=type_str)

        # Add a complement `no_*` argument for a boolean field AFTER the initial field has already been added.
        # Order is important for arguments with the same destination!
        # We use a copy of earlier kwargs because the original kwargs have changed a lot before reaching down
        # here and we do not need those changes/additional keys.
        if field.default is True and (field.type is bool or field.type == Optional[bool]):
            bool_kwargs["default"] = False
            parser.add_argument(f"--no_{field.name}", action="store_false", dest=field.name, **bool_kwargs)

    def _add_dataclass_arguments(self, dtype: DataClassType):
        if hasattr(dtype, "_argument_group_name"):
            parser = self.add_argument_group(dtype._argument_group_name)
        else:
            parser = self

        try:
            type_hints: Dict[str, type] = get_type_hints(dtype)
        except NameError:
            raise RuntimeError(
                f"Type resolution failed for f{dtype}. Try declaring the class in global scope or "
                "removing line of `from __future__ import annotations` which opts in Postponed "
                "Evaluation of Annotations (PEP 563)"
            )

        for field in dataclasses.fields(dtype):
            if not field.init:
                continue
            type_str = field.type
            field.type = type_hints[field.name]
            self._parse_dataclass_field(parser, field, type_str)

    def parse_args_into_dataclasses(
        self,
        args=None,
        return_remaining_strings=False,
        look_for_args_file=False,
        args_filename=None,
        args_file_flag=None,
    ) -> Tuple[DataClass, ...]:
        """
        Parse command-line args into instances of the specified dataclass types.

        This relies on argparse's `ArgumentParser.parse_known_args`. See the doc at:
        docs.python.org/3.7/library/argparse.html#argparse.ArgumentParser.parse_args

        Args:
            args:
                List of strings to parse. The default is taken from sys.argv. (same as argparse.ArgumentParser)
            return_remaining_strings:
                If true, also return a list of remaining argument strings.
            look_for_args_file:
                If true, will look for a ".args" file with the same base name as the entry point script for this
                process, and will append its potential content to the command line args.
            args_filename:
                If not None, will uses this file instead of the ".args" file specified in the previous argument.
            args_file_flag:
                If not None, will look for a file in the command-line args specified with this flag. The flag can be
                specified multiple times and precedence is determined by the order (last one wins).

        Returns:
            Tuple consisting of:

                - the dataclass instances in the same order as they were passed to the initializer.abspath
                - if applicable, an additional namespace for more (non-dataclass backed) arguments added to the parser
                  after initialization.
                - The potential list of remaining argument strings. (same as argparse.ArgumentParser.parse_known_args)
        """

        if args_file_flag or args_filename or (look_for_args_file and len(sys.argv)):
            args_files = []

            if args_filename:
                args_files.append(Path(args_filename))
            elif look_for_args_file and len(sys.argv):
                args_files.append(Path(sys.argv[0]).with_suffix(".args"))

            # args files specified via command line flag should overwrite default args files so we add them last
            if args_file_flag:
                # Create special parser just to extract the args_file_flag values
                args_file_parser = ArgumentParser(add_help=False)
                args_file_parser.add_argument(args_file_flag, type=str, action="append")

                # Use only remaining args for further parsing (remove the args_file_flag)
                cfg, args = args_file_parser.parse_known_args(args=args)
                cmd_args_file_paths = vars(cfg).get(args_file_flag.lstrip("-"), None)

                if cmd_args_file_paths:
                    args_files.extend([Path(p) for p in cmd_args_file_paths])

            file_args = []
            for args_file in args_files:
                if args_file.exists():
                    file_args += args_file.read_text().split()
                else:
                    print(f"dargparser | Warning: args file {args_file} does not exist. Ignoring it.")

            # in case of duplicate arguments the last one has precedence
            # args specified via the command line should overwrite args from files, so we add them last
            args = file_args + args if args is not None else file_args + sys.argv[1:]
        namespace, remaining_args = self.parse_known_args(args=args)
        outputs = []
        for dtype in self.dataclass_types:
            keys = {f.name for f in dataclasses.fields(dtype) if f.init}
            inputs = {k: v for k, v in vars(namespace).items() if k in keys}
            for k in keys:
                delattr(namespace, k)
            obj = dtype(**inputs)
            outputs.append(obj)
        if len(namespace.__dict__) > 0:
            # additional namespace.
            outputs.append(namespace)
        if return_remaining_strings:
            return (*outputs, remaining_args)
        else:
            if remaining_args:
                raise ValueError(f"Some specified arguments are not used by dargparse: {remaining_args}")

            return (*outputs,)
