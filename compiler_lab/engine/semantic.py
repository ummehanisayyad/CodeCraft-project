"""
CodeCraft Compiler Engine - Semantic Analysis and Symbol Table
Maintains multi-level lexical scope tables, verifies variable declarations,
performs type compatibility checks, and checks for semantic anomalies.
"""

from typing import Dict, List, Optional, Any
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


class Symbol:
    """Represents an entry in the compiler's Symbol Table."""
    def __init__(
        self,
        name: str,
        var_type: str,
        scope_level: int,
        scope_name: str,
        line: int,
        is_initialized: bool = False,
        kind: str = "variable"
    ):
        self.name = name
        self.var_type = var_type
        self.scope_level = scope_level
        self.scope_name = scope_name
        self.line = line
        self.is_initialized = is_initialized
        self.kind = kind
        self.memory_bytes = self._compute_memory_bytes()

    def _compute_memory_bytes(self) -> int:
        type_sizes = {
            "int": 4,
            "float": 8,
            "char": 1,
            "bool": 1,
            "string": 16,
            "void": 0
        }
        return type_sizes.get(self.var_type, 4)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.var_type,
            "scope_level": self.scope_level,
            "scope_name": self.scope_name,
            "line": self.line,
            "is_initialized": self.is_initialized,
            "kind": self.kind,
            "memory_bytes": self.memory_bytes
        }


class Scope:
    """A single lexical scope frame in the scope hierarchy."""
    def __init__(self, level: int, name: str, parent: Optional['Scope'] = None):
        self.level = level
        self.name = name
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, symbol: Symbol) -> bool:
        """Defines a symbol in the current scope. Returns False if already declared in this scope."""
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None


class SemanticResult:
    """Holds the symbol table, semantic errors, and warnings."""
    def __init__(
        self,
        symbols: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ):
        self.symbols = symbols
        self.errors = errors
        self.warnings = warnings

    @property
    def is_success(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "symbols": self.symbols,
            "errors": self.errors,
            "warnings": self.warnings,
            "is_success": self.is_success
        }


