"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class Parser:
    """Encapsulates access to the input code. Reads an assembly program
    by reading each command line-by-line, parses the current command,
    and provides convenient access to the commands components (fields
    and symbols). In addition, removes all white space and comments.
    """

    def __init__(self, input_file: typing.TextIO) -> None:
        """Opens the input file and gets ready to parse it.

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
            cur_line = "".join(line.split())
            cur_line = cur_line.split("//")[0]  # get rid of comments
            if len(cur_line) > 0:  # In case line is just a comment or white-spaces
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
        """Reads the next command from the input and makes it the current command.
        Should be called only if has_more_commands() is true.
        """
        self.__lines_index += 1
        self.__cur_line = self.__input_lines[self.__lines_index]

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current command:
            "A_COMMAND" for @Xxx where Xxx is either a symbol or a decimal number
            "C_COMMAND" for dest=comp;jump
            "L_COMMAND" (actually, pseudo-command) for (Xxx) where Xxx is a symbol
        """
        # Read the first non-white-space character in the current command.
        # If '@' - A-command, if '(' - L-command, else: C-command
        first_char = self.__cur_line[0]
        if first_char == '@':
            return "A_COMMAND"
        elif first_char == '(':
            return "L_COMMAND"
        else:
            return "C_COMMAND"

    def symbol(self) -> str:
        """
        Returns:
            str: the symbol or decimal Xxx of the current command @Xxx or
            (Xxx). Should be called only when command_type() is "A_COMMAND" or 
            "L_COMMAND".
        """
        symbol = ""
        for i in range(1, len(self.__cur_line)):  # start for index 1 of the string - past '(' and '@'
            if self.__cur_line[i] != ')':
                symbol += self.__cur_line[i]
        return symbol

    def dest(self) -> str:
        """
        Returns:
            str: the dest mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        if self.__cur_line.__contains__("="):  # Destination isn't empty
            return self.__cur_line.split("=")[0]
        else:
            return ""

    def comp(self) -> str:
        """
        Returns:
            str: the comp mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        if self.__cur_line.__contains__("="):  # Destination isn't empty
            post_eq: str = self.__cur_line.split("=")[1]
            return post_eq.split(";")[0]
        return self.__cur_line.split(";")[0]  # Dest is empty - it's enough to split by ';'

    def jump(self) -> str:
        """
        Returns:
            str: the jump mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        split: list[str] = self.__cur_line.split(";")
        if len(split) == 1:
            return ""
        return split[len(split) - 1]

    def reset(self) -> None:
        """
        Resets the index to 0- allowing the user to go over the file again.
        """
        self.__lines_index = 0
        self.__cur_line = self.__input_lines[self.__lines_index]
