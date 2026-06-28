# BBL (Baybayin Language) Compiler & Transpiler

BBL is a Tagalog-inspired, statically typed programming language designed to showcase clean compilation pipelines. It transpiles into multiple targets including **Python**, **JavaScript**, and **Solidity**.

> 📖 **Looking for a user guide?** Read the detailed [BBL AI Agent & User Guide](file:///C:/Users/janla/baybayin-language/docs/AGENT_GUIDE.md) to learn BBL syntax, CLI commands, and the AI agent system!

---

## Directory Structure

```
├── compiler/
│   ├── lexer.py                # Regex-based scanner with Baybayin Unicode support
│   ├── parser.py               # Recursive descent parser
│   ├── ast.py                  # Abstract Syntax Tree node definitions
│   ├── semantic.py             # Type-checking & scope validation compiler pass
│   ├── instructions.py         # VM OpCode instruction definitions
│   ├── vm_compiler.py          # Compiles AST down to custom VM bytecode (.bbv)
│   ├── transpiler_python.py    # Generates type-annotated, coerced Python code
│   ├── transpiler_js.py        # Generates clean, ES6-compliant JavaScript
│   ├── transpiler_solidity.py  # Generates production-ready Solidity smart contracts
│   └── compiler.py             # Orchestrates the lex-parse-semantic-transpile pipeline
│
├── runtime/
│   ├── cpp/
│   │   └── bbl_runtime.hpp     # C++ runtime headers
│   ├── python/
│   │   └── bbl_runtime.py      # Python runtime helper library
│   └── vm/
│       └── bbvm.py             # Stack-based BBVM execution engine
│
├── cli/
│   └── bbl.py                  # CLI utility for compiling and running scripts
│
├── ai/
│   ├── agents/                 # Multi-agent system folder
│   │   ├── base_agent.py       # Base model client configurations
│   │   ├── orchestrator.py     # Task router and semantic coordinator
│   │   ├── writer.py           # Specialized code generation agent
│   │   ├── auditor.py          # Type-safety & security audit agent
│   │   └── explainer.py        # Explains keywords and AST structures
│   └── guro/                   # Tagalog/Filipino Coding Tutor & Glossary
│       ├── glossary.json       # Filipino programming dictionary
│       └── guro_agent.py       # Guro agent logic class
│
├── examples/
│   └── hello.bbl               # Showcase of BBL syntax and contract compilation
│
├── tests/
│   └── test_compiler.py        # Automated test suite
│
└── README.md                   # This document
```

---

## Language Specifications

### Keywords Map

| BBL Keyword | English Equivalent | Description |
|---|---|---|
| `kontrata` | `contract` / `class` | Declares a contract or class encapsulation boundary |
| `tungkulin` | `function` / `def` | Declares a function or method |
| `itakda` | `let` / `var` | Declares a state or local variable |
| `ibahagi` | `public` / `export` | Marks a function or member as public/exported |
| `ibalik` | `return` | Returns a value from a function |
| `kung` | `if` | Conditional branch |
| `kundi` | `else` | Alternative conditional branch |
| `habang` | `while` | Loop control |
| `tama` | `true` | Boolean literal true |
| `mali` | `false` | Boolean literal false |
| `wala` | `null` / `void` | Null/empty literal |

### Built-in Types

| BBL Type | Solidity Target | Python Target | JavaScript Target |
|---|---|---|---|
| `buo` | `uint256` | `int` | `number` |
| `teksto` | `string` / `string memory` | `str` | `string` |
| `kondisyon` | `bool` | `bool` | `boolean` |
| `alamat` | `address` | `str` | `string` |

### Built-in Functions

- `ipakita(x)`: Outputs `x` to console. Transpiles to:
  - Python: `print(x)`
  - JavaScript: `console.log(x)`
  - Solidity: `console.log(x)` (via Hardhat's `console.sol`)

---

## Installation & Setup

1. Make sure you have **Python 3.8+** installed.
2. Initialize and activate the virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Run automated tests to verify correct setup:
   ```bash
   python -m unittest discover -s tests
   ```

---

## CLI Usage Guidelines

### 1. Run a BBL File Directly
Execute BBL code directly via in-memory Python transpilation:
```bash
python cli/bbl.py run examples/hello.bbl
```

### 2. Transpile to Target Language
Transpile a `.bbl` file into Python, JavaScript, or Solidity:
```bash
# Transpile to Python
python cli/bbl.py transpile examples/hello.bbl -t python -o examples/hello.py

# Transpile to JavaScript
python cli/bbl.py transpile examples/hello.bbl -t js -o examples/hello.js

# Transpile to Solidity
python cli/bbl.py transpile examples/hello.bbl -t solidity -o examples/hello.sol
```

### 3. Debugging Tokens (Lexer)
Dump the token stream produced by the scanner:
```bash
python cli/bbl.py lex examples/hello.bbl
```

### 4. Debugging the AST (Parser)
Dump the parsed Abstract Syntax Tree layout:
```bash
python cli/bbl.py parse examples/hello.bbl
```

### 5. Multi-Agent AI System
Explain, audit, or generate BBL code using the integrated Google Gemini API, coordinated by specialized sub-agents (Writer, Auditor, Explainer, and Orchestrator):
```bash
# Set your Gemini API key first (Windows PowerShell):
$env:GEMINI_API_KEY="your_api_key_here"

# Ask the AI to explain a BBL file line-by-line:
python cli/bbl.py ai explain examples/hello.bbl

# Ask the AI to perform an optimization and type audit:
python cli/bbl.py ai audit examples/hello.bbl

# Generate fresh BBL code from a prompt and save it:
python cli/bbl.py ai write "Gumawa ng contract para sa isang Token" -o examples/token.bbl

# Consult the Tagalog coding tutor (Guro Agent):
python cli/bbl.py ai guro "Paano gumagana ang variables?"
```

### 6. Interactive Web Dashboard & Playground
BBL features an interactive local playground where you can write BBL code, transpile to Python/JS/Solidity side-by-side, inspect the parsed AST tree, and chat with BBL AI Agents in real-time.

To launch the dashboard:
```bash
# Run the local dashboard server (defaults to port 5000)
python cli/bbl.py dashboard

# Or run on a custom port
python cli/bbl.py dashboard -p 8080
```
Open `http://127.0.0.1:5000` in your web browser.

### 7. Baybayin Virtual Machine (BBVM)
BBL includes a custom stack-based Virtual Machine (BBVM) and bytecode compiler. You can compile your BBL files down to custom VM bytecode (.bbv) and execute them natively inside the virtual machine.

To compile BBL to bytecode:
```bash
python cli/bbl.py compile examples/hello.bbl -o examples/hello.bbv
```

To run compiled bytecode on BBVM:
```bash
python cli/bbl.py run --vm examples/hello.bbv
```

Or run BBL source code directly on BBVM in-memory:
```bash
python cli/bbl.py run --vm examples/hello.bbl
```

---

## Code Example: `examples/hello.bbl`

```bbl
// Halimbawa ng Baybayin Language (BBL)
kontrata Pagbati {
    itakda mensahe: teksto = "Kamusta mula sa BBL!"
    itakda tagapamahala: alamat
    itakda bilang_ng_pagbabago: buo = 0

    tungkulin simulan(unang_alamat: alamat) {
        tagapamahala = unang_alamat
    }

    tungkulin kuninMensahe() ibahagi: teksto {
        ibalik mensahe
    }

    tungkulin baguhinMensahe(bagong_mensahe: teksto) ibahagi {
        kung (mensahe != bagong_mensahe) {
            mensahe = bagong_mensahe
            bilang_ng_pagbabago = bilang_ng_pagbabago + 1
            ipakita("Nabagong mensahe sa: " + bagong_mensahe)
        }
    }
}

// --- Script Executable Part ---
ipakita("Nagsisimula ang programa...")

itakda demo = Pagbati("0x1234567890123456789012345678901234567890")
itakda kasalukuyang_mensahe: teksto = demo.kuninMensahe()
ipakita(kasalukuyang_mensahe)

demo.baguhinMensahe("Bagong Mensahe 2026")
ipakita("Bilang ng pagbabago: " + demo.bilang_ng_pagbabago)
```

---

## Compiler Design Highlights

### 1. Baybayin Script Support
The compiler's regex scanner supports Unicode range `\u1700-\u171F` inside identifiers. This enables writing code utilizing native script representation:
```bbl
itakda ᜃᜋᜓᜐ᜔ᜆᜓ = "Kamusto"
ipakita(ᜃᜋᜓᜐ᜔ᜆᜓ)
```

### 2. Solidity Memory Allocation & String Comparison
- Reference parameters (e.g. `teksto`/`string`) are automatically decorated with `memory` in Solidity functions.
- Because Solidity does not natively support string comparisons using `==`, BBL automatically compiles string checks to `keccak256(bytes(a)) == keccak256(bytes(b))`.

### 3. Smart Contract Wrapping
To keep Solidity output correct, any top-level statements outside of a `kontrata` declaration block are wrapped inside a synthetic `contract Main` with a public `run()` function.

### 4. JavaScript class instantiation
To match standard JS requirements, class instantiations automatically append the `new` keyword (e.g., `new Pagbati(...)`).

---

## Editor Support (VS Code Extension)

BBL includes a custom VS Code extension folder located at `vscode-extension/` that provides:
1. **Syntax Highlighting**: Supports colorizing Tagalog keywords, primitive types, numbers, strings, comments, and native Unicode Baybayin characters (`U+1700` to `U+171F`).
2. **Language Configuration**: Autoclosing matching brackets `{}` `[]` `()` and quotes, plus comment toggle shortcuts (`Ctrl + /`).

### How to Install Locally:
1. Copy the `vscode-extension/` folder into your VS Code extensions directory:
   - **Windows**: `%USERPROFILE%\.vscode\extensions\bbl-lang-0.1.0`
   - **macOS/Linux**: `~/.vscode/extensions/bbl-lang-0.1.0`
2. Alternatively, open the `vscode-extension/` folder in VS Code, press `F5` to open the Extension Development Host window, and start opening/editing `.bbl` files with live coloring!
