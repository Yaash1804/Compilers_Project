import re

KEYWORDS = {"int", "float", "if", "else", "while", "return", "for", "char", "double", "void", "main"}
OPERATORS = {"+", "-", "*", "/", "=", "==", "!=", "<", ">", "<=", ">=", "&&", "||", "!", "++", "--"}
DELIMITERS = {";", ",", "(", ")", "{", "}", "[", "]"}
NUMBER_PATTERN = r'\b\d+(\.\d+)?\b'
IDENTIFIER_PATTERN = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
STRING_PATTERN = r'"[^"]*"'

def tokenize(code):
    tokens = []
    
    # Escape special characters in OPERATORS and DELIMITERS
    operator_delimiter_pattern = "|".join(map(re.escape, OPERATORS | DELIMITERS))

    # Full regex pattern
    token_patterns = f'({NUMBER_PATTERN})|({STRING_PATTERN})|({IDENTIFIER_PATTERN})|({operator_delimiter_pattern})'
    
    matches = re.finditer(token_patterns, code)

    for match in matches:
        token = match.group()
        if token in KEYWORDS:
            tokens.append({"type": "KEYWORD", "value": token})
        elif token in OPERATORS:
            tokens.append({"type": "OPERATOR", "value": token})
        elif token in DELIMITERS:
            tokens.append({"type": "DELIMITER", "value": token})
        elif re.fullmatch(NUMBER_PATTERN, token):
            tokens.append({"type": "NUMBER", "value": token})
        elif re.fullmatch(STRING_PATTERN, token):
            tokens.append({"type": "STRING", "value": token})
        elif re.fullmatch(IDENTIFIER_PATTERN, token):
            tokens.append({"type": "IDENTIFIER", "value": token})
        else:
            tokens.append({"type": "UNKNOWN", "value": token})

    return tokens