from typing import Any, Callable
from argparse import ArgumentDefaultsHelpFormatter, ArgumentTypeError

# From https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse
def string_to_bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise ArgumentTypeError(
            f"Truthy value expected: got {v} but expected one of yes/no, true/false, t/f, y/n, 1/0 (case insensitive)."
        )


def make_choice_type_function(choices: list) -> Callable[[str], Any]:
    """
    Creates a mapping function from each choices string representation to the actual value. Used to support multiple
    value types for a single argument.

    Args:
        choices (list): List of choices.

    Returns:
        Callable[[str], Any]: Mapping function from string representation to actual value for each choice.
    """
    str_to_choice = {str(choice): choice for choice in choices}
    return lambda arg: str_to_choice.get(arg, arg)


class ArgumentDefaultsLongHelpFormatter(ArgumentDefaultsHelpFormatter):
    def __init__(self, prog) -> None:
        super().__init__(prog, max_help_position=48)

    def _get_help_string(self, action):
        if action.help == None:
            return "(default: %(default)s)"
        return super()._get_help_string(action)
