import sys
from importlib.metadata import version
from dataclasses import dataclass
from dargparser import dargparse, dArg


@dataclass
class Args:
    version: bool = dArg(
        default=False,
        help="Print version and exit.",
        aliases=["-v"],
    )

def entry_point():
    args = dargparse(dataclasses=Args)
    if args.version:
        print(version("dargparser"))
        sys.exit()