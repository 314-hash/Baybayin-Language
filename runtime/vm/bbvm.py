import sys
from typing import List, Dict, Any, Tuple, Optional
from compiler.instructions import OpCode

class VMFrame:
    def __init__(self, instructions: List[Tuple[str, Any]], locals_dict: Optional[Dict[str, Any]] = None):
        self.instructions = instructions
        self.ip = 0
        self.locals = locals_dict or {}
        self.stack: List[Any] = []

class BBLObject:
    def __init__(self, class_name: str, fields: Dict[str, Any]):
        self.class_name = class_name
        self.fields = fields

    def __repr__(self):
        return f"<BBLObject {self.class_name}: {self.fields}>"

class BBVM:
    def __init__(self):
        self.globals: Dict[str, Any] = {}
        self.functions: Dict[str, Any] = {}
        self.contracts: Dict[str, Any] = {}
        self.frames: List[VMFrame] = []
        self.output_buffer: List[str] = []

    def log_print(self, text: str):
        self.output_buffer.append(text)
        print(text)

    def execute(self, bytecode: Dict[str, Any]) -> Any:
        """Loads and runs compiled BBL bytecode from main entry point."""
        self.functions = bytecode.get("functions", {})
        self.contracts = bytecode.get("contracts", {})
        
        main_code = bytecode.get("main_code", [])
        if not main_code:
            return None
            
        main_frame = VMFrame(main_code)
        self.frames.append(main_frame)
        
        last_val = None
        
        while self.frames:
            frame = self.frames[-1]
            if frame.ip >= len(frame.instructions):
                # End of current frame
                self.frames.pop()
                continue
                
            opcode, arg = frame.instructions[frame.ip]
            frame.ip += 1
            
            # Interpreter execution loop
            if opcode == OpCode.LOAD_CONST:
                frame.stack.append(arg)
                
            elif opcode == OpCode.STORE_FAST:
                val = frame.stack.pop()
                frame.locals[arg] = val
                
            elif opcode == OpCode.LOAD_FAST:
                # Resolve lookup in frame locals, then globals, then functions/contracts
                if arg in frame.locals:
                    frame.stack.append(frame.locals[arg])
                elif arg in self.globals:
                    frame.stack.append(self.globals[arg])
                elif arg in self.functions:
                    frame.stack.append(arg)
                elif arg in self.contracts:
                    frame.stack.append(arg)
                else:
                    # Treat as variable starting value
                    frame.stack.append(None)
                    
            elif opcode == OpCode.STORE_GLOBAL:
                val = frame.stack.pop()
                self.globals[arg] = val
                
            elif opcode == OpCode.LOAD_GLOBAL:
                if arg in self.globals:
                    frame.stack.append(self.globals[arg])
                elif arg in self.functions:
                    frame.stack.append(arg)
                elif arg in self.contracts:
                    frame.stack.append(arg)
                else:
                    frame.stack.append(None)
                    
            elif opcode == OpCode.BINARY_ADD:
                b = frame.stack.pop()
                a = frame.stack.pop()
                # Handle string conversion coercion
                if isinstance(a, str) or isinstance(b, str):
                    frame.stack.append(str(a) + str(b))
                else:
                    frame.stack.append(a + b)
                    
            elif opcode == OpCode.BINARY_SUB:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a - b)
                
            elif opcode == OpCode.BINARY_MUL:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a * b)
                
            elif opcode == OpCode.BINARY_DIV:
                b = frame.stack.pop()
                a = frame.stack.pop()
                frame.stack.append(a // b)
                
            elif opcode == OpCode.COMPARE_OP:
                b = frame.stack.pop()
                a = frame.stack.pop()
                if arg == '<': frame.stack.append(a < b)
                elif arg == '>': frame.stack.append(a > b)
                elif arg == '<=': frame.stack.append(a <= b)
                elif arg == '>=': frame.stack.append(a >= b)
                elif arg == '==': frame.stack.append(a == b)
                elif arg == '!=': frame.stack.append(a != b)
                
            elif opcode == OpCode.JUMP_IF_FALSE:
                cond = frame.stack.pop()
                if not cond:
                    frame.ip = arg
                    
            elif opcode == OpCode.JUMP:
                frame.ip = arg
                
            elif opcode == OpCode.CALL_FUNCTION:
                callee = frame.stack.pop()
                arg_count = arg
                
                args = []
                for _ in range(arg_count):
                    args.insert(0, frame.stack.pop())
                    
                if callee in self.contracts:
                    c_meta = self.contracts[callee]
                    # Copy contract default fields
                    obj_fields = dict(c_meta["fields"])
                    obj = BBLObject(callee, obj_fields)
                    
                    frame.stack.append(obj)
                    
                    if "simulan" in c_meta["methods"]:
                        constructor_meta = c_meta["methods"]["simulan"]
                        locals_dict = {"self": obj}
                        for i, param in enumerate(constructor_meta["params"]):
                            locals_dict[param] = args[i]
                            
                        new_frame = VMFrame(constructor_meta["code"], locals_dict)
                        new_frame.is_constructor = True
                        self.frames.append(new_frame)
                        
                elif callee in self.functions:
                    func_meta = self.functions[callee]
                    locals_dict = {}
                    for i, param in enumerate(func_meta["params"]):
                        locals_dict[param] = args[i]
                        
                    new_frame = VMFrame(func_meta["code"], locals_dict)
                    self.frames.append(new_frame)

            elif opcode == OpCode.CALL_METHOD:
                method_name, arg_count = arg
                obj = frame.stack.pop()
                if not isinstance(obj, BBLObject):
                    raise RuntimeError(f"Error: Sinubukang tumawag ng paraan sa hindi object: {obj}")
                
                args = []
                for _ in range(arg_count):
                    args.insert(0, frame.stack.pop())
                    
                c_meta = self.contracts[obj.class_name]
                if method_name in c_meta["methods"]:
                    method_meta = c_meta["methods"][method_name]
                    locals_dict = {"self": obj}
                    for i, param in enumerate(method_meta["params"]):
                        locals_dict[param] = args[i]
                    new_frame = VMFrame(method_meta["code"], locals_dict)
                    self.frames.append(new_frame)
                else:
                    raise RuntimeError(f"Error: Walang paraan na '{method_name}' sa kontrata '{obj.class_name}'")

            elif opcode == OpCode.LOAD_ATTR:
                obj = frame.stack.pop()
                if not isinstance(obj, BBLObject):
                    raise RuntimeError(f"Error: Sinubukang kumuha ng katangian sa hindi object: {obj}")
                frame.stack.append(obj.fields.get(arg))

            elif opcode == OpCode.STORE_ATTR:
                obj = frame.stack.pop()
                val = frame.stack.pop()
                if not isinstance(obj, BBLObject):
                    raise RuntimeError(f"Error: Sinubukang mag-imbak sa katangian ng hindi object: {obj}")
                obj.fields[arg] = val
                    
            elif opcode == OpCode.RETURN_VALUE:
                ret_val = frame.stack.pop()
                is_constructor = getattr(frame, "is_constructor", False)
                self.frames.pop()  # Remove current frame
                if self.frames:
                    if not is_constructor:
                        self.frames[-1].stack.append(ret_val)
                else:
                    last_val = ret_val
                    break
                    
            elif opcode == OpCode.PRINT:
                arg_count = arg
                args = []
                for _ in range(arg_count):
                    args.insert(0, frame.stack.pop())
                printed_text = " ".join(str(v) for v in args)
                self.log_print(printed_text)
                
            elif opcode == OpCode.HALT:
                break
                
        return last_val
