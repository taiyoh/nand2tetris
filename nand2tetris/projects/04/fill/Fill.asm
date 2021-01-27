// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(INPUTLOOP)
    @KBD
    D=M
    @FILLBLACK
    D;JGT
    @FILLWHITE
    0;JMP

(FILLWHITE)
    @color
    M=0
    @FILLSCREEN
    0;JMP

(FILLBLACK)
    @color
    M=-1
    @FILLSCREEN
    0;JMP

(FILLSCREEN)
    @SCREEN
    D=A
    @screenaddr
    M=D
    @cursor
    M=0
(LOOP)
    @color
    D=M
    @screenaddr
    A=M
    M=D
    @cursor
    MD=M+1
    @8192
    D=D-A
    @INPUTLOOP
    D;JGE
    @screenaddr
    M=M+1
    @LOOP
    0;JMP
