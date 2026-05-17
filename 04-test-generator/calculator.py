def add(a: int, b: int) -> int:
    """Складывает два числа."""
    return a + b

def divide(a: float, b: float) -> float:
    """Делит a на b."""
    if b == 0:
        raise ValueError("Division by zero")
    return a / b