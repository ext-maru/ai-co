def add(a: int, b: int) -> int:
    """
    Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b


def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y


class Calculator:
    """Simple calculator class."""

    def __init__(self):
        self.history = []

    def calculate(self, operation: str, a: float, b: float) -> float:
        if operation == "add":
            result = add(int(a), int(b))
        elif operation == "multiply":
            result = multiply(a, b)
        else:
            raise ValueError("Unknown operation")

        self.history.append(f"{operation}({a}, {b}) = {result}")
        return result