class SemanticAnalyzer:
    """
    Traverses the AST, builds the Symbol Table, and validates language semantics.
    """
    def __init__(self):
        self.global_scope = Scope(0, "global")
        self.current_scope = self.global_scope
        self.scope_counter = 0
        self.all_symbols: List[Symbol] = []
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def _enter_scope(self, scope_name: str) -> Scope:
        self.scope_counter += 1
        new_scope = Scope(
            level=self.current_scope.level + 1,
            name=f"{scope_name}_{self.scope_counter}",
            parent=self.current_scope
        )
        self.current_scope = new_scope
        return new_scope

    def _exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def analyze(self, ast: Optional[ProgramNode]) -> SemanticResult:
        if ast is None:
            return SemanticResult([], [], [])

        self._visit(ast)

        # Serialize symbols
        symbol_list = [s.to_dict() for s in self.all_symbols]
        return SemanticResult(
            symbols=symbol_list,
            errors=self.errors,
            warnings=self.warnings
        )

    def _visit(self, node: ASTNode) -> Optional[str]:
        """Visits an AST node and returns its inferred type string if an expression."""
        if isinstance(node, ProgramNode):
            return self._visit_program(node)
        elif isinstance(node, VarDeclNode):
            return self._visit_var_decl(node)
        elif isinstance(node, AssignmentNode):
            return self._visit_assignment(node)
        elif isinstance(node, BinaryOpNode):
            return self._visit_binary_op(node)
        elif isinstance(node, UnaryOpNode):
            return self._visit_unary_op(node)
        elif isinstance(node, LiteralNode):
            return node.literal_type
        elif isinstance(node, IdentifierNode):
            return self._visit_identifier(node)
        elif isinstance(node, IfNode):
            return self._visit_if(node)
        elif isinstance(node, WhileNode):
            return self._visit_while(node)
        elif isinstance(node, BlockNode):
            return self._visit_block(node)
        elif isinstance(node, ReturnNode):
            return self._visit_return(node)
        elif isinstance(node, ExpressionStatementNode):
            return self._visit(node.expr)
        return None

    def _visit_program(self, node: ProgramNode) -> None:
        for stmt in node.statements:
            self._visit(stmt)

    def _visit_var_decl(self, node: VarDeclNode) -> None:
        name = node.identifier
        var_type = node.var_type
        line = node.line
        col = node.column

        existing = self.current_scope.lookup_local(name)
        if existing:
            self.errors.append({
                "line": line,
                "column": col,
                "message": f"Duplicate declaration: Identifier '{name}' already declared in {self.current_scope.name} scope at line {existing.line}"
            })
            return

        has_init = node.init_expr is not None
        sym = Symbol(
            name=name,
            var_type=var_type,
            scope_level=self.current_scope.level,
            scope_name=self.current_scope.name,
            line=line,
            is_initialized=has_init,
            kind="variable"
        )
        self.current_scope.define(sym)
        self.all_symbols.append(sym)

        if has_init:
            expr_type = self._visit(node.init_expr)
            if expr_type and not self._is_type_compatible(var_type, expr_type):
                self.errors.append({
                    "line": line,
                    "column": col,
                    "message": f"Type mismatch: Cannot initialize variable '{name}' of type '{var_type}' with expression of type '{expr_type}'"
                })
            elif var_type == "int" and expr_type == "float":
                self.warnings.append({
                    "line": line,
                    "column": col,
                    "message": f"Narrowing conversion: Assigning 'float' to 'int' variable '{name}' may cause loss of precision"
                })

    def _visit_assignment(self, node: AssignmentNode) -> None:
        name = node.identifier
        line = node.line
        col = node.column

        sym = self.current_scope.lookup(name)
        if not sym:
            self.errors.append({
                "line": line,
                "column": col,
                "message": f"Undeclared identifier: Variable '{name}' must be declared before assignment"
            })
            # Still visit the expr to check inner identifiers
            self._visit(node.expr)
            return

        expr_type = self._visit(node.expr)
        sym.is_initialized = True

        if expr_type and not self._is_type_compatible(sym.var_type, expr_type):
            self.errors.append({
                "line": line,
                "column": col,
                "message": f"Type mismatch in assignment: Cannot assign type '{expr_type}' to '{sym.var_type}' variable '{name}'"
            })
        elif sym.var_type == "int" and expr_type == "float":
            self.warnings.append({
                "line": line,
                "column": col,
                "message": f"Precision loss: Assigning float expression to integer variable '{name}'"
            })

    def _visit_identifier(self, node: IdentifierNode) -> str:
        name = node.name
        sym = self.current_scope.lookup(name)
        if not sym:
            self.errors.append({
                "line": node.line,
                "column": node.column,
                "message": f"Undeclared identifier: Variable '{name}' is used without being declared"
            })
            return "unknown"

        if not sym.is_initialized:
            self.warnings.append({
                "line": node.line,
                "column": node.column,
                "message": f"Potential use of uninitialized variable '{name}'"
            })
        return sym.var_type

    def _visit_binary_op(self, node: BinaryOpNode) -> str:
        left_type = self._visit(node.left) or "unknown"
        right_type = self._visit(node.right) or "unknown"
        op = node.op

        # Division by zero check
        if op in ('/', '%') and isinstance(node.right, LiteralNode):
            try:
                if float(node.right.value) == 0:
                    self.errors.append({
                        "line": node.line,
                        "column": node.column,
                        "message": f"Semantic error: Division or modulo by zero constant in expression"
                    })
            except (ValueError, TypeError):
                pass

        # Relational and equality operators return boolean
        if op in ('==', '!=', '<', '<=', '>', '>='):
            if left_type != "unknown" and right_type != "unknown":
                if (left_type == "string" and right_type != "string") or (left_type != "string" and right_type == "string"):
                    self.warnings.append({
                        "line": node.line,
                        "column": node.column,
                        "message": f"Comparing incompatible types '{left_type}' and '{right_type}' with operator '{op}'"
                    })
            return "bool"

        # Logical operators (&&, ||)
        if op in ('&&', '||'):
            return "bool"

        # Arithmetic operators (+, -, *, /, %)
        if left_type == "float" or right_type == "float":
            return "float"
        if left_type == "int" and right_type == "int":
            return "int"
        if op == '+' and (left_type == "string" or right_type == "string"):
            return "string"  # String concatenation

        return left_type if left_type != "unknown" else right_type

    def _visit_unary_op(self, node: UnaryOpNode) -> str:
        operand_type = self._visit(node.operand) or "unknown"
        if node.op == '!':
            return "bool"
        return operand_type

    def _visit_if(self, node: IfNode) -> None:
        self._visit(node.condition)
        if node.then_branch:
            self._visit(node.then_branch)
        if node.else_branch:
            self._visit(node.else_branch)

    def _visit_while(self, node: WhileNode) -> None:
        self._visit(node.condition)
        if node.body:
            self._visit(node.body)

    def _visit_block(self, node: BlockNode) -> None:
        self._enter_scope("block")
        for stmt in node.statements:
            self._visit(stmt)
        self._exit_scope()

    def _visit_return(self, node: ReturnNode) -> None:
        if node.expr:
            self._visit(node.expr)

    def _is_type_compatible(self, target_type: str, expr_type: str) -> bool:
        if target_type == expr_type:
            return True
        if target_type == "float" and expr_type == "int":
            return True  # Widening conversion is compatible
        if target_type == "int" and expr_type == "float":
            return True  # Allowed with warning
        if target_type == "bool" and expr_type in ("int", "bool"):
            return True
        return False
