def loesung(formel: str, werte: tuple) -> bool:
    """
    Evaluates a logical formula with specified truth values for its variables.

    Args:
        formel (str): A logical formula as a string (e.g., 'a and (b or c)').
        werte (tuple): A tuple of booleans for each variable (e.g., (True, True, False)).

    Returns:
        bool: The result of the evaluated logical formula.
    """
    # Extract all variable names from the formula in sorted order (e.g., 'a', 'b', 'c', ...)
    variablen = sorted(set(char for char in formel if char.isalpha()))

    # Check if the number of values matches the number of variables
    if len(variablen) != len(werte):
        raise ValueError("The number of values does not match the number of variables.")

    # Create a dictionary that maps each variable to its corresponding value
    mapping = {variablen[i]: werte[i] for i in range(len(variablen))}

    # Replace the variables in the formula with their boolean values
    for var, value in mapping.items():
        formel = formel.replace(var, str(value))

    # Evaluate the logical formula using eval()
    try:
        result = eval(formel)
        if not isinstance(result, bool):
            raise ValueError("The formula must evaluate to a boolean value.")
    except Exception as e:
        raise ValueError(f"Error in evaluating the formula: {e}")

    return result


# Example usage:
if __name__ == "__main__":
    # Define a logical formula and the corresponding truth values
    formel = 'a and (b or c)'
    werte = (True, True, False)

    # Call the loesung function and print the result
    try:
        ergebnis = loesung(formel, werte)
        print(f"The result of the formula '{formel}' with values {werte} is: {ergebnis}")
    except ValueError as e:
        print(e)
