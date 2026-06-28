import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Ensure the root workspace is in sys.path so we can import compiler and ai packages
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from compiler.compiler import BBLCompiler
from ai.agents.orchestrator import BBLOrchestrator

class BBLDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        web_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=web_dir, **kwargs)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/compile':
            self.handle_compile()
        elif self.path == '/api/ai':
            self.handle_ai()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_compile(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            payload = json.loads(post_data)
            code = payload.get('code', '')

            # Parse AST & run semantic checks
            from compiler.lexer import Lexer
            from compiler.parser import Parser
            from compiler.semantic import SemanticAnalyzer

            # Helper to convert AST to dict for JSON serialization
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

            # Run lexer, parser, semantic analyzer
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()

            analyzer = SemanticAnalyzer()
            analyzer.analyze(ast)

            # Transpile targets
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
            self.send_json_response(200, res_payload)

        except Exception as e:
            self.send_json_response(200, {
                "success": False,
                "error": str(e)
            })

    def handle_ai(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        try:
            payload = json.loads(post_data)
            query = payload.get('query', '')
            code = payload.get('code', '')
            selected_agent = payload.get('agent', 'orchestrator')

            orchestrator = BBLOrchestrator()
            
            if selected_agent != 'orchestrator':
                if selected_agent == 'writer':
                    res = orchestrator.writer.write(query)
                elif selected_agent == 'auditor':
                    res = orchestrator.auditor.audit(code or query)
                elif selected_agent == 'guro':
                    res = orchestrator.guro.respond(query, context_code=code)
                else:
                    res = orchestrator.explainer.explain(code or query)
                
                response_payload = {
                    "success": True,
                    "response": res,
                    "route": selected_agent,
                    "browser_used": False
                }
            else:
                details = orchestrator.route_and_resolve_detailed(query, context_code=code)
                response_payload = {
                    "success": True,
                    "response": details["response"],
                    "route": details["route"],
                    "browser_used": details["browser_used"]
                }

            self.send_json_response(200, response_payload)
        except Exception as e:
            self.send_json_response(200, {
                "success": False,
                "error": str(e)
            })

    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def start_server(port=5000):
    server = HTTPServer(('127.0.0.1', port), BBLDashboardHandler)
    print(f"BBL Playground Server running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()

if __name__ == '__main__':
    start_server()
