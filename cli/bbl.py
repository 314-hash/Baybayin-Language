import argparse
import sys
import os
import subprocess
import tempfile
import json

# Adjust path to import compiler package when running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compiler.compiler import BBLCompiler
from compiler.lexer import Lexer, LexerError
from compiler.parser import Parser, ParserError

def cmd_lex(args):
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        lexer = Lexer(content)
        tokens = lexer.tokenize()
        print(f"{'Line':<6} | {'Column':<6} | {'Type':<15} | {'Value':<30}")
        print("-" * 65)
        for tok in tokens:
            print(f"{tok.line:<6} | {tok.column:<6} | {tok.type:<15} | {repr(tok.value):<30}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_parse(args):
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        lexer = Lexer(content)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Simple recursive printer for AST
        def print_ast(node, indent=0):
            prefix = "  " * indent
            if node is None:
                print(f"{prefix}None")
                return
            
            node_name = node.__class__.__name__
            
            if node_name == "Program":
                print(f"{prefix}Program:")
                for decl in node.declarations:
                    print_ast(decl, indent + 1)
            elif node_name == "ContractDecl":
                print(f"{prefix}ContractDecl: {node.name}")
                for member in node.members:
                    print_ast(member, indent + 1)
            elif node_name == "VarDecl":
                init_str = " = ..." if node.initializer else ""
                print(f"{prefix}VarDecl: {node.name} (type: {node.type_ann or 'any'}){init_str}")
                if node.initializer:
                    print_ast(node.initializer, indent + 2)
            elif node_name == "FuncDecl":
                pub_str = " [public]" if node.is_public else ""
                ret_str = f" -> {node.return_type}" if node.return_type else ""
                print(f"{prefix}FuncDecl: {node.name}{pub_str}{ret_str}")
                if node.params:
                    print(f"{prefix}  Params:")
                    for p in node.params:
                        print(f"{prefix}    {p.name}: {p.type_ann}")
                print_ast(node.body, indent + 1)
            elif node_name == "Block":
                print(f"{prefix}Block:")
                for stmt in node.statements:
                    print_ast(stmt, indent + 1)
            elif node_name == "AssignStmt":
                print(f"{prefix}AssignStmt:")
                print_ast(node.target, indent + 1)
                print_ast(node.value, indent + 1)
            elif node_name == "IfStmt":
                print(f"{prefix}IfStmt:")
                print_ast(node.condition, indent + 1)
                print_ast(node.then_branch, indent + 1)
                if node.else_branch:
                    print(f"{prefix}Else:")
                    print_ast(node.else_branch, indent + 1)
            elif node_name == "WhileStmt":
                print(f"{prefix}WhileStmt:")
                print_ast(node.condition, indent + 1)
                print_ast(node.body, indent + 1)
            elif node_name == "ReturnStmt":
                print(f"{prefix}ReturnStmt:")
                print_ast(node.expression, indent + 1)
            elif node_name == "ExprStmt":
                print(f"{prefix}ExprStmt:")
                print_ast(node.expression, indent + 1)
            elif node_name == "BinaryExpr":
                print(f"{prefix}BinaryExpr ({node.operator}):")
                print_ast(node.left, indent + 1)
                print_ast(node.right, indent + 1)
            elif node_name == "UnaryExpr":
                print(f"{prefix}UnaryExpr ({node.operator}):")
                print_ast(node.operand, indent + 1)
            elif node_name == "CallExpr":
                print(f"{prefix}CallExpr:")
                print_ast(node.callee, indent + 1)
                for arg in node.arguments:
                    print_ast(arg, indent + 2)
            elif node_name == "MemberExpr":
                print(f"{prefix}MemberExpr: .{node.member}")
                print_ast(node.obj, indent + 1)
            elif node_name == "Identifier":
                print(f"{prefix}Identifier: {node.name}")
            elif node_name == "Literal":
                print(f"{prefix}Literal: {repr(node.value)} (type: {node.value_type})")
        
        print_ast(ast)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_transpile(args):
    compiler = BBLCompiler()
    try:
        generated_code = compiler.transpile_file(args.file, args.target)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(generated_code)
            print(f"Naisulat ang code sa: {args.output}")
        else:
            print(generated_code)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_compile(args):
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        from compiler.lexer import Lexer
        from compiler.parser import Parser
        from compiler.semantic import SemanticAnalyzer
        from compiler.vm_compiler import BBLVMCompiler
        
        lexer = Lexer(content)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        
        vm_compiler = BBLVMCompiler()
        bytecode = vm_compiler.compile(ast)
        
        output_path = args.output or args.file.replace('.bbl', '.bbv')
        with open(output_path, 'w', encoding='utf-8') as out_f:
            json.dump(bytecode, out_f, indent=2)
            
        print(f"Matagumpay na na-compile sa BBVM Bytecode: {output_path}")
    except Exception as e:
        print(f"Error compiling to VM bytecode: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_run(args):
    if args.vm:
        try:
            from runtime.vm.bbvm import BBVM
            # If the file is BBL source, compile it in memory first
            if args.file.endswith('.bbl'):
                with open(args.file, 'r', encoding='utf-8') as f:
                    content = f.read()
                from compiler.lexer import Lexer
                from compiler.parser import Parser
                from compiler.semantic import SemanticAnalyzer
                from compiler.vm_compiler import BBLVMCompiler
                
                lexer = Lexer(content)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                ast = parser.parse()
                
                analyzer = SemanticAnalyzer()
                analyzer.analyze(ast)
                
                vm_compiler = BBLVMCompiler()
                bytecode = vm_compiler.compile(ast)
            else:
                with open(args.file, 'r', encoding='utf-8') as f:
                    bytecode = json.load(f)
            
            vm = BBVM()
            vm.execute(bytecode)
            return
        except Exception as e:
            print(f"Error running on BBVM: {e}", file=sys.stderr)
            sys.exit(1)

    compiler = BBLCompiler()
    try:
        # Transpile to Python in memory
        py_code = compiler.transpile_file(args.file, 'python')
        
        # Write to temporary file and execute
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as tmp:
            tmp_name = tmp.name
            tmp.write(py_code)
            
        try:
            # Run using the current python executable
            subprocess.run([sys.executable, tmp_name], check=True)
        finally:
            # Clean up the temp file
            os.remove(tmp_name)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_ai_explain(args):
    from ai.agents.orchestrator import BBLOrchestrator
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        print("Sinisimulan ang pag-analisa...")
        agent = BBLOrchestrator()
        explanation = agent.explain(content)
        print("\n=== AI Paliwanag (Explanation) ===")
        print(explanation)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_ai_audit(args):
    from ai.agents.orchestrator import BBLOrchestrator
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        print("Sinisimulan ang pagsusuri (auditing)...")
        agent = BBLOrchestrator()
        audit_report = agent.audit(content)
        print("\n=== AI Pagsusuri (Audit Report) ===")
        print(audit_report)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_ai_write(args):
    from ai.agents.orchestrator import BBLOrchestrator
    try:
        print("Sinisimulan ang paglikha ng code...")
        agent = BBLOrchestrator()
        generated_code = agent.write(args.prompt)
        print("\n=== Inilikhang BBL Code ===")
        print(generated_code)
        if args.output:
            code_lines = []
            in_block = False
            lines = generated_code.splitlines()
            for line in lines:
                if line.startswith("```"):
                    if not in_block:
                        in_block = True
                    else:
                        in_block = False
                    continue
                if in_block:
                    code_lines.append(line)
            
            to_save = "\n".join(code_lines) if code_lines else generated_code
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(to_save)
            print(f"\nNaisulat ang inilikhang code sa: {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_ai_guro(args):
    from ai.agents.orchestrator import BBLOrchestrator
    try:
        print("Sinisimulan ang pagkonsulta sa iyong Guro (AI Tutor)...")
        orchestrator = BBLOrchestrator()
        response = orchestrator.guro.respond(args.query)
        print("\n=== Paliwanag mula sa Guro ===")
        print(response)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_dashboard(args):
    from web.server import start_server
    try:
        start_server(port=args.port)
    except Exception as e:
        print(f"Error starting dashboard: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="BBL (Baybayin Language) Compiler CLI")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-commands")

    # Dashboard subcommand
    dash_parser = subparsers.add_parser("dashboard", help="Start the BBL Playground & AI Dashboard")
    dash_parser.add_argument("-p", "--port", type=int, default=5000, help="Port to run dashboard server (default: 5000)")
    dash_parser.set_defaults(func=cmd_dashboard)

    # Transpile subcommand
    transp_parser = subparsers.add_parser("transpile", help="Transpile BBL code to target language")
    transp_parser.add_argument("file", help="Source BBL file (.bbl)")
    transp_parser.add_argument("-t", "--target", required=True, choices=["python", "js", "solidity"], help="Target language")
    transp_parser.add_argument("-o", "--output", help="Output file path")
    transp_parser.set_defaults(func=cmd_transpile)

    # Compile subcommand (BBVM Bytecode)
    compile_parser = subparsers.add_parser("compile", help="Compile BBL code to VM Bytecode (.bbv)")
    compile_parser.add_argument("file", help="Source BBL file (.bbl)")
    compile_parser.add_argument("-o", "--output", help="Output bytecode file path (.bbv)")
    compile_parser.set_defaults(func=cmd_compile)

    # Run subcommand
    run_parser = subparsers.add_parser("run", help="Run BBL file directly (via Python or VM)")
    run_parser.add_argument("file", help="Source file (.bbl or .bbv)")
    run_parser.add_argument("--vm", action="store_true", help="Run inside the Baybayin Virtual Machine (BBVM)")
    run_parser.set_defaults(func=cmd_run)

    # Lex subcommand
    lex_parser = subparsers.add_parser("lex", help="Print token stream for debugging")
    lex_parser.add_argument("file", help="Source BBL file (.bbl)")
    lex_parser.set_defaults(func=cmd_lex)

    # Parse subcommand
    parse_parser = subparsers.add_parser("parse", help="Print AST tree structure for debugging")
    parse_parser.add_argument("file", help="Source BBL file (.bbl)")
    parse_parser.set_defaults(func=cmd_parse)

    # AI subcommand
    ai_parser = subparsers.add_parser("ai", help="AI Agent commands")
    ai_subparsers = ai_parser.add_subparsers(dest="ai_command", required=True, help="AI actions")

    # AI Explain
    ai_explain_parser = ai_subparsers.add_parser("explain", help="Explain BBL code line-by-line")
    ai_explain_parser.add_argument("file", help="Source BBL file (.bbl)")
    ai_explain_parser.set_defaults(func=cmd_ai_explain)

    # AI Audit
    ai_audit_parser = ai_subparsers.add_parser("audit", help="Audit BBL code for bugs and security risks")
    ai_audit_parser.add_argument("file", help="Source BBL file (.bbl)")
    ai_audit_parser.set_defaults(func=cmd_ai_audit)

    # AI Write
    ai_write_parser = ai_subparsers.add_parser("write", help="Generate fresh BBL code from a prompt")
    ai_write_parser.add_argument("prompt", help="Natural language prompt")
    ai_write_parser.add_argument("-o", "--output", help="Output file path to save code")
    ai_write_parser.set_defaults(func=cmd_ai_write)

    # AI Guro
    ai_guro_parser = ai_subparsers.add_parser("guro", help="Ask the friendly Filipino Programming Tutor")
    ai_guro_parser.add_argument("query", help="Your programming or Baybayin question")
    ai_guro_parser.set_defaults(func=cmd_ai_guro)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
