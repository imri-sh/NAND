"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""

SEGMENT = {"FIELD": "this", "STATIC": "static", "ARG": "argument", "VAR": "local"}


class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        self.__table: list[tuple[str, str, str, int]] = list()
        self.__static_index = 0
        self.__field_index = 0
        self.__arg_index = 0
        self.__local_index = 0  # for var <type> <identifier> (,<identifier>)*

    def start_subroutine(self) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's 
        symbol table).
        """
        self.__table: list[tuple[str, str, str, int]] = list()
        self.__static_index = 0
        self.__field_index = 0
        self.__arg_index = 0
        self.__local_index = 0  # for var <type> <identifier> (,<identifier>)*

    def define(self, name: str, var_type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class scope, 
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            var_type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        if kind == "STATIC":
            index = self.__static_index
            self.__static_index += 1
        elif kind == "FIELD":
            index = self.__field_index
            self.__field_index += 1
        elif kind == "ARG":
            index = self.__arg_index
            self.__arg_index += 1
        else:
            assert (kind == "VAR")  # sanity check
            index = self.__local_index
            self.__local_index += 1
        self.__table.append((name, var_type, SEGMENT[kind], index))

    def var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in 
            the current scope.
        """
        if kind == "STATIC":
            return self.__static_index
        elif kind == "FIELD":
            return self.__field_index
        elif kind == "ARG":
            return self.__arg_index
        else:
            assert (kind == "VAR")  # sanity check
            return self.__local_index

    def kind_of(self, name: str):
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str (kind): the kind of the named identifier in the current scope,
            can be "STATIC", "FIELD", "ARG", "VAR", or None
            if the identifier is unknown in the current scope.
        """
        assert (self.is_in(name))  # Sanity check
        for tup in self.__table:
            if tup[0] == name:
                return tup[2]
        return None

    def type_of(self, name: str) -> str:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope.
            str (type) can be: "int", "char", "boolean", className.
        """
        assert (self.is_in(name))  # Sanity check
        for tup in self.__table:
            if tup[0] == name:
                return tup[1]

    def index_of(self, name: str) -> int:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier.
        """
        assert (self.is_in(name))  # Sanity check
        for tup in self.__table:
            if tup[0] == name:
                return tup[3]

    def is_in(self, name: str) -> bool:
        """
        Checks whether the given variable name is registered in the SymbolTable.
        """
        for tup in self.__table:
            if tup[0] == name:
                return True
        return False
