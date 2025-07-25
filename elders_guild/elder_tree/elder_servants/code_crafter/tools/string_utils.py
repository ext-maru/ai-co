"""
String utility functions.

This module provides utility functions for string manipulation operations.
All functions follow defensive programming practices with proper error handling.
"""


def reverse_string(input_string):
    """
    Reverse a string.

    This function takes a string as input and returns the string with its
    characters in reverse order. It handles various edge cases and validates
    input types.

    Args:
        input_string (str): The string to reverse.

    Returns:
        str: The reversed string.

    Raises:
        ValueError: If input_string is None.
        TypeError: If input_string is not a string.

    Examples:
        >>> reverse_string("hello")
        'olleh'
        >>> reverse_string("")
        ''
        >>> reverse_string("abc")
        'cba'
    """
    # Handle None input
    if input_string is None:
        raise ValueError("Input cannot be None")
    
    # Handle non-string types
    if not isinstance(input_string, str):
        raise TypeError("Input must be a string")
    
    # Return reversed string using slice notation
    return input_string[::-1]
