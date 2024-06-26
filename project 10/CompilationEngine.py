"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""

import typing
from JackTokenizer import JackTokenizer


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

    def __init__(self, input_stream: JackTokenizer, output_stream: typing.TextIO) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self.__indent_level = 0
        self.__input_stream: JackTokenizer = input_stream
        self.__output_stream = output_stream

    def compile(self) -> None:
        # self.write_scope_open("tokens")
        self.compile_class()
        # self.write_scope_close("tokens")

    def compile_class(self) -> None:
        """Compiles a complete class."""
        self.write_scope_open("class")

        self.__write_keyword()  # class

        self.__write_identifier()  # className
        self.__write_symbol()  # {

        while (self.__input_stream.token_type() == "KEYWORD" and  # varDec*
               self.__input_stream.keyword() in CompilationEngine.VAR_DECLARATIONS):
            self.compile_class_var_dec()

        while (self.__input_stream.token_type() == "KEYWORD" and  # subDec*
               self.__input_stream.keyword() in CompilationEngine.SUBROUTINE_DECLARATIONS):
            self.compile_subroutine()

        self.__write_symbol()  # }

        self.write_scope_close("class")

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        self.write_scope_open("classVarDec")
        self.write_variables()
        self.write_scope_close("classVarDec")

    def write_variables(self) -> None:
        self.__write_keyword()  # Keyword (static/field) for class variable, var for non-class variable

        # Write keyword if type is 'int' | 'char' | 'boolean', write identifier if type is some other className
        if self.__input_stream.token_type() == "KEYWORD":
            self.__write_keyword()  # 'int' | 'char' | 'boolean'
        elif self.__input_stream.token_type() == "IDENTIFIER":
            self.__write_identifier()  # className

        self.__write_identifier()  # variableName

        # now handle (, type varName)*  :
        while self.__input_stream.token_type() == "SYMBOL" and self.__input_stream.symbol() == ',':
            self.__write_symbol()  # ,
            self.__write_identifier()  # variableName

        self.__write_symbol()  # ;

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        self.write_scope_open("subroutineDec")

        self.__write_keyword()  # method/function/constructor
        # Handle return type - Keyword or Identifier:
        if self.__input_stream.token_type() == "KEYWORD":
            self.__write_keyword()  # void|int|char|boolean
        elif self.__input_stream.token_type() == "IDENTIFIER":
            self.__write_identifier()  # custom type (some className)
        self.__write_identifier()  # name of method/function/constructor
        self.__write_symbol()  # (
        self.compile_parameter_list()
        self.__write_symbol()  # )

        self.__write_subroutine_body()

        self.write_scope_close("subroutineDec")

    def __write_subroutine_body(self) -> None:
        self.write_scope_open("subroutineBody")

        self.__write_symbol()  # {
        # Now handle varDec*:
        while self.__input_stream.token_type() == "KEYWORD" and self.__input_stream.keyword() == "VAR":
            self.compile_var_dec()
        self.compile_statements()
        self.__write_symbol()  # }

        self.write_scope_close("subroutineBody")

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        self.write_scope_open("parameterList")

        if self.__input_stream.token_type() != "SYMBOL" or self.__input_stream.symbol() != ")":
            self.__write_type_varname()  # type varName
            # Now to handle (',' type varName)*:
            while self.__input_stream.token_type() == "SYMBOL" and self.__input_stream.symbol() == ",":
                self.__write_symbol()  # ,
                self.__write_type_varname()

        self.write_scope_close("parameterList")

    def __write_type_varname(self) -> None:
        token_type: str = self.__input_stream.token_type()
        if token_type == "KEYWORD":
            self.__write_keyword()
        elif token_type == "IDENTIFIER":
            self.__write_identifier()
        # varName:
        self.__write_identifier()

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        self.write_scope_open("varDec")
        self.write_variables()
        self.write_scope_close("varDec")

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        self.write_scope_open("statements")

        while (self.__input_stream.token_type() == "KEYWORD" and
               self.__input_stream.keyword() in CompilationEngine.STATEMENTS):
            statement_type = self.__input_stream.keyword()
            if statement_type == "LET":
                self.compile_let()
            elif statement_type == "IF":
                self.compile_if()
            elif statement_type == "WHILE":
                self.compile_while()
            elif statement_type == "DO":
                self.compile_do()
            elif statement_type == "RETURN":
                self.compile_return()

        self.write_scope_close("statements")

    def compile_do(self) -> None:
        """Compiles a do statement."""
        self.write_scope_open("doStatement")

        self.__write_keyword()  # do
        # subroutine call:
        self.__write_identifier()  # subroutineName
        if self.__input_stream.symbol() == "(":
            self.__write_symbol()  # (
            self.compile_expression_list()
            self.__write_symbol()  # )
        elif self.__input_stream.symbol() == ".":
            self.__write_symbol()  # .
            self.__write_identifier()  # subroutineName
            self.__write_symbol()  # (
            self.compile_expression_list()
            self.__write_symbol()  # )

        self.__write_symbol()  # ;

        self.write_scope_close("doStatement")

    def compile_let(self) -> None:
        """Compiles a let statement."""
        self.write_scope_open("letStatement")
        # keyword (let):
        self.__write_keyword()
        # identifier (varName):
        self.__write_identifier()
        # Now handle ('[' expression ']')?:
        if self.__input_stream.symbol() == "[":
            self.__write_symbol()  # [
            self.compile_expression()
            self.__write_symbol()  # ]
        self.__write_symbol()  # =
        self.compile_expression()
        self.__write_symbol()  # ;

        self.write_scope_close("letStatement")

    def compile_while(self) -> None:
        """Compiles a while statement."""
        self.write_scope_open("whileStatement")

        self.__write_if_while_statement()

        self.write_scope_close("whileStatement")

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self.write_scope_open("returnStatement")

        self.__write_keyword()  # return
        if self.__input_stream.token_type() != "SYMBOL" or self.__input_stream.symbol() != ";":
            self.compile_expression()
        self.__write_symbol()  # ;

        self.write_scope_close("returnStatement")

    def compile_if(self) -> None:
        """Compiles an if statement, possibly with a trailing else clause."""
        self.write_scope_open("ifStatement")

        self.__write_if_while_statement()

        # Check for else - which is a continuation of this ifStatement (if exists):
        while self.__input_stream.token_type() == "KEYWORD" and self.__input_stream.keyword() == "ELSE":
            self.__write_keyword()  # else
            self.__write_symbol()  # {
            self.compile_statements()
            self.__write_symbol()  # }

        self.write_scope_close("ifStatement")

    def __write_if_while_statement(self) -> None:
        """Writes an if/while statement's XML"""
        self.__write_keyword()  # if / while
        self.__write_symbol()  # (
        self.compile_expression()
        self.__write_symbol()  # )
        self.__write_symbol()  # {
        self.compile_statements()
        self.__write_symbol()  # }

    def compile_expression(self) -> None:
        """Compiles an expression."""
        self.write_scope_open("expression")



        self.compile_term()
        # Now check if we have "term op term" or just "term" (in which case we're done):
        while (self.__input_stream.token_type() == "SYMBOL") and (
                self.__input_stream.symbol() in CompilationEngine.BINARY_OPERATORS):
            self.__write_symbol()
            self.compile_term()

        self.write_scope_close("expression")

    def compile_term(self) -> None:
        """Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        self.write_scope_open("term")

        token_type: str = self.__input_stream.token_type()
        if token_type == "IDENTIFIER":
            # We're in one of the following cases:
            # varName | varName[expression] | subroutineCall
            identifier_token: str = self.__input_stream.identifier()  # save current token, look ahead:
            self.__input_stream.advance()  # advance to check for [expression] or .subroutineCall
            self.__write_identifier_no_advance(identifier_token)  # varname / classname|varName / subroutineName

            if self.__input_stream.token_type() == "SYMBOL":
                symbol = self.__input_stream.symbol()
                if symbol == "[":  # varname[expression]
                    self.__write_symbol()  # [
                    self.compile_expression()
                    self.__write_symbol()  # ]

                elif symbol == ".":  # varname.foo (subroutine call)
                    self.__write_symbol()  # .
                    self.__write_identifier()  # subroutineName
                    self.__write_symbol()  # (
                    self.compile_expression_list()
                    self.__write_symbol()  # )

                elif symbol == "(":
                    self.__write_symbol()  # (
                    self.compile_expression_list()
                    self.__write_symbol()  # )

        elif token_type == "INT_CONST":
            self.__write_int_const()
        elif token_type == "STRING_CONST":
            self.__write_str_const()
        elif token_type == "KEYWORD":
            self.__write_keyword()
        elif token_type == "SYMBOL" and self.__input_stream.symbol() == '(':
            self.__write_symbol()  # (
            self.compile_expression()
            self.__write_symbol()  # )
        elif token_type == "SYMBOL" and self.__input_stream.symbol() in CompilationEngine.UNARY_OP:
            self.__write_symbol()  # some unary operator
            self.compile_term()

        self.write_scope_close("term")

    def compile_expression_list(self) -> None:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        self.write_scope_open("expressionList")
        # First check if the list is empty:
        if self.__input_stream.token_type() != "SYMBOL" or self.__input_stream.symbol() != ")":
            self.compile_expression()
            # Now to handle (',' expression)* :
            while self.__input_stream.token_type() == "SYMBOL" and self.__input_stream.symbol() == ",":
                self.__write_symbol()  # ,
                self.compile_expression()

        self.write_scope_close("expressionList")

    def __indent(self) -> None:
        """Writes indentation to the output stream according to the current level (self.__indent_level)"""
        self.__output_stream.write(CompilationEngine.INDENT * self.__indent_level)

    def __write_keyword(self) -> None:
        self.__indent()
        self.__output_stream.write("<keyword> " + self.__input_stream.keyword().lower() + " </keyword>\n")
        self.__input_stream.advance()

    def __write_identifier(self) -> None:
        self.__indent()
        self.__output_stream.write("<identifier> " + self.__input_stream.identifier() + " </identifier>\n")
        self.__input_stream.advance()

    def __write_identifier_no_advance(self, identifier: str) -> None:
        """To be used after looking ahead into input stream - no advance() call!"""
        self.__indent()
        self.__output_stream.write("<identifier> " + identifier + " </identifier>\n")

    def __write_symbol(self) -> None:
        self.__indent()
        symbol: str = self.__input_stream.symbol()
        if symbol in CompilationEngine.SYMBOLS_BYPASS:
            symbol = CompilationEngine.SYMBOLS_BYPASS[symbol]
        self.__output_stream.write("<symbol> " + symbol + " </symbol>\n")
        self.__input_stream.advance()

    def __write_int_const(self) -> None:
        self.__indent()
        self.__output_stream.write("<integerConstant> " + str(self.__input_stream.int_val()) + " </integerConstant>\n")
        self.__input_stream.advance()

    def __write_str_const(self) -> None:
        self.__indent()
        self.__output_stream.write("<stringConstant> " + self.__input_stream.string_val() + " </stringConstant>\n")
        self.__input_stream.advance()

    def write_scope_open(self, text: str) -> None:
        self.__indent()
        self.__output_stream.write("<" + text + ">\n")
        self.__indent_level += 1

    def write_scope_close(self, text: str) -> None:
        self.__indent_level -= 1
        self.__indent()
        self.__output_stream.write("</" + text + ">\n")
