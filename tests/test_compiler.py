import unittest
import sys
import os

# Adjust path to import compiler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compiler.lexer import Lexer, Token
from compiler.parser import Parser
from compiler.compiler import BBLCompiler

class TestBBLLexer(unittest.TestCase):
    def test_keywords(self):
        source = "kontrata tungkulin itakda ibahagi ibalik kung kundi habang tama mali wala"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        expected = [
            'KONTRATA', 'TUNGKULIN', 'ITAKDA', 'IBAHAGI', 'IBALIK', 
            'KUNG', 'KUNDI', 'HABANG', 'TAMA', 'MALI', 'WALA', 'EOF'
        ]
        self.assertEqual([t.type for t in tokens], expected)

    def test_types(self):
        source = "buo teksto kondisyon alamat"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        expected = ['TYPE_BUO', 'TYPE_TEKSTO', 'TYPE_KONDISYON', 'TYPE_ALAMAT', 'EOF']
        self.assertEqual([t.type for t in tokens], expected)

    def test_baybayin_unicode_identifiers(self):
        # Actual Baybayin unicode characters: ᜃᜋᜓᜐ᜔ᜆᜓ
        source = "itakda ᜃᜋᜓᜐ᜔ᜆᜓ = 10"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        self.assertEqual(tokens[0].type, 'ITAKDA')
        self.assertEqual(tokens[1].type, 'IDENTIFIER')
        self.assertEqual(tokens[1].value, 'ᜃᜋᜓᜐ᜔ᜆᜓ')
        self.assertEqual(tokens[2].type, 'ASSIGN')
        self.assertEqual(tokens[3].type, 'NUMBER')

