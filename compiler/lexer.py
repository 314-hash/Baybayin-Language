import re
from typing import List, NamedTuple

class Token(NamedTuple):
    type: str
    value: str
    line: int
    column: int

class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Lexer Error at line {line}, column {column}: {message}")
        self.message = message
        self.line = line
        self.column = column

class Lexer:
    # Baybayin script is in \u1700-\u171F. Let's include that in identifier characters.
    # Note: \u1700-\u171f covers the basic alphabet, kudlits (diacritics U+1712-1714), and pamudpod (virama U+1715).
    IDENTIFIER_REGEX = r'[a-zA-Z_ᜀ-ᜟ][a-zA-Z0-9_ᜀ-ᜟ]*'

    TOKEN_SPECIFICATION = [
        ('COMMENT_MULTI',  r'/\*[\s\S]*?\*/'),
        ('COMMENT_SINGLE', r'//.*'),
        ('NUMBER',         r'\d+(\.\d+)?'),
        ('STRING',         r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\''),
        ('EQ',             r'=='),
        ('NEQ',            r'!='),
        ('LTE',            r'<='),
        ('GTE',            r'>='),
        ('LT',             r'<'),
        ('GT',             r'>'),
        ('ASSIGN',         r'='),
        ('PLUS',           r'\+'),
        ('MINUS',          r'-'),
        ('MULTIPLY',       r'\*'),
        ('DIVIDE',         r'/'),
        ('NOT',            r'!'),
        ('LPAREN',         r'\('),
        ('RPAREN',         r'\)'),
        ('LBRACE',         r'\{'),
        ('RBRACE',         r'\}'),
        ('COMMA',          r','),
        ('COLON',          r':'),
        ('SEMICOLON',      r';'),
        ('DOT',            r'\.'),
        ('IDENTIFIER',     IDENTIFIER_REGEX),
        ('NEWLINE',        r'\n'),
        ('SKIP',           r'[ \t\r]+'),
        ('MISMATCH',       r'.'),
    ]

    KEYWORDS = {
        'kontrata': 'KONTRATA',
        'tungkulin': 'TUNGKULIN',
        'itakda': 'ITAKDA',
        'ibahagi': 'IBAHAGI',
        'ibalik': 'IBALIK',
        'kung': 'KUNG',
        'kundi': 'KUNDI',
        'habang': 'HABANG',
        'tama': 'TAMA',
        'mali': 'MALI',
        'wala': 'WALA',
        'buo': 'TYPE_BUO',
        'teksto': 'TYPE_TEKSTO',
        'kondisyon': 'TYPE_KONDISYON',
        'alamat': 'TYPE_ALAMAT',
        'ipakita': 'IPAKITA',
    }

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        # Compile all regular expressions into a single master regex
        regex_parts = [f'(?P<{name}>{pattern})' for name, pattern in self.TOKEN_SPECIFICATION]
        master_regex = re.compile('|'.join(regex_parts))

        line_num = 1
        line_start = 0
        for match in master_regex.finditer(self.source_code):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - line_start + 1

            if kind == 'NEWLINE':
                line_start = match.end()
                line_num += 1
                continue
            elif kind == 'SKIP':
                continue
            elif kind in ('COMMENT_SINGLE', 'COMMENT_MULTI'):
                # Track lines inside multiline comments
                line_num += value.count('\n')
                if '\n' in value:
                    line_start = match.start() + value.rfind('\n') + 1
                continue
            elif kind == 'MISMATCH':
                raise LexerError(f"Di-kilalang karakter: '{value}'", line_num, column)
            elif kind == 'IDENTIFIER':
                # Check if it's a reserved word/keyword
                kind = self.KEYWORDS.get(value, 'IDENTIFIER')
            elif kind == 'STRING':
                # Strip the enclosing quotes
                value = value[1:-1]
                # Handle escape characters
                value = bytes(value, "utf-8").decode("unicode_escape")

            self.tokens.append(Token(kind, value, line_num, column))

        self.tokens.append(Token('EOF', '', line_num, len(self.source_code) - line_start + 1))
        return self.tokens
