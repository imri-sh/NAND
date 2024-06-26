// This file is part of nand2tetris, as taught in The Hebrew University, and
// was written by Aviv Yaish. It is an extension to the specifications given
// [here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
// as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
// Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).

// This program illustrates low-level handling of the screen and keyboard
// devices, as follows.
//
// The program runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.
// 
// Assumptions:
// Your program may blacken and clear the screen's pixels in any spatial/visual
// Order, as long as pressing a key continuously for long enough results in a
// fully blackened screen, and not pressing any key for long enough results in a
// fully cleared screen.
//
// Test Scripts:
// For completeness of testing, test the Fill program both interactively and
// automatically.
// 
// The supplied FillAutomatic.tst script, along with the supplied compare file
// FillAutomatic.cmp, are designed to test the Fill program automatically, as 
// described by the test script documentation.
//
// The supplied Fill.tst script, which comes with no compare file, is designed
// to do two things:
// - Load the Fill.hack program
// - Remind you to select 'no animation', and then test the program
//   interactively by pressing and releasing some keyboard keys

// Put your code here.

(OUTLOOP)
    //set i=0 to loop on screen memory:
    @i
    M=0
    //Store user input in D:
    @KBD
    D=M
    //If D=0, whiten screen. Else, darken screen.
    @WHITEN
    D;JEQ
    @DARKEN
    0;JMP

    (WHITEN)
        //Check if i=8192 (out of bounds)
        @8192
        D=A
        @i
        D=D-M
        //terminate if i=8192:
        @OUTLOOP 
        D;JEQ
        //Set address to (SCREEN+i):
        @SCREEN
        D=A
        @i
        A=D+M //now A contains the address of the row we want to work on
        M=0 //"paint" row in white
        //increment i:
        @i
        M=M+1
        //Jump to start of whiten loop:
        @WHITEN
        0;JMP


    (DARKEN)
        //Check if i=8192 (out of bounds)
        @8192
        D=A
        @i
        D=D-M
        //terminate if i=8192:
        @OUTLOOP 
        D;JEQ
        //Set address to (SCREEN+i):
        @SCREEN
        D=A
        @i
        A=D+M //now A contains the address of the row we want to work on
        M=-1 //"paint" row in black
        //increment i:
        @i
        M=M+1
        //Jump to start of darken loop:
        @DARKEN
        0;JMP