"""
CodeCraft Compiler Engine - Intermediate Code Generator (ICG)
Transforms the validated AST into linearized Three-Address Code (TAC)
and explicit Quadruple records (op, arg1, arg2, result).
"""

from typing import List, Dict, Any, Optional
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


class Quadruple:
    """Represents a classical compiler quadruple: (Index, Op, Arg1, Arg2, Result)."""
    def __init__(self, index: int, op: str, arg1: str, arg2: str, result: str):
        self.index = index
        self.op = op
        self.arg1 = arg1 if arg1 is not None else "-"
        self.arg2 = arg2 if arg2 is not None else "-"
        self.result = result

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "op": self.op,
            "arg1": self.arg1,
            "arg2": self.arg2,
            "result": self.result
        }

    def __repr__(self) -> str:
        return f"Quad({self.index}: {self.op}, {self.arg1}, {self.arg2}, {self.result})"


class TACResult:
    """Holds the complete generated intermediate representation."""
    def __init__(
        self,
        instructions: List[str],
        quadruples: List[Quadruple],
        temporaries_count: int,
        labels_count: int,
        is_success: bool = True
    ):
        self.instructions = instructions
        self.quadruples = quadruples
        self.temporaries_count = temporaries_count
        self.labels_count = labels_count
        self.is_success = is_success

    def to_dict(self) -> dict:
        return {
            "instructions": self.instructions,
            "quadruples": [q.to_dict() for q in self.quadruples],
            "temporaries_count": self.temporaries_count,
            "labels_count": self.labels_count,
            "is_success": self.is_success
        }


class CodeGenerator:
    """
    Translates an Edu-C AST into Three-Address Code and Quadruples.
    """
    def __init__(self):
        self.temp_counter = 0
        self.label_counter = 0
        self.quadruples: List[Quadruple] = []
        self.instructions: List[str] = []

    def _new_temp(self) -> str:
        t = f"t{self.temp_counter}"
        self.temp_counter += 1
        return t

    def _new_label(self) -> str:
        lbl = f"L{self.label_counter}"
        self.label_counter += 1
        return lbl

    def _emit(self, instruction: str, op: str, arg1: str = "-", arg2: str = "-", result: str = ""):
        self.instructions.append(instruction)
        quad = Quadruple(
            index=len(self.quadruples),
            op=op,
            arg1=arg1,
            arg2=arg2,
            result=result or instruction
        )
        self.quadruples.append(quad)

    def generate(self, ast: Optional[ProgramNode]) -> TACResult:
        if ast is None:
            return TACResult([], [], 0, 0, False)

        for stmt in ast.statements:
            self._gen_statement(stmt)

        return TACResult(
            instructions=self.instructions,
            quadruples=self.quadruples,
            temporaries_count=self.temp_counter,
            labels_count=self.label_counter,
            is_success=True
        )

    def _gen_statement(self, node: ASTNode):
        if isinstance(node, VarDeclNode):
            if node.init_expr:
                val = self._gen_expression(node.init_expr)
                self._emit(f"{node.identifier} = {val}", "=", val, "-", node.identifier)
        elif isinstance(node, AssignmentNode):
            val = self._gen_expression(node.expr)
            if node.op == '=':
                self._emit(f"{node.identifier} = {val}", "=", val, "-", node.identifier)
            else:
                # Compound assignment: +=, -=, *=, /=
                base_op = node.op[0]
                temp = self._new_temp()
                self._emit(f"{temp} = {node.identifier} {base_op} {val}", base_op, node.identifier, val, temp)
                self._emit(f"{node.identifier} = {temp}", "=", temp, "-", node.identifier)
        elif isinstance(node, IfNode):
            self._gen_if(node)
        elif isinstance(node, WhileNode):
            self._gen_while(node)
        elif isinstance(node, BlockNode):
            for stmt in node.statements:
                self._gen_statement(stmt)
        elif isinstance(node, ReturnNode):
            if node.expr:
                val = self._gen_expression(node.expr)
                self._emit(f"return {val}", "return", val, "-", "-")
            else:
                self._emit("return", "return", "-", "-", "-")
        elif isinstance(node, ExpressionStatementNode):
            self._gen_expression(node.expr)

    def _gen_if(self, node: IfNode):
        cond_val = self._gen_expression(node.condition)
        label_else = self._new_label()
        label_end = self._new_label()

        target_false = label_else if node.else_branch else label_end
        self._emit(f"if_false {cond_val} goto {target_false}", "if_false", cond_val, "-", target_false)

        if node.then_branch:
            self._gen_statement(node.then_branch)

        if node.else_branch:
            self._emit(f"goto {label_end}", "goto", "-", "-", label_end)
            self._emit(f"{label_else}:", "label", "-", "-", label_else)
            self._gen_statement(node.else_branch)
            self._emit(f"{label_end}:", "label", "-", "-", label_end)
        else:
            self._emit(f"{target_false}:", "label", "-", "-", target_false)

    def _gen_while(self, node: WhileNode):
        label_start = self._new_label()
        label_end = self._new_label()

        self._emit(f"{label_start}:", "label", "-", "-", label_start)
        cond_val = self._gen_expression(node.condition)
        self._emit(f"if_false {cond_val} goto {label_end}", "if_false", cond_val, "-", label_end)

        if node.body:
            self._gen_statement(node.body)

        self._emit(f"goto {label_start}", "goto", "-", "-", label_start)
        self._emit(f"{label_end}:", "label", "-", "-", label_end)

    def _gen_expression(self, node: ASTNode) -> str:
        if isinstance(node, LiteralNode):
            return str(node.value)
        elif isinstance(node, IdentifierNode):
            return node.name
        elif isinstance(node, BinaryOpNode):
            left_val = self._gen_expression(node.left)
            right_val = self._gen_expression(node.right)
            temp = self._new_temp()
            self._emit(f"{temp} = {left_val} {node.op} {right_val}", node.op, left_val, right_val, temp)
            return temp
        elif isinstance(node, UnaryOpNode):
            operand_val = self._gen_expression(node.operand)
            temp = self._new_temp()
            self._emit(f"{temp} = {node.op} {operand_val}", node.op, operand_val, "-", temp)
            return temp
        return "0"
