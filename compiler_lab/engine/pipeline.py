"""
CodeCraft Compiler Engine - Pipeline Coordinator
Executes compilation passes sequentially, measures stage latencies,
and aggregates comprehensive results for the API and Workbench.
"""

import time
from typing import Dict, Any, Optional
from .lexer import Lexer, LexerResult
from .parser import Parser, ParserResult
from .semantic import SemanticAnalyzer, SemanticResult
from .codegen import CodeGenerator, TACResult
from .optimizer import TACOptimizer, OptimizationResult


class CompilerPipeline:
    """
    Orchestrates the complete multi-phase compiler pipeline.
    """
    MAX_SOURCE_LENGTH = 100_000  # 100 KB max to prevent DoS

    def __init__(self, source_code: str, mode: str = "all", run_optimizer: bool = True):
        self.raw_source = source_code or ""
        self.mode = mode.lower()  # 'all', 'lexical', 'syntax', 'semantic', 'tac'
        self.run_optimizer = run_optimizer

    def execute(self) -> Dict[str, Any]:
        start_total = time.perf_counter()

        # 1. Input Validation
        if not self.raw_source.strip():
            return {
                "is_success": False,
                "error_stage": "input",
                "error_message": "Source code cannot be empty. Please enter or load a code template.",
                "total_time_ms": 0.0,
                "metrics": {
                    "source_length": 0,
                    "line_count": 0,
                    "token_count": 0,
                    "quadruple_count": 0
                },
                "tokens": [],
                "comments": [],
                "lexer_errors": [],
                "ast": None,
                "syntax_errors": [],
                "mermaid_graph": "",
                "text_tree": "",
                "symbols": [],
                "semantic_errors": [],
                "semantic_warnings": [],
                "tac_instructions": [],
                "quadruples": [],
                "optimized_tac": [],
                "optimizations": []
            }

        if len(self.raw_source) > self.MAX_SOURCE_LENGTH:
            return {
                "is_success": False,
                "error_stage": "input",
                "error_message": f"Source code exceeds maximum allowed size ({self.MAX_SOURCE_LENGTH} characters).",
                "total_time_ms": 0.0,
                "metrics": {"source_length": len(self.raw_source)}
            }

        timings = {}

        # 2. Phase 1: Lexical Analysis
        t0 = time.perf_counter()
        lexer = Lexer(self.raw_source)
        lexer_res: LexerResult = lexer.tokenize()
        timings["lexer_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        if self.mode == "lexical" or not lexer_res.is_success:
            total_time = round((time.perf_counter() - start_total) * 1000, 2)
            has_errors = not lexer_res.is_success
            first_err = lexer_res.errors[0]["message"] if has_errors else None
            return {
                "is_success": not has_errors,
                "error_stage": "lexical" if has_errors else None,
                "error_message": first_err,
                "total_time_ms": total_time,
                "timings": timings,
                "metrics": {
                    "source_length": len(self.raw_source),
                    "line_count": lexer_res.stats.get("lines", 1),
                    "token_count": len(lexer_res.tokens),
                    "error_count": len(lexer_res.errors)
                },
                "tokens": [t.to_dict() for t in lexer_res.tokens],
                "comments": [c.to_dict() for c in lexer_res.comments],
                "lexer_errors": lexer_res.errors,
                "stats": lexer_res.stats,
                "ast": None,
                "syntax_errors": [],
                "mermaid_graph": "",
                "text_tree": "",
                "symbols": [],
                "semantic_errors": [],
                "semantic_warnings": [],
                "tac_instructions": [],
                "quadruples": [],
                "optimized_tac": [],
                "optimizations": []
            }

        # 3. Phase 2: Syntax Analysis
        t0 = time.perf_counter()
        parser = Parser(lexer_res.tokens)
        parser_res: ParserResult = parser.parse()
        timings["parser_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        if self.mode == "syntax" or not parser_res.is_success:
            total_time = round((time.perf_counter() - start_total) * 1000, 2)
            has_errors = not parser_res.is_success
            first_err = parser_res.errors[0]["message"] if has_errors else None
            return {
                "is_success": not has_errors,
                "error_stage": "syntax" if has_errors else None,
                "error_message": first_err,
                "total_time_ms": total_time,
                "timings": timings,
                "metrics": {
                    "source_length": len(self.raw_source),
                    "line_count": lexer_res.stats.get("lines", 1),
                    "token_count": len(lexer_res.tokens),
                    "error_count": len(parser_res.errors)
                },
                "tokens": [t.to_dict() for t in lexer_res.tokens],
                "comments": [c.to_dict() for c in lexer_res.comments],
                "lexer_errors": [],
                "stats": lexer_res.stats,
                "ast": parser_res.ast.to_dict() if parser_res.ast else None,
                "syntax_errors": parser_res.errors,
                "mermaid_graph": parser_res.mermaid_graph,
                "text_tree": parser_res.text_tree,
                "symbols": [],
                "semantic_errors": [],
                "semantic_warnings": [],
                "tac_instructions": [],
                "quadruples": [],
                "optimized_tac": [],
                "optimizations": []
            }

        # 4. Phase 3: Semantic Analysis & Symbol Table
        t0 = time.perf_counter()
        semantic_analyzer = SemanticAnalyzer()
        semantic_res: SemanticResult = semantic_analyzer.analyze(parser_res.ast)
        timings["semantic_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        if self.mode == "semantic" or not semantic_res.is_success:
            total_time = round((time.perf_counter() - start_total) * 1000, 2)
            has_errors = not semantic_res.is_success
            first_err = semantic_res.errors[0]["message"] if has_errors else None
            return {
                "is_success": not has_errors,
                "error_stage": "semantic" if has_errors else None,
                "error_message": first_err,
                "total_time_ms": total_time,
                "timings": timings,
                "metrics": {
                    "source_length": len(self.raw_source),
                    "line_count": lexer_res.stats.get("lines", 1),
                    "token_count": len(lexer_res.tokens),
                    "symbol_count": len(semantic_res.symbols),
                    "error_count": len(semantic_res.errors),
                    "warning_count": len(semantic_res.warnings)
                },
                "tokens": [t.to_dict() for t in lexer_res.tokens],
                "comments": [c.to_dict() for c in lexer_res.comments],
                "lexer_errors": [],
                "stats": lexer_res.stats,
                "ast": parser_res.ast.to_dict() if parser_res.ast else None,
                "syntax_errors": [],
                "mermaid_graph": parser_res.mermaid_graph,
                "text_tree": parser_res.text_tree,
                "symbols": semantic_res.symbols,
                "semantic_errors": semantic_res.errors,
                "semantic_warnings": semantic_res.warnings,
                "tac_instructions": [],
                "quadruples": [],
                "optimized_tac": [],
                "optimizations": []
            }

        # 5. Phase 4: Intermediate Code Generation (TAC & Quadruples)
        t0 = time.perf_counter()
        codegen = CodeGenerator()
        tac_res: TACResult = codegen.generate(parser_res.ast)
        timings["codegen_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        # 6. Phase 5: Optimization Pass (Bonus Compiler Pass)
        opt_res_dict = {"optimized_instructions": [], "transformations": []}
        if self.run_optimizer and tac_res.quadruples:
            t0 = time.perf_counter()
            optimizer = TACOptimizer(tac_res.quadruples, tac_res.instructions)
            opt_res: OptimizationResult = optimizer.optimize()
            timings["optimizer_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            opt_res_dict = opt_res.to_dict()

        total_time = round((time.perf_counter() - start_total) * 1000, 2)

        return {
            "is_success": True,
            "error_stage": None,
            "error_message": None,
            "total_time_ms": total_time,
            "timings": timings,
            "metrics": {
                "source_length": len(self.raw_source),
                "line_count": lexer_res.stats.get("lines", 1),
                "token_count": len(lexer_res.tokens),
                "symbol_count": len(semantic_res.symbols),
                "quadruple_count": len(tac_res.quadruples),
                "temporaries_used": tac_res.temporaries_count,
                "labels_generated": tac_res.labels_count,
                "warning_count": len(semantic_res.warnings),
                "optimizations_count": len(opt_res_dict.get("transformations", []))
            },
            "tokens": [t.to_dict() for t in lexer_res.tokens],
            "comments": [c.to_dict() for c in lexer_res.comments],
            "lexer_errors": [],
            "stats": lexer_res.stats,
            "ast": parser_res.ast.to_dict() if parser_res.ast else None,
            "syntax_errors": [],
            "mermaid_graph": parser_res.mermaid_graph,
            "text_tree": parser_res.text_tree,
            "symbols": semantic_res.symbols,
            "semantic_errors": [],
            "semantic_warnings": semantic_res.warnings,
            "tac_instructions": tac_res.instructions,
            "quadruples": [q.to_dict() for q in tac_res.quadruples],
            "optimized_tac": opt_res_dict.get("optimized_instructions", tac_res.instructions),
            "optimizations": opt_res_dict.get("transformations", [])
        }
