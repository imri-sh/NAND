"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import os
import sys
import typing
from SymbolTable import SymbolTable
from Parser import Parser
from Code import Code

A_CMD = "A_COMMAND"
C_CMD = "C_COMMAND"
L_CMD = "L_COMMAND"


def assemble_file(input_file: typing.TextIO, output_file: typing.TextIO) -> None:
    """Assembles a single file.

    Args:
        input_file (typing.TextIO): the file to assemble.
        output_file (typing.TextIO): writes all output to this file.
    """
    parser = Parser(input_file)  # Note - parser already removes all comments and white spaces
    symtable = SymbolTable()

    first_pass(parser, symtable)
    second_pass(parser, symtable, output_file)


def first_pass(parser: Parser, symtable: SymbolTable) -> None:
    next_address: int = 0
    # FIRST PASS - log all label declarations into symtable:
    while True:
        command_type = parser.command_type()

        if command_type == A_CMD or command_type == C_CMD:
            next_address += 1
        elif command_type == L_CMD:
            symbol: str = parser.symbol()
            if not symtable.contains(symbol):
                symtable.add_entry(symbol, next_address)

        if not parser.has_more_commands():
            break
        parser.advance()

    parser.reset()


def second_pass(parser: Parser, symtable: SymbolTable, output_file: typing.TextIO) -> None:
    symbol_address: int = 16
    while True:
        # Check current line command type:
        command_type = parser.command_type()
        if command_type == A_CMD:
            post_at = parser.symbol()
            if post_at.isnumeric():  # The command uses a decimal number and not a symbol.
                binary_rep: str = Code.convert_to_binary(post_at)
                output_file.write(Code.get_padding(binary_rep) + binary_rep + "\n")
            else:  # The command uses a symbol.
                if symtable.contains(post_at):  # The command uses a pre-existing symbol
                    pre_existing_address: str = str(symtable.get_address(post_at))
                    binary_rep: str = Code.convert_to_binary(pre_existing_address)
                    output_file.write(Code.get_padding(binary_rep) + binary_rep + "\n")
                else:  # The command is not a pre-existing symbol. Add to symtable and write binary command:
                    symtable.add_entry(post_at, symbol_address)
                    binary_rep = Code.convert_to_binary(str(symbol_address))
                    output_file.write(Code.get_padding(binary_rep) + binary_rep + "\n")
                    symbol_address += 1

        elif command_type == C_CMD:
            dest: str = Code.dest(parser.dest())
            comp: str = Code.comp(parser.comp())
            jump: str = Code.jump(parser.jump())
            c_instruction_prefix: str = "1"
            output: str = c_instruction_prefix + comp + dest + jump + "\n"
            output_file.write(output)

        if not parser.has_more_commands():
            break
        parser.advance()


if "__main__" == __name__:
    # Parses the input path and calls assemble_file on each input file.
    # This opens both the input and the output files!
    # Both are closed automatically when the code finishes running.
    # If the output file does not exist, it is created automatically in the
    # correct path, using the correct filename.
    if not len(sys.argv) == 2:
        sys.exit("Invalid usage, please use: Assembler <input path>")
    argument_path = os.path.abspath(sys.argv[1])
    if os.path.isdir(argument_path):
        files_to_assemble = [
            os.path.join(argument_path, filename)
            for filename in os.listdir(argument_path)]
    else:
        files_to_assemble = [argument_path]
    for input_path in files_to_assemble:
        filename, extension = os.path.splitext(input_path)
        if extension.lower() != ".asm":
            continue
        output_path = filename + ".hack"
        with open(input_path, 'r') as input_file, \
                open(output_path, 'w') as output_file:
            assemble_file(input_file, output_file)
