"""
CodeCraft Compiler Engine - Abstract Syntax Tree (AST) Nodes
Defines AST data structures, serialization to JSON, Mermaid diagram generators,
and text tree visualization.
"""

from typing import List, Optional, Any, Dict


class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""
    def __init__(self, line: int = 1, column: int = 1):
        self.line = line
        self.column = column

    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def to_mermaid(self, node_id_prefix: str = "n") -> str:
        """Returns Mermaid.js syntax for this node and its sub-tree."""
        lines: List[str] = ["graph TD"]
        counter = [0]

        def walk(node: 'ASTNode') -> str:
            counter[0] += 1
            current_id = f"{node_id_prefix}{counter[0]}"
            label = node._mermaid_label().replace('"', '\\"')
            lines.append(f'    {current_id}["{label}"]')

            for child in node._get_children():
                if child is not None:
                    child_id = walk(child)
                    lines.append(f'    {current_id} --> {child_id}')
            return current_id

        walk(self)
        return "\n".join(lines)

    def _mermaid_label(self) -> str:
        return self.__class__.__name__

    def _get_children(self) -> List['ASTNode']:
        return []

    def to_text_tree(self, prefix: str = "", is_last: bool = True) -> str:
        label = self._mermaid_label()
        branch = "└── " if is_last else "├── "
        result = [f"{prefix}{branch}{label}"]

        children = [c for c in self._get_children() if c is not None]
        for i, child in enumerate(children):
            child_is_last = (i == len(children) - 1)
            child_prefix = prefix + ("    " if is_last else "│   ")
            result.append(child.to_text_tree(child_prefix, child_is_last))

        return "\n".join(result)


class ProgramNode(ASTNode):
    """Root node representing a whole program or list of top-level statements."""
    def __init__(self, statements: List[ASTNode], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.statements = statements

    def _mermaid_label(self) -> str:
        return f"Program ({len(self.statements)} stmts)"

    def _get_children(self) -> List[ASTNode]:
        return self.statements

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Program",
            "line": self.line,
            "column": self.column,
            "statements": [s.to_dict() for s in self.statements]
        }


class VarDeclNode(ASTNode):
    """Variable declaration node (e.g. `int x = 10;` or `float y;`)."""
    def __init__(self, var_type: str, identifier: str, init_expr: Optional[ASTNode] = None, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.var_type = var_type
        self.identifier = identifier
        self.init_expr = init_expr

    def _mermaid_label(self) -> str:
        if self.init_expr:
            return f"VarDecl: {self.var_type} {self.identifier} ="
        return f"VarDecl: {self.var_type} {self.identifier}"

    def _get_children(self) -> List[ASTNode]:
        return [self.init_expr] if self.init_expr else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "VarDecl",
            "var_type": self.var_type,
            "identifier": self.identifier,
            "init_expr": self.init_expr.to_dict() if self.init_expr else None,
            "line": self.line,
            "column": self.column
        }


class AssignmentNode(ASTNode):
    """Assignment statement (e.g. `x = a + b;` or `x += 1;`)."""
    def __init__(self, identifier: str, op: str, expr: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.identifier = identifier
        self.op = op
        self.expr = expr

    def _mermaid_label(self) -> str:
        return f"Assign: {self.identifier} {self.op}"

    def _get_children(self) -> List[ASTNode]:
        return [self.expr]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Assignment",
            "identifier": self.identifier,
            "op": self.op,
            "expr": self.expr.to_dict(),
            "line": self.line,
            "column": self.column
        }


class BinaryOpNode(ASTNode):
    """Binary operation node (+, -, *, /, ==, !=, <, &&, etc.)."""
    def __init__(self, left: ASTNode, op: str, right: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.left = left
        self.op = op
        self.right = right

    def _mermaid_label(self) -> str:
        return f"BinaryOp '{self.op}'"

    def _get_children(self) -> List[ASTNode]:
        return [self.left, self.right]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "BinaryOp",
            "op": self.op,
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "line": self.line,
            "column": self.column
        }


