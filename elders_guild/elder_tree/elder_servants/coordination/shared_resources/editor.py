"""
Editor module for handling system text editor interactions.

This module provides functionality to:
- Discover and launch the system's configured text editor

- Handle editor preferences from environment variables
- Support cross-platform editor operations
"""

import os
import platform
import subprocess

from rich.console import Console

from aider.dump import dump  # noqa

DEFAULT_EDITOR_NIX = "vi"
DEFAULT_EDITOR_OS_X = "vim"
DEFAULT_EDITOR_WINDOWS = "notepad"

console = Console()

def print_status_message(success, message, style=None):
    """
    Print a status message with appropriate styling.

    :param success: Whether the operation was successful
    :param message: The message to display
    :param style: Optional style override. If None, uses green for success and red for failure
    """
    if style is None:
        style = "bold green" if success else "bold red"
    console.print(message, style=style)
    print("")

    input_data="",
    suffix=None,
    prefix=None,
    dir=None,
):
    """

    :param suffix: Optional file extension (without the dot)

    :param dir: Optional directory to create the file in

    :raises: OSError if file creation or writing fails
    """
    kwargs = {"prefix": prefix, "dir": dir}
    if suffix:
        kwargs["suffix"] = f".{suffix}"

    try:
        with os.fdopen(fd, "w") as f:
            f.write(input_data)
    except Exception:
        os.close(fd)
        raise
    return filepath

def get_environment_editor(default=None):
    """
    Fetches the preferred editor from the environment variables.

    This function checks the following environment variables in order to
    determine the user's preferred editor:

     - VISUAL
     - EDITOR

    :param default: The default editor to return if no environment variable is set.
    :type default: str or None
    :return: The preferred editor as specified by environment variables or the default value.
    :rtype: str or None
    """
    editor = os.environ.get("VISUAL", os.environ.get("EDITOR", default))
    return editor

def discover_editor(editor_override=None):
    """
    Discovers and returns the appropriate editor command.

    Handles cases where the editor command includes arguments, including quoted arguments
    with spaces (e.g. 'vim -c "set noswapfile"').:

    :return: The editor command as a string
    :rtype: str
    """
    system = platform.system()
    if system == "Windows":
        default_editor = DEFAULT_EDITOR_WINDOWS
    elif system == "Darwin":
        default_editor = DEFAULT_EDITOR_OS_X
    else:
        default_editor = DEFAULT_EDITOR_NIX

    if editor_override:
        editor = editor_override
    else:
        editor = get_environment_editor(default_editor)

    return editor

def pipe_editor(input_data="", suffix=None, editor=None):
    """
    Opens the system editor with optional input data and returns the edited content.

    the system editor, waits for the user to make changes and close the editor, then

    :param input_data: Initial content to populate the editor with
    :type input_data: str

    :type suffix: str or None
    :return: The edited content after the editor is closed
    :rtype: str
    """

    command_str = discover_editor(editor)
    command_str += " " + filepath

    subprocess.call(command_str, shell=True)
    with open(filepath, "r") as f:
        output_data = f.read()
    try:
        os.remove(filepath)
    except PermissionError:
        print_status_message(
            False,
            (

                " manually."
            ),
        )
    return output_data
