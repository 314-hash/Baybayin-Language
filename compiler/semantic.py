from typing import List, Dict, Any, Optional
from compiler.ast import (
    ASTVisitor, Program, ContractDecl, VarDecl, Param, FuncDecl, Block,
    AssignStmt, IfStmt, WhileStmt, ReturnStmt, ExprStmt,
    BinaryExpr, UnaryExpr, CallExpr, MemberExpr, Identifier, Literal, ASTNode
)

class SemanticError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0):
        super().__init__(f"Semantic Error at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column

class SemanticAnalyzer(ASTVisitor):
    def __init__(self):
        self.scopes: List[Dict[str, Dict[str, Any]]] = []  # Stack of symbol tables: name -> {'type': str, 'kind': str, 'params': list}
        self.contracts: Dict[str, Dict[str, Any]] = {}     # contract_name -> {'fields': {name: type}, 'methods': {name: signature}}
        self.current_contract: Optional[ContractDecl] = None
        self.current_function: Optional[FuncDecl] = None

    def analyze(self, program: Program):
        """Entry point for semantic analysis."""
        # Phase 1: Pre-pass to scan contract and top-level definitions to support forward references
        self.pre_pass(program)
        
        # Phase 2: Detailed AST analysis
        self.visit(program)

    def visit(self, node: ASTNode) -> Any:
        if node is None:
            return None
        return node.accept(self)

    # --- Scope Management ---

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare(self, name: str, type_ann: str, kind: str = "var", params: Optional[List[str]] = None, line: int = 0, col: int = 0):
        if not self.scopes:
            raise RuntimeError("No active scope")
        if name in self.scopes[-1]:
            raise SemanticError(f"Ang pangalang '{name}' ay idineklara na sa saklaw (scope) na ito.", line, col)
        self.scopes[-1][name] = {
            'type': type_ann,
            'kind': kind,
            'params': params or []
        }

    def lookup(self, name: str) -> Optional[Dict[str, Any]]:
        # 1. Search local scopes (stack)
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        
        # 2. Search current contract state if inside contract
        if self.current_contract:
            c_meta = self.contracts.get(self.current_contract.name)
            if c_meta:
                if name in c_meta['fields']:
                    return {'type': c_meta['fields'][name], 'kind': 'field'}
                if name in c_meta['methods']:
                    method_meta = c_meta['methods'][name]
                    return {
                        'type': method_meta['return_type'],
                        'kind': 'method',
                        'params': method_meta['params']
                    }
        
        # 3. Search global contracts
        if name in self.contracts:
            return {'type': name, 'kind': 'contract'}
            
        return None

    # --- Type Checking Helpers ---

    def assert_type(self, expected: str, actual: str, msg: str, line: int, col: int):
        if expected == 'any' or actual == 'any':
            return
        if expected == 'alamat' and actual == 'teksto':
            # Address literals can be written as text/strings
            return
        if expected != actual:
            raise SemanticError(f"{msg}: Inaasahan ang uri (type) na '{expected}' ngunit nakita ang '{actual}'", line, col)

    # --- Pre-Pass ---

    def pre_pass(self, program: Program):
        for decl in program.declarations:
            if isinstance(decl, ContractDecl):
                fields = {}
                methods = {}
                for member in decl.members:
                    if isinstance(member, VarDecl):
                        fields[member.name] = member.type_ann or 'any'
                    elif isinstance(member, FuncDecl):
                        methods[member.name] = {
                            'params': [p.type_ann for p in member.params],
                            'return_type': member.return_type or 'wala'
                        }
                self.contracts[decl.name] = {
                    'fields': fields,
                    'methods': methods
                }
            elif isinstance(decl, FuncDecl):
                # Top level functions
                pass

    # --- Visitor Implementations ---

    def visit_program(self, node: Program) -> Any:
        self.enter_scope()
        
        # Register global functions
        for decl in node.declarations:
            if isinstance(decl, FuncDecl):
                self.declare(
                    decl.name,
                    decl.return_type or 'wala',
                    kind='func',
                    params=[p.type_ann for p in decl.params]
                )
                
        # Visit all declarations
        for decl in node.declarations:
            self.visit(decl)
            
        self.exit_scope()

    def visit_contract_decl(self, node: ContractDecl) -> Any:
        self.current_contract = node
        self.enter_scope()

        # Gather state variables in scope
        c_meta = self.contracts[node.name]
        for field, t in c_meta['fields'].items():
            self.declare(field, t, kind='field')

        for member in node.members:
            if isinstance(member, FuncDecl):
                self.visit(member)

        self.exit_scope()
        self.current_contract = None

    def visit_var_decl(self, node: VarDecl) -> str:
        var_type = node.type_ann or 'any'
        
        if node.initializer:
            init_type = self.visit(node.initializer)
            if var_type == 'any':
                var_type = init_type
            else:
                self.assert_type(
                    var_type, init_type,
                    f"Di-tugmang uri sa pagtatalaga ng lalagyan '{node.name}'",
                    0, 0
                )
                
        self.declare(node.name, var_type)
        return var_type

    def visit_param(self, node: Param) -> str:
        self.declare(node.name, node.type_ann, kind='param')
        return node.type_ann

    def visit_func_decl(self, node: FuncDecl) -> Any:
        self.current_function = node
        self.enter_scope()

        for param in node.params:
            self.visit(param)

        self.visit(node.body)

        self.exit_scope()
        self.current_function = None

    def visit_block(self, node: Block) -> Any:
        self.enter_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self.exit_scope()

    def visit_assign_stmt(self, node: AssignStmt) -> Any:
        target_type = self.visit(node.target)
        value_type = self.visit(node.value)
        self.assert_type(
            target_type, value_type,
            "Di-tugmang uri sa pagtatalaga ng halaga (assignment type mismatch)",
            0, 0
        )

    def visit_if_stmt(self, node: IfStmt) -> Any:
        cond_type = self.visit(node.condition)
        self.assert_type(
            'kondisyon', cond_type,
            "Ang kondisyon sa 'kung' ay dapat isang boolean",
            0, 0
        )
        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_while_stmt(self, node: WhileStmt) -> Any:
        cond_type = self.visit(node.condition)
        self.assert_type(
            'kondisyon', cond_type,
            "Ang kondisyon sa 'habang' ay dapat isang boolean",
            0, 0
        )
        self.visit(node.body)

    def visit_return_stmt(self, node: ReturnStmt) -> Any:
        ret_type = 'wala'
        if node.expression:
            ret_type = self.visit(node.expression)
            
        if self.current_function:
            expected_ret = self.current_function.return_type or 'wala'
            self.assert_type(
                expected_ret, ret_type,
                f"Ang ibinabalik na halaga sa tungkulin '{self.current_function.name}' ay di-tugma",
                0, 0
            )
        return ret_type

    def visit_expr_stmt(self, node: ExprStmt) -> Any:
        self.visit(node.expression)

    def visit_binary_expr(self, node: BinaryExpr) -> str:
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        op = node.operator

        if op == '+':
            # String concatenation (coerced) or addition
            if left_type == 'teksto' or right_type == 'teksto':
                return 'teksto'
            self.assert_type('buo', left_type, "Kailangan ng buo para sa aritmetikong '+'", 0, 0)
            self.assert_type('buo', right_type, "Kailangan ng buo para sa aritmetikong '+'", 0, 0)
            return 'buo'
            
        if op in ('-', '*', '/'):
            self.assert_type('buo', left_type, f"Kailangan ng buo para sa '{op}'", 0, 0)
            self.assert_type('buo', right_type, f"Kailangan ng buo para sa '{op}'", 0, 0)
            return 'buo'
            
        if op in ('<', '>', '<=', '>='):
            self.assert_type('buo', left_type, f"Kailangan ng buo para sa '{op}'", 0, 0)
            self.assert_type('buo', right_type, f"Kailangan ng buo para sa '{op}'", 0, 0)
            return 'kondisyon'
            
        if op in ('==', '!='):
            self.assert_type(left_type, right_type, "Kailangan magkatugma ang uri sa paghahambing", 0, 0)
            return 'kondisyon'

        return 'any'

    def visit_unary_expr(self, node: UnaryExpr) -> str:
        operand_type = self.visit(node.operand)
        op = node.operator

        if op == '!':
            self.assert_type('kondisyon', operand_type, "Kailangan ng kondisyon para sa operator na '!'", 0, 0)
            return 'kondisyon'
        if op == '-':
            self.assert_type('buo', operand_type, "Kailangan ng buo para sa operator na '-'", 0, 0)
            return 'buo'
            
        return 'any'

    def visit_call_expr(self, node: CallExpr) -> str:
        callee_type = 'any'
        
        # Check constructor call
        if isinstance(node.callee, Identifier):
            name = node.callee.name
            sym = self.lookup(name)
            
            # Case A: Contract constructor call
            if sym and sym['kind'] == 'contract':
                # Check constructor parameters in simulan
                c_meta = self.contracts[name]
                constructor_params = []
                if 'simulan' in c_meta['methods']:
                    constructor_params = c_meta['methods']['simulan']['params']
                
                if len(constructor_params) != len(node.arguments):
                    raise SemanticError(
                        f"Maling bilang ng mga argumento sa kontrata '{name}': "
                        f"Inaasahan ang {len(constructor_params)} ngunit nakita ang {len(node.arguments)}",
                        0, 0
                    )
                
                for i, arg in enumerate(node.arguments):
                    arg_type = self.visit(arg)
                    self.assert_type(
                        constructor_params[i], arg_type,
                        f"Maling uri sa argumento {i+1} ng kontrata '{name}'",
                        0, 0
                    )
                return name
                
            # Case B: Standard function call
            elif sym and sym['kind'] in ('func', 'method'):
                expected_params = sym['params']
                if len(expected_params) != len(node.arguments):
                    raise SemanticError(
                        f"Maling bilang ng mga argumento sa tungkulin '{name}': "
                        f"Inaasahan ang {len(expected_params)} ngunit nakita ang {len(node.arguments)}",
                        0, 0
                    )
                for i, arg in enumerate(node.arguments):
                    arg_type = self.visit(arg)
                    self.assert_type(
                        expected_params[i], arg_type,
                        f"Maling uri sa argumento {i+1} ng tungkulin '{name}'",
                        0, 0
                    )
                return sym['type']
                
            elif name == 'ipakita':
                # Built-in print supports any type
                for arg in node.arguments:
                    self.visit(arg)
                return 'wala'
                
        # Case C: Method member call (e.g. obj.method())
        elif isinstance(node.callee, MemberExpr):
            obj_type = self.visit(node.callee.obj)
            method_name = node.callee.member
            
            if obj_type in self.contracts:
                c_meta = self.contracts[obj_type]
                if method_name in c_meta['methods']:
                    sig = c_meta['methods'][method_name]
                    expected_params = sig['params']
                    
                    if len(expected_params) != len(node.arguments):
                        raise SemanticError(
                            f"Maling bilang ng mga argumento sa paraan (method) '{method_name}' ng kontrata '{obj_type}'",
                            0, 0
                        )
                    for i, arg in enumerate(node.arguments):
                        arg_type = self.visit(arg)
                        self.assert_type(
                            expected_params[i], arg_type,
                            f"Maling uri sa argumento {i+1} ng paraan '{method_name}'",
                            0, 0
                        )
                    return sig['return_type']
                else:
                    raise SemanticError(
                        f"Walang paraan (method) na '{method_name}' sa kontrata '{obj_type}'",
                        0, 0
                    )
                    
        return 'any'

    def visit_member_expr(self, node: MemberExpr) -> str:
        obj_type = self.visit(node.obj)
        member = node.member

        if obj_type in self.contracts:
            c_meta = self.contracts[obj_type]
            if member in c_meta['fields']:
                return c_meta['fields'][member]
            if member in c_meta['methods']:
                return c_meta['methods'][member]['return_type']
            raise SemanticError(
                f"Walang miyembro (member) na '{member}' sa kontrata '{obj_type}'",
                0, 0
            )
        return 'any'

    def visit_identifier(self, node: Identifier) -> str:
        sym = self.lookup(node.name)
        if not sym:
            raise SemanticError(
                f"Ang pangalang '{node.name}' ay hindi pa idinedeklara sa saklaw na ito (undeclared variable).",
                0, 0
            )
        return sym['type']

    def visit_literal(self, node: Literal) -> str:
        if node.value_type == 'numero':
            return 'buo'
        return node.value_type
