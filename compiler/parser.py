from typing import List, Optional, Union
from compiler.lexer import Token
from compiler.ast import (
    Program, ContractDecl, VarDecl, Param, FuncDecl, Block,
    AssignStmt, IfStmt, WhileStmt, ReturnStmt, ExprStmt,
    BinaryExpr, UnaryExpr, CallExpr, MemberExpr, Identifier, Literal, ASTNode
)

class ParserError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Parser Error at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        declarations = []
        try:
            while not self.is_at_end():
                declarations.append(self.declaration())
            return Program(declarations)
        except ParserError as e:
            raise e

    # --- AST Parsing Rules ---

    def declaration(self) -> ASTNode:
        if self.match('KONTRATA'):
            return self.contract_decl()
        if self.match('TUNGKULIN'):
            return self.func_decl()
        if self.match('ITAKDA'):
            return self.var_decl()
        return self.statement()

    def contract_decl(self) -> ContractDecl:
        name_tok = self.consume('IDENTIFIER', "Inaasahan ang pangalan ng kontrata")
        self.consume('LBRACE', "Inaasahan ang '{' bago ang katawan ng kontrata")
        members = []
        while not self.check('RBRACE') and not self.is_at_end():
            if self.match('ITAKDA'):
                members.append(self.var_decl())
            elif self.match('TUNGKULIN'):
                members.append(self.func_decl())
            else:
                tok = self.peek()
                raise ParserError(f"Di-wastong deklarasyon sa loob ng kontrata: '{tok.value}'", tok.line, tok.column)
        self.consume('RBRACE', "Inaasahan ang '}' pagkatapos ng katawan ng kontrata")
        return ContractDecl(name_tok.value, members)

    def func_decl(self) -> FuncDecl:
        name_tok = self.consume('IDENTIFIER', "Inaasahan ang pangalan ng tungkulin")
        self.consume('LPAREN', "Inaasahan ang '(' pagkatapos ng pangalan ng tungkulin")
        params = []
        if not self.check('RPAREN'):
            while True:
                p_name = self.consume('IDENTIFIER', "Inaasahan ang pangalan ng parameter")
                self.consume('COLON', "Inaasahan ang ':' pagkatapos ng pangalan ng parameter")
                # Parse type
                p_type = self.parse_type()
                params.append(Param(p_name.value, p_type))
                if not self.match('COMMA'):
                    break
        self.consume('RPAREN', "Inaasahan ang ')' pagkatapos ng mga parameter")

        is_public = False
        if self.match('IBAHAGI'):
            is_public = True

        return_type = None
        if self.match('COLON'):
            return_type = self.parse_type()

        body = self.block_statement()
        return FuncDecl(name_tok.value, params, return_type, is_public, body)

    def var_decl(self) -> VarDecl:
        name_tok = self.consume('IDENTIFIER', "Inaasahan ang pangalan ng lalagyan (variable name)")
        type_ann = None
        if self.match('COLON'):
            type_ann = self.parse_type()

        initializer = None
        if self.match('ASSIGN'):
            initializer = self.expression()

        # Optional semicolon
        self.match('SEMICOLON')
        return VarDecl(name_tok.value, type_ann, initializer)

    def parse_type(self) -> str:
        # Match built-in types or custom identifiers
        if self.match('TYPE_BUO'):
            return 'buo'
        if self.match('TYPE_TEKSTO'):
            return 'teksto'
        if self.match('TYPE_KONDISYON'):
            return 'kondisyon'
        if self.match('TYPE_ALAMAT'):
            return 'alamat'
        if self.check('IDENTIFIER'):
            return self.advance().value
        tok = self.peek()
        raise ParserError(f"Di-wastong uri (invalid type): '{tok.value}'", tok.line, tok.column)

    def statement(self) -> ASTNode:
        if self.match('KUNG'):
            return self.if_statement()
        if self.match('HABANG'):
            return self.while_statement()
        if self.match('IBALIK'):
            return self.return_statement()
        if self.check('LBRACE'):
            return self.block_statement()
        return self.expression_statement()

    def if_statement(self) -> IfStmt:
        # Optional parens around condition
        has_paren = self.match('LPAREN')
        condition = self.expression()
        if has_paren:
            self.consume('RPAREN', "Inaasahan ang ')' pagkatapos ng kondisyon")

        then_branch = self.block_statement()
        else_branch = None
        if self.match('KUNDI'):
            if self.match('KUNG'):
                else_branch = self.if_statement()
            else:
                else_branch = self.block_statement()

        return IfStmt(condition, then_branch, else_branch)

    def while_statement(self) -> WhileStmt:
        has_paren = self.match('LPAREN')
        condition = self.expression()
        if has_paren:
            self.consume('RPAREN', "Inaasahan ang ')' pagkatapos ng kondisyon")

        body = self.block_statement()
        return WhileStmt(condition, body)

    def return_statement(self) -> ReturnStmt:
        expr = None
        if not self.check('SEMICOLON') and not self.check('RBRACE') and not self.is_at_end():
            expr = self.expression()
        self.match('SEMICOLON')
        return ReturnStmt(expr)

    def block_statement(self) -> Block:
        self.consume('LBRACE', "Inaasahan ang '{' bago ang bloke ng mga pahayag")
        statements = []
        while not self.check('RBRACE') and not self.is_at_end():
            statements.append(self.declaration())
        self.consume('RBRACE', "Inaasahan ang '}' pagkatapos ng bloke")
        return Block(statements)

    def expression_statement(self) -> ASTNode:
        expr = self.expression()
        self.match('SEMICOLON')
        return ExprStmt(expr)

    # --- Expression Parsing Rules (Operator Precedence) ---

    def expression(self) -> ASTNode:
        return self.assignment()

    def assignment(self) -> ASTNode:
        expr = self.equality()
        if self.match('ASSIGN'):
            equals_tok = self.previous()
            value = self.assignment()  # Right-associative
            if isinstance(expr, (Identifier, MemberExpr)):
                return AssignStmt(expr, value)
            else:
                raise ParserError("Di-wastong pagtatalaga (invalid assignment target)", equals_tok.line, equals_tok.column)
        return expr

    def equality(self) -> ASTNode:
        expr = self.comparison()
        while self.match('EQ', 'NEQ'):
            operator = self.previous().value
            right = self.comparison()
            expr = BinaryExpr(expr, operator, right)
        return expr

    def comparison(self) -> ASTNode:
        expr = self.term()
        while self.match('LT', 'GT', 'LTE', 'GTE'):
            operator = self.previous().value
            right = self.term()
            expr = BinaryExpr(expr, operator, right)
        return expr

    def term(self) -> ASTNode:
        expr = self.factor()
        while self.match('PLUS', 'MINUS'):
            operator = self.previous().value
            right = self.factor()
            expr = BinaryExpr(expr, operator, right)
        return expr

    def factor(self) -> ASTNode:
        expr = self.unary()
        while self.match('MULTIPLY', 'DIVIDE'):
            operator = self.previous().value
            right = self.unary()
            expr = BinaryExpr(expr, operator, right)
        return expr

    def unary(self) -> ASTNode:
        if self.match('NOT', 'MINUS'):
            operator = self.previous().value
            operand = self.unary()
            return UnaryExpr(operator, operand)
        return self.call()

    def call(self) -> ASTNode:
        expr = self.primary()
        while True:
            if self.match('LPAREN'):
                args = []
                if not self.check('RPAREN'):
                    while True:
                        args.append(self.expression())
                        if not self.match('COMMA'):
                            break
                self.consume('RPAREN', "Inaasahan ang ')' pagkatapos ng mga argumento")
                expr = CallExpr(expr, args)
            elif self.match('DOT'):
                name_tok = self.consume('IDENTIFIER', "Inaasahan ang pangalan ng miyembro pagkatapos ng '.'")
                expr = MemberExpr(expr, name_tok.value)
            else:
                break
        return expr

    def primary(self) -> ASTNode:
        if self.match('TAMA'):
            return Literal(True, 'kondisyon')
        if self.match('MALI'):
            return Literal(False, 'kondisyon')
        if self.match('WALA'):
            return Literal(None, 'wala')
        if self.match('NUMBER'):
            val = self.previous().value
            num_val = float(val) if '.' in val else int(val)
            return Literal(num_val, 'numero')
        if self.match('STRING'):
            return Literal(self.previous().value, 'teksto')
        if self.match('IDENTIFIER'):
            return Identifier(self.previous().value)
        if self.match('IPAKITA'):
            return Identifier('ipakita')
        if self.match('LPAREN'):
            expr = self.expression()
            self.consume('RPAREN', "Inaasahan ang ')' pagkatapos ng ekspresyon")
            return expr

        tok = self.peek()
        raise ParserError(f"Inaasahan ang ekspresyon ngunit nakita ang: '{tok.value}' (type: {tok.type})", tok.line, tok.column)

    # --- Parser Helpers ---

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def is_at_end(self) -> bool:
        return self.peek().type == 'EOF'

    def check(self, token_type: str) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type == token_type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def match(self, *token_types: str) -> bool:
        for t in token_types:
            if self.check(t):
                self.advance()
                return True
        return False

    def consume(self, token_type: str, error_msg: str) -> Token:
        if self.check(token_type):
            return self.advance()
        tok = self.peek()
        raise ParserError(error_msg, tok.line, tok.column)
