"""
CodeCraft Compiler Engine - Recursive-Descent Syntax Analyzer (Parser)
Parses token streams into Abstract Syntax Trees based on the documented Edu-C grammar.
Provides error recovery and syntax diagnostics.
"""

from typing import List, Optional, Dict, Any
from .tokens import Token, TokenType, TYPE_KEYWORDS
from .ast_nodes import (
    ASTNode,
    ProgramNode,
    VarDeclNode,
    AssignmentNode,
    BinaryOpNode,
    UnaryOpNode,
    LiteralNode,
    IdentifierNode,
    IfNode,
    WhileNode,
    BlockNode,
    ReturnNode,
    ExpressionStatementNode
)


class ParserError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(message)
        self.message = message
        self.token = token
        self.line = token.line
        self.column = token.column


class ParserResult:
    """Holds the syntax analysis outcome."""
    def __init__(
        self,
        ast: Optional[ProgramNode],
        errors: List[Dict[str, Any]],
        mermaid_graph: str = "",
        text_tree: str = ""
    ):
        self.ast = ast
        self.errors = errors
        self.mermaid_graph = mermaid_graph
        self.text_tree = text_tree

    @property
    def is_success(self) -> bool:
        return len(self.errors) == 0 and self.ast is not None

    def to_dict(self) -> dict:
        return {
            "ast": self.ast.to_dict() if self.ast else None,
            "errors": self.errors,
            "mermaid_graph": self.mermaid_graph,
            "text_tree": self.text_tree,
            "is_success": self.is_success
        }


