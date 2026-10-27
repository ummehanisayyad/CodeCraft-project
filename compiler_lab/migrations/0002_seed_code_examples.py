from django.db import migrations


def seed_examples(apps, schema_editor):
    CodeExample = apps.get_model('compiler_lab', 'CodeExample')

    examples = [
        {
            "title": "Arithmetic Expressions & Precedence",
            "category": "basic",
            "description": "Demonstrates tokenization, operator precedence (*, /, +, -) and Three-Address Code generation.",
            "code": (
                "// Example 1: Arithmetic Expression & Precedence\n"
                "int a = 15;\n"
                "int b = 4;\n"
                "int c = 2;\n"
                "int result = (a + b) * c - 8 / 2;\n"
            ),
            "expected_stage": "all",
            "order": 1
        },
        {
            "title": "Control Flow - If / Else",
            "category": "control",
            "description": "Tests relational operators (>=), boolean conditional branching, and jump label generation.",
            "code": (
                "// Example 2: Grade Evaluation with If-Else\n"
                "int score = 88;\n"
                "int status = 0;\n"
                "\n"
                "if (score >= 75) {\n"
                "    status = 1;\n"
                "} else {\n"
                "    status = 2;\n"
                "}\n"
            ),
            "expected_stage": "all",
            "order": 2
        },
        {
            "title": "While Loop Iteration",
            "category": "control",
            "description": "Evaluates loop conditional evaluation, back-edges, and sequential quadruples generation.",
            "code": (
                "// Example 3: Factorial Calculation using While Loop\n"
                "int n = 5;\n"
                "int fact = 1;\n"
                "int i = 1;\n"
                "\n"
                "while (i <= n) {\n"
                "    fact = fact * i;\n"
                "    i = i + 1;\n"
                "}\n"
            ),
            "expected_stage": "all",
            "order": 3
        },
        {
            "title": "Constant Folding & Code Optimization",
            "category": "optimization",
            "description": "Demonstrates compile-time constant arithmetic evaluation and algebraic identity simplification.",
            "code": (
                "// Example 4: Constant Folding & Algebraic Simplification\n"
                "int base = 100;\n"
                "int x = 10 + 20 * 2;\n"
                "int y = x * 1;\n"
                "int z = y + 0;\n"
                "int total = base + z;\n"
            ),
            "expected_stage": "all",
            "order": 4
        },
        {
            "title": "Semantic Analysis & Type Checking",
            "category": "semantic",
            "description": "Highlights detection of duplicate identifier declarations, undeclared usage, and division by zero.",
            "code": (
                "// Example 5: Semantic Diagnostics Demo\n"
                "int count = 10;\n"
                "int count = 25;\n"
                "target = 100;\n"
                "int div_err = 50 / 0;\n"
            ),
            "expected_stage": "semantic",
            "order": 5
        },
        {
            "title": "Syntax Error Diagnostics",
            "category": "errors",
            "description": "Demonstrates parser error recovery and precise line/column reporting for malformed constructs.",
            "code": (
                "// Example 6: Syntax Error Recovery Demo\n"
                "int val = ;\n"
                "if (val > 10 {\n"
                "    val = 20;\n"
                "}\n"
            ),
            "expected_stage": "syntax",
            "order": 6
        }
    ]

    for ex in examples:
        CodeExample.objects.create(**ex)


def unseed_examples(apps, schema_editor):
    CodeExample = apps.get_model('compiler_lab', 'CodeExample')
    CodeExample.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('compiler_lab', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_examples, unseed_examples),
    ]
