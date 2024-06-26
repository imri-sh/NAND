"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class JackTokenizer:
    """Removes all comments from the input stream and breaks it
    into Jack language tokens, as specified by the Jack grammar.
    
    # Jack Language Grammar

    A Jack file is a stream of characters. If the file represents a
    valid program, it can be tokenized into a stream of valid tokens. The
    tokens may be separated by an arbitrary number of whitespace characters, 
    and comments, which are ignored. There are three possible comment formats: 
    /* comment until closing */ , /** API comment until closing */ , and
    // comment until the line’s end.

    - ‘xxx’: quotes are used for tokens that appear verbatim (‘terminals’).
    - xxx: regular typeface is used for names of language constructs 
           (‘non-terminals’).
    - (): parentheses are used for grouping of language constructs.
    - x | y: indicates that either x or y can appear.
    - x?: indicates that x appears 0 or 1 times.
    - x*: indicates that x appears 0 or more times.

    ## Lexical Elements

    The Jack language includes five types of terminal elements (tokens).

    - keyword: 'class' | 'constructor' | 'function' | 'method' | 'field' | 
               'static' | 'var' | 'int' | 'char' | 'boolean' | 'void' | 'true' |
               'false' | 'null' | 'this' | 'let' | 'do' | 'if' | 'else' | 
               'while' | 'return'
    - symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
    - integerConstant: A decimal number in the range 0-32767.
    - StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"'
    - identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.

    ## Program Structure

    A Jack program is a collection of classes, each appearing in a separate 
    file. A compilation unit is a single class. A class is a sequence of tokens 
    structured according to the following context free syntax:
    
    - class: 'class' className '{' classVarDec* subroutineDec* '}'
    - classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    - type: 'int' | 'char' | 'boolean' | className
    - subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) subroutineName
                                                                                    '(' parameterList ')' subroutineBody
    - parameterList: (type varName (',' type varName)*)?
    - subroutineBody: '{' varDec* statements '}'
    - varDec: 'var' type varName (',' varName)* ';'
    - className: identifier
    - subroutineName: identifier
    - varName: identifier

    ## Statements

    - statements: statement*
    - statement: letStatement | ifStatement | whileStatement | doStatement | 
                 returnStatement
    - letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
    - ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' 
                   statements '}')?
    - whileStatement: 'while' '(' 'expression' ')' '{' statements '}'
    - doStatement: 'do' subroutineCall ';'
    - returnStatement: 'return' expression? ';'

    ## Expressions
    
    - expression: term (op term)*
    - term: integerConstant | stringConstant | keywordConstant |     -- INT_CONST / STRING_CONST / KEYWORD
            varName | varName '['expression']' | subroutineCall |    -- IDENTIFIER
            '(' expression ')' | unaryOp term                        -- '(' / '-' / '~'
    - subroutineCall: subroutineName '(' expressionList ')' | (className | 
                      varName) '.' subroutineName '(' expressionList ')'
    - expressionList: (expression (',' expression)* )?
    - op: '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    - unaryOp: '-' | '~' | '^' | '#'
    - keywordConstant: 'true' | 'false' | 'null' | 'this'
    
    Note that ^, # correspond to shiftleft and shiftright, respectively.
    """
    WHITESPACES = {" ", "\n", "	", "", "	", "\r"}
    KEYWORDS = {'class', 'constructor', 'function', 'method', 'field',
                'static', 'var', 'int', 'char', 'boolean', 'void', 'true',
                'false', 'null', 'this', 'let', 'do', 'if', 'else',
                'while', 'return'}
    SYMBOLS = {'{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '|', '<', '>', '=', '~', '^', '#'}
    BINARY_OPERATORS = {"+", "-", "*", "/", "&", "|", "<", ">", "="}
    UNARY_OP = {"-", "~", "^", "#"}
    KEYWORD_CONST = {"TRUE", "FALSE", "NULL", "THIS"}
    TYPES = {"INT", "CHAR", "BOOLEAN"}

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.
        """
        self.__text: str = str()
        self.process_text(input_stream)
        self.__text_length = len(self.__text)
        self.__text_index = 0  # index of the first letter not yet read

        self.current_token: str = str()
        self.__token_type: str = str()
        self.token_str_val: str = str()

        self.advance()

    def process_text(self, input_file: typing.TextIO) -> None:
        """Removes all comments from the input file:
        //                (till end of line)
        /* <comment> */   (can be multi-line)
        /** <comment> */  (can be multi-line)
        (Does not count as comments if inside a string!)
        Sets self.__text to the text without comments, with no trailing whitespaces, which is critical
        for advance() and has_more_tokens()!.
        """
        # First - add padding to text. Lets us check and jump 2 characters forward without going out of bounds, extra
        # whitespaces do not change the tokenized result.
        raw_text: str = input_file.read() + "   "
        text_index: int = 0
        processed_text: str = str()
        string_flag: bool = False
        multi_line_comment: bool = False
        line_comment: bool = False

        while text_index < len(raw_text) - 3:  # -3 as we've padded the text.
            # Check if we're in a comment:
            if line_comment:
                # Inside a line comment:
                if raw_text[text_index] == "\n":  # Comment ended, append the new-line char which ended it
                    line_comment = False
                    processed_text += raw_text[text_index]
                    text_index += 1
                    continue
                else:  # Still inside line-comment - no need to add the current character
                    text_index += 1
                    continue
            elif multi_line_comment:
                # Inside a multi-line comment:
                if raw_text[text_index] + raw_text[text_index + 1] == "*/":
                    multi_line_comment = False  # multi-line comment end. Skip the characters..
                    text_index += 2
                else:  # Still inside comment - move to next character
                    text_index += 1
                continue
            # Everything below this line is the case in which we're not inside a comment:
            elif raw_text[text_index] == '"':  # Checks for string start/end:
                processed_text += raw_text[text_index]
                if string_flag:  # string end
                    string_flag = False
                else:  # string start
                    string_flag = True
                text_index += 1
                continue
            else:  # Not a string start/end, not inside a comment. Check for comment start, outside of string only!
                if raw_text[text_index] + raw_text[text_index + 1] == "//" and not string_flag:  # line-comment start
                    line_comment = True
                    text_index += 2
                    continue
                elif raw_text[text_index] + raw_text[text_index + 1] == "/*" and not string_flag:
                    # Note - this case also holds for /** comment open.
                    multi_line_comment = True
                    text_index += 2
                    continue
                else:  # Not string start/end, not inside comment, not comment start.
                    # append character to text and move to next one:
                    processed_text += raw_text[text_index]
                    text_index += 1
        self.__text = processed_text.strip()

    def has_more_tokens(self) -> bool:
        """Do we have more tokens in the input?

        Returns:
            bool: True if there are more tokens, False otherwise.
            relies on the fact that the text is strip - no trailing whitespace!
        """
        return self.__text_index <= self.__text_length - 1

    def advance(self) -> None:
        """Gets the next token from the input and makes it the current token. 
        This method should be called if has_more_tokens() is true.
        Only works when the text is stripped - no trailing whitespace!
        """
        if not self.has_more_tokens():
            return

        # Read first letter of token:
        first_letter: str = self.__text[self.__text_index]
        self.__text_index += 1
        # skip whitespaces:
        while first_letter in JackTokenizer.WHITESPACES:
            first_letter = self.__text[self.__text_index]
            self.__text_index += 1
        # set the current token to be the first letter:
        self.current_token = first_letter
        # In case current token is a symbol:
        if first_letter in JackTokenizer.SYMBOLS:
            self.__token_type = "SYMBOL"
            return

        # Now, keep appending letters until token ender is found.
        if first_letter == '"':  # In case of a string constant:
            is_string = True
        else:
            is_string = False
        break_flag = False
        while self.__text_index < self.__text_length - 1:
            next_letter = self.__text[self.__text_index]
            if (next_letter in JackTokenizer.WHITESPACES or next_letter in JackTokenizer.SYMBOLS) and not is_string:
                break
            if is_string and next_letter == '"':  # read last letter and break
                break_flag = True
            # Add the next letter and increment the index:
            self.current_token = self.current_token + next_letter
            self.__text_index += 1
            # In case of string end:
            if break_flag:
                break

        if self.current_token in JackTokenizer.KEYWORDS:
            self.__token_type = "KEYWORD"
        elif self.current_token.isnumeric():
            self.__token_type = "INT_CONST"
        elif self.current_token[0] == '"' and self.current_token[len(self.current_token) - 1] == '"':
            self.__token_type = "STRING_CONST"
            self.token_str_val = self.current_token[1:len(self.current_token) - 1]
        else:
            self.__token_type = "IDENTIFIER"

    def token_type(self) -> str:
        """
        Returns:
            str: the type of the current token, can be
                "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
        """
        return self.__token_type

    def keyword(self) -> str:
        """
        Returns:
            str: the keyword which is the current token.
            Should be called only when token_type() is "KEYWORD".
            Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT", 
            "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO", 
            "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
        """
        return self.current_token.upper()

    def symbol(self) -> str:
        """
        Returns:
            str: the character which is the current token.
            Should be called only when token_type() is "SYMBOL".
            Recall that symbol was defined in the grammar like so:
            symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
        """
        return self.current_token

    def identifier(self) -> str:
        """
        Returns:
            str: the identifier which is the current token.
            Should be called only when token_type() is "IDENTIFIER".
            Recall that identifiers were defined in the grammar like so:
            identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc.'.
        """
        return self.current_token

    def int_val(self) -> int:
        """
        Returns:
            str: the integer value of the current token.
            Should be called only when token_type() is "INT_CONST".
            Recall that integerConstant was defined in the grammar like so:
            integerConstant: A decimal number in the range 0-32767.
        """
        return int(self.current_token)

    def string_val(self) -> str:
        """
        Returns:
            str: the string value of the current token, without the double 
            quotes. Should be called only when token_type() is "STRING_CONST".
            Recall that StringConstant was defined in the grammar like so:
            StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"'
        """
        return self.token_str_val
