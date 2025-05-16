import re
import sys

# === Exception Classes for Error Handling ===

# Base exception for all SNOL-related issues
class SNOLException(Exception): pass

# Raised when command syntax is incorrect
class SNOLSyntaxError(SNOLException): pass

# Raised when the command structure is unknown or unrecognized
class SNOLUnknownCommandError(SNOLException): pass

# Raised when a variable name is invalid or uses a keyword
class SNOLInvalidVariableError(SNOLException): pass

# === Variable Storage ===

variable_store = {}  # Simulates memory for variables

# === Tokenization Patterns ===

# Define individual token types using regex
TOKEN_PATTERNS = {
    "KEYWORD": r"\bBEG\b|\bPRINT\b|EXIT!", # Reserved SNOL commands
    "IDENT": r"[a-zA-Z][a-zA-Z0-9]*",     # Valid variable name (starts with letter followed by letters/digits)
    "NUMBER": r"-?\d+(\.\d+)?",           # Integer or floating-point literals
    "OPERATOR": r"[\+\-\*/%]",            # Arithmetic operators
    "ASSIGN": r"=",                       # Assignment operator
    "WHITESPACE": r"\s+",                # To be ignored
    "UNKNOWN": r"."                      # Catch-all for unrecognized tokens
}

# Compile the final regex for all token types
TOKEN_REGEX = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_PATTERNS.items()))


# === Token Representation ===

# Class representing a lexical token
class Token:
    def __init__(self, kind, value):
        self.kind = kind  # e.g., IDENT, OPERATOR
        self.value = value

    def __repr__(self):
        return f"Token({self.kind}, {self.value})"


# === Lexer: Converts raw input string into a list of Tokens ===

def tokenize(line):
    tokens = []
    for match in TOKEN_REGEX.finditer(line):
        kind = match.lastgroup
        value = match.group()

        if kind == "WHITESPACE":
            continue  # Ignore spaces
        if kind == "UNKNOWN":
            raise SNOLUnknownCommandError()  # Any unknown token breaks the command

        tokens.append(Token(kind, value))
    return tokens


# === Command Classes: One per supported command ===

# Base Command class (abstract)
class Command:
    def execute(self):
        raise NotImplementedError()


# BEG command - asks user input and passes it to Task 2
class BegCommand(Command):
    def __init__(self, var):
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9]*", var):
            raise SNOLInvalidVariableError(var)
        self.var = var

    def execute(self):
        print(f"SNOL> Please enter value for [{self.var}]")
        value = input("Input: ").strip()
        task2_beg_variable(self.var, value)


# PRINT command - passes variable or literal to Task 2
class PrintCommand(Command):
    def __init__(self, operand):
        self.operand = operand

    def execute(self):
        task2_print_variable(self.operand)


# Assignment command - var = expression
class AssignCommand(Command):
    def __init__(self, var, expr):
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9]*", var):
            raise SNOLInvalidVariableError(var)
        self.var = var
        self.expr = expr

    def execute(self):
        task2_assign_variable(self.var, self.expr)


# Arithmetic expression or single variable/literal
class ExprCommand(Command):
    def __init__(self, expr):
        self.expr = expr

    def execute(self):
        task2_eval_expression(self.expr)

class ExitCommand(Command):
    def execute(self):
        print("Interpreter is now terminated...")
        sys.exit(0)
        
# === Parser: Interprets list of tokens and creates a Command object ===

def parse(tokens):
    if not tokens:
        raise SNOLUnknownCommandError()

    # Handle keyword-based commands
    if tokens[0].kind == "KEYWORD":
        keyword = tokens[0].value

        if keyword == "EXIT!":
            if len(tokens) != 1:  # EXIT! must be the only token
                raise SNOLSyntaxError("EXIT! must be used alone")
            return ExitCommand()  # Return a proper command object

        if keyword == "BEG":
            if len(tokens) != 2 or tokens[1].kind != "IDENT":
                raise SNOLSyntaxError()
            return BegCommand(tokens[1].value)

        if keyword == "PRINT":
            if len(tokens) != 2:
                raise SNOLSyntaxError()
            return PrintCommand(tokens[1].value)

    # Reject commands that start with an operator
    if tokens[0].kind == "OPERATOR":
        raise SNOLUnknownCommandError()

    # Reject any command that contains a keyword in an invalid position
    for t in tokens[1:]:
        if t.kind == "KEYWORD":
            raise SNOLUnknownCommandError()
    # Handle assignment: var = expr
    if "=" in [t.value for t in tokens]:
        try:
            idx = next(i for i, t in enumerate(tokens) if t.value == "=")
            var = tokens[:idx]
            expr = tokens[idx+1:]

            if len(var) != 1 or var[0].kind != "IDENT":
                raise SNOLInvalidVariableError(var[0].value if var else "?")

            expr_str = " ".join(t.value for t in expr)
            return AssignCommand(var[0].value, expr_str)
        except Exception:
            raise SNOLSyntaxError()

    # Handle general expression or a single variable
    expr_str = " ".join(t.value for t in tokens)
    return ExprCommand(expr_str)

