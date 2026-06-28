from compiler.ast import (
    ASTVisitor, Program, ContractDecl, VarDecl, Param, FuncDecl, Block,
    AssignStmt, IfStmt, WhileStmt, ReturnStmt, ExprStmt,
    BinaryExpr, UnaryExpr, CallExpr, MemberExpr, Identifier, Literal
)

class PythonTranspiler(ASTVisitor):
    def __init__(self):
        self.indent_level = 0
        self.current_state_vars = set()
        self.state_var_types = {}
        self.scopes = []  # Stack of dicts: var_name -> type_ann

    def indent(self) -> str:
        return "    " * self.indent_level

    def visit(self, node) -> str:
        if node is None:
            return ""
        return node.accept(self)

    # --- Scope Management Helpers ---

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare_local(self, name: str, type_ann: str):
        if self.scopes:
            self.scopes[-1][name] = type_ann

    def is_local(self, name: str) -> bool:
        for scope in reversed(self.scopes):
            if name in scope:
                return True
        return False

    def get_type_of_identifier(self, name: str) -> str:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        if name in self.state_var_types:
            return self.state_var_types[name]
        return ""

    def get_expression_type(self, node) -> str:
        if isinstance(node, Literal):
            return node.value_type
        if isinstance(node, Identifier):
            return self.get_type_of_identifier(node.name)
        return ""

    # --- Type Mapping ---

    def map_type(self, type_ann: str) -> str:
        types = {
            'buo': 'int',
            'teksto': 'str',
            'kondisyon': 'bool',
            'alamat': 'str',
            'wala': 'None'
        }
        return types.get(type_ann, type_ann)

    # --- Visitor Methods ---

    def visit_program(self, node: Program) -> str:
        code_parts = []
        for decl in node.declarations:
            code_parts.append(self.visit(decl))
        return "\n\n".join(part for part in code_parts if part)

    def visit_contract_decl(self, node: ContractDecl) -> str:
        class_name = node.name
        self.current_state_vars = set()
        self.state_var_types = {}
        
        # Discover all state variables first
        for member in node.members:
            if isinstance(member, VarDecl):
                self.current_state_vars.add(member.name)
                # Store type
                inferred_type = member.type_ann
                if not inferred_type and member.initializer:
                    if isinstance(member.initializer, Literal):
                        inferred_type = member.initializer.value_type
                if not inferred_type:
                    inferred_type = 'buo'
                self.state_var_types[member.name] = inferred_type

        code = f"class {class_name}:\n"
        self.indent_level += 1

        # We will separate fields and methods
        fields = [m for m in node.members if isinstance(m, VarDecl)]
        methods = [m for m in node.members if isinstance(m, FuncDecl)]

        # Class level type annotations/defaults if any
        if fields:
            for field in fields:
                field_type = f": {self.map_type(field.type_ann)}" if field.type_ann else ""
                init_val = self.visit(field.initializer) if field.initializer else "None"
                code += f"{self.indent()}{field.name}{field_type} = {init_val}\n"
            code += "\n"

        # Check if constructor "simulan" is explicitly defined
        has_constructor = any(m.name == 'simulan' for m in methods)
        
        if not has_constructor:
            # Generate default __init__ to initialize state variables on self
            code += f"{self.indent()}def __init__(self):\n"
            self.indent_level += 1
            if fields:
                for field in fields:
                    init_val = self.visit(field.initializer) if field.initializer else "None"
                    code += f"{self.indent()}self.{field.name} = {init_val}\n"
            else:
                code += f"{self.indent()}pass\n"
            self.indent_level -= 1
            code += "\n"

        # Write methods
        method_codes = []
        for method in methods:
            method_codes.append(self.visit(method))
            
        code += "\n\n".join(method_codes)
        self.indent_level -= 1
        
        self.current_state_vars = set() # Reset
        return code

    def visit_var_decl(self, node: VarDecl) -> str:
        # If in local scope, generate assignment
        name = node.name
        raw_type = node.type_ann
        if not raw_type and node.initializer:
            if isinstance(node.initializer, Literal):
                raw_type = node.initializer.value_type
        if not raw_type:
            raw_type = 'buo'
        self.declare_local(name, raw_type)
        
        type_hint = f": {self.map_type(node.type_ann)}" if node.type_ann else ""
        init_val = self.visit(node.initializer) if node.initializer else "None"
        
        return f"{name}{type_hint} = {init_val}"

    def visit_param(self, node: Param) -> str:
        type_hint = f": {self.map_type(node.type_ann)}" if node.type_ann else ""
        return f"{node.name}{type_hint}"

    def visit_func_decl(self, node: FuncDecl) -> str:
        name = node.name
        # If inside a contract and name is "simulan", translate to __init__
        is_constructor = (name == 'simulan')
        py_name = "__init__" if is_constructor else name

        self.enter_scope()
        
        # Build params
        params_str = ["self"]
        for p in node.params:
            self.declare_local(p.name, p.type_ann)
            params_str.append(self.visit(p))
            
        params_code = ", ".join(params_str)
        
        ret_hint = ""
        if not is_constructor:
            ret_type = self.map_type(node.return_type) if node.return_type else "None"
            ret_hint = f" -> {ret_type}"

        code = f"{self.indent()}def {py_name}({params_code}){ret_hint}:\n"
        self.indent_level += 1
        
        # If it is the constructor, we should also write initializations for state variables that aren't inside fields,
        # or we just let it execute.
        # Let's check body statements
        body_code = ""
        if not node.body.statements:
            body_code = f"{self.indent()}pass"
        else:
            stmt_codes = []
            for stmt in node.body.statements:
                stmt_codes.append(f"{self.indent()}{self.visit(stmt)}")
            body_code = "\n".join(stmt_codes)

        code += body_code
        self.indent_level -= 1
        self.exit_scope()
        return code

    def visit_block(self, node: Block) -> str:
        # Blocks are visited within IfStmt, WhileStmt, etc.
        self.enter_scope()
        stmt_codes = []
        for stmt in node.statements:
            stmt_codes.append(f"{self.indent()}{self.visit(stmt)}")
        
        if not stmt_codes:
            stmt_codes.append(f"{self.indent()}pass")
            
        self.exit_scope()
        return "\n".join(stmt_codes)

    def visit_assign_stmt(self, node: AssignStmt) -> str:
        target = self.visit(node.target)
        value = self.visit(node.value)
        return f"{target} = {value}"

    def visit_if_stmt(self, node: IfStmt) -> str:
        cond = self.visit(node.condition)
        
        code = f"if {cond}:\n"
        self.indent_level += 1
        code += self.visit(node.then_branch)
        self.indent_level -= 1
        
        if node.else_branch:
            if isinstance(node.else_branch, IfStmt):
                # elif branch
                self.indent_level += 1
                # Remove indent prefix since we chain it as 'elif'
                elif_code = self.visit(node.else_branch).strip()
                self.indent_level -= 1
                code += f"\n{self.indent()}el{elif_code}"
            else:
                code += f"\n{self.indent()}else:\n"
                self.indent_level += 1
                code += self.visit(node.else_branch)
                self.indent_level -= 1
                
        return code

    def visit_while_stmt(self, node: WhileStmt) -> str:
        cond = self.visit(node.condition)
        code = f"while {cond}:\n"
        self.indent_level += 1
        code += self.visit(node.body)
        self.indent_level -= 1
        return code

    def visit_return_stmt(self, node: ReturnStmt) -> str:
        if node.expression:
            return f"return {self.visit(node.expression)}"
        return "return"

    def visit_expr_stmt(self, node: ExprStmt) -> str:
        return self.visit(node.expression)

    def visit_binary_expr(self, node: BinaryExpr) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.operator
        
        if op == '+':
            left_type = self.get_expression_type(node.left)
            right_type = self.get_expression_type(node.right)
            if left_type == 'teksto' or right_type == 'teksto':
                left_expr = left if left_type == 'teksto' and isinstance(node.left, Literal) else f"str({left})"
                right_expr = right if right_type == 'teksto' and isinstance(node.right, Literal) else f"str({right})"
                return f"({left_expr} + {right_expr})"
                
        return f"({left} {op} {right})"

    def visit_unary_expr(self, node: UnaryExpr) -> str:
        op = 'not ' if node.operator == '!' else node.operator
        operand = self.visit(node.operand)
        return f"({op}{operand})"

    def visit_call_expr(self, node: CallExpr) -> str:
        # Check for built-in prints
        if isinstance(node.callee, Identifier) and node.callee.name == 'ipakita':
            args = ", ".join(self.visit(arg) for arg in node.arguments)
            return f"print({args})"
            
        callee = self.visit(node.callee)
        args = ", ".join(self.visit(arg) for arg in node.arguments)
        return f"{callee}({args})"

    def visit_member_expr(self, node: MemberExpr) -> str:
        obj = self.visit(node.obj)
        return f"{obj}.{node.member}"

    def visit_identifier(self, node: Identifier) -> str:
        name = node.name
        if name == 'ipakita':
            return 'print'
            
        # Check variable scoping
        if self.is_local(name):
            return name
        elif name in self.current_state_vars:
            return f"self.{name}"
        return name

    def visit_literal(self, node: Literal) -> str:
        if node.value is True:
            return "True"
        if node.value is False:
            return "False"
        if node.value is None:
            return "None"
        if node.value_type == 'teksto':
            # Escape internal quotes if needed, or represent simple repr
            return repr(node.value)
        return str(node.value)
