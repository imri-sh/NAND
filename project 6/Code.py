"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""

COMPUTATION_DICT = {
    "0": "110101010",
    "1": "110111111",
    "-1": "110111010",
    "D": "110001100",
    "A": "110110000",
    "M": "111110000",
    "!D": "110001101",
    "!A": "110110001",
    "!M": "111110001",
    "-D": "110001111",
    "-A": "110110011",
    "-M": "111110011",
    "D+1": "110011111",
    "A+1": "110110111",
    "M+1": "111110111",
    "D-1": "110001110",
    "A-1": "110110010",
    "M-1": "111110010",
    "D+A": "110000010",
    "D+M": "111000010",
    "D-A": "110010011",
    "D-M": "111010011",
    "A-D": "110000111",
    "M-D": "111000111",
    "D&A": "110000000",
    "D&M": "111000000",
    "D|A": "110010101",
    "D|M": "111010101",
    "A<<": "010100000",
    "D<<": "010110000",
    "M<<": "011100000",
    "A>>": "010000000",
    "D>>": "010010000",
    "M>>": "011000000",
}


class Code:
    """Translates Hack assembly language mnemonics into binary codes."""

    @staticmethod
    def dest(mnemonic: str) -> str:
        """
        Args:
            mnemonic (str): a dest mnemonic string.

        Returns:
            str: 3-bit long binary code of the given mnemonic.
        """
        a_bit = '0'
        d_bit = '0'
        m_bit = '0'

        for i in range(len(mnemonic)):
            if mnemonic[i] == 'A':
                a_bit = '1'
            elif mnemonic[i] == 'D':
                d_bit = '1'
            elif mnemonic[i] == 'M':
                m_bit = '1'

        code = a_bit + d_bit + m_bit
        return code

    @staticmethod
    def comp(mnemonic: str) -> str:
        """
        Args:
            mnemonic (str): a comp mnemonic string.

        Returns:
            str: the binary code of the given mnemonic.
        """
        return COMPUTATION_DICT[mnemonic]

    @staticmethod
    def jump(mnemonic: str) -> str:
        """
        Args:
            mnemonic (str): a jump mnemonic string.

        Returns:
            str: 3-bit long binary code of the given mnemonic.
        """
        if mnemonic == "":
            return "000"
        elif mnemonic == "JGT":
            return "001"
        elif mnemonic == "JEQ":
            return "010"
        elif mnemonic == "JGE":
            return "011"
        elif mnemonic == "JLT":
            return "100"
        elif mnemonic == "JNE":
            return "101"
        elif mnemonic == "JLE":
            return "110"
        elif mnemonic == "JMP":
            return "111"

    @staticmethod
    def convert_to_binary(string: str) -> str:
        """
        Args:
            string (str): a string of a decimal number

        Returns:
            str: the binary representation of the given number.
        """
        integer = int(string)
        return format(integer, 'b')

    @staticmethod
    def get_padding(string: str) -> str:
        """
        Args:
            string (str): a string of up to 15 characters

        Returns:
            str: A padding of 0-s needed to complete the string into 15 characters
        """
        pad_count: int = 16 - len(string)
        return "0" * pad_count
