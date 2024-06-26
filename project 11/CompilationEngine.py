"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""

import typing
from JackTokenizer import JackTokenizer
from SymbolTable import SymbolTable
from VMWriter import VMWriter


class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """

    INDENT = "  "
    STATEMENTS = {"IF", "LET", "WHILE", "DO", "RETURN"}
    VAR_DECLARATIONS = {"STATIC", "FIELD"}
    SUBROUTINE_DECLARATIONS = {"FUNCTION", "CONSTRUCTOR", "METHOD"}
    SYMBOLS_BYPASS = {"<": "&lt;", ">": "&gt;", "\"": "&quot;", "&": "&amp;"}
    BINARY_OPERATORS = {"+", "-", "*", "/", "&", "|", "<", ">", "="}
    UNARY_OP = {"-", "~", "^", "#"}
    KEYWORD_CONST = {"TRUE", "FALSE", "NULL", "THIS"}
    PRIMITIVE_TYPES = {"INT", "CHAR", "BOOLEAN"}
    SEGMENT = {"FIELD": "this", "STATIC": "static", "ARG": "argument", "LOCAL": "local"}
    BIN_OP_COMMANDS = {"+": "ADD", "-": "SUB", "&": "AND", "|": "OR",
                       "<": "LT", ">": "GT", "=": "EQ"}
    UNARY_OP_COMMANDS = {"-": "NEG", "~": "NOT", "^": "LEFTSHIFT", "#": "RIGHTSHIT"}

    def __init__(self, input_stream: JackTokenizer, output_stream: typing.TextIO) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self.__indent_level = 0
        self.__input_stream: JackTokenizer = input_stream
        self.__class_symbol_table: SymbolTable = SymbolTable()
        self.__class_name: str = ""
        self.__label_index: int = 0
        self.vm_writer = VMWriter(output_stream)

    def compile(self) -> None:
        assert (self.__input_stream.keyword() == "CLASS")  # sanity check
        self.compile_class()

    def compile_class(self) -> None:
        self.__input_stream.advance()  # class
        self.__class_name: str = self.__input_stream.identifier()  # for labels, SymbolTable
        self.__input_stream.advance()  # class_name
        self.__input_stream.advance()  # {

        while (self.__input_stream.token_type() == "KEYWORD" and  # varDec*
               self.__input_stream.keyword() in CompilationEngine.VAR_DECLARATIONS):
            self.compile_class_var_dec()  # Updates the class symbol table with the vars in current line

        while (self.__input_stream.token_type() == "KEYWORD" and  # subDec*
               self.__input_stream.keyword() in CompilationEngine.SUBROUTINE_DECLARATIONS):
            self.compile_subroutine()

        assert (self.__input_stream.symbol() == "}")  # Sanity check
        self.__input_stream.advance()  # }

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        subroutine_symbol_table = SymbolTable()

        routine_type: str = self.__input_stream.keyword()  # method/function/constructor
        self.__input_stream.advance()
        # Get return type - Keyword or Identifier:
        if self.__input_stream.token_type() == "KEYWORD":
            return_type = self.__input_stream.keyword()  # void|int|char|boolean
            self.__input_stream.advance()
        else:  # Return type is some class_name:
            assert (self.__input_stream.token_type() == "IDENTIFIER")  # sanity check
            return_type = self.__input_stream.identifier()  # custom type (some className)
            self.__input_stream.advance()

        assert (self.__input_stream.token_type() == "IDENTIFIER")  # sanity check
        routine_identifier: str = self.__input_stream.identifier()  # name of method/function/constructor
        self.__input_stream.advance()

        vm_func_name = self.__class_name + "." + routine_identifier

        assert (self.__input_stream.symbol() == "(")
        self.__input_stream.advance()  # (
        if routine_type == "METHOD":  # If method - insert THIS to the subroutine's SymbolTable as arg 0
            subroutine_symbol_table.define("this", self.__class_name, "ARG")
        self.read_args(subroutine_symbol_table)  # Update symbol table with the function arguments
        assert (self.__input_stream.symbol() == ")")
        self.__input_stream.advance()  # )

        # subroutineBody:
        self.__input_stream.advance()  # {
        self.read_vars(subroutine_symbol_table)  # handles varDec*, updates symbol table.
        # Write function declaration in VM code: function <vm_func_name> <num_of_local_variables>
        self.vm_writer.write_function(vm_func_name, subroutine_symbol_table.var_count("VAR"))

        if routine_type == "CONSTRUCTOR":  # add memoryAlloc in case of constructor:
            # push number of required registers for the object - the amount of fields:
            self.vm_writer.write_push("constant", self.__class_symbol_table.var_count("FIELD"))
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop("pointer", 0)  # pointer 0 now holds address of object, THIS will access object
        elif routine_type == "METHOD":  # Set THIS (arg 0 to pointer 0)
            self.vm_writer.write_push("argument", 0)  # object address on top of stack
            self.vm_writer.write_pop("pointer", 0)  # pointer 0 now holds address of object, THIS will access object
        else:  # Jack Function (not tied to object, no need to do anything special)
            pass

        # Statements (in subroutineBody):
        self.compile_statements(subroutine_symbol_table)
        assert (self.__input_stream.symbol() == "}")  # Sanity check
        self.__input_stream.advance()  # }

    def compile_statements(self, subroutine_symbol_table: SymbolTable) -> None:
        """Compiles a sequence of statements, not including the enclosing
        "{}".
        """
        while (self.__input_stream.token_type() == "KEYWORD" and
               self.__input_stream.keyword() in CompilationEngine.STATEMENTS):
            statement_type = self.__input_stream.keyword()
            if statement_type == "LET":
                self.compile_let(subroutine_symbol_table)
            elif statement_type == "IF":
                self.compile_if(subroutine_symbol_table)
            elif statement_type == "WHILE":
                self.compile_while(subroutine_symbol_table)
            elif statement_type == "DO":
                self.compile_do(subroutine_symbol_table)
            elif statement_type == "RETURN":
                self.compile_return(subroutine_symbol_table)

    def compile_let(self, subroutine_symbol_table: SymbolTable) -> None:
        self.__input_stream.advance()  # let
        assert (self.__input_stream.token_type() == "IDENTIFIER")
        var_name: str = self.__input_stream.identifier()
        var_kind, var_index, var_type = self.var_lookup(var_name, subroutine_symbol_table)
        self.__input_stream.advance()  # var_name
        assert (self.__input_stream.token_type() == "SYMBOL" and (self.__input_stream.symbol() == "=" or
                                                                  self.__input_stream.symbol() == "["))  # Sanity check

        if self.__input_stream.token_type() == "SYMBOL" and self.__input_stream.symbol() == "=":  # non-array variable:
            self.__input_stream.advance()  # =
            self.compile_expression(subroutine_symbol_table)  # Pushes expression to top of stack
            self.vm_writer.write_pop(var_kind, var_index)  # Expression-value assigned to the variable
        elif self.__input_stream.token_type() == "SYMBOL" and self.__input_stream.symbol() == "[":  # Var is an array
            self.__input_stream.advance()  # [
            self.compile_expression(subroutine_symbol_table)  # Pushes array index into the stack
            self.__input_stream.advance()  # ]
            self.vm_writer.write_push(var_kind, var_index)  # Pushes array base address into the stack
            self.vm_writer.write_arithmetic("ADD")  # Top of stack is now the address of arr[index]
            self.__input_stream.advance()  # =

            self.compile_expression(
                subroutine_symbol_table)  # The expression-value to assign to array[index] is now at the top of stack
            # Store the expression-value in temp 0, so we can get arr[index] address at top of stack again:
            self.vm_writer.write_pop("temp", 0)
            self.vm_writer.write_pop("pointer", 1)  # THAT points to arr[index]
            self.vm_writer.write_push("temp", 0)  # Expression-value to assign into THAT now on top of stack
            self.vm_writer.write_pop("that", 0)  # Expression-value assigned to arr[index]
        else:
            assert False  # Sanity check - should never be here.

        self.__input_stream.advance()  # ;

    def var_lookup(self, var_name: str, subroutine_symbol_table: SymbolTable):
        """
        Looks up a variable name in the given subroutine SymbolTable, and if not found in the class SymbolTable.
        Returns: (variable_kind, variable_index)
        """
        table: SymbolTable  # Will be set to either the class' symbolTable, or the subroutine's
        if subroutine_symbol_table.is_in(var_name):  # In the subroutine symbolTable
            table = subroutine_symbol_table
        else:  # In the class symbolTable or doesn't exist
            if not self.__class_symbol_table.is_in(var_name):  # Not in either table - not a registered variable
                return None, None, None
            table = self.__class_symbol_table

        return table.kind_of(var_name), table.index_of(var_name), table.type_of(var_name)

    def compile_if(self, subroutine_symbol_table: SymbolTable) -> None:
        label_if_true = self.__class_name + ".IF_TRUE." + str(self.__label_index)
        self.__label_index += 1
        label_if_false = self.__class_name + ".IF_FALSE." + str(self.__label_index)
        self.__label_index += 1

        self.__input_stream.advance()  # if
        self.__input_stream.advance()  # (
        self.compile_expression(subroutine_symbol_table)  # Evaluated expression on top of stack.
        self.__input_stream.advance()  # )
        # Write the VM if-goto/goto commands:
        self.vm_writer.write_if(label_if_true)
        self.vm_writer.write_goto(label_if_false)
        # Continue with expressions inside if clause:
        self.__input_stream.advance()  # {
        self.vm_writer.write_label(label_if_true)  # if-true label - to execute if clause
        self.compile_statements(subroutine_symbol_table)
        self.__input_stream.advance()  # }

        else_flag = False
        label_end: str = str()  # To be used only when there's an else clause
        # Check for else - which is a continuation of this ifStatement (if exists):
        if self.__input_stream.token_type() == "KEYWORD" and self.__input_stream.keyword() == "ELSE":
            label_end: str = self.__class_name + ".IF_END." + str(self.__label_index)
            self.__label_index += 1
            else_flag = True
            self.vm_writer.write_goto(label_end)

            self.__input_stream.advance()  # else
            self.__input_stream.advance()  # {
            self.vm_writer.write_label(label_if_false)  # if-false label - to skip to else clause
            self.compile_statements(subroutine_symbol_table)
            self.__input_stream.advance()  # }

        if else_flag:  # Write the end-label, skipping the execution of the else-clause statements:
            self.vm_writer.write_label(label_end)
        else:
            # Write the if_false label, skipping the execution of the if-clause statements:
            self.vm_writer.write_label(label_if_false)

    def compile_while(self, subroutine_symbol_table: SymbolTable) -> None:
        label_while_begin = self.__class_name + ".WHILE_BEGIN." + str(self.__label_index)
        self.__label_index += 1
        label_while_end = self.__class_name + ".WHILE_END." + str(self.__label_index)
        self.__label_index += 1

        self.vm_writer.write_label(label_while_begin)  # To return here at the end of the while statements execution

        self.__input_stream.advance()  # while
        self.__input_stream.advance()  # (
        self.compile_expression(subroutine_symbol_table)  # Evaluated expression on top of stack.
        self.vm_writer.write_arithmetic("NOT")  # To flip expression's boolean value
        self.vm_writer.write_if(label_while_end)  # In case expression is false (true after flipping) - go to end.
        assert (self.__input_stream.symbol() == ")")  # Sanity check
        self.__input_stream.advance()  # )
        assert (self.__input_stream.symbol() == "{")
        self.__input_stream.advance()  # {

        self.compile_statements(subroutine_symbol_table)

        self.vm_writer.write_goto(label_while_begin)

        self.vm_writer.write_label(label_while_end)

        assert (self.__input_stream.symbol() == "}")  # Sanity check
        self.__input_stream.advance()  # }

    def compile_do(self, subroutine_symbol_table: SymbolTable) -> None:
        """Compiles a do statement."""
        self.__input_stream.advance()  # do
        self.compile_call(subroutine_symbol_table)  # Handles calling the function
        self.__input_stream.advance()  # ;

    def compile_call(self, subroutine_symbol_table: SymbolTable, first_identifier: str = None,
                     do_statement_flag=True) -> None:
        # Handle function call:
        num_of_args: int = 0
        if first_identifier is None:
            first_identifier = self.__input_stream.identifier()
            self.__input_stream.advance()

        if self.__input_stream.token_type() == "SYMBOL" and self.__input_stream.symbol() == ".":
            self.__input_stream.advance()  # .
            assert (self.__input_stream.token_type() == "IDENTIFIER")  # Sanity check
            # call will be to Classname.funcName.
            # Check whether first_identifier is objectName (push address, convert to className) or already className:
            var_kind, var_index, var_type = self.var_lookup(first_identifier, subroutine_symbol_table)
            if var_kind is None:  # Already classname
                to_call = first_identifier + "." + self.__input_stream.identifier()
            else:  # objectName.funcName. Jack method - push the object's address onto stack (arg 0 in called function)
                to_call = var_type + "." + self.__input_stream.identifier()
                num_of_args += 1
                self.vm_writer.write_push(var_kind, var_index)  # push this 0

            self.__input_stream.advance()  # subroutine_name

        else:  # No dot - works on correct obj (need to push pointer 0 which points to THIS object as function's arg 0 )
            to_call = self.__class_name + "." + first_identifier
            num_of_args += 1  # To take into account THIS as arg 0
            self.vm_writer.write_push("pointer", 0)  # push THIS as arg 0

        assert (self.__input_stream.token_type() == "SYMBOL" and self.__input_stream.symbol() == "(")  # Sanity check

        self.__input_stream.advance()  # (
        # Read parameter list and push params onto stack:
        num_of_args += self.compile_expression_list(subroutine_symbol_table)
        assert (self.__input_stream.symbol() == ")")  # Sanity check
        self.__input_stream.advance()  # )
        # Now call function:
        self.vm_writer.write_call(to_call, num_of_args)  # Return value on top of stack
        if do_statement_flag:
            self.vm_writer.write_pop("temp",
                                     0)  # Since we're not using return value (do statement) - pop it out of stack

    def compile_expression_list(self, subroutine_symbol_table: SymbolTable) -> int:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        num_of_expressions: int = 0
        # First check if the list is empty:
        if self.__input_stream.token_type() != "SYMBOL" or self.__input_stream.symbol() != ")":
            self.compile_expression(subroutine_symbol_table)  # Evaluate and push expression onto stack
            num_of_expressions += 1
            # Now to handle (',' expression)* :
            while self.__input_stream.token_type() == "SYMBOL" and self.__input_stream.symbol() == ",":
                self.__input_stream.advance()  # ,
                self.compile_expression(subroutine_symbol_table)  # Evaluate and push expression onto stack
                num_of_expressions += 1

        return num_of_expressions

    def compile_expression(self, subroutine_symbol_table: SymbolTable) -> None:
        """Compiles an expression. Pushes it onto the stack"""
        self.compile_term(subroutine_symbol_table)
        # Now check if we have an "(op term)*" left:
        while (self.__input_stream.token_type() == "SYMBOL") and (
                self.__input_stream.symbol() in CompilationEngine.BINARY_OPERATORS):
            binary_operator = self.__input_stream.symbol()  # Save to write later (VM is post-fix notation)
            self.__input_stream.advance()  # binary operator

            self.compile_term(subroutine_symbol_table)  # Push term to top of stack

            if binary_operator not in {"*", "/"}:
                self.vm_writer.write_arithmetic(CompilationEngine.BIN_OP_COMMANDS[binary_operator])
            else:  # The operator is for multiplication/division - call the relevant OS function:
                if binary_operator == "*":
                    func_name = "Math.multiply"
                else:
                    func_name = "Math.divide"
                self.vm_writer.write_call(func_name, 2)

    def compile_term(self, subroutine_symbol_table: SymbolTable) -> None:
        """Compiles a term.
        This routine is faced with a slight difficulty when
        trying to decide between some alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        token_type: str = self.__input_stream.token_type()
        if token_type == "IDENTIFIER":
            # We're in one of the following cases:
            # varName | varName[expression] | subroutineCall

            # save current token which is: varname / prefix of subroutineName. Then look ahead:
            identifier_token: str = self.__input_stream.identifier()
            self.__input_stream.advance()  # advance to check for: varname or varname[expression] or subroutineCall:

            if self.__input_stream.token_type() == "SYMBOL":
                symbol = self.__input_stream.symbol()

                if symbol == "[":  # varname[expression] == array[index]
                    var_name = identifier_token
                    var_kind, var_index, var_type = self.var_lookup(var_name, subroutine_symbol_table)
                    self.__input_stream.advance()  # [
                    self.compile_expression(subroutine_symbol_table)  # Pushes array index into the stack
                    self.__input_stream.advance()  # ]
                    self.vm_writer.write_push(var_kind, var_index)  # Pushes array base address into the stack
                    self.vm_writer.write_arithmetic("ADD")  # Top of stack is now the address of arr[index]
                    self.vm_writer.write_pop("pointer", 1)  # THAT points to arr[index]
                    self.vm_writer.write_push("that", 0)  # value of arr[index] is now on top of stack

                elif symbol == "." or symbol == "(":  # varname.foo(args) or foo(args) (subroutine call)
                    self.compile_call(subroutine_symbol_table,
                                      first_identifier=identifier_token, do_statement_flag=False)

                else:  # just varName - push variable on top of stack
                    var_name = identifier_token
                    var_kind, var_index, var_type = self.var_lookup(var_name, subroutine_symbol_table)
                    self.vm_writer.write_push(var_kind, var_index)

        elif token_type == "INT_CONST":
            self.vm_writer.write_push("constant", self.__input_stream.int_val())
            self.__input_stream.advance()  # int_const
        elif token_type == "STRING_CONST":
            string_const: str = self.__input_stream.string_val()
            self.vm_writer.write_push("constant", len(string_const))
            self.vm_writer.write_call("String.new", 1)  # Use OS's string class
            for i in range(0, len(string_const)):  # Append the string char by char
                self.vm_writer.write_push("constant", ord(string_const[i]))
                self.vm_writer.write_call("String.appendChar", 2)
            self.__input_stream.advance()  # the string_const
        elif token_type == "KEYWORD":
            self.compile_keyword()
            self.__input_stream.advance()  # keyword
        elif token_type == "SYMBOL" and self.__input_stream.symbol() == '(':
            self.__input_stream.advance()  # (
            self.compile_expression(subroutine_symbol_table)  # Respect parenthesis - regard as a new expression.
            self.__input_stream.advance()  # )
        elif token_type == "SYMBOL" and self.__input_stream.symbol() in CompilationEngine.UNARY_OP:
            unary_op = self.__input_stream.symbol()  # Save operator, as VM is post-fix
            self.__input_stream.advance()  # some unary operator
            self.compile_term(subroutine_symbol_table)  # Push term onto stack
            self.vm_writer.write_arithmetic(CompilationEngine.UNARY_OP_COMMANDS[unary_op])  # Apply the unary op

    def compile_keyword(self):
        key_word = self.__input_stream.keyword()
        if key_word == "TRUE":
            self.vm_writer.write_push("constant", 0)
            self.vm_writer.write_arithmetic("NOT")
        elif key_word == "FALSE":
            self.vm_writer.write_push("constant", 0)
        elif key_word == "NULL":
            self.vm_writer.write_push("constant", 0)
        elif key_word == "THIS":
            self.vm_writer.write_push("pointer", 0)

    def compile_return(self, subroutine_symbol_table: SymbolTable) -> None:
        """Compiles a return statement."""
        self.__input_stream.advance()  # return
        if self.__input_stream.token_type() != "SYMBOL" or self.__input_stream.symbol() != ";":
            self.compile_expression(subroutine_symbol_table)  # Push return value to top of stack
        else:  # No return value - push constant 0 for placeholder (as all functions must return a value)
            self.vm_writer.write_push("constant", 0)

        assert (self.__input_stream.symbol() == ";")
        self.__input_stream.advance()  # ;
        self.vm_writer.write_return()

    def read_vars(self, symbol_table: SymbolTable) -> None:
        """
        Handles varDec* in subroutineBody - registers the variables into the given symbol_table.
        """
        while self.__input_stream.token_type() == "KEYWORD" and self.__input_stream.keyword() == "VAR":
            self.__input_stream.advance()  # var

            token_type: str = self.__input_stream.token_type()
            # Get var type:
            if token_type == "KEYWORD":  # int|char|boolean
                var_type = self.__input_stream.keyword().lower()
            else:  # some class_name - identifier
                assert (token_type == "IDENTIFIER")  # Sanity check
                var_type = self.__input_stream.identifier()
            self.__input_stream.advance()  # type

            # Get varname(s) (identifier):
            assert (self.__input_stream.token_type() == "IDENTIFIER")  # Sanity check - at least one varname

            while self.__input_stream.token_type() == "IDENTIFIER":
                var_name = self.__input_stream.identifier()
                symbol_table.define(var_name, var_type, "VAR")
                self.__input_stream.advance()  # varName
                if self.__input_stream.token_type() != "SYMBOL" or self.__input_stream.symbol() != ",":  # No more vars
                    assert (self.__input_stream.symbol() == ";")  # Sanity check
                    self.__input_stream.advance()  # ;
                    break
                self.__input_stream.advance()  # ,  # Move on to next varname to register

    def read_args(self, symbol_table: SymbolTable) -> None:
        """
        Handles parameterList in subroutineDec - registers the parameters into the given symbol table.
        """
        while True:
            token_type: str = self.__input_stream.token_type()
            # Get var type:
            if token_type == "KEYWORD":  # int|char|boolean
                assert (self.__input_stream.keyword() in CompilationEngine.PRIMITIVE_TYPES)
                var_type = self.__input_stream.keyword().lower()
            elif token_type == "IDENTIFIER":  # some class_name
                var_type = self.__input_stream.identifier()
            else:
                assert (self.__input_stream.symbol() == ")")  # Sanity check
                break
            self.__input_stream.advance()  # type
            # Get varname (identifier):
            var_name: str = self.__input_stream.identifier()
            symbol_table.define(var_name, var_type, "ARG")
            self.__input_stream.advance()  # varname
            if self.__input_stream.token_type() == "SYMBOL" and self.__input_stream.symbol() == ",":
                self.__input_stream.advance()  # ,

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        var_kind: str = self.__input_stream.keyword()  # static or field
        self.__input_stream.advance()

        if self.__input_stream.token_type() == "KEYWORD":  # INT/BOOLEAN/CHAR (keyword)
            assert (self.__input_stream.keyword() in {"INT", "BOOLEAN", "CHAR"})  # Sanity check
            var_type: str = self.__input_stream.keyword().lower()
        else:  # class_name (identifier)
            var_type: str = self.__input_stream.identifier()
        self.__input_stream.advance()

        name: str = self.__input_stream.identifier()
        self.__input_stream.advance()

        self.__class_symbol_table.define(name, var_type, var_kind)

        while self.__input_stream.token_type() == "SYMBOL" and self.__input_stream.symbol() == ",":
            self.__input_stream.advance()
            name: str = self.__input_stream.identifier()
            self.__class_symbol_table.define(name, var_type, var_kind)
            self.__input_stream.advance()

        self.__input_stream.advance()  # ;
