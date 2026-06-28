from typing import List, Dict, Any, Tuple
from compiler.ast import (
    ASTVisitor, Program, ContractDecl, VarDecl, Param, FuncDecl, Block,
    AssignStmt, IfStmt, WhileStmt, ReturnStmt, ExprStmt,
    BinaryExpr, UnaryExpr, CallExpr, MemberExpr, Identifier, Literal, ASTNode
)
from compiler.instructions import OpCode

class BBLVMCompiler(ASTVisitor):
    def __init__(self):
        self.instructions: List[Tuple[str, Any]] = []
        self.functions: Dict[str, Dict[str, Any]] = {}  # func_name -> {"params": List[str], "code": List[Tuple[str, Any]]}
        self.contracts: Dict[str, Dict[str, Any]] = {}  # contract_name -> {"fields": List[str], "methods": Dict}

    def compile(self, program: Program) -> Dict[str, Any]:
        """Compiles a Program AST to BBVM Bytecode JSON-compatible layout."""
        self.instructions = []
        self.functions = {}
        
        # 1. Compile top-level code (placed into a __main__ entry point)
        for decl in program.declarations:
            if isinstance(decl, FuncDecl):
                # Compile function decl separately
                func_compiler = BBLVMCompiler()
                func_compiler.compile_function(decl)
                self.functions[decl.name] = {
                    "params": [p.name for p in decl.params],
                    "code": func_compiler.instructions
                }
            elif isinstance(decl, ContractDecl):
                # Compile contract methods and fields
                fields = {}
                methods = {}
                for member in decl.members:
                    if isinstance(member, VarDecl):
                        val = None
                        if member.initializer and isinstance(member.initializer, Literal):
                            val = member.initializer.value
                        fields[member.name] = val
                
                # Set fields for method compiler
                self.current_contract_fields = list(fields.keys())
                
                for member in decl.members:
                    if isinstance(member, FuncDecl):
                        func_compiler = BBLVMCompiler()
                        func_compiler.current_contract_fields = list(fields.keys())
                        func_compiler.compile_function(member)
                        methods[member.name] = {
                            "params": [p.name for p in member.params],
                            "code": func_compiler.instructions
                        }
                self.contracts[decl.name] = {
                    "fields": fields,
                    "methods": methods
                }
                self.current_contract_fields = []
            else:
                # Compile top-level statements into __main__
                self.visit(decl)
                
        # Emit HALT at the end of __main__
        self.emit(OpCode.HALT)
        
        return {
            "entry": "__main__",
            "main_code": self.instructions,
            "functions": self.functions,
            "contracts": self.contracts
        }

    def compile_function(self, node: FuncDecl):
        """Compiles a single function declaration's body."""
        for stmt in node.body.statements:
            self.visit(stmt)
            
        # Ensure return is always emitted at the end of function
        if not self.instructions or self.instructions[-1][0] != OpCode.RETURN_VALUE:
            self.emit(OpCode.LOAD_CONST, None)
            self.emit(OpCode.RETURN_VALUE)

    def visit(self, node: ASTNode) -> Any:
        if node is None:
            return
        node.accept(self)

    # --- Bytecode Generation Helpers ---

    def emit(self, opcode: str, arg: Any = None):
        self.instructions.append((opcode, arg))

    def current_index(self) -> int:
        return len(self.instructions)

    def patch(self, index: int, new_arg: Any):
        op, _ = self.instructions[index]
        self.instructions[index] = (op, new_arg)

    # --- Visitor Methods ---

    def visit_program(self, node: Program) -> Any:
        # Program node handled directly in compile()
        pass

    def visit_contract_decl(self, node: ContractDecl) -> Any:
        # ContractDecl node handled directly in compile()
        pass

    def visit_var_decl(self, node: VarDecl) -> Any:
        if node.initializer:
            self.visit(node.initializer)
        else:
            self.emit(OpCode.LOAD_CONST, None)
        self.emit(OpCode.STORE_FAST, node.name)

    def visit_param(self, node: Param) -> Any:
        pass

    def visit_func_decl(self, node: FuncDecl) -> Any:
        # FuncDecl compiled separately
        pass

    def visit_block(self, node: Block) -> Any:
        for stmt in node.statements:
            self.visit(stmt)

    def visit_assign_stmt(self, node: AssignStmt) -> Any:
        self.visit(node.value)
        if isinstance(node.target, Identifier):
            self.emit(OpCode.STORE_FAST, node.target.name)
        elif isinstance(node.target, MemberExpr):
            # Member expression assignment
            self.visit(node.target.obj)
            self.emit(OpCode.STORE_GLOBAL, node.target.member)  # Simplified: set member on object

    def visit_if_stmt(self, node: IfStmt) -> Any:
        self.visit(node.condition)
        
        # Emit JUMP_IF_FALSE with placeholder index
        jump_false_idx = self.current_index()
        self.emit(OpCode.JUMP_IF_FALSE, 0)
        
        # Visit then branch
        self.visit(node.then_branch)
        
        if node.else_branch:
            # Emit JUMP to skip else branch
            jump_end_idx = self.current_index()
            self.emit(OpCode.JUMP, 0)
            
            # Patch JUMP_IF_FALSE to jump to else branch start
            self.patch(jump_false_idx, self.current_index())
            
            # Visit else branch
            self.visit(node.else_branch)
            
            # Patch JUMP to point to end of else branch
            self.patch(jump_end_idx, self.current_index())
        else:
            # Patch JUMP_IF_FALSE to jump to instruction after then branch
            self.patch(jump_false_idx, self.current_index())

    def visit_while_stmt(self, node: WhileStmt) -> Any:
        start_idx = self.current_index()
        
        # Evaluate condition
        self.visit(node.condition)
        
        # Emit JUMP_IF_FALSE placeholder
        jump_false_idx = self.current_index()
        self.emit(OpCode.JUMP_IF_FALSE, 0)
        
        # Visit body
        self.visit(node.body)
        
        # Loop back
        self.emit(OpCode.JUMP, start_idx)
        
        # Patch exit JUMP
        self.patch(jump_false_idx, self.current_index())

    def visit_return_stmt(self, node: ReturnStmt) -> Any:
        if node.expression:
            self.visit(node.expression)
        else:
            self.emit(OpCode.LOAD_CONST, None)
        self.emit(OpCode.RETURN_VALUE)

    def visit_expr_stmt(self, node: ExprStmt) -> Any:
        self.visit(node.expression)

    def visit_binary_expr(self, node: BinaryExpr) -> Any:
        self.visit(node.left)
        self.visit(node.right)
        
        op = node.operator
        if op == '+':
            self.emit(OpCode.BINARY_ADD)
        elif op == '-':
            self.emit(OpCode.BINARY_SUB)
        elif op == '*':
            self.emit(OpCode.BINARY_MUL)
        elif op == '/':
            self.emit(OpCode.BINARY_DIV)
        elif op in ('<', '>', '<=', '>=', '==', '!='):
            self.emit(OpCode.COMPARE_OP, op)

    def visit_unary_expr(self, node: UnaryExpr) -> Any:
        self.visit(node.operand)
        op = node.operator
        if op == '-':
            # Unary minus implemented as multiplying by -1
            self.emit(OpCode.LOAD_CONST, -1)
            self.emit(OpCode.BINARY_MUL)
        elif op == '!':
            # Unary negation implemented as checking equality with False
            self.emit(OpCode.LOAD_CONST, False)
            self.emit(OpCode.COMPARE_OP, '==')

    def visit_call_expr(self, node: CallExpr) -> Any:
        # Handle built-in ipakita
        if isinstance(node.callee, Identifier) and node.callee.name == "ipakita":
            for arg in node.arguments:
                self.visit(arg)
            self.emit(OpCode.PRINT, len(node.arguments))
        elif isinstance(node.callee, MemberExpr):
            # Method call on object
            for arg in node.arguments:
                self.visit(arg)
            self.visit(node.callee.obj)
            self.emit(OpCode.CALL_METHOD, (node.callee.member, len(node.arguments)))
        else:
            # Standard call (global function or constructor)
            for arg in node.arguments:
                self.visit(arg)
                
            if isinstance(node.callee, Identifier):
                self.emit(OpCode.LOAD_GLOBAL, node.callee.name)
            else:
                self.visit(node.callee)
                
            self.emit(OpCode.CALL_FUNCTION, len(node.arguments))

    def visit_member_expr(self, node: MemberExpr) -> Any:
        self.visit(node.obj)
        self.emit(OpCode.LOAD_ATTR, node.member)

    def visit_identifier(self, node: Identifier) -> Any:
        # Load local or global variable (dynamic check in VM)
        if hasattr(self, 'current_contract_fields') and self.current_contract_fields and node.name in self.current_contract_fields:
            self.emit(OpCode.LOAD_FAST, "self")
            self.emit(OpCode.LOAD_ATTR, node.name)
        else:
            self.emit(OpCode.LOAD_FAST, node.name)

    def visit_literal(self, node: Literal) -> Any:
        self.emit(OpCode.LOAD_CONST, node.value)

    def visit_assign_stmt(self, node: AssignStmt) -> Any:
        if isinstance(node.target, Identifier):
            if hasattr(self, 'current_contract_fields') and self.current_contract_fields and node.target.name in self.current_contract_fields:
                self.visit(node.value)
                self.emit(OpCode.LOAD_FAST, "self")
                self.emit(OpCode.STORE_ATTR, node.target.name)
            else:
                self.visit(node.value)
                self.emit(OpCode.STORE_FAST, node.target.name)
        elif isinstance(node.target, MemberExpr):
            self.visit(node.value)
            self.visit(node.target.obj)
            self.emit(OpCode.STORE_ATTR, node.target.member)
