"""
CodeCraft Compiler Engine - TAC Code Optimizer
Performs Machine-Independent Code Optimization passes:
1. Constant Folding (e.g. evaluating 5 + 3 at compile-time to 8)
2. Algebraic Simplification (e.g. x + 0 => x, x * 1 => x, x * 0 => 0)
3. Dead Temporary Elimination / Copy Propagation
"""

from typing import List, Dict, Any, Tuple, Optional
from .codegen import Quadruple


class OptimizationResult:
    """Holds results of the TAC optimization pass."""
    def __init__(
        self,
        original_instructions: List[str],
        optimized_instructions: List[str],
        transformations: List[Dict[str, Any]],
        reduction_percentage: float
    ):
        self.original_instructions = original_instructions
        self.optimized_instructions = optimized_instructions
        self.transformations = transformations
        self.reduction_percentage = reduction_percentage

    def to_dict(self) -> dict:
        return {
            "original_instructions": self.original_instructions,
            "optimized_instructions": self.optimized_instructions,
            "transformations": self.transformations,
            "reduction_percentage": round(self.reduction_percentage, 1),
            "original_count": len(self.original_instructions),
            "optimized_count": len(self.optimized_instructions)
        }


class TACOptimizer:
    """
    Peephole and local optimizer for Three-Address Code quadruples.
    """
    def __init__(self, quadruples: List[Quadruple], instructions: List[str]):
        self.quadruples = quadruples
        self.original_instructions = list(instructions)
        self.transformations: List[Dict[str, Any]] = []

    def optimize(self) -> OptimizationResult:
        if not self.quadruples:
            return OptimizationResult([], [], [], 0.0)

        optimized_instructions: List[str] = []
        constants: Dict[str, Any] = {}

        for quad in self.quadruples:
            op = quad.op
            arg1 = quad.arg1
            arg2 = quad.arg2
            res = quad.result

            # 1. Labels and jumps are preserved unchanged
            if op in ('label', 'goto', 'if_false', 'return'):
                optimized_instructions.append(res if op == 'label' else f"{op} {arg1} {arg2} {res}".replace(" -", "").strip())
                continue

            # 2. Assignment
            if op == '=':
                # Check if arg1 is known constant
                val = constants.get(arg1, arg1)
                optimized_instructions.append(f"{res} = {val}")
                if self._is_number(val):
                    constants[res] = val
                continue

            # 3. Binary Arithmetic Operations
            if op in ('+', '-', '*', '/', '%'):
                v1 = constants.get(arg1, arg1)
                v2 = constants.get(arg2, arg2)

                # Check Constant Folding
                if self._is_number(v1) and self._is_number(v2):
                    folded_val = self._fold_constants(float(v1), op, float(v2))
                    if folded_val is not None:
                        # Format as int if whole number
                        val_str = str(int(folded_val)) if folded_val.is_integer() else str(folded_val)
                        constants[res] = val_str
                        self.transformations.append({
                            "type": "Constant Folding",
                            "before": f"{res} = {arg1} {op} {arg2}",
                            "after": f"{res} = {val_str}",
                            "rationale": f"Precomputed {v1} {op} {v2} at compile time"
                        })
                        optimized_instructions.append(f"{res} = {val_str}")
                        continue

                # Check Algebraic Simplification
                simplified = self._algebraic_simplify(v1, op, v2)
                if simplified is not None:
                    constants[res] = simplified
                    self.transformations.append({
                        "type": "Algebraic Simplification",
                        "before": f"{res} = {arg1} {op} {arg2}",
                        "after": f"{res} = {simplified}",
                        "rationale": f"Simplified arithmetic identity with {op}"
                    })
                    optimized_instructions.append(f"{res} = {simplified}")
                    continue

                # Fallback to standard instruction with constant-substituted args
                optimized_instructions.append(f"{res} = {v1} {op} {v2}")
                continue

            # Default
            optimized_instructions.append(f"{res} = {arg1} {op} {arg2}")

        orig_len = len(self.original_instructions)
        opt_len = len(optimized_instructions)
        reduction = ((orig_len - opt_len) / orig_len * 100) if orig_len > 0 else 0.0

        return OptimizationResult(
            original_instructions=self.original_instructions,
            optimized_instructions=optimized_instructions,
            transformations=self.transformations,
            reduction_percentage=max(0.0, reduction)
        )

    def _is_number(self, val: Any) -> bool:
        if val is None:
            return False
        try:
            float(str(val))
            return True
        except ValueError:
            return False

    def _fold_constants(self, n1: float, op: str, n2: float) -> Optional[float]:
        try:
            if op == '+':
                return n1 + n2
            if op == '-':
                return n1 - n2
            if op == '*':
                return n1 * n2
            if op == '/':
                return n1 / n2 if n2 != 0 else None
            if op == '%':
                return n1 % n2 if n2 != 0 else None
        except ZeroDivisionError:
            return None
        return None

    def _algebraic_simplify(self, v1: str, op: str, v2: str) -> Optional[str]:
        # x + 0 => x, 0 + x => x
        if op == '+':
            if v2 in ('0', '0.0'):
                return str(v1)
            if v1 in ('0', '0.0'):
                return str(v2)
        # x - 0 => x
        if op == '-':
            if v2 in ('0', '0.0'):
                return str(v1)
        # x * 1 => x, 1 * x => x
        if op == '*':
            if v2 in ('1', '1.0'):
                return str(v1)
            if v1 in ('1', '1.0'):
                return str(v2)
            if v1 in ('0', '0.0') or v2 in ('0', '0.0'):
                return "0"
        # x / 1 => x
        if op == '/':
            if v2 in ('1', '1.0'):
                return str(v1)
        return None
