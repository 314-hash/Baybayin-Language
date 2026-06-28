# Opcode definitions for the Baybayin Virtual Machine (BBVM)

class OpCode:
    LOAD_CONST = "LOAD_CONST"       # Push constant on stack
    STORE_FAST = "STORE_FAST"       # Store top of stack in local variable
    LOAD_FAST = "LOAD_FAST"         # Push local variable on stack
    STORE_GLOBAL = "STORE_GLOBAL"   # Store top of stack in global variable
    LOAD_GLOBAL = "LOAD_GLOBAL"     # Push global variable on stack
    
    BINARY_ADD = "BINARY_ADD"       # Pop 2, add, push result
    BINARY_SUB = "BINARY_SUB"       # Pop 2, subtract, push result
    BINARY_MUL = "BINARY_MUL"       # Pop 2, multiply, push result
    BINARY_DIV = "BINARY_DIV"       # Pop 2, divide, push result
    
    COMPARE_OP = "COMPARE_OP"       # Compare top 2 elements (operator like '<', '==')
    
    JUMP_IF_FALSE = "JUMP_IF_FALSE" # Pop top. If false, jump to index
    JUMP = "JUMP"                   # Jump to absolute instruction index
    
    CALL_FUNCTION = "CALL_FUNCTION" # Call function with N arguments
    RETURN_VALUE = "RETURN_VALUE"   # Return from function
    
    PRINT = "PRINT"                 # Print top elements (arg_count)
    HALT = "HALT"                   # Stop execution
    
    CALL_METHOD = "CALL_METHOD"     # Call object method
    LOAD_ATTR = "LOAD_ATTR"         # Load object field
    STORE_ATTR = "STORE_ATTR"       # Store to object field
