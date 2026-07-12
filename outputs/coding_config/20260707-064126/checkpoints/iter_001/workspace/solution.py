"""
SimpleCalculator
A command-line calculator supporting addition, subtraction, multiplication,
and division of two numbers, with input validation and error handling.
"""

# Import the sys module so we can exit the program cleanly.
import sys


def add(a, b):
    """
    Return the sum of two numbers.
    """
    return a + b


def subtract(a, b):
    """
    Return the difference between two numbers.
    """
    return a - b


def multiply(a, b):
    """
    Return the product of two numbers.
    """
    return a * b


def divide(a, b):
    """
    Return the quotient of two numbers.

    Raises:
        ZeroDivisionError: If the divisor (b) is zero.
    """
    if b == 0:
        # Raise an exception instead of returning a string so the caller
        # can decide how to present the error to the user.
        raise ZeroDivisionError("Cannot divide by zero.")
    return a / b


def get_number(prompt):
    """
    Prompt the user for a number and validate the input.

    Continuously asks until a valid numeric value is entered.
    Supports both integers and floating-point numbers.

    Args:
        prompt (str): The message displayed to the user.

    Returns:
        float: The validated numeric input.
    """
    while True:
        # Read input from the user and strip surrounding whitespace.
        user_input = input(prompt).strip()

        # Reject empty input immediately.
        if not user_input:
            print("Input cannot be empty. Please enter a number.")
            continue

        try:
            # Attempt to convert the input to a float.
            return float(user_input)
        except ValueError:
            # If conversion fails, inform the user and ask again.
            print(f"'{user_input}' is not a valid number. Please try again.")


def get_operation():
    """
    Prompt the user to choose an arithmetic operation.

    Continuously asks until a valid operation symbol is entered.

    Returns:
        str: One of '+', '-', '*', '/'.
    """
    # Define the supported operations for validation and display.
    valid_operations = ('+', '-', '*', '/')

    while True:
        # Show the available options to the user.
        op = input("Enter an operation (+, -, *, /): ").strip()

        if op in valid_operations:
            return op

        # If the input is not recognized, explain the valid choices.
        print(f"'{op}' is not a valid operation. Please choose one of {valid_operations}.")


def calculate(num1, num2, operation):
    """
    Perform the requested arithmetic operation on two numbers.

    Args:
        num1 (float): The first operand.
        num2 (float): The second operand.
        operation (str): The operation symbol.

    Returns:
        float: The result of the calculation.

    Raises:
        ZeroDivisionError: If division by zero is requested.
        ValueError: If an unsupported operation is provided.
    """
    # Map operation symbols to their corresponding functions.
    operations = {
        '+': add,
        '-': subtract,
        '*': multiply,
        '/': divide,
    }

    # Look up the function for the requested operation.
    func = operations.get(operation)

    if func is None:
        # Defensive check in case an invalid operation slips through.
        raise ValueError(f"Unsupported operation: {operation}")

    # Execute the selected function and return its result.
    return func(num1, num2)


def run_calculator():
    """
    Run the SimpleCalculator command-line interface.

    Repeatedly prompts the user for input until they choose to quit.
    """
    print("Welcome to SimpleCalculator!")
    print("Supported operations: + (add), - (subtract), * (multiply), / (divide)")
    print("Type 'q' at any prompt to quit.\n")

    while True:
        # --- Get first number ---
        first_input = input("Enter the first number (or 'q' to quit): ").strip()
        if first_input.lower() == 'q':
            break

        # Validate the first number before moving on.
        try:
            num1 = float(first_input)
        except ValueError:
            print(f"'{first_input}' is not a valid number. Please try again.\n")
            continue

        # --- Get second number ---
        second_input = input("Enter the second number (or 'q' to quit): ").strip()
        if second_input.lower() == 'q':
            break

        try:
            num2 = float(second_input)
        except ValueError:
            print(f"'{second_input}' is not a valid number. Please try again.\n")
            continue

        # --- Get operation ---
        op_input = input("Enter an operation (+, -, *, /) (or 'q' to quit): ").strip()
        if op_input.lower() == 'q':
            break

        if op_input not in ('+', '-', '*', '/'):
            print(f"'{op_input}' is not a valid operation. Please try again.\n")
            continue

        # --- Perform calculation and handle errors ---
        try:
            result = calculate(num1, num2, op_input)
            # Display the result, formatting integers without a trailing .0.
            if result == int(result):
                print(f"Result: {int(result)}\n")
            else:
                print(f"Result: {result}\n")
        except ZeroDivisionError as zde:
            # Handle division by zero with a clear, friendly message.
            print(f"Error: {zde}\n")
        except ValueError as ve:
            # Handle any unexpected validation errors.
            print(f"Error: {ve}\n")

    print("Thank you for using SimpleCalculator. Goodbye!")


# Entry point of the program.
if __name__ == "__main__":
    try:
        run_calculator()
    except KeyboardInterrupt:
        # Allow the user to exit with Ctrl+C without showing a traceback.
        print("\nExiting SimpleCalculator. Goodbye!")
        sys.exit(0)