"""
Comprehensive Automated Test Suite for CodeCraft Compiler Engine,
Database Models, Analysis API, and History Ownership Isolation.
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from compiler_lab.engine import (
    Lexer,
    TokenType,
    Parser,
    SemanticAnalyzer,
    CodeGenerator,
    TACOptimizer,
    CompilerPipeline
)
from compiler_lab.models import AnalysisRecord, CodeExample


class LexerTestCase(TestCase):
    """Verifies deterministic lexical scanning, token categorization, and error handling."""

    def test_keywords_and_identifiers(self):
        code = "int count = 42; float rate = 3.14; bool flag = true;"
        lexer = Lexer(code)
        res = lexer.tokenize()
        self.assertTrue(res.is_success)

        types = [t.type for t in res.tokens if t.type != TokenType.EOF]
        self.assertIn(TokenType.KEYWORD, types)
        self.assertIn(TokenType.IDENTIFIER, types)
        self.assertIn(TokenType.INT_LITERAL, types)
        self.assertIn(TokenType.FLOAT_LITERAL, types)
        self.assertIn(TokenType.BOOL_LITERAL, types)

    def test_operators_relational_and_logical(self):
        code = "a == b && c != d || e <= f"
        lexer = Lexer(code)
        res = lexer.tokenize()
        self.assertTrue(res.is_success)
        lexemes = [t.lexeme for t in res.tokens]
        self.assertIn("==", lexemes)
        self.assertIn("&&", lexemes)
        self.assertIn("!=", lexemes)
        self.assertIn("||", lexemes)
        self.assertIn("<=", lexemes)

    def test_single_and_multiline_comments(self):
        code = (
            "// Single line comment\n"
            "int x = 5;\n"
            "/* Multi-line\n"
            "   comment block */\n"
            "int y = 10;"
        )
        lexer = Lexer(code)
        res = lexer.tokenize()
        self.assertTrue(res.is_success)
        self.assertEqual(len(res.comments), 2)
        # Verify tokens exclude comments
        tokens_lexemes = [t.lexeme for t in res.tokens if t.type != TokenType.EOF]
        self.assertNotIn("// Single line comment", tokens_lexemes)

    def test_invalid_characters_detection(self):
        code = "int x = @ + #;"
        lexer = Lexer(code)
        res = lexer.tokenize()
        self.assertFalse(res.is_success)
        self.assertEqual(len(res.errors), 2)
        self.assertEqual(res.errors[0]["character"], "@")
        self.assertEqual(res.errors[1]["character"], "#")


class ParserTestCase(TestCase):
    """Verifies recursive-descent parsing, AST structure, and syntax error diagnostics."""

    def test_valid_arithmetic_precedence(self):
        # Multiplicative should have higher precedence than additive
        code = "int res = 2 + 3 * 4;"
        pipeline = CompilerPipeline(code)
        res = pipeline.execute()
        self.assertTrue(res["is_success"])
        ast = res["ast"]
        self.assertIsNotNone(ast)
        self.assertEqual(len(ast["statements"]), 1)
        var_decl = ast["statements"][0]
        self.assertEqual(var_decl["identifier"], "res")
        # Root of init_expr should be '+' with right child '*'
        init_expr = var_decl["init_expr"]
        self.assertEqual(init_expr["op"], "+")
        self.assertEqual(init_expr["right"]["op"], "*")

    def test_if_else_and_while_ast(self):
        code = (
            "int x = 5;\n"
            "if (x > 0) {\n"
            "    x = x - 1;\n"
            "} else {\n"
            "    x = 0;\n"
            "}\n"
            "while (x < 10) {\n"
            "    x = x + 1;\n"
            "}"
        )
        pipeline = CompilerPipeline(code)
        res = pipeline.execute()
        self.assertTrue(res["is_success"])
        self.assertEqual(len(res["ast"]["statements"]), 3)
        self.assertEqual(res["ast"]["statements"][1]["node_type"], "If")
        self.assertEqual(res["ast"]["statements"][2]["node_type"], "While")

    def test_syntax_error_missing_semicolon(self):
        code = "int x = 10\nint y = 20;"
        pipeline = CompilerPipeline(code)
        res = pipeline.execute()
        self.assertFalse(res["is_success"])
        self.assertEqual(res["error_stage"], "syntax")
        self.assertIn(";", res["error_message"])

    def test_syntax_error_unclosed_parenthesis(self):
        code = "if (x > 5 { x = 10; }"
        pipeline = CompilerPipeline(code)
        res = pipeline.execute()
        self.assertFalse(res["is_success"])
        self.assertEqual(res["error_stage"], "syntax")


class SemanticTestCase(TestCase):
    """Verifies multi-scope symbol table, duplicate check, and type checks."""

    def test_undeclared_variable_error(self):
        code = "int a = 5;\nb = a + 10;"  # b is undeclared
        pipeline = CompilerPipeline(code)
        res = pipeline.execute()
        self.assertFalse(res["is_success"])
        self.assertEqual(res["error_stage"], "semantic")
        self.assertTrue(any("b" in err["message"] for err in res["semantic_errors"]))

    def test_duplicate_declaration_error(self):
        code = "int count = 1;\nint count = 2;"
        pipeline = CompilerPipeline(code)
        res = pipeline.execute()
        self.assertFalse(res["is_success"])
        self.assertEqual(res["error_stage"], "semantic")
        self.assertTrue(any("Duplicate" in err["message"] for err in res["semantic_errors"]))

    def test_nested_block_scopes(self):
        code = (
            "int x = 10;\n"
            "{\n"
            "    int y = 20;\n"
            "    int z = x + y;\n"
            "}"
        )
        pipeline = CompilerPipeline(code)
        res = pipeline.execute()
        self.assertTrue(res["is_success"])
        symbol_names = [s["name"] for s in res["symbols"]]
        self.assertIn("x", symbol_names)
        self.assertIn("y", symbol_names)
        self.assertIn("z", symbol_names)


class IntermediateCodeTestCase(TestCase):
    """Verifies Three-Address Code generation, Quadruples, and Constant Folding."""

    def test_three_address_code_generation(self):
        code = "int a = 1;\nint b = 2;\nint c = 3;\nint d = 4;\nint result = a * b + c * d;"
        pipeline = CompilerPipeline(code)
        res = pipeline.execute()
        self.assertTrue(res["is_success"])
        tac = res["tac_instructions"]
        self.assertGreaterEqual(len(tac), 3)
        self.assertTrue(any("=" in inst for inst in tac))

    def test_quadruples_structure(self):
        code = "int x = 10 + 20;"
        pipeline = CompilerPipeline(code)
        res = pipeline.execute()
        self.assertTrue(res["is_success"])
        quads = res["quadruples"]
        self.assertEqual(len(quads), 2)
        self.assertEqual(quads[0]["op"], "+")
        self.assertEqual(quads[0]["arg1"], "10")
        self.assertEqual(quads[0]["arg2"], "20")

    def test_constant_folding_optimization(self):
        code = "int folded = 10 + 20 * 2;"
        pipeline = CompilerPipeline(code, run_optimizer=True)
        res = pipeline.execute()
        self.assertTrue(res["is_success"])
        optimized = res["optimized_tac"]
        # 20 * 2 = 40, 10 + 40 = 50 -> should be folded
        self.assertTrue(any("50" in inst for inst in optimized))


class CompilerAPITestCase(TestCase):
    """Verifies AJAX API endpoint validation, CSRF, and execution."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="teststudent", password="password123")

    def test_api_empty_source_code_rejected(self):
        response = self.client.post(
            reverse('compiler_lab:api_analyze'),
            data=json.dumps({"source_code": "   ", "mode": "all"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_success"])
        self.assertEqual(data["error_stage"], "input")

    def test_api_authenticated_analysis_saves_record(self):
        self.client.login(username="teststudent", password="password123")
        response = self.client.post(
            reverse('compiler_lab:api_analyze'),
            data=json.dumps({
                "source_code": "int a = 100;\nint b = a + 50;",
                "mode": "all",
                "title": "API Persistence Test"
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_success"])
        self.assertIsNotNone(data["record_id"])

        # Check DB persistence
        record = AnalysisRecord.objects.get(id=data["record_id"])
        self.assertEqual(record.user, self.user)
        self.assertEqual(record.title, "API Persistence Test")
        self.assertTrue(record.is_success)

    def test_api_guest_analysis_runs_without_crashing(self):
        response = self.client.post(
            reverse('compiler_lab:api_analyze'),
            data=json.dumps({
                "source_code": "int x = 5;",
                "mode": "all"
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_success"])
        self.assertIsNone(data["record_id"])


class HistoryOwnershipTestCase(TestCase):
    """Verifies strict isolation: users must never view or delete other users' records."""

    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(username="alice", password="password123")
        self.user_b = User.objects.create_user(username="bob", password="password123")

        self.record_a = AnalysisRecord.objects.create(
            user=self.user_a,
            title="Alice's Private Experiment",
            source_code="int secret_a = 1;",
            mode="all",
            is_success=True
        )

    def test_history_list_requires_authentication(self):
        response = self.client.get(reverse('compiler_lab:history_list'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_user_cannot_view_other_user_record(self):
        # Login as Bob and try to view Alice's record
        self.client.login(username="bob", password="password123")
        response = self.client.get(reverse('compiler_lab:history_detail', kwargs={'pk': self.record_a.id}))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_other_user_record(self):
        # Login as Bob and try to delete Alice's record
        self.client.login(username="bob", password="password123")
        response = self.client.post(reverse('compiler_lab:history_delete', kwargs={'pk': self.record_a.id}))
        self.assertEqual(response.status_code, 404)
        # Verify Alice's record still exists
        self.assertTrue(AnalysisRecord.objects.filter(id=self.record_a.id).exists())

    def test_user_can_view_and_delete_own_record(self):
        self.client.login(username="alice", password="password123")
        # Alice can view
        response = self.client.get(reverse('compiler_lab:history_detail', kwargs={'pk': self.record_a.id}))
        self.assertEqual(response.status_code, 200)

        # Alice can delete
        del_response = self.client.post(reverse('compiler_lab:history_delete', kwargs={'pk': self.record_a.id}))
        self.assertEqual(del_response.status_code, 302)
        self.assertFalse(AnalysisRecord.objects.filter(id=self.record_a.id).exists())