# === Task 2 Functionalities ===

# Simulate variable storage via BEG
def task2_beg_variable(var, value):
    try:
        if re.fullmatch(r"-?\d+", value):
            parsed_value = int(value)
        elif re.fullmatch(r"-?\d+\.\d+", value):
            parsed_value = float(value)
        else:
            raise SNOLSyntaxError(f"Invalid input for variable [{var}]")
    except Exception:
        raise SNOLSyntaxError(f"Invalid input for variable [{var}]")

    variable_store[var] = parsed_value

# Simulate variable print
def task2_print_variable(operand):
    if operand in variable_store:
        value = variable_store[operand]
        print(f"SNOL> [{operand}] = {value}")
    elif re.fullmatch(r"-?\d+(\.\d+)?", operand):
        print(f"SNOL> [literal] = [{operand}]")
    else:
        raise SNOLSyntaxError(f"Variable [{operand}] not found.")

# Simulate assignment operation
def task2_assign_variable(var, expr):
    try:
        # Replace variables in the expression with their values
        tokens = expr.split()
        evaluated_tokens = []
        for token in tokens:
            if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9]*", token):
                if token not in variable_store:
                    raise SNOLSyntaxError(f"Variable [{token}] not found.")
                evaluated_tokens.append(str(variable_store[token]))
            else:
                evaluated_tokens.append(token)

        final_expr = " ".join(evaluated_tokens)
        result = eval(final_expr)
        variable_store[var] = result
    except Exception:
        raise SNOLSyntaxError("Invalid expression in assignment.")

# Simulate expression evaluation
def task2_eval_expression(expr):
    try:
        tokens = expr.split()
        evaluated_tokens = []
        types = set()
        for token in tokens:
            if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9]*", token):
                if token not in variable_store:
                    print(f"SNOL> Error! [{token}] is not defined!")
                    return
                value = variable_store[token]
                evaluated_tokens.append(str(value))
                types.add(type(value))
            elif re.fullmatch(r"-?\d+\.\d+", token):
                evaluated_tokens.append(token)
                types.add(float)
            elif re.fullmatch(r"-?\d+", token):
                evaluated_tokens.append(token)
                types.add(int)
            else:
                evaluated_tokens.append(token)

        # Check for mixed int and float
        if int in types and float in types:
            print("SNOL> Error! Operands must be of the same type in an\narithmetic operation!")
            return

        final_expr = " ".join(evaluated_tokens)
        result = eval(final_expr)
        
    except Exception:
        raise SNOLSyntaxError("Invalid expression.")




# === Interpreter Main Loop ===

class SNOLInterpreter:
    def __init__(self):
        # Initial instructions
        print("The SNOL environment is now active, you may proceed with giving your commands.")

    def run(self):
        while True:
            try:
                # Read user input line
                line = input("Command: ").strip()
                if not line:
                    continue

                # Check for multiple keywords (e.g., BEG PRINT EXIT! in one line)
                if self.has_multiple_keywords(line):
                    self.print_error("Only one command per line is allowed.")
                    continue

                # Tokenize and parse the input line
                tokens = tokenize(line)
                cmd = parse(tokens)

                # Exit command: terminate immediately
                if isinstance(cmd, ExitCommand):
                    cmd.execute()
                    break

                # Execute the parsed command
                cmd.execute()

            # Handle specific SNOL errors with user-friendly messages
            except SNOLInvalidVariableError as e:
                self.print_error(f"Unknown word [{e}]")
            except SNOLSyntaxError:
                self.print_error("Unknown command! Does not match any valid command of the language.")
            except SNOLUnknownCommandError:
                self.print_error("Unknown command! Does not match any valid command of the language.")
            except Exception as e:
                self.print_error(f"Error! {e}")

    def print_error(self, msg):
        print(f"SNOL> {msg}")

    # Utility to count how many keywords are in a line
    def has_multiple_keywords(self, line):
        return sum(1 for k in {"BEG", "PRINT", "EXIT!"} if k in line) > 1


# === Task 2 Integration Placeholders ===
'''
# Simulate variable storage via BEG
def task2_beg_variable(var, value):
    print(f"[DEBUG: Task 2 stores input: {var} = {value}]")

# Simulate variable print
def task2_print_variable(operand):
    print(f"SNOL> [{operand}] = [placeholder_value]")

# Simulate assignment operation
def task2_assign_variable(var, expr):
    print(f"[DEBUG: Task 2 assigns: {var} = {expr}]")

# Simulate expression evaluation
def task2_eval_expression(expr):
    print(f"[DEBUG: Task 2 evaluates: {expr}]")
'''

# === Entry Point ===
if __name__ == "__main__":
    SNOLInterpreter().run()
