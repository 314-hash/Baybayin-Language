import os
import sys
from typing import Dict, Any

from compiler.lexer import Lexer, LexerError
from compiler.parser import Parser, ParserError
from compiler.transpiler_python import PythonTranspiler
from compiler.transpiler_js import JsTranspiler
from compiler.transpiler_solidity import SolidityTranspiler

class BBLCompiler:
    def __init__(self):
        self.transpilers = {
            'python': PythonTranspiler,
            'js': JsTranspiler,
            'javascript': JsTranspiler,
            'solidity': SolidityTranspiler,
            'sol': SolidityTranspiler
        }

    def transpile(self, source_code: str, target: str) -> str:
        """Transpiles BBL source code to the specified target language."""
        target_normalized = target.lower().strip()
        if target_normalized not in self.transpilers:
            valid_targets = ", ".join(self.transpilers.keys())
            raise ValueError(f"Di-kilalang target: '{target}'. Mga tanggap na target: {valid_targets}")

        # Lexical analysis
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()

        # Syntax analysis
        parser = Parser(tokens)
        ast = parser.parse()

        # Semantic analysis (Type checking and name resolution)
        from compiler.semantic import SemanticAnalyzer
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        # Transpilation
        transpiler_class = self.transpilers[target_normalized]
        transpiler = transpiler_class()
        generated_code = transpiler.visit(ast)

        return generated_code

    def transpile_file(self, file_path: str, target: str) -> str:
        """Reads a file and transpiles its content to the specified target language."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Hindi mahanap ang file: '{file_path}'")

        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        return self.transpile(source_code, target)
