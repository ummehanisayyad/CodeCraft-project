"""
CodeCraft Compiler Engine
Modular compiler pipeline for C-subset language (Edu-C):
- tokens: Token definitions & Token types
- lexer: Lexical analyzer with position tracking and error handling
- ast_nodes: AST node specifications and serialization
- parser: Recursive-descent parser and parse tree generator
- semantic: Symbol table management, scope analysis, and type checking
- codegen: Intermediate Code Generation (Three-Address Code & Quadruples)
- optimizer: Constant folding and algebraic simplification
- pipeline: Compiler pipeline coordinator
"""

from .tokens import TokenType, Token
from .lexer import Lexer, LexerResult
from .parser import Parser, ParserResult
from .semantic import SemanticAnalyzer, SemanticResult, Symbol
from .codegen import CodeGenerator, TACResult, Quadruple
from .optimizer import TACOptimizer
from .pipeline import CompilerPipeline

__all__ = [
    'TokenType',
    'Token',
    'Lexer',
    'LexerResult',
    'Parser',
    'ParserResult',
    'SemanticAnalyzer',
    'SemanticResult',
    'Symbol',
    'CodeGenerator',
    'TACResult',
    'Quadruple',
    'TACOptimizer',
    'CompilerPipeline',
]
