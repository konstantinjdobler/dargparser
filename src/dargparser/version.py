from dataclasses import dataclass
import sys
from importlib.metadata import version
from dataclasses import dataclass
from .parsing import dArg, dargparse


def entry_point():
    @dataclass
    class Args:
        version: bool = dArg(default=False, aliases="-v", help="Print version and exit.")

    args = dargparse(Args)

    if args.version:
        print(version("dargparser"))
        sys.exit()
