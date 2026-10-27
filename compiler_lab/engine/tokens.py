"""
CodeCraft Compiler Engine - Token Definitions
Defines Token types, categories, and Token representation for the Edu-C language subset.
"""

from enum import Enum
from typing import Any, Optional


class TokenType(str, Enum):
    # Keywords
    KEYWORD = "KEYWORD"
    
    # Identifiers & Literals
    IDENTIFIER = "IDENTIFIER"
    INT_LITERAL = "INT_LITERAL"
    FLOAT_LITERAL = "FLOAT_LITERAL"
    STRING_LITERAL = "STRING_LITERAL"
    CHAR_LITERAL = "CHAR_LITERAL"
    BOOL_LITERAL = "BOOL_LITERAL"

    # Operators
    OP_ARITHMETIC = "OP_ARITHMETIC"      # +, -, *, /, %
    OP_RELATIONAL = "OP_RELATIONAL"      # ==, !=, <, <=, >, >=
    OP_LOGICAL = "OP_LOGICAL"            # &&, ||, !
    OP_ASSIGNMENT = "OP_ASSIGNMENT"      # =, +=, -=, *=, /=
    OP_INCREMENT = "OP_INCREMENT"        # ++, --

    # Delimiters and Separators
    SEPARATOR = "SEPARATOR"              # ;, ,, (, ), {, }, [, ]

    # Comments & Special
    COMMENT = "COMMENT"
    INVALID = "INVALID"
    EOF = "EOF"


KEYWORDS = {
    "int", "float", "char", "string", "bool", "void",
    "if", "else", "while", "for", "return",
    "true", "false", "const", "break", "continue"
}

TYPE_KEYWORDS = {"int", "float", "char", "string", "bool", "void"}

ARITHMETIC_OPS = {"+", "-", "*", "/", "%"}
RELATIONAL_OPS = {"==", "!=", "<", "<=", ">", ">="}
LOGICAL_OPS = {"&&", "||", "!"}
ASSIGNMENT_OPS = {"=", "+=", "-=", "*=", "/="}
INCREMENT_OPS = {"++", "--"}
SEPARATORS = {";", ",", "(", ")", "{", "}", "[", "]"}


class Token:
    """Represents a lexical token produced by the CodeCraft lexer."""
    def __init__(
        self,
        token_type: TokenType,
        lexeme: str,
        value: Any = None,
        line: int = 1,
        column: int = 1,
        index: int = 0,
        description: str = "",
        error_msg: Optional[str] = None
    ):
        self.type = token_type
        self.lexeme = lexeme
        self.value = value if value is not None else lexeme
        self.line = line
        self.column = column
        self.index = index
        self.error_msg = error_msg
        self.description = description or self._default_description()

    def _default_description(self) -> str:
        if self.type == TokenType.KEYWORD:
            return f"Reserved keyword '{self.lexeme}'"
        if self.type == TokenType.IDENTIFIER:
            return f"User-defined identifier '{self.lexeme}'"
        if self.type == TokenType.INT_LITERAL:
            return f"Integer constant ({self.value})"
        if self.type == TokenType.FLOAT_LITERAL:
            return f"Floating-point constant ({self.value})"
        if self.type == TokenType.STRING_LITERAL:
            return "String literal"
        if self.type == TokenType.CHAR_LITERAL:
            return f"Character literal '{self.value}'"
        if self.type == TokenType.BOOL_LITERAL:
            return f"Boolean literal ({self.value})"
        if self.type == TokenType.OP_ARITHMETIC:
            return f"Arithmetic operator '{self.lexeme}'"
        if self.type == TokenType.OP_RELATIONAL:
            return f"Relational operator '{self.lexeme}'"
        if self.type == TokenType.OP_LOGICAL:
            return f"Logical operator '{self.lexeme}'"
        if self.type == TokenType.OP_ASSIGNMENT:
            return f"Assignment operator '{self.lexeme}'"
        if self.type == TokenType.OP_INCREMENT:
            return f"Increment/Decrement operator '{self.lexeme}'"
        if self.type == TokenType.SEPARATOR:
            sep_names = {
                ';': 'Semicolon (statement terminator)',
                ',': 'Comma separator',
                '(': 'Left parenthesis',
                ')': 'Right parenthesis',
                '{': 'Left brace (block start)',
                '}': 'Right brace (block end)',
                '[': 'Left bracket',
                ']': 'Right bracket'
            }
            return sep_names.get(self.lexeme, f"Punctuation separator '{self.lexeme}'")
        if self.type == TokenType.COMMENT:
            return "Source code comment"
        if self.type == TokenType.INVALID:
            return f"Lexical error: {self.error_msg or 'Unrecognized symbol'}"
        if self.type == TokenType.EOF:
            return "End of file marker"
        return str(self.type.value)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "type": self.type.value,
            "lexeme": self.lexeme,
            "value": str(self.value),
            "line": self.line,
            "column": self.column,
            "description": self.description,
            "error_msg": self.error_msg
        }

    def __repr__(self) -> str:
        return f"Token({self.type.name}, '{self.lexeme}', line={self.line}, col={self.column})"
