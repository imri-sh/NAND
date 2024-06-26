"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class Parser:
    """
    # Parser
    
    Handles the parsing of a single .vm file, and encapsulates access to the
    input code. It reads VM commands, parses them, and provides convenient 
    access to their components. 
    In addition, it removes all white space and comments.

    ## VM Language Specification

    A .vm file is a stream of characters. If the file represents a
    valid program, it can be translated into a stream of valid assembly 
    commands. VM commands may be separated by an arbitrary number of whitespace
    characters and comments, which are ignored. Comments begin with "//" and
    last until the line’s end.
    The different parts of each VM command may also be separated by an arbitrary
    number of non-newline whitespace characters.

    - Arithmetic commands:
      - add, sub, and, or, eq, gt, lt
      - neg, not, shiftleft, shiftright
    - Memory segment manipulation:
      - push <segment> <number>
      - pop <segment that is not constant> <number>
      - <segment> can be any of: argument, local, static, constant, this, that, 
                                 pointer, temp
    - Branching (only relevant for project 8):
      - label <label-name>
      - if-goto <label-name>
      - goto <label-name>
      - <label-name> can be any combination of non-whitespace characters.
    - Functions (only relevant for project 8):
      - call <function-name> <n-args>
      - function <function-name> <n-vars>
      - return
    """

    ARITHMETIC_LOGICAL_COMMANDS = {
        "add",
        "sub",
        "neg",
        "eq",
        "gt",
        "lt",
        "and",
        "or",
        "not",
        "shiftleft",
        "shiftright"
    }

    COMMANDS = {
        "pop": "C_POP",
        "push": "C_PUSH",
        "label": "C_LABEL",  # TODO - Placeholder until project 8
        "goto": "C_GOTO",  # TODO - Placeholder until project 8
        "if-goto": "C_IF",  # TODO - Placeholder until project 8
        "function": "C_FUNCTION",  # TODO - Placeholder until project 8
        "return": "C_RETURN",  # TODO - Placeholder until project 8
        "call": "C_CALL"  # TODO - Placeholder until project 8
    }

    def __init__(self, input_file: typing.TextIO) -> None:
        """Gets ready to parse the input file.

        Args:
            input_file (typing.TextIO): input file.
        """
        self.__input_lines = list()
        self.strip_lines(input_file)

        self.__lines_index = 0
        self.__cur_line: str = self.__input_lines[self.__lines_index]

    def strip_lines(self, input_file: typing.TextIO) -> None:
        lines_raw: list[str] = input_file.read().strip().splitlines()
        for line in lines_raw:
            cur_line = line.strip()
            cur_line = cur_line.split("//")[0]  # get rid of comments
            if len(cur_line) > 0:  # In case line was just a comment or white-spaces
                self.__input_lines.append(cur_line)

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        if self.__lines_index < len(self.__input_lines) - 1:
            return True
        return False

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current 
        command. Should be called only if has_more_commands() is true. Initially
        there is no current command.
        """
        self.__lines_index += 1
        self.__cur_line = self.__input_lines[self.__lines_index]

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current VM command.
            "C_ARITHMETIC" is returned for all arithmetic commands.
            For other commands, can return:
            "C_PUSH", "C_POP", "C_LABEL", "C_GOTO", "C_IF", "C_FUNCTION",
            "C_RETURN", "C_CALL".
        """
        # TODO - For project 8 - implement support for the rest of the commands. Done? I think
        command: str = self.__cur_line.split()[0]
        if command in Parser.ARITHMETIC_LOGICAL_COMMANDS:
            return "C_ARITHMETIC"
        else:
            return Parser.COMMANDS[command]

    def arg1(self) -> str:
        """
        Returns:
            str: the first argument of the current command. In case of 
            "C_ARITHMETIC", the command itself (add, sub, etc.) is returned. 
            Should not be called if the current command is "C_RETURN".
        """
        # TODO - For project 8 - implement reading lines which aren't C/Memory commands. (Already) Done? I think
        if self.command_type() == "C_ARITHMETIC":
            return self.__cur_line.split()[0]
        else:  # Not an arithmetic command - return first argument:
            return self.__cur_line.split()[1]

    def arg2(self) -> int:
        """
        Returns:
            int: the second argument of the current command. Should be
            called only if the current command is "C_PUSH", "C_POP", 
            "C_FUNCTION" or "C_CALL".
        """
        val = self.__cur_line.split()[2]
        return int(val)