class TestBBLParser(unittest.TestCase):
    def test_simple_program(self):
        source = """
        itakda x = 5
        itakda y = x + 10
        ipakita(y)
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        self.assertEqual(len(ast.declarations), 3)

class TestBBLCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = BBLCompiler()

    def test_python_transpilation(self):
        source = """
        kontrata Test {
            itakda x: buo = 5
            tungkulin simulan() {
                x = 10
            }
        }
        """
        py_code = self.compiler.transpile(source, 'python')
        self.assertIn("class Test:", py_code)
        self.assertIn("def __init__(self):", py_code)
        self.assertIn("self.x = 10", py_code)

    def test_javascript_transpilation(self):
        source = """
        kontrata Test {
            itakda x: buo = 5
            tungkulin simulan() {
                x = 10
            }
        }
        """
        js_code = self.compiler.transpile(source, 'js')
        self.assertIn("class Test {", js_code)
        self.assertIn("constructor() {", js_code)
        self.assertIn("this.x = 10", js_code)

    def test_solidity_transpilation(self):
        source = """
        kontrata Test {
            itakda x: buo = 5
            tungkulin baguhin(bagong_x: buo) {
                x = bagong_x
            }
        }
        """
        sol_code = self.compiler.transpile(source, 'solidity')
        self.assertIn("contract Test {", sol_code)
        self.assertIn("uint256 public x = 5;", sol_code)
        self.assertIn("function baguhin(uint256 bagong_x) public {", sol_code)
        self.assertIn("x = bagong_x;", sol_code)

    def test_solidity_string_comparison(self):
        source = """
        kontrata Test {
            itakda pangalan: teksto = "bbl"
            tungkulin ihambing(bagong_pangalan: teksto): kondisyon {
                ibalik pangalan == bagong_pangalan
            }
        }
        """
        sol_code = self.compiler.transpile(source, 'solidity')
        self.assertIn("keccak256(bytes(pangalan)) == keccak256(bytes(bagong_pangalan))", sol_code)

class TestBBLAgent(unittest.TestCase):
    def test_missing_api_key(self):
        from ai.agents.orchestrator import BBLOrchestrator
        # Force empty key to test error handling
        agent = BBLOrchestrator(api_key="")
        with self.assertRaises(ValueError) as context:
            agent.explain("itakda x = 5")
        self.assertIn("Nawawala ang GEMINI_API_KEY", str(context.exception))

    def test_system_instruction_setup(self):
        from ai.agents.base_agent import BBLBaseAgent
        agent = BBLBaseAgent(api_key="dummy_key")
        self.assertIn("kontrata", agent.SYSTEM_INSTRUCTION)
        self.assertIn("tungkulin", agent.SYSTEM_INSTRUCTION)

    def test_guro_agent_glossary_loading(self):
        from ai.guro.guro_agent import BBLGuroAgent
        guro = BBLGuroAgent(api_key="")
        self.assertIsNotNone(guro.glossary)
        self.assertIn("variable", guro.glossary)

class TestBBLSemanticAnalyzer(unittest.TestCase):
    def setUp(self):
        self.compiler = BBLCompiler()

    def test_undeclared_variable(self):
        from compiler.semantic import SemanticError
        source = "itakda x = y"
        with self.assertRaises(SemanticError) as context:
            self.compiler.transpile(source, 'python')
        self.assertIn("hindi pa idinedeklara", str(context.exception))

    def test_redeclared_variable(self):
        from compiler.semantic import SemanticError
        source = """
        itakda x = 5
        itakda x = 10
        """
        with self.assertRaises(SemanticError) as context:
            self.compiler.transpile(source, 'python')
        self.assertIn("idineklara na", str(context.exception))

    def test_type_mismatch_variable(self):
        from compiler.semantic import SemanticError
        source = 'itakda x: buo = "maling uri"'
        with self.assertRaises(SemanticError) as context:
            self.compiler.transpile(source, 'python')
        self.assertIn("Di-tugmang uri", str(context.exception))

    def test_wrong_method_arguments_count(self):
        from compiler.semantic import SemanticError
        source = """
        kontrata Test {
            tungkulin simulan(a: buo) {}
        }
        itakda demo = Test(5, 10)
        """
        with self.assertRaises(SemanticError) as context:
            self.compiler.transpile(source, 'python')
        self.assertIn("Maling bilang ng mga argumento", str(context.exception))

class DummyWfile:
    def __init__(self):
        self.data = b""
    def write(self, b):
        self.data += b

class TestBBLDashboard(unittest.TestCase):
    def test_handler_compile_success(self):
        import json
        import io
        from web.server import BBLDashboardHandler

        class MockHandler(BBLDashboardHandler):
            def __init__(self):
                self.rfile = io.BytesIO(json.dumps({"code": "itakda x = 5"}).encode('utf-8'))
                self.headers = {'Content-Length': str(len(self.rfile.getvalue()))}
                self.wfile = DummyWfile()
                self.response_status = None
                self.response_headers = {}

            def send_response(self, code, message=None):
                self.response_status = code

            def send_header(self, keyword, value):
                self.response_headers[keyword] = value

            def end_headers(self):
                pass

        handler = MockHandler()
        handler.handle_compile()

        res = json.loads(handler.wfile.data.decode('utf-8'))
        self.assertTrue(res['success'])
        self.assertIn("x = 5", res['python'])
        self.assertIn("ast", res)

class TestBBLVirtualMachine(unittest.TestCase):
    def test_simple_addition_and_print(self):
        from compiler.lexer import Lexer
        from compiler.parser import Parser
        from compiler.vm_compiler import BBLVMCompiler
        from runtime.vm.bbvm import BBVM
        
        source = """
        itakda x = 5 + 10
        ipakita(x)
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        compiler = BBLVMCompiler()
        bytecode = compiler.compile(ast)
        
        vm = BBVM()
        vm.execute(bytecode)
        
        self.assertIn("15", vm.output_buffer)

    def test_conditional_if_else(self):
        from compiler.lexer import Lexer
        from compiler.parser import Parser
        from compiler.vm_compiler import BBLVMCompiler
        from runtime.vm.bbvm import BBVM
        
        source = """
        itakda x = 10
        kung (x > 5) {
            ipakita("Malaki")
        } kundi {
            ipakita("Maliit")
        }
        """
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        compiler = BBLVMCompiler()
        bytecode = compiler.compile(ast)
        
        vm = BBVM()
        vm.execute(bytecode)
        
        self.assertIn("Malaki", vm.output_buffer)
        self.assertNotIn("Maliit", vm.output_buffer)

if __name__ == "__main__":
    unittest.main()
