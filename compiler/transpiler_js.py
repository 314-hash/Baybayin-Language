from compiler.ast import (
    ASTVisitor, Program, ContractDecl, VarDecl, Param, FuncDecl, Block,
    AssignStmt, IfStmt, WhileStmt, ReturnStmt, ExprStmt,
    BinaryExpr, UnaryExpr, CallExpr, MemberExpr, Identifier, Literal
)

class JsTranspiler(ASTVisitor):
    def __init__(self):
        self.indent_level = 0
        self.current_state_vars = set()
        self.scopes = []  # Stack of sets for local variable and parameter names
        self.inside_class = False
        self.declared_contracts = set()

    def indent(self) -> str:
        return "    " * self.indent_level

    def visit(self, node) -> str:
        if node is None:
            return ""
        return node.accept(self)

    # --- Scope Management Helpers ---

    def enter_scope(self):
        self.scopes.append(set())

    def exit_scope(self):
        self.scopes.pop()

    def declare_local(self, name: str):
        if self.scopes:
            self.scopes[-1].add(name)

    def is_local(self, name: str) -> bool:
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return False

    # --- Visitor Methods ---

    def visit_program(self, node: Program) -> str:
        self.declared_contracts = set()
        for decl in node.declarations:
            if isinstance(decl, ContractDecl):
                self.declared_contracts.add(decl.name)

        code_parts = []
        for decl in node.declarations:
            code_parts.append(self.visit(decl))
        return "\n\n".join(part for part in code_parts if part)

    def visit_contract_decl(self, node: ContractDecl) -> str:
        class_name = node.name
        self.current_state_vars = set()
        self.inside_class = True
        
        # Discover all state variables first
        for member in node.members:
            if isinstance(member, VarDecl):
                self.current_state_vars.add(member.name)

        code = f"class {class_name} {{\n"
        self.indent_level += 1

        fields = [m for m in node.members if isinstance(m, VarDecl)]
        methods = [m for m in node.members if isinstance(m, FuncDecl)]

        # Class level variables in modern JS
        if fields:
            for field in fields:
                init_val = self.visit(field.initializer) if field.initializer else "null"
                code += f"{self.indent()}{field.name} = {init_val};\n"
            code += "\n"

        # Check if constructor "simulan" is explicitly defined
        has_constructor = any(m.name == 'simulan' for m in methods)
        
        if not has_constructor:
            # Generate default constructor to initialize state variables
            code += f"{self.indent()}constructor() {{\n"
            self.indent_level += 1
            if fields:
                for field in fields:
                    init_val = self.visit(field.initializer) if field.initializer else "null"
                    code += f"{self.indent()}this.{field.name} = {init_val};\n"
            else:
                code += f"{self.indent()}// no-op\n"
            self.indent_level -= 1
            code += f"{self.indent()}}}\n\n"

        # Write methods
        method_codes = []
        for method in methods:
            method_codes.append(self.visit(method))
            
        code += "\n\n".join(method_codes)
        
        self.indent_level -= 1
        code += f"\n{self.indent()}}}"
        
        self.current_state_vars = set() # Reset
        self.inside_class = False
        return code

    def visit_var_decl(self, node: VarDecl) -> str:
        name = node.name
        self.declare_local(name)
        
        # If inside class definition and at class level (handled inside visit_contract_decl),
        # but if we get called elsewhere, use standard `let`.
        init_val = self.visit(node.initializer) if node.initializer else "null"
        
        # If inside a function body, prefix with let
        return f"let {name} = {init_val};"

    def visit_param(self, node: Param) -> str:
        return node.name

    def visit_func_decl(self, node: FuncDecl) -> str:
        name = node.name
        is_constructor = (name == 'simulan') and self.inside_class
        js_name = "constructor" if is_constructor else name

        self.enter_scope()
        
        # Build params
        params_str = []
        for p in node.params:
            self.declare_local(p.name)
            params_str.append(self.visit(p))
            
        params_code = ", ".join(params_str)
        
        # In JS: function keyword only if not inside a class
        prefix = "" if self.inside_class else "function "
        
        code = f"{self.indent()}{prefix}{js_name}({params_code}) "
        
        # Visit function body (which is a Block)
        # We don't indent inside Block's visit because visit_block handles braces.
        body_code = self.visit(node.body).strip()
        code += body_code

        self.exit_scope()
        return code

    def visit_block(self, node: Block) -> str:
        self.enter_scope()
        
        code = "{\n"
        self.indent_level += 1
        
        stmt_codes = []
        for stmt in node.statements:
            stmt_val = self.visit(stmt)
            # Ensure semi-colon if it is a statement
            if stmt_val and not stmt_val.endswith(';') and not stmt_val.endswith('}'):
                stmt_val += ';'
            stmt_codes.append(f"{self.indent()}{stmt_val}")
            
        code += "\n".join(stmt_codes)
        
        self.indent_level -= 1
        code += f"\n{self.indent()}}}"
        
        self.exit_scope()
        return code

    def visit_assign_stmt(self, node: AssignStmt) -> str:
        target = self.visit(node.target)
        value = self.visit(node.value)
        return f"{target} = {value}"

    def visit_if_stmt(self, node: IfStmt) -> str:
        cond = self.visit(node.condition)
        then_branch = self.visit(node.then_branch)
        
        code = f"if ({cond}) {then_branch}"
        
        if node.else_branch:
            else_code = self.visit(node.else_branch).strip()
            if isinstance(node.else_branch, IfStmt):
                # Chain elif as "else if"
                code += f" else {else_code}"
            else:
                code += f" else {else_code}"
                
        return code

    def visit_while_stmt(self, node: WhileStmt) -> str:
        cond = self.visit(node.condition)
        body = self.visit(node.body)
        return f"while ({cond}) {body}"

    def visit_return_stmt(self, node: ReturnStmt) -> str:
        if node.expression:
            return f"return {self.visit(node.expression)};"
        return "return;"

    def visit_expr_stmt(self, node: ExprStmt) -> str:
        val = self.visit(node.expression)
        if val and not val.endswith(';'):
            val += ';'
        return val

    def visit_binary_expr(self, node: BinaryExpr) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.operator
        # Convert strict equality/inequality to === and !==
        if op == '==':
            op = '==='
        elif op == '!=':
            op = '!=='
        return f"({left} {op} {right})"

    def visit_unary_expr(self, node: UnaryExpr) -> str:
        operand = self.visit(node.operand)
        return f"({node.operator}{operand})"

    def visit_call_expr(self, node: CallExpr) -> str:
        # Check for built-in print
        if isinstance(node.callee, Identifier) and node.callee.name == 'ipakita':
            args = ", ".join(self.visit(arg) for arg in node.arguments)
            return f"console.log({args})"
            
        callee = self.visit(node.callee)
        args = ", ".join(self.visit(arg) for arg in node.arguments)
        
        # Prepend 'new' if callee is a known contract
        if isinstance(node.callee, Identifier) and node.callee.name in self.declared_contracts:
            return f"new {callee}({args})"
            
        return f"{callee}({args})"

    def visit_member_expr(self, node: MemberExpr) -> str:
        obj = self.visit(node.obj)
        return f"{obj}.{node.member}"

    def visit_identifier(self, node: Identifier) -> str:
        name = node.name
        if name == 'ipakita':
            return 'console.log'
            
        # Check variable scoping
        if self.is_local(name):
            return name
        elif name in self.current_state_vars:
            return f"this.{name}"
        return name

    def visit_literal(self, node: Literal) -> str:
        if node.value is True:
            return "true"
        if node.value is False:
            return "false"
        if node.value is None:
            return "null"
        if node.value_type == 'teksto':
            return repr(node.value)
        return str(node.value)
