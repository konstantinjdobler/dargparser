import sys
from dataclasses import dataclass
from importlib.metadata import version

from .parsing import dArg, dargparse


def entry_point():
    @dataclass
    class Args:
        version: bool = dArg(default=False, aliases="-v", help="Print version and exit.")

    args = dargparse(Args)

    if args.version:
        print(version("dargparser"))
        sys.exit()
