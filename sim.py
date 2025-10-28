#!/usr/bin/python3
# Eric Cheung

"""
CS-UY 2214
Adapted from Jeff Epstein
Starter code for E20 simulator
sim.py
"""

from collections import namedtuple
import re
import argparse

# Some helpful constant values that we'll be using.
Constants = namedtuple("Constants",["NUM_REGS", "MEM_SIZE", "REG_SIZE"])
constants = Constants(NUM_REGS = 8,
                      MEM_SIZE = 2**13,
                      REG_SIZE = 2**16)

def load_machine_code(machine_code, mem):
    """
    Loads an E20 machine code file into the list
    provided by mem. We assume that mem is
    large enough to hold the values in the machine
    code file.
    sig: list(str) -> list(int) -> NoneType
    """
    machine_code_re = re.compile("^ram\[(\d+)\] = 16'b(\d+);.*$")
    expectedaddr = 0
    for line in machine_code:
        match = machine_code_re.match(line)
        if not match:
            raise ValueError("Can't parse line: %s" % line)
        addr, instr = match.groups()
        addr = int(addr,10)
        instr = int(instr,2)
        if addr != expectedaddr:
            raise ValueError("Memory addresses encountered out of sequence: %s" % addr)
        if addr >= len(mem):
            raise ValueError("Program too big for memory")
        expectedaddr += 1
        mem[addr] = instr

def print_state(pc, regs, memory, memquantity):
    """
    Prints the current state of the simulator, including
    the current program counter, the current register values,
    and the first memquantity elements of memory.
    sig: int -> list(int) -> list(int) - int -> NoneType
    """
    print("Final state:")
    print("\tpc="+format(pc,"5d"))
    for reg, regval in enumerate(regs):
        print(("\t$%s=" % reg)+format(regval,"5d"))
    line = ""
    for count in range(memquantity):
        line += format(memory[count], "04x")+ " "
        if count % 8 == 7:
            print(line)
            line = ""
    if line != "":
        print(line)

def main():
    parser = argparse.ArgumentParser(description='Simulate E20 machine')
    parser.add_argument('filename', help='The file containing machine code, typically with .bin suffix')
    cmdline = parser.parse_args()

    mem = [0] * constants.MEM_SIZE
    with open(cmdline.filename) as file:
        # TODO: your code here. Load file and parse using load_machine_code
        load_machine_code(file, mem)

    # TODO: your code here. Do simulation.

    # initialize processor state
    pc = 0
    regs = [0] * constants.NUM_REGS
    running = True
     
    # main simulation loop
    while running:
        current_pc = pc
        instr_addr = pc & 0b1111111111111
        instr = mem[instr_addr]
        # handle 13-bit PC wraparound later
        pc += 1 
        opcode = (instr >> 13) & 0b111

        try:
            # (and sub or and slt jr)
            if opcode == 0b000:
                result = None
                # lass 4 bits
                func = instr & 0b1111
                # 3 register fileds
                regSrcA = (instr >> 10) & 0b111
                regSrcB = (instr >> 7) & 0b111
                regDst = (instr >> 4) & 0b111
                if func == 0b0000: # add
                    regs[regDst] = (regs[regSrcA] + regs[regSrcB]) & 0xFFFF
                elif func == 0b0001: # sub
                    regs[regDst] = (regs[regSrcA] - regs[regSrcB]) & 0xFFFF
                elif func == 0b0010: # or
                    regs[regDst] = (regs[regSrcA] | regs[regSrcB]) & 0xFFFF
                elif func == 0b0011: # and
                    regs[regDst] = (regs[regSrcA] & regs[regSrcB]) & 0xFFFF
                elif func == 0b0100: # slt (unsigned)
                    valA = regs[regSrcA] & 0b1111111111111111
                    valB = regs[regSrcB] & 0b1111111111111111
                    result = 1 if valA < valB else 0
                elif func == 0b1000: # jr
                    pc = regs[regSrcA]
                    result = None
                else:
                    result = None
                
                # write result to regdest unless it's $0
                if regDst != 0 and result is not None:
                    regs[regDst] = result
            elif opcode == 0b001: # addi
                regSrc = (instr >> 10) & 0b111
                regDst = (instr >> 7) & 0b111
                imm7 = instr & 0b1111111
                # sign extend imm7 to 16 bits
                if (imm7 >> 6) & 0b1:
                    imm7 -= 128
                
                result = (regs[regSrc] + imm7) & 0xFFFF
                if regDst != 0:
                    regs[regDst] = result
            elif opcode == 0b010: # j
                imm13 = instr & 0b1111111111111
                if imm13 == current_pc:
                    # halt
                    running = False
                    pc = current_pc
                else:
                    pc = imm13
            elif opcode == 0b011: # jal
                imm13 = instr & 0b1111111111111
                regs[7] = pc
                pc = imm13
            elif opcode == 0b100: # lw
                regAddr = (instr >> 10) & 0b111
                regDst = (instr >> 7) & 0b111
                imm7 = instr & 0b1111111

                # sign extend imm7
                if (imm7 >> 6) & 0b1:
                    imm7 -= 128
                
                # calculate address and wrap to 13 bits
                addr = (regs[regAddr] + imm7) & 0b11111111111111
                if regDst != 0:
                    regs[regDst] = mem[addr] & 0b1111111111111111
            elif opcode == 0b101: # sw
                regAddr = (instr >> 10) & 0b111
                regSrc = (instr >> 7) & 0b111
                imm7 = instr & 0b1111111

                # sign extend imm7
                if (imm7 >> 6) & 0b1:
                    imm7 -= 128
                
                # calculate address and wrap to 13 bits
                addr = (regs[regAddr] + imm7) & 0b11111111111111
                mem[addr] = regs[regSrc] & 0b1111111111111111
            elif opcode == 0b110: # jeq
                regA = (instr >> 10) & 0b111
                regB = (instr >> 7) & 0b111
                imm7 = instr & 0b1111111

                # sign extend imm7
                if (imm7 >> 6) & 0b1:
                    imm7 -= 128
                if regs[regA] == regs[regB]:
                    pc = (pc + imm7)
            elif opcode == 0b111: # slti
                regSrc = (instr >> 10) & 0b111
                regDst = (instr >> 7) & 0b111
                imm7 = instr & 0b1111111

                # sign extend imm7
                if (imm7 >> 6) & 0b1:
                    imm7 -= 128
                # unsigned comparison
                valSrc = regs[regSrc] & 0xFFFF
                valImm = imm7 & 0xFFFF
                result = 1 if valSrc < valImm else 0
                if regDst != 0:
                    regs[regDst] = result
            
            # always ensure $0 is zero
            regs[0] = 0

            # wrap pc
            pc = pc & 0b1111111111111

        except IndexError:
            print(f"Error: PC {pc} out of bounds, halting")
            running = False
        except Exception as e:
            print(f"Error occured: {e}, halting")
            running = False
        
    # TODO: your code here. print the final state of the simulator before ending, using print_state
    print_state(pc, regs, mem, 128)

if __name__ == "__main__":
    main()
