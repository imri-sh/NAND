"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class CodeWriter:
    """Translates VM commands into Hack assembly code."""

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Initializes the CodeWriter.

        Args:
            output_stream (typing.TextIO): output stream.
        """
        self.output_stream = output_stream
        self.label_index = 0
        self.current_filename = "N/A"

    def set_file_name(self, filename: str) -> None:
        """Informs the code writer that the translation of a new VM file is 
        started.

        Args:
            filename (str): The name of the VM file.
        """
        # Your code goes here!
        # This function is useful when translating code that handles the
        # static segment. For example, in order to prevent collisions between two
        # .vm files which push/pop to the static segment, one can use the current
        # file's name in the assembly variable's name and thus differentiate between
        # static variables belonging to different files.
        # To avoid problems with Linux/Windows/MacOS differences with regards
        # to filenames and paths, you are advised to parse the filename in
        # the function "translate_file" in Main.py using python's os library,
        # For example, using code similar to:
        # input_filename, input_extension = os.path.splitext(os.path.basename(input_file.name))
        self.label_index = 0
        self.current_filename = filename

    def write_arithmetic(self, command: str) -> None:
        """Writes assembly code that is the translation of the given 
        arithmetic command. For the commands: eq, lt, gt, you should correctly
        compare between all numbers our computer supports, and we define the
        value "true" to be -1, and "false" to be 0.

        Args:
            command (str): an arithmetic command.
        """
        output: str = CodeWriter.ARITHMETIC_COMMANDS[command]
        if command in {"add", "sub", "neg", "not", "shiftleft", "shiftright"}:  # Commands with no labels
            self.output_stream.write(CodeWriter.ARITHMETIC_COMMANDS[command])
        elif command == "eq" or command == "and" or command == "or":  # Commands with 2 labels
            label_result: str = self.current_filename + ".LABEL." + str(self.label_index)
            label_end: str = self.current_filename + ".LABEL." + str(self.label_index + 1)
            self.output_stream.write(output.format(RES=label_result, END=label_end))
            self.label_index += 2
        elif command == "gt" or command == "lt":  # Commands with 5 labels
            labels = list()
            for i in range(0, 5):
                labels.append(self.current_filename + ".LABEL." + str(self.label_index + i))
            self.output_stream.write(output.format(Y_LT_ZERO=labels[0],
                                                   X_LT_Y=labels[1],
                                                   SUBTRACT=labels[2],
                                                   END=labels[3],
                                                   Y_LT_X=labels[4])
                                     )
            self.label_index += 5

    def write_push_pop(self, command: str, segment: str, index: int) -> None:
        """Writes assembly code that is the translation of the given 
        command, where command is either C_PUSH or C_POP.

        Args:
            command (str): "C_PUSH" or "C_POP".
            segment (str): the memory segment to operate on.
            index (int): the index in the memory segment.
        """
        if segment in {"local", "argument", "this", "that"}:
            segment_code: str = CodeWriter.SEGMENT_CODES[segment]
            if command == "C_PUSH":  # Push from segment (not static/constant)
                self.push_from_segment(segment_code, str(index))
                return
            elif command == "C_POP":  # Pop to segment (not static/constant)
                self.output_stream.write(CodeWriter.PUSH_POP_CMDS["pop_segment"].format(segment_code=segment_code,
                                                                                        index=index))
                return
        elif segment in {"temp", "pointer"}:
            # Set up the base index according to segment:
            if segment == "pointer":
                base_address = 3
            else:  # segment is temp
                base_address = 5
            # Write to file the push/pop command:
            if command == "C_PUSH":
                self.output_stream.write(
                    CodeWriter.PUSH_POP_CMDS["push_temp_or_pointer"].format(base_address=base_address, index=index))
                return
            elif command == "C_POP":
                self.output_stream.write(
                    CodeWriter.PUSH_POP_CMDS["pop_temp_or_pointer"].format(base_address=base_address, index=index))
        elif segment == "constant":  # Push to constant (pop is invalid)
            self.output_stream.write(CodeWriter.PUSH_POP_CMDS["push_const"].format(const_value=index))
            return
        elif segment == 'static':
            if command == "C_PUSH":  # Push static
                self.output_stream.write(CodeWriter.PUSH_POP_CMDS["push_static"].format(file_name=self.current_filename,
                                                                                        index=index))
                return
            elif command == "C_POP":  # Pop static
                self.output_stream.write(CodeWriter.PUSH_POP_CMDS["pop_static"].format(file_name=self.current_filename,
                                                                                       index=index))

    def push_from_segment(self, segment_code: str, index: str) -> None:
        self.output_stream.write(CodeWriter.PUSH_POP_CMDS["load_D"].format(segment_code=segment_code, index=index))
        self.output_stream.write(CodeWriter.PUSH_POP_CMDS["push_D"])
        self.output_stream.write(CodeWriter.PUSH_POP_CMDS["inc_SP"])

    def write_label(self, label: str) -> None:
        """Writes assembly code that affects the label command. 
        Let "Xxx.foo" be a function within the file Xxx.vm. The handling of
        each "label bar" command within "Xxx.foo" generates and injects the symbol
        "Xxx.foo$bar" into the assembly code stream.
        When translating "goto bar" and "if-goto bar" commands within "foo",
        the label "Xxx.foo$bar" must be used instead of "bar".

        Args:
            label (str): the label to write.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        pass

    def write_goto(self, label: str) -> None:
        """Writes assembly code that affects the goto command.

        Args:
            label (str): the label to go to.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        pass

    def write_if(self, label: str) -> None:
        """Writes assembly code that affects the if-goto command. 

        Args:
            label (str): the label to go to.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        pass

    def write_function(self, function_name: str, n_vars: int) -> None:
        """Writes assembly code that affects the function command. 
        The handling of each "function Xxx.foo" command within the file Xxx.vm
        generates and injects a symbol "Xxx.foo" into the assembly code stream,
        that labels the entry-point to the function's code.
        In the subsequent assembly process, the assembler translates this 
        symbol into the physical address where the function code starts.

        Args:
            function_name (str): the name of the function.
            n_vars (int): the number of local variables of the function.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        # The pseudo-code of "function function_name n_vars" is:
        # (function_name)       // injects a function entry label into the code
        # repeat n_vars times:  // n_vars = number of local variables
        #   push constant 0     // initializes the local variables to 0
        pass

    def write_call(self, function_name: str, n_args: int) -> None:
        """Writes assembly code that affects the call command. 
        Let "Xxx.foo" be a function within the file Xxx.vm.
        The handling of each "call" command within Xxx.foo's code generates and
        injects a symbol "Xxx.foo$ret.i" into the assembly code stream, where
        "i" is a running integer (one such symbol is generated for each "call"
        command within "Xxx.foo").
        This symbol is used to mark the return address within the caller's 
        code. In the subsequent assembly process, the assembler translates this
        symbol into the physical memory address of the command immediately
        following the "call" command.

        Args:
            function_name (str): the name of the function to call.
            n_args (int): the number of arguments of the function.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        # The pseudo-code of "call function_name n_args" is:
        # push return_address   // generates a label and pushes it to the stack
        # push LCL              // saves LCL of the caller
        # push ARG              // saves ARG of the caller
        # push THIS             // saves THIS of the caller
        # push THAT             // saves THAT of the caller
        # ARG = SP-5-n_args     // repositions ARG
        # LCL = SP              // repositions LCL
        # goto function_name    // transfers control to the callee
        # (return_address)      // injects the return address label into the code
        pass

    def write_return(self) -> None:
        """Writes assembly code that affects the return command."""
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        # The pseudo-code of "return" is:
        # frame = LCL                   // frame is a temporary variable
        # return_address = *(frame-5)   // puts the return address in a temp var
        # *ARG = pop()                  // repositions the return value for the caller
        # SP = ARG + 1                  // repositions SP for the caller
        # THAT = *(frame-1)             // restores THAT for the caller
        # THIS = *(frame-2)             // restores THIS for the caller
        # ARG = *(frame-3)              // restores ARG for the caller
        # LCL = *(frame-4)              // restores LCL for the caller
        # goto return_address           // go to the return address
        pass

    # Note - In the comments - y is the last element in the stack when the command began.
    # x is the second to last element.

    ARITHMETIC_COMMANDS = {
        "and": "\n//And (bitwise) command:\n"
               "@SP \n"
               "AM=M-1 // SP->y, A armed with y's address \n"
               "D=M //D==y \n"
               "A=A-1 //A armed with x's address \n"
               "M=D&M\n",
        "or": "\n//And (bitwise) command:\n"
              "@SP \n"
              "AM=M-1 // SP->y, A armed with y's address \n"
              "D=M //D==y \n"
              "A=A-1 //A armed with x's address \n"
              "M=D|M\n",
        "not": "\n//not command: \n"
               "@SP \n"
               "A=M-1 \n"
               "M=!M \n",
        "shiftleft": "\n//Shift-left command: \n"
               "@SP \n"
               "A=M-1 \n"
               "M=M<< \n",
        "shiftright": "\n//Shift-right command: \n"
               "@SP \n"
               "A=M-1 \n"
               "M=M>> \n",
        "add": "\n//add command: \n"
               "@SP \n"
               "AM=M-1 //SP->y, A armed with y's address \n"
               "D=M //D==y \n"
               "@SP //SP->y \n"
               "AM=M-1 //SP->x, A armed with x's address \n"
               "M=M+D //x=x+y\n"
               "//increment top of stack address (SP): \n"
               "@SP \n"
               "M=M+1 \n",
        "sub": "\n//subtract command: \n"
               "@SP \n"
               "AM=M-1 //SP->y, A armed with y's address \n"
               "D=M //D==y \n"
               "@SP //SP->y \n"
               "AM=M-1 //SP->x, A armed with x's address \n"
               "M=M-D //x=x-y\n"
               "//increment top of stack address (SP): \n"
               "@SP \n"
               "M=M+1 \n",
        "neg": "\n//negate command: \n"
               "@SP \n"
               "A=M-1 \n"
               "M=-M \n",
        "eq": "\n//equals command:\n"
              "@SP \n"
              "AM=M-1 //SP->y, A armed with y's address \n"
              "D=M //D==y \n"
              "A=A-1 //A armed with x's address \n"
              "D=D-M //D==y-x \n"
              "//Jump if result is true: \n"
              "@{RES} \n"
              "D;JEQ \n"
              "//Result is false: \n"
              "@SP //SP->y \n"
              "A=M-1 //A armed with x's address \n"
              "M=0 \n"
              "@{END} \n"
              "0;JMP \n"
              "({RES}) //Result is true: \n"
              "@SP //SP->y \n"
              "A=M-1 //A armed with x's address \n"
              "M=-1 \n"
              "({END}) \n",
        "gt": "\n//greater-than command: \n"
              "//Load y: \n"
              "@SP \n"
              "AM=M-1 //A armed with y's address. SP->y \n"
              "D=M // D==y \n"
              "//Check if y<0: \n"
              "@{Y_LT_ZERO} \n"
              "D;JLT \n"
              "//If the jump was not performed - it means y >= 0. Now we can just check if x<0: \n"
              "//Load x: \n"
              "@SP //SP->y \n"
              "AM=M-1 //A armed with x's address. SP->x \n"
              "D=M // D==x \n"
              "//Check if x<0: \n"
              "@{X_LT_Y} \n"
              "D;JLT \n"
              "//If we're here - it means that y>=0 and x>=0. We can perform normal subtraction and compare to 0: \n"
              "@{SUBTRACT} \n"
              "0;JMP \n"
              "({X_LT_Y}) // x<0<=y. insert false(0) and jump to end: \n"
              "@SP //SP->x \n"
              "A=M //A armed with x's address. \n"
              "M=0 \n"
              "@{END} \n"
              "0;JMP \n"
              "({Y_LT_ZERO}) //SP->y. y<0. Need to check if x>=0, in which case x>y (result is true) \n"
              "//Load x: \n"
              "@SP \n"
              "AM=M-1 //A Armed with x's address. SP->x \n"
              "D=M //D==x \n"
              "//Check if x>=0: \n"
              "@{Y_LT_X} //y<0<=x - result is true \n"
              "D;JGE \n"
              "//If we're here - it means that y<0 and x<=0. We can perform normal subtraction and compare to 0: \n"
              "({SUBTRACT}) \n"
              "@SP //SP->x \n"
              "A=M //A armed with x's address \n"
              "D=M //D==x \n"
              "M=0 //Pre-emptively put false. If the result is true we'll change it, else we'll jump to the end. \n"
              "A=A+1 //Armed with y's address \n"
              "D=D-M //D==x-y. If D>0 then x>y - result is true. \n"
              "@{Y_LT_X} \n"
              "D;JGT \n"
              "//If here - D<=0. Result is false. Go to END: \n"
              "@{END} \n"
              "0;JMP \n"
              "({Y_LT_X}) //y<0<=x. Insert true(-1) and continue to END (no jump) \n"
              "@SP //SP->x \n"
              "A=M  //A armed with x's address \n"
              "M=-1 \n"
              "({END}) \n"
              "@SP //SP->x \n"
              "M=M+1 //Set SP to next index in stack. \n",

        "lt": "\n//less-than command: \n"
              "//Load y: \n"
              "@SP \n"
              "AM=M-1 //A armed with y's address. SP->y \n"
              "D=M // D==y \n"
              "//Check if y<0: \n"
              "@{Y_LT_ZERO} \n"
              "D;JLT \n"
              "//If the jump was not performed - it means 0<=y. Now we can just check if x<0: \n"
              "//Load x: \n"
              "@SP //SP->y \n"
              "AM=M-1 //A armed with x's address. SP->x \n"
              "D=M // D==x \n"
              "//Check if x<0: \n"
              "@{X_LT_Y} \n"
              "D;JLT \n"
              "//If we're here - it means that y>=0 and x>=0. We can perform normal subtraction and compare to 0: \n"
              "@{SUBTRACT} \n"
              "0;JMP \n"
              "({X_LT_Y}) // x<0<=y. insert true(-1) and jump to end: \n"
              "@SP //SP->x \n"
              "A=M //A armed with x's address. \n"
              "M=-1 \n"
              "@{END} \n"
              "0;JMP \n"
              "({Y_LT_ZERO}) //SP->y. y<0. Need to check if x>=0, in which case x>y (result is false) \n"
              "//Load x: \n"
              "@SP \n"
              "AM=M-1 //A Armed with x's address. SP->x \n"
              "D=M //D==x \n"
              "//Check if x>=0: \n"
              "@{Y_LT_X} //y<0<=x - result is false \n"
              "D;JGE \n"
              "//If we're here - it means that y<0 and x<=0. We can perform normal subtraction and compare to 0: \n"
              "({SUBTRACT}) \n"
              "@SP //SP->x \n"
              "A=M //A armed with x's address \n"
              "D=M //D==x \n"
              "M=-1 //Pre-emptively put true. If the result is false we'll change it, else we'll jump to the end. \n"
              "A=A+1 //Armed with y's address \n"
              "D=D-M //D==x-y. If D>=0 then x>=y - result is false. \n"
              "@{Y_LT_X} \n"
              "D;JGE \n"
              "//If here - D<0. Result is true. Go to END: \n"
              "@{END} \n"
              "0;JMP \n"
              "({Y_LT_X}) //y<0<=x. Insert false(0) and continue to END (no jump) \n"
              "@SP //SP->x \n"
              "A=M  //A armed with x's address \n"
              "M=0 \n"
              "({END}) \n"
              "@SP //SP->x \n"
              "M=M+1 //Set SP to next index in stack. \n"
    }

    SEGMENT_CODES = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT"
    }

    PUSH_POP_CMDS = {
        "load_D": "\n//Push {segment_code} {index}\n"
                  "//Load desired value into D: \n"
                  "@{index} \n"
                  "D=A \n"
                  "@{segment_code} //(LCL,ARG,THIS,THAT) \n"
                  "A=D+M //A = segment_address+index \n"
                  "D=M //D now holds segment[index] \n",
        "push_D": "//Push D into stack: \n"
                  "@SP \n"
                  "A = M // A now holds the address to the top of the stack \n"
                  "M = D // Push the value \n",
        "inc_SP": "//increment top of stack pointer (SP) by 1 \n"
                  "@SP \n"
                  "M=M+1 // Increase stack pointer by 1 \n",
        "push_const": "\n// push constant {const_value}: \n"
                      "@{const_value} \n"
                      "D=A //D holds the constant \n"
                      "@SP \n"
                      "M=M+1 //SP->new top \n"
                      "A=M-1 \n"
                      "M=D \n",
        "push_static": "\n// Push static {index} \n"
                       "@{file_name}.{index} //A armed with the static variable address \n"
                       "D=M //D loaded with the value we want to push \n"
                       "@SP \n"
                       "M=M+1 //SP-> new stack top \n"
                       "A=M-1 \n"
                       "M=D \n",
        "pop_segment": "\n//Pop {segment_code} {index}: \n"
                       "//save index into D: \n"
                       "@{index} \n"
                       "D=A \n"
                       "@{segment_code} \n"
                       "A=M //A armed with segment's base address \n"
                       "D=D+A //D==index+base_address \n"
                       "@R15 \n"
                       "M=D // R15 now armed with the desired index to pop into \n"
                       "//Take the value from top of stack: \n"
                       "@SP \n"
                       "AM=M-1 //SP->y, A armed with y's address \n"
                       "D=M //D==y \n"
                       "//Load address into A and insert value: \n"
                       "@R15 \n"
                       "A=M \n"
                       "M=D \n",
        "pop_static": "\n//Pop into static variable {file_name}.{index}: \n"
                      "@SP \n"
                      "AM=M-1 //SP->y, A armed with y's address. \n"
                      "D=M //D==y. \n"
                      "@{file_name}.{index} //A armed with the static variable address \n"
                      "M=D \n",
        "push_temp_or_pointer": "\n//Push into temp/pointer segment in index {index}"
                                "//Load A with the address to push from: \n"
                                "@{index} \n"
                                "D=A \n"
                                "@{base_address} \n"
                                "A=D+A \n"
                                "// Insert value into D: \n"
                                "D=M \n"
                                "//Push value into top of stack: \n"
                                "@SP \n"
                                "A=M \n"
                                "M=D \n"
                                "//Increment SP: \n"
                                "@SP \n"
                                "M=M+1 \n",
        "pop_temp_or_pointer": "\n//Pop temp/pointer (fixed segments) {index}: \n"
                               "//Calculate desired address and store in D: \n"
                               "@{base_address} \n"
                               "D=A \n"
                               "@{index} \n"
                               "D=D+A //D==base_address+index \n"
                               "//Move desired address into R15: \n"
                               "@R15 \n"
                               "M=D //RAM[R15]==base_address+index \n"
                               "//Load popped value into D: \n"
                               "@SP \n"
                               "A=M-1 \n"
                               "D=M //D==y \n"
                               "//Load desired address into A: \n"
                               "@R15 \n"
                               "A=M // A==base_address+index \n"
                               "//Insert the popped value into RAM[base_address+index]: \n"
                               "M=D \n"
                               "//decrement top of stack address: \n"
                               "@SP \n"
                               "M=M-1 \n"
    }
