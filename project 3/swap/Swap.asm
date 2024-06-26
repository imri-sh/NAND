// This file is part of nand2tetris, as taught in The Hebrew University, and
// was written by Aviv Yaish. It is an extension to the specifications given
// [here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
// as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
// Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).

// The program should swap between the max. and min. elements of an array.
// Assumptions:
// - The array's start address is stored in R14, and R15 contains its length
// - Each array value x is between -16384 < x < 16384
// - The address in R14 is at least >= 2048
// - R14 + R15 <= 16383
//
// Requirements:
// - Changing R14, R15 is not allowed.

// Put your code here.


//Make sure array isn't empty
@R15
D=M
@END
D;JEQ //If it is, jump to end (nothing to swap)

//Initialize variables (addresses to the array's beginning, values to first element in the array)
@R14
D=M
@minAddress
M=D
@maxAddress
M=D
@R14
A=M
D=M
@minValue
M=D
@maxValue
M=D
//Now initialize i - the index variable
@i
M=-1 //-1, as i increments at start of loop to avoid duplicating code.

//start the search for min and max values in the array:
(SEARCH)
    @i
    M=M+1
    //Check that i is still in bounds:
    @R15
    D=M //D= array.length
    @i
    D=D-M //D now holds (array.length-i). If D<=0 then we're done iterating over the array, move to swap:
    @SWAP
    D;JEQ
    //Check if arr[i] is an element bigger/smaller than current max/min, respectively:
    //Bigger:
    @R14
    D=M
    @i
    A=D+M //A now holds the address arr+i
    D=M //D now holds arr[i]
    @maxValue
    D=D-M //D is now (arr[i]-maxValue). Check if it positive (new max found):
    @NEWMAX
    D;JGT
    //Smaller:
    @R14
    D=M
    @i
    A=D+M //A now holds the address arr+i
    D=M //D now holds arr[i]
    @minValue
    D=D-M //D is now (arr[i]-minValue). Check if it is negative (new min found):
    @NEWMIN
    D;JLT
    //arr[i] is not a new min/max. Continue SEARCH:
    @SEARCH
    0;JMP

    (NEWMAX) //New max was found. Save it and continue SEARCH:
        @R14
        D=M
        @i
        D=D+M //D now holds the address arr+i (the address of the new max)
        @maxAddress
        AM=D
        D=M //D now holds arr[i] (the new maximum value)
        @maxValue
        M=D
        //Finished, continue SEARCH
        @SEARCH
        0;JMP

    (NEWMIN) //New min was found. Save it and continue SEARCH:
        @R14
        D=M
        @i
        D=D+M //D now holds the address arr+i
        @minAddress
        AM=D
        D=M
        @minValue
        M=D
        //Finished, continue SEARCH
        @SEARCH
        0;JMP

(SWAP) //Swap min and max elements found, according to the variables (minAddress, minValue, maxAddress, maxValue)
    //Swap max with min:
    @minValue
    D=M
    @maxAddress
    A=M
    M=D
    //swap min with max:
    @maxValue
    D=M
    @minAddress
    A=M
    M=D

(END)
    @END
    0;JMP