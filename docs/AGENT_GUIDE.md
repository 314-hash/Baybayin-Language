# BBL AI Agent & User Guide

Welcome to the **Baybayin Language (BBL)** developer guide! This document explains BBL's syntax, details how to operate the Command Line Interface (CLI), and walks through the multi-agent AI system.

---

## 1. Baybayin Language (BBL) Syntax Reference

BBL uses Filipino-inspired keywords while remaining fully compatible with Unicode symbols.

### Keywords
- `kontrata`: Defines a class / smart contract.
- `tungkulin`: Declares a function or contract method.
- `simulan`: Represents the contract constructor method.
- `itakda`: Assigns or defines local variables.
- `kung`: Conditional `if` branch.
- `kundi`: Conditional `else` fallback branch.
- `ibalik`: Returns a value from a function.
- `ipakita`: Built-in function to print output to the console.

### Types
- `buo`: Integer / number type.
- `teksto`: String type.
- `alamat`: Ethereum / blockchain address type.

### Example Code: `hello.bbl`
```bbl
// Halimbawa ng BBL
kontrata Pagbati {
    itakda mensahe: teksto = "Kamusta mula sa BBL!"
    itakda bilang_ng_pagbabago: buo = 0

    tungkulin kuninMensahe() ibahagi: teksto {
        ibalik mensahe
    }

    tungkulin baguhinMensahe(bagong_mensahe: teksto) ibahagi {
        mensahe = bagong_mensahe
        bilang_ng_pagbabago = bilang_ng_pagbabago + 1
        ipakita("Nabagong mensahe sa: " + bagong_mensahe)
    }
}

// Script run
ipakita("Nagsisimula ang programa...")
itakda demo = Pagbati()
demo.baguhinMensahe("Bagong Mensahe 2026")
ipakita(demo.kuninMensahe())
```

---

## 2. Command Line Interface (CLI) Guide

BBL features a unified command utility. Access these commands using the CLI runner `cli/bbl.py`.

### Compile BBL to Bytecode
Generates compiled `.bbv` JSON-based bytecode ready for execution on the virtual machine:
```bash
python cli/bbl.py compile examples/hello.bbl -o examples/hello.bbv
```

### Run on the BBVM (Baybayin Virtual Machine)
Runs bytecode or source code directly inside the VM interpreter:
```bash
# Run compiled bytecode
python cli/bbl.py run --vm examples/hello.bbv

# Run source code in-memory on the VM
python cli/bbl.py run --vm examples/hello.bbl
```

### Transpile to Target Code
Transpile BBL source code to Python, JavaScript, or Solidity:
```bash
# Transpile to Python
python cli/bbl.py run examples/hello.bbl

# Transpile to JavaScript
python cli/bbl.py run examples/hello.bbl -t js

# Transpile to Solidity
python cli/bbl.py run examples/hello.bbl -t solidity
```

### Launch Web Dashboard Playground
Runs a local playground server with transpilers side-by-side, AST view, and the visual AI Agents panel:
```bash
python cli/bbl.py dashboard
```
Open `http://127.0.0.1:5000` to access the playground.

---

## 3. Multi-Agent AI System Guide

The BBL environment features a built-in AI Multi-Agent system that acts as a pair programmer.

### The Agents
1. **Orchestrator (`orchestrator`)**: Receives queries, checks if web documentation is required, and routes intents to the optimal specialized sub-agent.
2. **Code Writer (`writer`)**: Generates fresh BBL code templates or functions based on user requests.
3. **Auditor (`auditor`)**: Audits BBL files for type errors, formatting syntax, or security issues (such as Solidity reentrancy risk when transpiled).
4. **Code Explainer (`explainer`)**: Explains BBL keywords, AST structural concepts, or translates standard code to BBL line-by-line.
5. **Guro Agent (`guro`)**: Explains core programming principles, VM execution, and BBL constructs entirely in Tagalog/Taglish using real-world Filipino analogies. Loads dynamic dictionary mappings from `ai/guro/glossary.json`.

### CLI AI Subcommands
Use the AI Agents directly from your terminal:

```bash
# Set your Gemini API key (Windows)
$env:GEMINI_API_KEY="your_key"

# Explaining code
python cli/bbl.py ai explain examples/hello.bbl

# Audit code
python cli/bbl.py ai audit examples/hello.bbl

# Write code to file
python cli/bbl.py ai write "Gumawa ng voting contract" -o examples/vote.bbl

# Consult the Guro Tutor Agent
python cli/bbl.py ai guro "Paano gumagana ang loops o pag-ulit sa BBL?"
```

### Dynamic Web Integration (Auto-Browser)
If a local `auto-browser` instance is running at `http://127.0.0.1:8000`, the Orchestrator will automatically execute Google searches and retrieve real-time documentation or framework syntax, injecting it into the prompt context to solve tasks accurately.
