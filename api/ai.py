from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add workspace root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.agents.orchestrator import BBLOrchestrator

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
            status = 200
        except Exception as e:
            response_payload = {
                "success": False,
                "error": str(e)
            }
            status = 200

        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_payload).encode('utf-8'))
