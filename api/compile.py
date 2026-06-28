from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add workspace root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer
from compiler.compiler import BBLCompiler

def ast_to_dict(node):
    if node is None:
        return None
    result = {"node_type": node.__class__.__name__}
    for k, v in node.__dict__.items():
        if isinstance(v, list):
            result[k] = [ast_to_dict(item) for item in v]
        elif hasattr(v, '__dict__'):
            result[k] = ast_to_dict(v)
        else:
            result[k] = v
    return result

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            payload = json.loads(post_data)
            code = payload.get('code', '')

            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()

            analyzer = SemanticAnalyzer()
            analyzer.analyze(ast)

            compiler = BBLCompiler()
            py_code = compiler.transpile(code, 'python')
            js_code = compiler.transpile(code, 'js')
            sol_code = compiler.transpile(code, 'solidity')

            res_payload = {
                "success": True,
                "python": py_code,
                "javascript": js_code,
                "solidity": sol_code,
                "ast": ast_to_dict(ast)
            }
            status = 200
        except Exception as e:
            res_payload = {
                "success": False,
                "error": str(e)
            }
            status = 200

        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(res_payload).encode('utf-8'))
