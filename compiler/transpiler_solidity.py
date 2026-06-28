from compiler.ast import (
    ASTVisitor, Program, ContractDecl, VarDecl, Param, FuncDecl, Block,
    AssignStmt, IfStmt, WhileStmt, ReturnStmt, ExprStmt,
    BinaryExpr, UnaryExpr, CallExpr, MemberExpr, Identifier, Literal
)

class SolidityTranspiler(ASTVisitor):
    def __init__(self):
        self.indent_level = 0
        self.current_state_vars = set()
        self.state_var_types = {}    # var_name -> type_ann
        self.scopes = []             # Stack of dicts: var_name -> type_ann
        self.inside_class = False
        self.inside_function = False
        self.needs_console_import = False
        self.declared_contracts = set()

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

    def get_type_of_identifier(self, name: str) -> str:
        # Search local scopes
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        # Search state variables
        if name in self.state_var_types:
            return self.state_var_types[name]
        return ""

    def get_expression_type(self, node) -> str:
        if isinstance(node, Literal):
            return node.value_type
        if isinstance(node, Identifier):
            return self.get_type_of_identifier(node.name)
        if isinstance(node, CallExpr):
            if isinstance(node.callee, Identifier):
                if node.callee.name in self.declared_contracts:
                    return node.callee.name
        return ""

    # --- Type Mapping ---

    def map_type(self, type_ann: str, is_local_or_param: bool = False) -> str:
        if not type_ann:
            return "uint256" # Default fallback
            
        types = {
            'buo': 'uint256',
            'teksto': 'string memory' if is_local_or_param else 'string',
            'kondisyon': 'bool',
            'alamat': 'address',
            'wala': 'void'
        }
        return types.get(type_ann, type_ann)

    # --- State Modification Checker ---

    def check_state_modification(self, node) -> bool:
        """Walks AST node recursively to check if any state variable is modified."""
        if node is None:
            return False
            
        if isinstance(node, AssignStmt):
            # If target is Identifier, check if it's a state variable
            if isinstance(node.target, Identifier):
                if node.target.name in self.current_state_vars:
                    return True
            return self.check_state_modification(node.target) or self.check_state_modification(node.value)
            
        if isinstance(node, Block):
            return any(self.check_state_modification(stmt) for stmt in node.statements)
            
        if isinstance(node, IfStmt):
            return (self.check_state_modification(node.condition) or 
                    self.check_state_modification(node.then_branch) or 
                    (self.check_state_modification(node.else_branch) if node.else_branch else False))
                    
        if isinstance(node, WhileStmt):
            return self.check_state_modification(node.condition) or self.check_state_modification(node.body)
            
        if isinstance(node, ExprStmt):
            return self.check_state_modification(node.expression)
            
        if isinstance(node, CallExpr):
            # We assume calls don't modify state unless they are state-modifying.
            # In a basic check, we just check arguments.
            return any(self.check_state_modification(arg) for arg in node.arguments)
            
        return False

    # --- Visitor Methods ---

    def visit_program(self, node: Program) -> str:
        self.declared_contracts = set()
        for decl in node.declarations:
            if isinstance(decl, ContractDecl):
                self.declared_contracts.add(decl.name)

        # First scan for debug print to decide if hardhat/console.sol import is needed
        self.needs_console_import = self.scan_for_print(node)

        contract_decls = [d for d in node.declarations if isinstance(d, ContractDecl)]
        other_decls = [d for d in node.declarations if not isinstance(d, ContractDecl)]

        code_parts = []
        for decl in contract_decls:
            code_parts.append(self.visit(decl))

        if other_decls:
            main_methods = [d for d in other_decls if isinstance(d, FuncDecl)]
            main_statements = [d for d in other_decls if not isinstance(d, FuncDecl)]

            main_code = "contract Main {\n"
            self.indent_level += 1

            for method in main_methods:
                main_code += self.visit(method) + "\n\n"

            if main_statements:
                main_code += f"{self.indent()}function run() public {{\n"
                self.indent_level += 1
                for stmt in main_statements:
                    stmt_val = self.visit(stmt)
                    if stmt_val:
                        if not stmt_val.endswith(';') and not stmt_val.endswith('}'):
                            stmt_val += ';'
                        main_code += f"{self.indent()}{stmt_val}\n"
                self.indent_level -= 1
                main_code += f"{self.indent()}}}\n"

            self.indent_level -= 1
            main_code += "}"
            code_parts.append(main_code)

        header = "// SPDX-License-Identifier: MIT\n"
        header += "pragma solidity ^0.8.0;\n\n"
        if self.needs_console_import:
            header += "import \"hardhat/console.sol\";\n\n"
            
        return header + "\n\n".join(part for part in code_parts if part)

    def scan_for_print(self, node) -> bool:
        """Helper to scan if the program calls 'ipakita'."""
        if node is None:
            return False
        if isinstance(node, Program):
            return any(self.scan_for_print(decl) for decl in node.declarations)
        if isinstance(node, ContractDecl):
            return any(self.scan_for_print(member) for member in node.members)
        if isinstance(node, FuncDecl):
            return self.scan_for_print(node.body)
        if isinstance(node, Block):
            return any(self.scan_for_print(stmt) for stmt in node.statements)
        if isinstance(node, IfStmt):
            return (self.scan_for_print(node.condition) or 
                    self.scan_for_print(node.then_branch) or 
                    (self.scan_for_print(node.else_branch) if node.else_branch else False))
        if isinstance(node, WhileStmt):
            return self.scan_for_print(node.condition) or self.scan_for_print(node.body)
        if isinstance(node, ExprStmt):
            return self.scan_for_print(node.expression)
        if isinstance(node, AssignStmt):
            return self.scan_for_print(node.value)
        if isinstance(node, CallExpr):
            if isinstance(node.callee, Identifier) and node.callee.name == 'ipakita':
                return True
            return any(self.scan_for_print(arg) for arg in node.arguments)
        return False

    def visit_contract_decl(self, node: ContractDecl) -> str:
        class_name = node.name
        self.current_state_vars = set()
        self.state_var_types = {}
        self.inside_class = True
        
        # Gather state variables and their types
        for member in node.members:
            if isinstance(member, VarDecl):
                self.current_state_vars.add(member.name)
                # Infer type if not explicitly annotated
                inferred_type = member.type_ann
                if not inferred_type and member.initializer:
                    inferred_type = self.get_expression_type(member.initializer)
                if not inferred_type:
                    inferred_type = 'buo' # Default fallback
                self.state_var_types[member.name] = inferred_type

        code = f"contract {class_name} {{\n"
        self.indent_level += 1

        fields = [m for m in node.members if isinstance(m, VarDecl)]
        methods = [m for m in node.members if isinstance(m, FuncDecl)]

        # Class level variables
        if fields:
            for field in fields:
                # Solidity needs type and public modifier
                raw_type = self.state_var_types[field.name]
                solidity_type = self.map_type(raw_type, is_local_or_param=False)
                
                init_val = f" = {self.visit(field.initializer)}" if field.initializer else ""
                code += f"{self.indent()}{solidity_type} public {field.name}{init_val};\n"
            code += "\n"

        # Check if constructor "simulan" is explicitly defined
        has_constructor = any(m.name == 'simulan' for m in methods)
        if not has_constructor:
            # We don't necessarily generate an empty constructor in Solidity
            pass

        # Write methods
        method_codes = []
        for method in methods:
            method_codes.append(self.visit(method))
            
        code += "\n\n".join(method_codes)
        
        self.indent_level -= 1
        code += f"\n{self.indent()}}}"
        
        self.current_state_vars = set()
        self.state_var_types = {}
        self.inside_class = False
        return code

    def visit_var_decl(self, node: VarDecl) -> str:
        name = node.name
        raw_type = node.type_ann
        if not raw_type and node.initializer:
            raw_type = self.get_expression_type(node.initializer)
        if not raw_type:
            raw_type = 'buo' # Default fallback
            
        self.declare_local(name, raw_type)
        
        solidity_type = self.map_type(raw_type, is_local_or_param=True)
        init_val = f" = {self.visit(node.initializer)}" if node.initializer else ""
        
        return f"{solidity_type} {name}{init_val}"

    def visit_param(self, node: Param) -> str:
        solidity_type = self.map_type(node.type_ann, is_local_or_param=True)
        return f"{solidity_type} {node.name}"

    def visit_func_decl(self, node: FuncDecl) -> str:
        name = node.name
        is_constructor = (name == 'simulan') and self.inside_class
        
        self.enter_scope()
        self.inside_function = True
        
        # Build params
        params_str = []
        for p in node.params:
            self.declare_local(p.name, p.type_ann)
            params_str.append(self.visit(p))
            
        params_code = ", ".join(params_str)
        
        # Determine visibility and view/pure modifier
        if is_constructor:
            # Solidity constructors: `constructor(...)`
            decl_header = f"constructor({params_code})"
        else:
            # Check if function is view (does not modify state variables)
            is_view = not self.check_state_modification(node.body)
            view_modifier = " view" if is_view else ""
            
            # Return type
            ret_code = ""
            if node.return_type:
                ret_solidity_type = self.map_type(node.return_type, is_local_or_param=True)
                ret_code = f" returns ({ret_solidity_type})"
                
            decl_header = f"function {name}({params_code}) public{view_modifier}{ret_code}"

        code = f"{self.indent()}{decl_header} "
        
        # Visit function body
        body_code = self.visit(node.body).strip()
        code += body_code

        self.inside_function = False
        self.exit_scope()
        return code

    def visit_block(self, node: Block) -> str:
        self.enter_scope()
        
        code = "{\n"
        self.indent_level += 1
        
        stmt_codes = []
        for stmt in node.statements:
            stmt_val = self.visit(stmt)
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
        op = node.operator
        left_type = self.get_expression_type(node.left)
        right_type = self.get_expression_type(node.right)
        
        # Solidity string comparison handling
        if op in ('==', '!='):
            if left_type == 'teksto' or right_type == 'teksto':
                # Convert string comparison to keccak256
                left_expr = self.visit(node.left)
                right_expr = self.visit(node.right)
                
                # Check for Keccak comparison
                comp_left = f"keccak256(bytes({left_expr}))"
                comp_right = f"keccak256(bytes({right_expr}))"
                return f"({comp_left} {op} {comp_right})"
                
        left = self.visit(node.left)
        right = self.visit(node.right)
        return f"({left} {op} {right})"

    def visit_unary_expr(self, node: UnaryExpr) -> str:
        operand = self.visit(node.operand)
        return f"({node.operator}{operand})"

    def visit_call_expr(self, node: CallExpr) -> str:
        # Check for built-in print
        if isinstance(node.callee, Identifier) and node.callee.name == 'ipakita':
            args = ", ".join(self.visit(arg) for arg in node.arguments)
            # In solidity, maps to console.log (from hardhat)
            return f"console.log({args})"
            
        callee = self.visit(node.callee)
        args = ", ".join(self.visit(arg) for arg in node.arguments)
        
        # Prepend 'new' if callee is a known contract in Solidity
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
        return name

    def visit_literal(self, node: Literal) -> str:
        if node.value is True:
            return "true"
        if node.value is False:
            return "false"
        if node.value is None:
            # Solidity doesn't have null, but depending on context, address(0) or 0
            return "0"
        if node.value_type == 'teksto':
            return f'"{node.value}"'
        return str(node.value)
