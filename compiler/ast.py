from typing import List, Optional, Union, Any

class ASTNode:
    """Base class for all AST nodes in the Baybayin Language (BBL)."""
    def accept(self, visitor: 'ASTVisitor') -> Any:
        pass

class Program(ASTNode):
    def __init__(self, declarations: List[ASTNode]):
        self.declarations = declarations

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_program(self)

class ContractDecl(ASTNode):
    def __init__(self, name: str, members: List[ASTNode]):
        self.name = name
        self.members = members

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_contract_decl(self)

class VarDecl(ASTNode):
    def __init__(self, name: str, type_ann: Optional[str], initializer: Optional[ASTNode]):
        self.name = name
        self.type_ann = type_ann
        self.initializer = initializer

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_var_decl(self)

class Param(ASTNode):
    def __init__(self, name: str, type_ann: str):
        self.name = name
        self.type_ann = type_ann

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_param(self)

class FuncDecl(ASTNode):
    def __init__(self, name: str, params: List[Param], return_type: Optional[str], is_public: bool, body: 'Block'):
        self.name = name
        self.params = params
        self.return_type = return_type
        self.is_public = is_public
        self.body = body

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_func_decl(self)

class Block(ASTNode):
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_block(self)

class AssignStmt(ASTNode):
    def __init__(self, target: ASTNode, value: ASTNode):
        self.target = target
        self.value = value

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_assign_stmt(self)

class IfStmt(ASTNode):
    def __init__(self, condition: ASTNode, then_branch: Block, else_branch: Optional[Union[Block, 'IfStmt']]):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_if_stmt(self)

class WhileStmt(ASTNode):
    def __init__(self, condition: ASTNode, body: Block):
        self.condition = condition
        self.body = body

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_while_stmt(self)

class ReturnStmt(ASTNode):
    def __init__(self, expression: Optional[ASTNode]):
        self.expression = expression

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_return_stmt(self)

class ExprStmt(ASTNode):
    def __init__(self, expression: ASTNode):
        self.expression = expression

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_expr_stmt(self)

class BinaryExpr(ASTNode):
    def __init__(self, left: ASTNode, operator: str, right: ASTNode):
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_binary_expr(self)

class UnaryExpr(ASTNode):
    def __init__(self, operator: str, operand: ASTNode):
        self.operator = operator
        self.operand = operand

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_unary_expr(self)

class CallExpr(ASTNode):
    def __init__(self, callee: ASTNode, arguments: List[ASTNode]):
        self.callee = callee
        self.arguments = arguments

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_call_expr(self)

class MemberExpr(ASTNode):
    def __init__(self, obj: ASTNode, member: str):
        self.obj = obj
        self.member = member

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_member_expr(self)

class Identifier(ASTNode):
    def __init__(self, name: str):
        self.name = name

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_identifier(self)

class Literal(ASTNode):
    def __init__(self, value: Any, value_type: str):
        self.value = value
        self.value_type = value_type  # 'numero', 'teksto', 'kondisyon', 'wala'

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_literal(self)

class ASTVisitor:
    """Visitor base class for BBL AST traversal."""
    def visit_program(self, node: Program) -> Any: pass
    def visit_contract_decl(self, node: ContractDecl) -> Any: pass
    def visit_var_decl(self, node: VarDecl) -> Any: pass
    def visit_param(self, node: Param) -> Any: pass
    def visit_func_decl(self, node: FuncDecl) -> Any: pass
    def visit_block(self, node: Block) -> Any: pass
    def visit_assign_stmt(self, node: AssignStmt) -> Any: pass
    def visit_if_stmt(self, node: IfStmt) -> Any: pass
    def visit_while_stmt(self, node: WhileStmt) -> Any: pass
    def visit_return_stmt(self, node: ReturnStmt) -> Any: pass
    def visit_expr_stmt(self, node: ExprStmt) -> Any: pass
    def visit_binary_expr(self, node: BinaryExpr) -> Any: pass
    def visit_unary_expr(self, node: UnaryExpr) -> Any: pass
    def visit_call_expr(self, node: CallExpr) -> Any: pass
    def visit_member_expr(self, node: MemberExpr) -> Any: pass
    def visit_identifier(self, node: Identifier) -> Any: pass
    def visit_literal(self, node: Literal) -> Any: pass
