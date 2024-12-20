def loesung(formel: str, werte: tuple) -> bool:
    """
    Evaluates a logical formula with given truth values for variables.

    Args:
        formel (str): A logical formula like 'a and (b or c)'
        werte (tuple): Tuple of boolean values corresponding to variables in order of appearance

    Returns:
        bool: Result of evaluating the formula

    Example:
        >>> loesung('a and (b or c)', (True, False, True))
        True
    """
    # Create mapping of variables to their values
    variables = []
    for char in formel:
        if char.isalpha() and char not in variables:
            variables.append(char)
    print(variables)

    if len(variables) != len(werte):
        raise ValueError("Number of variables doesn't match number of values")

    var_dict = dict(zip(variables, werte))

    # Replace variables with their values
    formula_with_values = formel
    for var, value in var_dict.items():
        formula_with_values = formula_with_values.replace(var, str(value))

    # Replace logical operators with Python operators
    formula_with_values = formula_with_values.replace('and', 'and')
    formula_with_values = formula_with_values.replace('or', 'or')
    formula_with_values = formula_with_values.replace('not', 'not')

    # Evaluate the resulting expression
    try:
        return eval(formula_with_values)
    except Exception as e:
        raise ValueError(f"Invalid formula: {e}")

loesung('a and (b or c)', (True, False, True))