class Parser:
    """
    Predictive Recursive-Descent Parser for Edu-C grammar.
    """
    def __init__(self, tokens: List[Token]):
        # Filter out comments and invalid tokens for parsing, but keep note of lexical errors
        self.tokens = [t for t in tokens if t.type != TokenType.COMMENT]
        self.pos = 0
        self.errors: List[Dict[str, Any]] = []

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1] if self.tokens else Token(TokenType.EOF, "", line=1, column=1)

    def _peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1] if self.tokens else Token(TokenType.EOF, "", line=1, column=1)

    def _advance(self) -> Token:
        tok = self._current()
        if self.pos < len(self.tokens):
            self.pos += 1
        return tok

    def _match(self, token_type: TokenType, lexeme: Optional[str] = None) -> bool:
        curr = self._current()
        if curr.type == token_type:
            if lexeme is None or curr.lexeme == lexeme:
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, lexeme: Optional[str] = None, err_msg: str = "") -> Token:
        curr = self._current()
        if curr.type == token_type and (lexeme is None or curr.lexeme == lexeme):
            return self._advance()

        msg = err_msg or f"Expected {lexeme or token_type.value}, but found '{curr.lexeme}'"
        raise ParserError(msg, curr)

    def _synchronize(self):
        """Discards tokens until a statement boundary (semicolon or closing brace) is reached."""
        self._advance()
        while self._current().type != TokenType.EOF:
            if self._current().lexeme == ';':
                self._advance()
                return
            if self._current().lexeme in ('}', '{', 'if', 'while', 'return'):
                return
            self._advance()

    def parse(self) -> ParserResult:
        statements: List[ASTNode] = []

        if not self.tokens or (len(self.tokens) == 1 and self.tokens[0].type == TokenType.EOF):
            return ParserResult(
                ast=ProgramNode([], 1, 1),
                errors=[],
                mermaid_graph="graph TD\n    n1[\"Empty Program\"]",
                text_tree="Program (empty)"
            )

        while self._current().type != TokenType.EOF:
            try:
                stmt = self._parse_statement()
                if stmt:
                    statements.append(stmt)
            except ParserError as e:
                self.errors.append({
                    "line": e.line,
                    "column": e.column,
                    "message": e.message,
                    "token": e.token.lexeme
                })
                self._synchronize()

        ast = ProgramNode(statements, 1, 1) if not self.errors else None
        mermaid = ast.to_mermaid() if ast else ""
        text_tree = ast.to_text_tree() if ast else ""

        return ParserResult(
            ast=ast,
            errors=self.errors,
            mermaid_graph=mermaid,
            text_tree=text_tree
        )

    # ---------------- Grammar Rules ----------------

    def _parse_statement(self) -> Optional[ASTNode]:
        curr = self._current()

        # Empty statement
        if curr.lexeme == ';':
            self._advance()
            return None

        # Block statement
        if curr.lexeme == '{':
            return self._parse_block()

        # Variable declaration: starts with type keyword (int, float, char, string, bool)
        if curr.type == TokenType.KEYWORD and curr.lexeme in TYPE_KEYWORDS:
            return self._parse_var_decl()

        # If statement
        if curr.type == TokenType.KEYWORD and curr.lexeme == 'if':
            return self._parse_if_stmt()

        # While statement
        if curr.type == TokenType.KEYWORD and curr.lexeme == 'while':
            return self._parse_while_stmt()

        # Return statement
        if curr.type == TokenType.KEYWORD and curr.lexeme == 'return':
            return self._parse_return_stmt()

        # Assignment statement: identifier followed by assignment operator
        if curr.type == TokenType.IDENTIFIER and self._peek().type == TokenType.OP_ASSIGNMENT:
            return self._parse_assignment()

        # Expression statement (e.g. function call or standalone expression)
        expr = self._parse_expression()
        self._consume(TokenType.SEPARATOR, ';', f"Missing semicolon ';' after expression at line {curr.line}")
        return ExpressionStatementNode(expr, curr.line, curr.column)

    def _parse_block(self) -> BlockNode:
        brace = self._consume(TokenType.SEPARATOR, '{', "Expected '{' to start block")
        statements: List[ASTNode] = []

        while self._current().type != TokenType.EOF and self._current().lexeme != '}':
            try:
                stmt = self._parse_statement()
                if stmt:
                    statements.append(stmt)
            except ParserError as e:
                self.errors.append({
                    "line": e.line,
                    "column": e.column,
                    "message": e.message,
                    "token": e.token.lexeme
                })
                self._synchronize()

        self._consume(TokenType.SEPARATOR, '}', "Expected '}' to close block")
        return BlockNode(statements, brace.line, brace.column)

    def _parse_var_decl(self) -> VarDeclNode:
        type_tok = self._advance()  # int, float, etc.
        id_tok = self._consume(TokenType.IDENTIFIER, None, f"Expected variable name after '{type_tok.lexeme}'")

        init_expr = None
        if self._match(TokenType.OP_ASSIGNMENT, '='):
            init_expr = self._parse_expression()

        self._consume(TokenType.SEPARATOR, ';', f"Expected ';' after variable declaration of '{id_tok.lexeme}'")
        return VarDeclNode(type_tok.lexeme, id_tok.lexeme, init_expr, type_tok.line, type_tok.column)

    def _parse_assignment(self) -> AssignmentNode:
        id_tok = self._consume(TokenType.IDENTIFIER, None, "Expected identifier in assignment")
        op_tok = self._consume(TokenType.OP_ASSIGNMENT, None, "Expected assignment operator (=, +=, etc.)")
        expr = self._parse_expression()
        self._consume(TokenType.SEPARATOR, ';', f"Expected ';' after assignment to '{id_tok.lexeme}'")
        return AssignmentNode(id_tok.lexeme, op_tok.lexeme, expr, id_tok.line, id_tok.column)

    def _parse_if_stmt(self) -> IfNode:
        if_tok = self._consume(TokenType.KEYWORD, 'if', "Expected 'if'")
        self._consume(TokenType.SEPARATOR, '(', "Expected '(' after 'if'")
        condition = self._parse_expression()
        self._consume(TokenType.SEPARATOR, ')', "Expected ')' after if condition")

        then_branch = self._parse_statement()
        else_branch = None
        if self._match(TokenType.KEYWORD, 'else'):
            else_branch = self._parse_statement()

        return IfNode(condition, then_branch, else_branch, if_tok.line, if_tok.column)

    def _parse_while_stmt(self) -> WhileNode:
        while_tok = self._consume(TokenType.KEYWORD, 'while', "Expected 'while'")
        self._consume(TokenType.SEPARATOR, '(', "Expected '(' after 'while'")
        condition = self._parse_expression()
        self._consume(TokenType.SEPARATOR, ')', "Expected ')' after while condition")
        body = self._parse_statement()
        return WhileNode(condition, body, while_tok.line, while_tok.column)

    def _parse_return_stmt(self) -> ReturnNode:
        ret_tok = self._consume(TokenType.KEYWORD, 'return', "Expected 'return'")
        expr = None
        if self._current().lexeme != ';':
            expr = self._parse_expression()
        self._consume(TokenType.SEPARATOR, ';', "Expected ';' after return statement")
        return ReturnNode(expr, ret_tok.line, ret_tok.column)

    # ---------------- Expression Rules (Precedence Hierarchy) ----------------

    def _parse_expression(self) -> ASTNode:
        return self._parse_logical_or()

    def _parse_logical_or(self) -> ASTNode:
        expr = self._parse_logical_and()
        while self._match(TokenType.OP_LOGICAL, '||'):
            op = '||'
            right = self._parse_logical_and()
            expr = BinaryOpNode(expr, op, right, expr.line, expr.column)
        return expr

    def _parse_logical_and(self) -> ASTNode:
        expr = self._parse_equality()
        while self._match(TokenType.OP_LOGICAL, '&&'):
            op = '&&'
            right = self._parse_equality()
            expr = BinaryOpNode(expr, op, right, expr.line, expr.column)
        return expr

    def _parse_equality(self) -> ASTNode:
        expr = self._parse_relational()
        while self._current().type == TokenType.OP_RELATIONAL and self._current().lexeme in ('==', '!='):
            op_tok = self._advance()
            right = self._parse_relational()
            expr = BinaryOpNode(expr, op_tok.lexeme, right, expr.line, expr.column)
        return expr

    def _parse_relational(self) -> ASTNode:
        expr = self._parse_additive()
        while self._current().type == TokenType.OP_RELATIONAL and self._current().lexeme in ('<', '<=', '>', '>='):
            op_tok = self._advance()
            right = self._parse_additive()
            expr = BinaryOpNode(expr, op_tok.lexeme, right, expr.line, expr.column)
        return expr

    def _parse_additive(self) -> ASTNode:
        expr = self._parse_multiplicative()
        while self._current().type == TokenType.OP_ARITHMETIC and self._current().lexeme in ('+', '-'):
            op_tok = self._advance()
            right = self._parse_multiplicative()
            expr = BinaryOpNode(expr, op_tok.lexeme, right, expr.line, expr.column)
        return expr

    def _parse_multiplicative(self) -> ASTNode:
        expr = self._parse_unary()
        while self._current().type == TokenType.OP_ARITHMETIC and self._current().lexeme in ('*', '/', '%'):
            op_tok = self._advance()
            right = self._parse_unary()
            expr = BinaryOpNode(expr, op_tok.lexeme, right, expr.line, expr.column)
        return expr

    def _parse_unary(self) -> ASTNode:
        curr = self._current()
        if (curr.type == TokenType.OP_LOGICAL and curr.lexeme == '!') or \
           (curr.type == TokenType.OP_ARITHMETIC and curr.lexeme in ('-', '+')):
            op_tok = self._advance()
            operand = self._parse_unary()
            return UnaryOpNode(op_tok.lexeme, operand, op_tok.line, op_tok.column)
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        curr = self._current()

        # Parenthesized expression
        if self._match(TokenType.SEPARATOR, '('):
            expr = self._parse_expression()
            self._consume(TokenType.SEPARATOR, ')', "Expected ')' after grouped expression")
            return expr

        # Integer constant
        if curr.type == TokenType.INT_LITERAL:
            self._advance()
            return LiteralNode("int", curr.value, curr.lexeme, curr.line, curr.column)

        # Float constant
        if curr.type == TokenType.FLOAT_LITERAL:
            self._advance()
            return LiteralNode("float", curr.value, curr.lexeme, curr.line, curr.column)

        # String constant
        if curr.type == TokenType.STRING_LITERAL:
            self._advance()
            return LiteralNode("string", curr.value, curr.lexeme, curr.line, curr.column)

        # Character constant
        if curr.type == TokenType.CHAR_LITERAL:
            self._advance()
            return LiteralNode("char", curr.value, curr.lexeme, curr.line, curr.column)

        # Boolean constant
        if curr.type == TokenType.BOOL_LITERAL:
            self._advance()
            return LiteralNode("bool", curr.value, curr.lexeme, curr.line, curr.column)

        # Identifier
        if curr.type == TokenType.IDENTIFIER:
            self._advance()
            return IdentifierNode(curr.lexeme, curr.line, curr.column)

        raise ParserError(f"Unexpected token '{curr.lexeme}' in expression", curr)
