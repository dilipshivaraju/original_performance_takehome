"""
# Anthropic's Original Performance Engineering Take-home (Release version)

Copyright Anthropic PBC 2026. Permission is granted to modify and use, but not
to publish or redistribute your solutions so it's hard to find spoilers.

# Task

- Optimize the kernel (in KernelBuilder.build_kernel) as much as possible in the
  available time, as measured by test_kernel_cycles on a frozen separate copy
  of the simulator.

Validate your results using `python tests/submission_tests.py` without modifying
anything in the tests/ folder.

We recommend you look through problem.py next.
"""

import random
import unittest
from copy import copy

from problem import (
    Engine,
    DebugInfo,
    SLOT_LIMITS,
    VLEN,
    N_CORES,
    SCRATCH_SIZE,
    Machine,
    Tree,
    Input,
    HASH_STAGES,
    reference_kernel,
    build_mem_image,
    reference_kernel2,
    Instruction
)

class InstructionStream:
    def __init__(self, instructions: list[Instruction]) -> None:
        self.instructions: list[Instruction] = copy(instructions)
        self.length: int = len(instructions)
        self.cur_pointer: int = 0

class KernelBuilder:
    def __init__(self):
        self.instrs = []
        self.scratch = {}
        self.scratch_debug = {}
        self.scratch_ptr = 0
        self.const_map = {}

    def debug_info(self):
        return DebugInfo(scratch_map=self.scratch_debug)

    def build(self, slots: list[tuple[Engine, tuple]], vliw: bool = False):
        # Simple slot packing that just uses one slot per instruction bundle
        instrs = []
        for engine, slot in slots:
            instrs.append({engine: [slot]})
        return instrs

    def add(self, engine, slot):
        self.instrs.append({engine: [slot]})

    def alloc_scratch(self, name=None, length=1):
        addr = self.scratch_ptr
        if name is not None:
            self.scratch[name] = addr
            self.scratch_debug[addr] = (name, length)
        self.scratch_ptr += length
        assert self.scratch_ptr <= SCRATCH_SIZE, "Out of scratch space"
        return addr

    def scratch_const(self, val, name=None):
        if val not in self.const_map:
            addr = self.alloc_scratch(name)
            self.add("load", ("const", addr, val))
            self.const_map[val] = addr
        return self.const_map[val]
    
    def scratch_const_dilip(self, val, name=None):
        if val not in self.const_map:
            addr = self.alloc_scratch(name)
            #self.add("load", ("const", addr, val))
            self.const_map[val] = addr
        return self.const_map[val]

    def build_hash(self, val_hash_addr, tmp1, tmp2, round, i):
        slots = []

        for hi, (op1, val1, op2, op3, val3) in enumerate(HASH_STAGES):
            slots.append(("alu", (op1, tmp1, val_hash_addr, self.scratch_const(val1))))
            slots.append(("alu", (op3, tmp2, val_hash_addr, self.scratch_const(val3))))
            slots.append(("alu", (op2, val_hash_addr, tmp1, tmp2)))
            slots.append(("debug", ("compare", val_hash_addr, (round, i, "hash_stage", hi))))

        return slots
    
    def schedule_instructions(self, InstructionStreams):
        total_slots = [0, 0, 0, 0, 0]
        instrs = []
        while len(InstructionStreams) > 0:
            cur_instr: dict = {}
            valu_slots: int = 6

            for stream in InstructionStreams:
                cur = stream.instructions[stream.cur_pointer]

                if "valu" in cur:
                    current_value_slot = len(cur["valu"])

                    while valu_slots > 0 and current_value_slot > 0:
                        total_slots[1] += 1
                        slot = cur["valu"].pop(0)
                        cur_instr["valu"] = cur_instr.get("valu", [])
                        cur_instr["valu"].append(slot)
                        valu_slots -= 1
                        current_value_slot -= 1

                if valu_slots == 0:
                    break
            
            alu_slots: int = 12

            for stream in InstructionStreams:
                cur = stream.instructions[stream.cur_pointer]

                if "alu" in cur:
                    current_value_slot = len(cur["alu"])

                    while alu_slots > 0 and current_value_slot > 0:
                        total_slots[0] += 1
                        slot = cur["alu"].pop(0)
                        cur_instr["alu"] = cur_instr.get("alu", [])
                        cur_instr["alu"].append(slot)
                        alu_slots -= 1
                        current_value_slot -= 1

                if alu_slots == 0:
                    break
            
            load_slots: int = 2

            for stream in InstructionStreams:
                cur = stream.instructions[stream.cur_pointer]

                if "load" in cur:
                    current_value_slot = len(cur["load"])

                    while load_slots > 0 and current_value_slot > 0:
                        total_slots[2] += 1
                        slot = cur["load"].pop(0)
                        cur_instr["load"] = cur_instr.get("load", [])
                        cur_instr["load"].append(slot)
                        load_slots -= 1
                        current_value_slot -= 1

                if load_slots == 0:
                    break
            
            store_slots: int = 2

            for stream in InstructionStreams:
                cur = stream.instructions[stream.cur_pointer]

                if "store" in cur:
                    current_value_slot = len(cur["store"])

                    while store_slots > 0 and current_value_slot > 0:
                        total_slots[4] += 1
                        slot = cur["store"].pop(0)
                        cur_instr["store"] = cur_instr.get("store", [])
                        cur_instr["store"].append(slot)
                        store_slots -= 1
                        current_value_slot -= 1

                if store_slots == 0:
                    break

            flow_slots: int = 1

            for stream in InstructionStreams:
                cur = stream.instructions[stream.cur_pointer]

                if "flow" in cur:
                    current_value_slot = len(cur["flow"])

                    while flow_slots > 0 and current_value_slot > 0:
                        total_slots[3] += 1
                        slot = cur["flow"].pop(0)
                        cur_instr["flow"] = cur_instr.get("flow", [])
                        cur_instr["flow"].append(slot)
                        flow_slots -= 1
                        current_value_slot -= 1

                if flow_slots == 0:
                    break
            
            debug_slots: int = 64

            for stream in InstructionStreams:
                cur = stream.instructions[stream.cur_pointer]

                if "debug" in cur:
                    current_value_slot = len(cur["debug"])

                    while debug_slots > 0 and current_value_slot > 0:
                        slot = cur["debug"].pop(0)
                        cur_instr["debug"] = cur_instr.get("debug", [])
                        cur_instr["debug"].append(slot)
                        debug_slots -= 1
                        current_value_slot -= 1

                if debug_slots == 0:
                    break
            
            for key in list(cur_instr.keys()):
                if len(cur_instr[key]) == 0:
                    del cur_instr[key]

            instrs.append(cur_instr)

            for stream in InstructionStreams.copy():
                cur_instr = stream.instructions[stream.cur_pointer]

                all_empty = all(len(cur_instr[key]) == 0 for key in cur_instr.keys())

                if all_empty:
                    stream.cur_pointer += 1

                    if stream.cur_pointer == stream.length:
                        InstructionStreams.remove(stream)
        return instrs

    def build_kernel(
        self, forest_height: int, n_nodes: int, batch_size: int, rounds: int
    ):
        """
        Like reference_kernel2 but building actual instructions.
        Scalar implementation using only scalar ALU and load/store.
        """

        #allocate all required scratch memory
        V_CONST_1 = self.alloc_scratch("V_CONST_1", 8)
        V_CONST_2 = self.alloc_scratch("V_CONST_2", 8)
        V_CONST_3 = self.alloc_scratch("V_CONST_3", 8)
        V_CONST_7 = self.alloc_scratch("V_CONST_7", 8)
        FIRST_8_VALUES = self.alloc_scratch("FIRST_8_VALUES", 8)
        SECOND_8_VALUES = self.alloc_scratch("SECOND_8_VALUES", 8)

        V_7ED55D16 = self.alloc_scratch("V_7ED55D16", 8)
        V_C761C23C = self.alloc_scratch("V_C761C23C", 8)
        V_165667B1 = self.alloc_scratch("V_165667B1", 8)
        V_D3A2646C = self.alloc_scratch("V_D3A2646C", 8)
        V_FD7046C5 = self.alloc_scratch("V_FD7046C5", 8)
        V_B55A4F09 = self.alloc_scratch("V_B55A4F09", 8)
        
        V_4097 = self.alloc_scratch("V_4097", 8)
        V_19 = self.alloc_scratch("V_19", 8)
        V_33 = self.alloc_scratch("V_33", 8)
        V_9 = self.alloc_scratch("V_9", 8)
        V_16 = self.alloc_scratch("V_16", 8)

        V_FOREST_VAL_0 = self.alloc_scratch("V_FOREST_VAL_0", 8)
        V_FOREST_VAL_1 = self.alloc_scratch("V_FOREST_VAL_1", 8) #FOREST_VALUE 1
        V_FOREST_VAL_2 = self.alloc_scratch("V_FOREST_VAL_2", 8) #FOREST_VALUE 2
        V_FOREST_VAL_3 = self.alloc_scratch("V_FOREST_VAL_3", 8)
        V_FOREST_VAL_4 = self.alloc_scratch("V_FOREST_VAL_4", 8)
        V_FOREST_VAL_5 = self.alloc_scratch("V_FOREST_VAL_5", 8)
        V_FOREST_VAL_6 = self.alloc_scratch("V_FOREST_VAL_6", 8)

        V_FOREST_VAL_7 = self.alloc_scratch("V_FOREST_VAL_7", 8) 
        V_FOREST_VAL_8 = self.alloc_scratch("V_FOREST_VAL_8", 8) 
        V_FOREST_VAL_9 = self.alloc_scratch("V_FOREST_VAL_9", 8)
        V_FOREST_VAL_10 = self.alloc_scratch("V_FOREST_VAL_10", 8)
        V_FOREST_VAL_11 = self.alloc_scratch("V_FOREST_VAL_11", 8)
        V_FOREST_VAL_12 = self.alloc_scratch("V_FOREST_VAL_12", 8)
        V_FOREST_VAL_13 = self.alloc_scratch("V_FOREST_VAL_13", 8)
        V_FOREST_VAL_14 = self.alloc_scratch("V_FOREST_VAL_14", 8)
        

        V_NUM_NODES = self.alloc_scratch("V_NUM_NODES", 8)
        V_FOREST_VALUE_P = self.alloc_scratch("V_FOREST_VALUE_P", 8)

        tmp4_batch = [self.alloc_scratch(f"tmp4_batch_{i}") for i in range(batch_size//8)]
        tmp5_batch = [self.alloc_scratch(f"tmp5_batch_{i}") for i in range(batch_size//8)]
        vtmp1_batch = [self.alloc_scratch(f"vtmp1_batch_{i}", 8) for i in range(batch_size//8)]
        vtmp2_batch = [self.alloc_scratch(f"vtmp2_batch_{i}", 8) for i in range(batch_size//8)]
        vtmp4_batch = [self.alloc_scratch(f"vtmp2_batch_{i}", 8) for i in range(batch_size//8)]
        vtmp5_batch = [self.alloc_scratch(f"vtmp2_batch_{i}", 8) for i in range(batch_size//8)]
        
        vtmp6 = [self.alloc_scratch(f"vtmp6_{i}", 8) for i in range(7)]
        vtmp7 = [self.alloc_scratch(f"vtmp7_{i}", 8) for i in range(7)]

        batches = [0, 1, 2, 3, 4, 5, 6]

        CONST = [self.scratch_const_dilip(i * 8) for i in range(batch_size//8)]

        #allocate all required const scratch memory
        CONST_1 = self.scratch_const_dilip(1)
        CONST_2 = self.scratch_const_dilip(2)
        CONST_3 = self.scratch_const_dilip(3)
        CONST_4 = self.scratch_const_dilip(4)
        CONST_5 = self.scratch_const_dilip(5)
        CONST_6 = self.scratch_const_dilip(6)
        CONST_7 = self.scratch_const_dilip(7)

        HASH_VALUE_1 = self.scratch_const_dilip(0x7ED55D16)
        HASH_VALUE_2 = self.scratch_const_dilip(0xC761C23C)
        HASH_VALUE_3 = self.scratch_const_dilip(0x165667B1)
        HASH_VALUE_4 = self.scratch_const_dilip(0xD3A2646C)
        HASH_VALUE_5 = self.scratch_const_dilip(0xFD7046C5)
        HASH_VALUE_6 = self.scratch_const_dilip(0xB55A4F09)
        CONST_4097 = self.scratch_const_dilip(4097)
        CONST_19 = self.scratch_const_dilip(19)
        CONST_9 = self.scratch_const_dilip(9)

        CONST_33 = self.scratch_const_dilip(33)
        tmp1 = self.alloc_scratch("tmp1")
        tmp2 = self.alloc_scratch("tmp2")
        forest_val_8_p = self.alloc_scratch("forest_val_8_p")
        FOREST_VALUE_P = self.alloc_scratch("FOREST_VALUE_P")
        NUM_NODES = self.alloc_scratch("NUM_NODES")
        vtmp8 = self.alloc_scratch("vtmp8", 10)

        InstructionStreams = []
        instrs = []

        instrs[:] = [{"load":[("const", CONST[0], 0)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST_1, 1)]},
                    {"valu":[('vbroadcast', V_CONST_1, CONST_1)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST_2, 2)]},
                    {"valu":[('vbroadcast', V_CONST_2, CONST_2)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST_3, 3)]},
                     {"valu":[('vbroadcast', V_CONST_3, CONST_3)]}]
                     
        InstructionStreams.append(InstructionStream(instrs))
        
        instrs[:] = [{"load":[("const", CONST_4, 4), ("const", CONST[1], 8)]},
                     {"load":[("load", FOREST_VALUE_P, CONST_4)]},
                     {"load":[("vload", FIRST_8_VALUES, FOREST_VALUE_P)], "alu": [('+', forest_val_8_p, FOREST_VALUE_P, CONST[1])], "valu":[('vbroadcast', V_FOREST_VALUE_P, FOREST_VALUE_P)]},
                     {"load":[("vload", SECOND_8_VALUES, forest_val_8_p)]},

                     {"valu":[("vbroadcast", V_FOREST_VAL_1, FIRST_8_VALUES + 1), ("vbroadcast", V_FOREST_VAL_2, FIRST_8_VALUES + 2), 
                              ("vbroadcast", V_FOREST_VAL_3, FIRST_8_VALUES + 3), ("vbroadcast", V_FOREST_VAL_4, FIRST_8_VALUES + 4), 
                              ("vbroadcast", V_FOREST_VAL_5, FIRST_8_VALUES + 5), ("vbroadcast", V_FOREST_VAL_6, FIRST_8_VALUES + 6)]},

                     {"valu":[("vbroadcast", V_FOREST_VAL_7, FIRST_8_VALUES + 7), ("vbroadcast", V_FOREST_VAL_8, SECOND_8_VALUES), 
                              ("vbroadcast", V_FOREST_VAL_9, SECOND_8_VALUES + 1), ("vbroadcast", V_FOREST_VAL_10, SECOND_8_VALUES + 2), 
                              ("vbroadcast", V_FOREST_VAL_11, SECOND_8_VALUES + 3), ("vbroadcast", V_FOREST_VAL_12, SECOND_8_VALUES + 4)]},

                     {"valu":[("vbroadcast", V_FOREST_VAL_13, SECOND_8_VALUES + 5), ("vbroadcast", V_FOREST_VAL_14, SECOND_8_VALUES + 6),
                              ("vbroadcast", V_FOREST_VAL_0, FIRST_8_VALUES)]}]
        
        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST_5, 5)]},
                    {"load":[("load", tmp2, CONST_5)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST_6, 6)]},
                    {"load":[("load", tmp1, CONST_6)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST_7, 7)]},
                     {"valu":[('vbroadcast', V_CONST_7, CONST_7)], "load":[("load", V_NUM_NODES, CONST_7)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST_33, 33)]},
                    {"valu":[('vbroadcast', V_33, CONST_33)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", HASH_VALUE_1, 0x7ED55D16)]},
                    {"valu":[('vbroadcast', V_7ED55D16, HASH_VALUE_1)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", HASH_VALUE_2, 0xC761C23C)]},
                    {"valu":[('vbroadcast', V_C761C23C, HASH_VALUE_2)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", HASH_VALUE_3, 0x165667B1)]},
                    {"valu":[('vbroadcast', V_165667B1, HASH_VALUE_3)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", HASH_VALUE_4, 0xD3A2646C)]},
                    {"valu":[('vbroadcast', V_D3A2646C, HASH_VALUE_4)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", HASH_VALUE_5, 0xFD7046C5)]},
                    {"valu":[('vbroadcast', V_FD7046C5, HASH_VALUE_5)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", HASH_VALUE_6, 0xB55A4F09)]},
                    {"valu":[('vbroadcast', V_B55A4F09, HASH_VALUE_6)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST_4097, 4097)]},
                    {"valu":[('vbroadcast', V_4097, CONST_4097)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST_19, 19)]},
                    {"valu":[('vbroadcast', V_19, CONST_19)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST_9, 9)]},
                    {"valu":[('vbroadcast', V_9, CONST_9)]}]

        InstructionStreams.append(InstructionStream(instrs))

        instrs[:] = [{"load":[("const", CONST[2], 16)]},
                    {"valu":[('vbroadcast', V_16, CONST[2])]}]

        InstructionStreams.append(InstructionStream(instrs))

        for i in range(3, batch_size//8, 1):
            instr = [{"load":[("const", CONST[i], i * 8)]}]
            InstructionStreams.append(InstructionStream(instr))
        
        a = []
        res = self.schedule_instructions(InstructionStreams)
        
        a.extend(res)
        self.instrs.extend(a)
        InstructionStreams.clear()
        self.add("flow", ("pause",))

        #res = []
        def valu_alu_select(i, index, perm):
            valu_alu_select_array = [
                [
                    [{"valu": [('multiply_add', vtmp1_batch[i], vtmp1_batch[i], V_4097, V_7ED55D16)]}],
                    [
                        {"alu": [
                            ('*', vtmp1_batch[i],     vtmp1_batch[i],     V_4097),
                            ('*', vtmp1_batch[i] + 1, vtmp1_batch[i] + 1, V_4097),
                            ('*', vtmp1_batch[i] + 2, vtmp1_batch[i] + 2, V_4097),
                            ('*', vtmp1_batch[i] + 3, vtmp1_batch[i] + 3, V_4097),
                            ('*', vtmp1_batch[i] + 4, vtmp1_batch[i] + 4, V_4097),
                            ('*', vtmp1_batch[i] + 5, vtmp1_batch[i] + 5, V_4097),
                            ('*', vtmp1_batch[i] + 6, vtmp1_batch[i] + 6, V_4097),
                            ('*', vtmp1_batch[i] + 7, vtmp1_batch[i] + 7, V_4097)
                        ]},
                        {"alu": [
                            ('+', vtmp1_batch[i],     vtmp1_batch[i],     V_7ED55D16),
                            ('+', vtmp1_batch[i] + 1, vtmp1_batch[i] + 1, V_7ED55D16),
                            ('+', vtmp1_batch[i] + 2, vtmp1_batch[i] + 2, V_7ED55D16),
                            ('+', vtmp1_batch[i] + 3, vtmp1_batch[i] + 3, V_7ED55D16),
                            ('+', vtmp1_batch[i] + 4, vtmp1_batch[i] + 4, V_7ED55D16),
                            ('+', vtmp1_batch[i] + 5, vtmp1_batch[i] + 5, V_7ED55D16),
                            ('+', vtmp1_batch[i] + 6, vtmp1_batch[i] + 6, V_7ED55D16),
                            ('+', vtmp1_batch[i] + 7, vtmp1_batch[i] + 7, V_7ED55D16)
                        ]},
                    ]
                ],
                [
                    [{"valu": [
                        ('^',  vtmp4_batch[i], vtmp1_batch[i], V_C761C23C),
                        ('>>', vtmp5_batch[i], vtmp1_batch[i], V_19),
                    ]}],
                    [
                        {"alu": [
                            ('^',  vtmp4_batch[i],     vtmp1_batch[i],     V_C761C23C),
                            ('^',  vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_C761C23C),
                            ('^',  vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_C761C23C),
                            ('^',  vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_C761C23C),
                            ('^',  vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_C761C23C),
                            ('^',  vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_C761C23C),
                            ('^',  vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_C761C23C),
                            ('^',  vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_C761C23C),
                            ('>>', vtmp5_batch[i],     vtmp1_batch[i],     V_19),
                            ('>>', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_19),
                            ('>>', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_19),
                            ('>>', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_19),
                        ]},
                        {"alu": [
                            ('>>', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_19),
                            ('>>', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_19),
                            ('>>', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_19),
                            ('>>', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_19),
                        ]},
                    ]
                ],
                [
                    [{"valu": [('^', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]}],
                    [{"alu": [
                        ('^', vtmp1_batch[i],     vtmp4_batch[i],     vtmp5_batch[i]),
                        ('^', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
                        ('^', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2),
                        ('^', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
                        ('^', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4),
                        ('^', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
                        ('^', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6),
                        ('^', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7),
                    ]}],
                ],
                [
                    [{"valu": [('multiply_add', vtmp1_batch[i], vtmp1_batch[i], V_33, V_165667B1)]}],
                    [
                        {"alu": [
                            ('*', vtmp1_batch[i],     vtmp1_batch[i],     V_33),
                            ('*', vtmp1_batch[i] + 1, vtmp1_batch[i] + 1, V_33),
                            ('*', vtmp1_batch[i] + 2, vtmp1_batch[i] + 2, V_33),
                            ('*', vtmp1_batch[i] + 3, vtmp1_batch[i] + 3, V_33),
                            ('*', vtmp1_batch[i] + 4, vtmp1_batch[i] + 4, V_33),
                            ('*', vtmp1_batch[i] + 5, vtmp1_batch[i] + 5, V_33),
                            ('*', vtmp1_batch[i] + 6, vtmp1_batch[i] + 6, V_33),
                            ('*', vtmp1_batch[i] + 7, vtmp1_batch[i] + 7, V_33)
                        ]},
                        {"alu": [
                            ('+', vtmp1_batch[i],     vtmp1_batch[i],     V_165667B1),
                            ('+', vtmp1_batch[i] + 1, vtmp1_batch[i] + 1, V_165667B1),
                            ('+', vtmp1_batch[i] + 2, vtmp1_batch[i] + 2, V_165667B1),
                            ('+', vtmp1_batch[i] + 3, vtmp1_batch[i] + 3, V_165667B1),
                            ('+', vtmp1_batch[i] + 4, vtmp1_batch[i] + 4, V_165667B1),
                            ('+', vtmp1_batch[i] + 5, vtmp1_batch[i] + 5, V_165667B1),
                            ('+', vtmp1_batch[i] + 6, vtmp1_batch[i] + 6, V_165667B1),
                            ('+', vtmp1_batch[i] + 7, vtmp1_batch[i] + 7, V_165667B1)
                        ]},
                    ]
                ],
                [
                    [{"valu": [
                        ('+',  vtmp4_batch[i], vtmp1_batch[i], V_D3A2646C),
                        ('<<', vtmp5_batch[i], vtmp1_batch[i], V_9),
                    ]}],
                    [
                        {"alu": [
                            ('+',  vtmp4_batch[i],     vtmp1_batch[i],     V_D3A2646C),
                            ('+',  vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_D3A2646C),
                            ('+',  vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_D3A2646C),
                            ('+',  vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_D3A2646C),
                            ('+',  vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_D3A2646C),
                            ('+',  vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_D3A2646C),
                            ('+',  vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_D3A2646C),
                            ('+',  vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_D3A2646C),
                            ('<<', vtmp5_batch[i],     vtmp1_batch[i],     V_9),
                            ('<<', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_9),
                            ('<<', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_9),
                            ('<<', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_9),
                        ]},
                        {"alu": [
                            ('<<', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_9),
                            ('<<', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_9),
                            ('<<', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_9),
                            ('<<', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_9),
                        ]},
                    ],
                ],
                [
                    [{"valu": [('^', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]}],
                    [{"alu": [
                        ('^', vtmp1_batch[i],     vtmp4_batch[i],     vtmp5_batch[i]),
                        ('^', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
                        ('^', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2),
                        ('^', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
                        ('^', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4),
                        ('^', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
                        ('^', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6),
                        ('^', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7),
                    ]}],
                ],
                [
                    [{"valu": [('multiply_add', vtmp1_batch[i], vtmp1_batch[i], V_9, V_FD7046C5)]}],
                    [
                        {"alu": [
                            ('*', vtmp1_batch[i],     vtmp1_batch[i],     V_9),
                            ('*', vtmp1_batch[i] + 1, vtmp1_batch[i] + 1, V_9),
                            ('*', vtmp1_batch[i] + 2, vtmp1_batch[i] + 2, V_9),
                            ('*', vtmp1_batch[i] + 3, vtmp1_batch[i] + 3, V_9),
                            ('*', vtmp1_batch[i] + 4, vtmp1_batch[i] + 4, V_9),
                            ('*', vtmp1_batch[i] + 5, vtmp1_batch[i] + 5, V_9),
                            ('*', vtmp1_batch[i] + 6, vtmp1_batch[i] + 6, V_9),
                            ('*', vtmp1_batch[i] + 7, vtmp1_batch[i] + 7, V_9)
                        ]},
                        {"alu": [
                            ('+', vtmp1_batch[i],     vtmp1_batch[i],     V_FD7046C5),
                            ('+', vtmp1_batch[i] + 1, vtmp1_batch[i] + 1, V_FD7046C5),
                            ('+', vtmp1_batch[i] + 2, vtmp1_batch[i] + 2, V_FD7046C5),
                            ('+', vtmp1_batch[i] + 3, vtmp1_batch[i] + 3, V_FD7046C5),
                            ('+', vtmp1_batch[i] + 4, vtmp1_batch[i] + 4, V_FD7046C5),
                            ('+', vtmp1_batch[i] + 5, vtmp1_batch[i] + 5, V_FD7046C5),
                            ('+', vtmp1_batch[i] + 6, vtmp1_batch[i] + 6, V_FD7046C5),
                            ('+', vtmp1_batch[i] + 7, vtmp1_batch[i] + 7, V_FD7046C5)
                        ]},
                    ]
                ],
                [
                    [{"valu": [
                        ('^',  vtmp4_batch[i], vtmp1_batch[i], V_B55A4F09),
                        ('>>', vtmp5_batch[i], vtmp1_batch[i], V_16),
                    ]}],
                    [
                        {"alu": [
                            ('^',  vtmp4_batch[i],     vtmp1_batch[i],     V_B55A4F09),
                            ('^',  vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_B55A4F09),
                            ('^',  vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_B55A4F09),
                            ('^',  vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_B55A4F09),
                            ('^',  vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_B55A4F09),
                            ('^',  vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_B55A4F09),
                            ('^',  vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_B55A4F09),
                            ('^',  vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_B55A4F09),
                            ('>>', vtmp5_batch[i],     vtmp1_batch[i],     V_16),
                            ('>>', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_16),
                            ('>>', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_16),
                            ('>>', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_16),
                        ]},
                        {"alu": [
                            ('>>', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_16),
                            ('>>', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_16),
                            ('>>', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_16),
                            ('>>', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_16),
                        ]},
                    ],
                ],
                [
                    [{"valu": [('^', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]}],
                    [{"alu": [
                        ('^', vtmp1_batch[i],     vtmp4_batch[i],     vtmp5_batch[i]),
                        ('^', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
                        ('^', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2),
                        ('^', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
                        ('^', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4),
                        ('^', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
                        ('^', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6),
                        ('^', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7),
                    ]}],
                ]
            ]

            #print(len(valu_alu_select_array))
            #print(index)
            return valu_alu_select_array[index][perm[index]]
            #return len(valu_alu_select_array)
        
        def round_2_alu_valu_select(instruction_stream, i, perm):
            valu_alu_select_array = [
                [
                    [{"valu": [('-', vtmp2_batch[i], vtmp2_batch[i], V_CONST_3)]}],
                    [
                        {"alu": [
                            ('-', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_3),
                            ('-', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_3 + 1),
                            ('-', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_3 + 2),
                            ('-', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_3 + 3),
                            ('-', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_3 + 4),
                            ('-', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_3 + 5),
                            ('-', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_3 + 6),
                            ('-', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_3 + 7),
                        ]}
                    ]
                ],
                [   
                    [{"valu": [('&', vtmp5_batch[i], vtmp2_batch[i], V_CONST_1)]}],
                    [
                        {"alu": [
                            ('&', vtmp5_batch[i],     vtmp2_batch[i],     V_CONST_1),
                            ('&', vtmp5_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                            ('&', vtmp5_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                            ('&', vtmp5_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                            ('&', vtmp5_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                            ('&', vtmp5_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                            ('&', vtmp5_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                            ('&', vtmp5_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                        ]}
                    ]
                ],
                [
                    [{"valu": [('>>', vtmp2_batch[i], vtmp2_batch[i], V_CONST_1)]}],
                    [
                        {"alu": [
                            ('>>', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                            ('>>', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                            ('>>', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                            ('>>', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                            ('>>', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                            ('>>', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                            ('>>', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                            ('>>', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                        ]}
                    ]
                ],
                [
                    [{"valu": [('&', vtmp2_batch[i], vtmp2_batch[i], V_CONST_1)]}],
                    [
                        {"alu": [
                            ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                            ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                            ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                            ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                            ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                            ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                            ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                            ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                        ]}
                    ]
                ]
            ]
            idx = 0
            instruction_stream.extend([
                        {"store":[('vstore', tmp5_batch[i], vtmp2_batch[i])]}])


            for _ in range(2):
                instruction_stream.extend(valu_alu_select_array[idx][perm[idx]])
                idx += 1
            
            instruction_stream.extend([{"flow": [("vselect", vtmp4_batch[i], vtmp5_batch[i], V_FOREST_VAL_4, V_FOREST_VAL_3)]},
                        {"flow": [("vselect", vtmp5_batch[i], vtmp5_batch[i], V_FOREST_VAL_6, V_FOREST_VAL_5)]}])

            for _ in range(2):
                instruction_stream.extend(valu_alu_select_array[idx][perm[idx]])
                idx += 1
            
            instruction_stream.extend([{"flow": [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp4_batch[i])]}])

        def hash_instrs(instruction_stream, batch, perm):
            for idx in range(9):
                instruction_stream.extend(valu_alu_select(batch, idx, perm))
        
        batch_idx = 0
        default = (0, 0, 1, 0, 0, 1, 0, 0, 0)

        overrides = {
            (0,  0):  (0, 0, 0, 0, 0, 0, 0, 0, 0),
            (15, 14): (0, 0, 0, 1, 1, 0, 0, 1, 0),
            (25, 14): (0, 0, 0, 1, 1, 0, 1, 1, 0),
            (27, 14): (1, 1, 0, 1, 1, 0, 0, 0, 0),
            (28, 4):  (0, 1, 0, 1, 1, 1, 0, 1, 0),
            (28, 10): (0, 0, 0, 0, 0, 0, 0, 1, 0),
            (29, 14): (0, 1, 1, 0, 1, 0, 1, 1, 0),
        }

        perm_hash_instructions = [
            [overrides.get((b, r), default) for r in range(16)]
            for b in range(32)
        ]

        perm = (0, 0, 0, 0)
        for i in range(0, batch_size//8, 1):
            instruction_stream = []
            instruction_stream.extend([
                {"alu": [('+', tmp4_batch[i], tmp1, CONST[i]), ('+', tmp5_batch[i], tmp2, CONST[i])]},
                {"load": [('vload', vtmp1_batch[i], tmp4_batch[i])]}
            ])

            for round in range(rounds):
                if round == 0:
                    instruction_stream.extend([
                        {"valu": [('^', vtmp1_batch[i], V_FOREST_VAL_0, vtmp1_batch[i])]}
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    instruction_stream.extend([
                        {"valu": [('%', vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect', vtmp2_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                    ])

                elif round == 1:
                    instruction_stream.extend([
                        {"flow": [('vselect', vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_2, V_FOREST_VAL_1)]},
                        {"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',    vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])

                elif round == 2:
                    round_2_alu_valu_select(instruction_stream, i, perm)
                    instruction_stream.extend([
                        {"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',    vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"load": [('vload',      vtmp2_batch[i], tmp5_batch[i])]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])

                elif round == 3:
                    if i in {1, 3, 5, 7, 9, 11, 13}:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i],             vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i],             vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", vtmp6[batches[batch_idx]],  vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i],             vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", vtmp7[batches[batch_idx]], vtmp2_batch[i], V_CONST_1)]},
                            {"valu":  [("&",  vtmp7[batches[batch_idx]], vtmp7[batches[batch_idx]], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp7[batches[batch_idx]], vtmp5_batch[i],            vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp7[batches[batch_idx]], vtmp4_batch[i],            vtmp6[batches[batch_idx]])]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    elif i == 15:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", CONST[0],       vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i], vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", CONST[8], vtmp2_batch[i], V_CONST_1)]},
                            {"valu":  [("&",  CONST[8], CONST[8],       V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], CONST[8], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], CONST[8], vtmp4_batch[i], CONST[0])]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    elif i == 17:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", CONST[16],      vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i], vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", CONST[24], vtmp2_batch[i], V_CONST_1)]},
                            {"valu":  [("&",  CONST[24], CONST[24],      V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], CONST[24], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], CONST[24], vtmp4_batch[i], CONST[16])]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    elif i == 19:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", CONST_1,        vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i], vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", HASH_VALUE_2, vtmp2_batch[i], V_CONST_1)]},
                            {"valu":  [("&",  HASH_VALUE_2, HASH_VALUE_2,   V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], HASH_VALUE_2, vtmp5_batch[i], vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], HASH_VALUE_2, vtmp4_batch[i], CONST_1)]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    elif i == 21:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i],   vtmp2_batch[i],   V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i],   vtmp2_batch[i],   V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i],  vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i],  vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", FIRST_8_VALUES,  vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i],  vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", SECOND_8_VALUES, vtmp2_batch[i],    V_CONST_1)]},
                            {"valu":  [("&",  SECOND_8_VALUES, SECOND_8_VALUES,   V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], SECOND_8_VALUES, vtmp5_batch[i],   vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], SECOND_8_VALUES, vtmp4_batch[i],   FIRST_8_VALUES)]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    elif i == 23:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", CONST_33,       vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i], vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", vtmp8 + 2, vtmp2_batch[i], V_CONST_1)]},
                            {"valu":  [("&",  vtmp8 + 2, vtmp8 + 2,      V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp8 + 2, vtmp5_batch[i], vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp8 + 2, vtmp4_batch[i], CONST_33)]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    else:
                        instruction_stream.extend([
                            {"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]},
                            {"load": [('load', vtmp5_batch[i],     vtmp4_batch[i]),     ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                            {"load": [('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                            {"load": [('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                            {"load": [('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]},
                        ])

                    instruction_stream.extend([
                        {"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',    vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])

                elif 4 <= round <= 9:
                    instruction_stream.extend([
                        {"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]},
                        {"load": [('load', vtmp5_batch[i],     vtmp4_batch[i]),     ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                        {"load": [('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                        {"load": [('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                        {"load": [('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]},
                    ])
                    instruction_stream.extend([
                        {"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',    vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])

                elif round == 10:
                    instruction_stream.extend([
                        {"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]},
                        {"load": [('load', vtmp5_batch[i],     vtmp4_batch[i]),     ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                        {"load": [('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                        {"load": [('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                        {"load": [('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]},
                    ])
                    instruction_stream.extend([
                        {"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

                elif round == 11:
                    instruction_stream.extend([
                        {"valu": [('^', vtmp1_batch[i], V_FOREST_VAL_0, vtmp1_batch[i])]}
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    instruction_stream.extend([
                        {"valu": [('%', vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect', vtmp2_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                    ])

                elif round == 12:
                    instruction_stream.extend([
                        {"flow": [('vselect', vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_2, V_FOREST_VAL_1)]},
                        {"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',    vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])

                elif round == 13:
                    round_2_alu_valu_select(instruction_stream, i, perm)
                    instruction_stream.extend([
                        {"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',    vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"load": [('vload',      vtmp2_batch[i], tmp5_batch[i])]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])

                elif round == 14:
                    if i in {1, 3, 5, 7, 9, 11, 13}:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i],            vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i],            vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", vtmp6[batches[batch_idx]], vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i],            vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", vtmp7[batches[batch_idx]], vtmp2_batch[i],              V_CONST_1)]},
                            {"valu":  [("&",  vtmp7[batches[batch_idx]], vtmp7[batches[batch_idx]],   V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp7[batches[batch_idx]], vtmp5_batch[i],           vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp7[batches[batch_idx]], vtmp4_batch[i],           vtmp6[batches[batch_idx]])]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])
                        batch_idx += 1

                    elif i == 15:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", CONST[0],       vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i], vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", CONST[8], vtmp2_batch[i], V_CONST_1)]},
                            {"valu":  [("&",  CONST[8], CONST[8],       V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], CONST[8], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], CONST[8], vtmp4_batch[i], CONST[0])]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    elif i == 17:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", CONST[16],      vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i], vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", CONST[24], vtmp2_batch[i], V_CONST_1)]},
                            {"valu":  [("&",  CONST[24], CONST[24],      V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], CONST[24], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], CONST[24], vtmp4_batch[i], CONST[16])]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    elif i == 19:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", CONST_1,        vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i], vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", HASH_VALUE_2, vtmp2_batch[i], V_CONST_1)]},
                            {"valu":  [("&",  HASH_VALUE_2, HASH_VALUE_2,   V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], HASH_VALUE_2, vtmp5_batch[i], vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], HASH_VALUE_2, vtmp4_batch[i], CONST_1)]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    elif i == 21:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i],  vtmp2_batch[i],  V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i],  vtmp2_batch[i],  V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp4_batch[i],  V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp4_batch[i],  V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", FIRST_8_VALUES, vtmp4_batch[i],  V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i], vtmp4_batch[i],  V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", SECOND_8_VALUES, vtmp2_batch[i],   V_CONST_1)]},
                            {"valu":  [("&",  SECOND_8_VALUES, SECOND_8_VALUES,  V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], SECOND_8_VALUES, vtmp5_batch[i],  vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], SECOND_8_VALUES, vtmp4_batch[i],  FIRST_8_VALUES)]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    elif i == 23:
                        instruction_stream.extend([
                            {"store": [('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]},
                            {"valu":  [("-",  vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]},
                            {"valu":  [("&",  vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp4_batch[i], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", CONST_33,       vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow":  [("vselect", vtmp4_batch[i], vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", vtmp8 + 2, vtmp2_batch[i], V_CONST_1)]},
                            {"valu":  [("&",  vtmp8 + 2, vtmp8 + 2,      V_CONST_1)]},
                            {"flow":  [("vselect", vtmp1_batch[i], vtmp8 + 2, vtmp5_batch[i], vtmp1_batch[i])]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp8 + 2, vtmp4_batch[i], CONST_33)]},
                            {"valu":  [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]},
                            {"alu":   [
                                ('&', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_1),
                                ('&', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                                ('&', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                                ('&', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                                ('&', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                                ('&', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                                ('&', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                                ('&', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                            ]},
                            {"flow":  [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"load":  [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]},
                        ])

                    else:
                        instruction_stream.extend([
                            {"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]},
                            {"load": [('load', vtmp5_batch[i],     vtmp4_batch[i]),     ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                            {"load": [('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                            {"load": [('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                            {"load": [('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]},
                        ])

                    instruction_stream.extend([
                        {"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',    vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])

                else:  # round >= 15
                    instruction_stream.extend([
                        {"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]},
                        {"load": [('load', vtmp5_batch[i],     vtmp4_batch[i]),     ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                        {"load": [('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                        {"load": [('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                        {"load": [('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]},
                    ])
                    instruction_stream.extend([
                        {"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}
                    ])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

            instruction_stream.extend([
                {"store": [('vstore', tmp4_batch[i], vtmp1_batch[i])]}
            ])
            InstructionStreams.append(InstructionStream(instruction_stream))

        res = self.schedule_instructions(InstructionStreams)
        self.instrs.extend(res)
        self.instrs.append({"flow": [("pause",)]})

BASELINE = 147734

def do_kernel_test(
    forest_height: int,
    rounds: int,
    batch_size: int,
    seed: int = 123,
    trace: bool = False,
    prints: bool = False,
):
    print(f"{forest_height=}, {rounds=}, {batch_size=}")
    random.seed(seed)
    forest = Tree.generate(forest_height)
    inp = Input.generate(forest, batch_size, rounds)
    mem = build_mem_image(forest, inp)

    #reference_kernel(forest, inp)
    kb = KernelBuilder()
    kb.build_kernel(forest.height, len(forest.values), len(inp.indices), rounds)
    # print(kb.instrs)

    value_trace = {}
    machine = Machine(
        mem,
        kb.instrs,
        kb.debug_info(),
        n_cores=N_CORES,
        value_trace=value_trace,
        trace=trace,
    )
    machine.prints = prints
    for i, ref_mem in enumerate(reference_kernel2(mem, value_trace)):
        machine.run()
        inp_values_p = ref_mem[6]
        if prints:
            print(machine.mem[inp_values_p : inp_values_p + len(inp.values)])
            print(ref_mem[inp_values_p : inp_values_p + len(inp.values)])
        assert (
            machine.mem[inp_values_p : inp_values_p + len(inp.values)]
            == ref_mem[inp_values_p : inp_values_p + len(inp.values)]
        ), f"Incorrect result on round {i}"
        inp_indices_p = ref_mem[5]
        if prints:
            print(machine.mem[inp_indices_p : inp_indices_p + len(inp.indices)])
            print(ref_mem[inp_indices_p : inp_indices_p + len(inp.indices)])
        # Updating these in memory isn't required, but you can enable this check for debugging
        # assert machine.mem[inp_indices_p:inp_indices_p+len(inp.indices)] == ref_mem[inp_indices_p:inp_indices_p+len(inp.indices)]

    print("CYCLES: ", machine.cycle)
    print("Speedup over baseline: ", BASELINE / machine.cycle)
    return machine.cycle


class Tests(unittest.TestCase):
    def test_ref_kernels(self):
        """
        Test the reference kernels against each other
        """
        random.seed(123)
        for i in range(10):
            f = Tree.generate(4)
            inp = Input.generate(f, 10, 6)
            mem = build_mem_image(f, inp)
            reference_kernel(f, inp)
            for _ in reference_kernel2(mem, {}):
                pass
            assert inp.indices == mem[mem[5] : mem[5] + len(inp.indices)]
            assert inp.values == mem[mem[6] : mem[6] + len(inp.values)]

    def test_kernel_trace(self):
        # Full-scale example for performance testing
        do_kernel_test(10, 16, 256, trace=True, prints=False)

    # Passing this test is not required for submission, see submission_tests.py for the actual correctness test
    # You can uncomment this if you think it might help you debug
    # def test_kernel_correctness(self):
    #     for batch in range(1, 3):
    #         for forest_height in range(3):
    #             do_kernel_test(
    #                 forest_height + 2, forest_height + 4, batch * 16 * VLEN * N_CORES
    #             )

    def test_kernel_cycles(self):
        do_kernel_test(10, 16, 256, trace=False, prints=False)


# To run all the tests:
#    python perf_takehome.py
# To run a specific test:
#    python perf_takehome.py Tests.test_kernel_cycles
# To view a hot-reloading trace of all the instructions:  **Recommended debug loop**
# NOTE: The trace hot-reloading only works in Chrome. In the worst case if things aren't working, drag trace.json onto https://ui.perfetto.dev/
#    python perf_takehome.py Tests.test_kernel_trace
# Then run `python watch_trace.py` in another tab, it'll open a browser tab, then click "Open Perfetto"
# You can then keep that open and re-run the test to see a new trace.

# To run the proper checks to see which thresholds you pass:
#    python tests/submission_tests.py

if __name__ == "__main__":
    unittest.main()
