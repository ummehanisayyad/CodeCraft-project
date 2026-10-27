"""
CodeCraft Compiler Engine - Lexical Analyzer (Tokenizer)
Performs lexical analysis on C-subset source code, categorizing tokens,
tracking line/column positions, and detecting lexical errors.
"""

from typing import List, Dict, Any, Optional
from .tokens import (
    Token,
    TokenType,
    KEYWORDS,
    TYPE_KEYWORDS,
    ARITHMETIC_OPS,
    RELATIONAL_OPS,
    LOGICAL_OPS,
    ASSIGNMENT_OPS,
    INCREMENT_OPS,
    SEPARATORS
)


class LexerResult:
    """Encapsulates the complete outcome of lexical analysis."""
    def __init__(
        self,
        tokens: List[Token],
        comments: List[Token],
        errors: List[Dict[str, Any]],
        stats: Dict[str, int],
        source_code: str
    ):
        self.tokens = tokens
        self.comments = comments
        self.errors = errors
        self.stats = stats
        self.source_code = source_code

    @property
    def is_success(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "tokens": [t.to_dict() for t in self.tokens],
            "comments": [c.to_dict() for c in self.comments],
            "errors": self.errors,
            "stats": self.stats,
            "is_success": self.is_success
        }


class Lexer:
    """
    Deterministic Lexical Analyzer for the Edu-C language subset.
    """
    def __init__(self, source_code: str):
        self.source = source_code or ""
        self.length = len(self.source)
        self.pos = 0
        self.line = 1
        self.column = 1
        self.token_counter = 0

        self.tokens: List[Token] = []
        self.comments: List[Token] = []
        self.errors: List[Dict[str, Any]] = []

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return ""

    def _advance(self) -> str:
        if self.pos >= self.length:
            return ""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def tokenize(self) -> LexerResult:
        """Tokenizes the entire source string and returns LexerResult."""
        while self.pos < self.length:
            ch = self._peek()

            # 1. Whitespace
            if ch.isspace():
                self._advance()
                continue

            start_line = self.line
            start_col = self.column

            # 2. Comments or Division
            if ch == '/':
                next_ch = self._peek(1)
                if next_ch == '/':
                    self._lex_single_line_comment(start_line, start_col)
                    continue
                elif next_ch == '*':
                    self._lex_multi_line_comment(start_line, start_col)
                    continue
                elif next_ch == '=':
                    # /= assignment
                    self._advance()
                    self._advance()
                    self._add_token(TokenType.OP_ASSIGNMENT, "/=", "/=", start_line, start_col)
                    continue
                else:
                    self._advance()
                    self._add_token(TokenType.OP_ARITHMETIC, "/", "/", start_line, start_col)
                    continue

            # 3. Numeric Literals
            if ch.isdigit():
                self._lex_number(start_line, start_col)
                continue

            # 4. String Literals
            if ch == '"':
                self._lex_string(start_line, start_col)
                continue

            # 5. Character Literals
            if ch == "'":
                self._lex_char(start_line, start_col)
                continue

            # 6. Identifiers and Keywords
            if ch.isalpha() or ch == '_':
                self._lex_identifier(start_line, start_col)
                continue

            # 7. Multi-character and Single-character Operators
            if self._lex_operator_or_separator(start_line, start_col):
                continue

            # 8. Unrecognized / Invalid Character
            bad_ch = self._advance()
            err_msg = f"Unrecognized character '{bad_ch}' (ASCII {ord(bad_ch)})"
            self.errors.append({
                "line": start_line,
                "column": start_col,
                "message": err_msg,
                "character": bad_ch
            })
            self._add_token(TokenType.INVALID, bad_ch, bad_ch, start_line, start_col, error_msg=err_msg)

        # Append EOF token
        self._add_token(TokenType.EOF, "", "", self.line, self.column)

        stats = self._compute_stats()
        return LexerResult(self.tokens, self.comments, self.errors, stats, self.source)

    def _add_token(
        self,
        token_type: TokenType,
        lexeme: str,
        value: Any,
        line: int,
        col: int,
        error_msg: Optional[str] = None
    ) -> Token:
        if token_type != TokenType.COMMENT and token_type != TokenType.EOF:
            self.token_counter += 1
            idx = self.token_counter
        else:
            idx = 0

        tok = Token(
            token_type=token_type,
            lexeme=lexeme,
            value=value,
            line=line,
            column=col,
            index=idx,
            error_msg=error_msg
        )
        if token_type == TokenType.COMMENT:
            self.comments.append(tok)
        else:
            self.tokens.append(tok)
        return tok

    def _lex_single_line_comment(self, start_line: int, start_col: int):
        lexeme = []
        # Consume //
        lexeme.append(self._advance())
        lexeme.append(self._advance())
        while self.pos < self.length and self._peek() != '\n':
            lexeme.append(self._advance())
        full_comment = "".join(lexeme)
        self._add_token(TokenType.COMMENT, full_comment, full_comment.strip(), start_line, start_col)

    def _lex_multi_line_comment(self, start_line: int, start_col: int):
        lexeme = []
        # Consume /*
        lexeme.append(self._advance())
        lexeme.append(self._advance())
        closed = False
        while self.pos < self.length:
            if self._peek() == '*' and self._peek(1) == '/':
                lexeme.append(self._advance())
                lexeme.append(self._advance())
                closed = True
                break
            lexeme.append(self._advance())

        full_comment = "".join(lexeme)
        if not closed:
            err_msg = "Unterminated multi-line comment (expected '*/')"
            self.errors.append({
                "line": start_line,
                "column": start_col,
                "message": err_msg,
                "character": "/*"
            })
            self._add_token(TokenType.INVALID, full_comment, full_comment, start_line, start_col, error_msg=err_msg)
        else:
            self._add_token(TokenType.COMMENT, full_comment, full_comment, start_line, start_col)

    def _lex_number(self, start_line: int, start_col: int):
        lexeme = []
        is_float = False
        has_error = False

        while self.pos < self.length and (self._peek().isdigit() or self._peek() == '.'):
            if self._peek() == '.':
                if is_float:
                    # Multiple decimals in number
                    has_error = True
                is_float = True
            lexeme.append(self._advance())

        num_str = "".join(lexeme)
        if has_error:
            err_msg = f"Malformed floating-point literal '{num_str}'"
            self.errors.append({
                "line": start_line,
                "column": start_col,
                "message": err_msg,
                "character": num_str
            })
            self._add_token(TokenType.INVALID, num_str, num_str, start_line, start_col, error_msg=err_msg)
        elif is_float:
            try:
                val = float(num_str)
                self._add_token(TokenType.FLOAT_LITERAL, num_str, val, start_line, start_col)
            except ValueError:
                err_msg = f"Invalid float value '{num_str}'"
                self.errors.append({"line": start_line, "column": start_col, "message": err_msg})
                self._add_token(TokenType.INVALID, num_str, num_str, start_line, start_col, error_msg=err_msg)
        else:
            try:
                val = int(num_str)
                self._add_token(TokenType.INT_LITERAL, num_str, val, start_line, start_col)
            except ValueError:
                err_msg = f"Invalid integer value '{num_str}'"
                self.errors.append({"line": start_line, "column": start_col, "message": err_msg})
                self._add_token(TokenType.INVALID, num_str, num_str, start_line, start_col, error_msg=err_msg)

    def _lex_string(self, start_line: int, start_col: int):
        self._advance()  # consume opening quote
        chars = []
        closed = False

        while self.pos < self.length:
            ch = self._peek()
            if ch == '"':
                self._advance()
                closed = True
                break
            elif ch == '\n':
                break  # newlines not allowed in single-line strings without escape
            elif ch == '\\':
                self._advance()
                esc = self._advance()
                if esc == 'n':
                    chars.append('\n')
                elif esc == 't':
                    chars.append('\t')
                elif esc == 'r':
                    chars.append('\r')
                elif esc == '"':
                    chars.append('"')
                elif esc == '\\':
                    chars.append('\\')
                else:
                    chars.append(esc)
            else:
                chars.append(self._advance())

        value = "".join(chars)
        raw = f'"{value}"'
        if not closed:
            err_msg = "Unterminated string literal (missing closing quote '\"')"
            self.errors.append({
                "line": start_line,
                "column": start_col,
                "message": err_msg,
                "character": '"'
            })
            self._add_token(TokenType.INVALID, raw, value, start_line, start_col, error_msg=err_msg)
        else:
            self._add_token(TokenType.STRING_LITERAL, raw, value, start_line, start_col)

    def _lex_char(self, start_line: int, start_col: int):
        self._advance()  # consume opening '
        chars = []
        closed = False

        while self.pos < self.length:
            ch = self._peek()
            if ch == "'":
                self._advance()
                closed = True
                break
            elif ch == '\n':
                break
            elif ch == '\\':
                self._advance()
                esc = self._advance()
                if esc == 'n':
                    chars.append('\n')
                elif esc == 't':
                    chars.append('\t')
                elif esc == '0':
                    chars.append('\0')
                elif esc == "'":
                    chars.append("'")
                elif esc == '\\':
                    chars.append('\\')
                else:
                    chars.append(esc)
            else:
                chars.append(self._advance())

        val = "".join(chars)
        raw = f"'{val}'"
        if not closed:
            err_msg = "Unterminated character literal (missing closing quote ''')"
            self.errors.append({"line": start_line, "column": start_col, "message": err_msg})
            self._add_token(TokenType.INVALID, raw, val, start_line, start_col, error_msg=err_msg)
        elif len(val) != 1:
            err_msg = f"Character literal must contain exactly one character, got {len(val)}"
            self.errors.append({"line": start_line, "column": start_col, "message": err_msg})
            self._add_token(TokenType.INVALID, raw, val, start_line, start_col, error_msg=err_msg)
        else:
            self._add_token(TokenType.CHAR_LITERAL, raw, val, start_line, start_col)

    def _lex_identifier(self, start_line: int, start_col: int):
        chars = []
        while self.pos < self.length and (self._peek().isalnum() or self._peek() == '_'):
            chars.append(self._advance())
        name = "".join(chars)

        if name in KEYWORDS:
            if name in ("true", "false"):
                self._add_token(TokenType.BOOL_LITERAL, name, name == "true", start_line, start_col)
            else:
                self._add_token(TokenType.KEYWORD, name, name, start_line, start_col)
        else:
            self._add_token(TokenType.IDENTIFIER, name, name, start_line, start_col)

    def _lex_operator_or_separator(self, start_line: int, start_col: int) -> bool:
        two_chars = self.source[self.pos:self.pos + 2]
        one_char = self._peek()

        # Check two-character operators first
        if two_chars in ("==", "!=", "<=", ">="):
            self._advance()
            self._advance()
            self._add_token(TokenType.OP_RELATIONAL, two_chars, two_chars, start_line, start_col)
            return True
        if two_chars in ("&&", "||"):
            self._advance()
            self._advance()
            self._add_token(TokenType.OP_LOGICAL, two_chars, two_chars, start_line, start_col)
            return True
        if two_chars in ("+=", "-=", "*=", "/="):
            self._advance()
            self._advance()
            self._add_token(TokenType.OP_ASSIGNMENT, two_chars, two_chars, start_line, start_col)
            return True
        if two_chars in ("++", "--"):
            self._advance()
            self._advance()
            self._add_token(TokenType.OP_INCREMENT, two_chars, two_chars, start_line, start_col)
            return True

        # Check single-character separators
        if one_char in SEPARATORS:
            self._advance()
            self._add_token(TokenType.SEPARATOR, one_char, one_char, start_line, start_col)
            return True

        # Check single-character assignment or relational
        if one_char == '=':
            self._advance()
            self._add_token(TokenType.OP_ASSIGNMENT, "=", "=", start_line, start_col)
            return True
        if one_char in ('<', '>'):
            self._advance()
            self._add_token(TokenType.OP_RELATIONAL, one_char, one_char, start_line, start_col)
            return True

        # Check single-character arithmetic
        if one_char in ('+', '-', '*', '%'):
            self._advance()
            self._add_token(TokenType.OP_ARITHMETIC, one_char, one_char, start_line, start_col)
            return True

        # Check logical NOT
        if one_char == '!':
            self._advance()
            self._add_token(TokenType.OP_LOGICAL, "!", "!", start_line, start_col)
            return True

        return False

    def _compute_stats(self) -> Dict[str, int]:
        stats = {
            "total_tokens": self.token_counter,
            "keywords": 0,
            "identifiers": 0,
            "literals": 0,
            "operators": 0,
            "separators": 0,
            "comments": len(self.comments),
            "errors": len(self.errors),
            "lines": max(1, self.line)
        }
        for tok in self.tokens:
            if tok.type == TokenType.KEYWORD:
                stats["keywords"] += 1
            elif tok.type == TokenType.IDENTIFIER:
                stats["identifiers"] += 1
            elif tok.type in (TokenType.INT_LITERAL, TokenType.FLOAT_LITERAL, TokenType.STRING_LITERAL, TokenType.CHAR_LITERAL, TokenType.BOOL_LITERAL):
                stats["literals"] += 1
            elif tok.type in (TokenType.OP_ARITHMETIC, TokenType.OP_RELATIONAL, TokenType.OP_LOGICAL, TokenType.OP_ASSIGNMENT, TokenType.OP_INCREMENT):
                stats["operators"] += 1
            elif tok.type == TokenType.SEPARATOR:
                stats["separators"] += 1
        return stats