class UnaryOpNode(ASTNode):
    """Unary operation node (!, -, +)."""
    def __init__(self, op: str, operand: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.op = op
        self.operand = operand

    def _mermaid_label(self) -> str:
        return f"UnaryOp '{self.op}'"

    def _get_children(self) -> List[ASTNode]:
        return [self.operand]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "UnaryOp",
            "op": self.op,
            "operand": self.operand.to_dict(),
            "line": self.line,
            "column": self.column
        }


class LiteralNode(ASTNode):
    """Literal constant (int, float, string, char, bool)."""
    def __init__(self, literal_type: str, value: Any, raw: str, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.literal_type = literal_type
        self.value = value
        self.raw = raw

    def _mermaid_label(self) -> str:
        return f"Literal ({self.literal_type}): {self.value}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Literal",
            "literal_type": self.literal_type,
            "value": str(self.value),
            "raw": self.raw,
            "line": self.line,
            "column": self.column
        }


class IdentifierNode(ASTNode):
    """Identifier reference."""
    def __init__(self, name: str, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.name = name

    def _mermaid_label(self) -> str:
        return f"Id: {self.name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Identifier",
            "name": self.name,
            "line": self.line,
            "column": self.column
        }


class IfNode(ASTNode):
    """Conditional statement `if (cond) stmt else stmt`."""
    def __init__(
        self,
        condition: ASTNode,
        then_branch: ASTNode,
        else_branch: Optional[ASTNode] = None,
        line: int = 1,
        column: int = 1
    ):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def _mermaid_label(self) -> str:
        return "IfStmt"

    def _get_children(self) -> List[ASTNode]:
        children = [self.condition, self.then_branch]
        if self.else_branch:
            children.append(self.else_branch)
        return children

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "If",
            "condition": self.condition.to_dict(),
            "then_branch": self.then_branch.to_dict(),
            "else_branch": self.else_branch.to_dict() if self.else_branch else None,
            "line": self.line,
            "column": self.column
        }


class WhileNode(ASTNode):
    """While loop statement `while (cond) stmt`."""
    def __init__(self, condition: ASTNode, body: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

    def _mermaid_label(self) -> str:
        return "WhileLoop"

    def _get_children(self) -> List[ASTNode]:
        return [self.condition, self.body]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "While",
            "condition": self.condition.to_dict(),
            "body": self.body.to_dict(),
            "line": self.line,
            "column": self.column
        }


class BlockNode(ASTNode):
    """Compound statement / code block `{ stmt1; stmt2; }`."""
    def __init__(self, statements: List[ASTNode], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.statements = statements

    def _mermaid_label(self) -> str:
        return f"Block ({len(self.statements)} stmts)"

    def _get_children(self) -> List[ASTNode]:
        return self.statements

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Block",
            "statements": [s.to_dict() for s in self.statements],
            "line": self.line,
            "column": self.column
        }


class ReturnNode(ASTNode):
    """Return statement `return expr;` or `return;`."""
    def __init__(self, expr: Optional[ASTNode] = None, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.expr = expr

    def _mermaid_label(self) -> str:
        return "Return"

    def _get_children(self) -> List[ASTNode]:
        return [self.expr] if self.expr else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "Return",
            "expr": self.expr.to_dict() if self.expr else None,
            "line": self.line,
            "column": self.column
        }


class ExpressionStatementNode(ASTNode):
    """Expression statement (e.g. `x + 1;` or `foo();`)."""
    def __init__(self, expr: ASTNode, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.expr = expr

    def _mermaid_label(self) -> str:
        return "ExprStmt"

    def _get_children(self) -> List[ASTNode]:
        return [self.expr]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "ExpressionStatement",
            "expr": self.expr.to_dict(),
            "line": self.line,
            "column": self.column
        }
