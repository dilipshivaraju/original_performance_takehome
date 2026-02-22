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

    def build_hash(self, val_hash_addr, tmp1, tmp2, round, i):
        slots = []

        for hi, (op1, val1, op2, op3, val3) in enumerate(HASH_STAGES):
            slots.append(("alu", (op1, tmp1, val_hash_addr, self.scratch_const(val1))))
            slots.append(("alu", (op3, tmp2, val_hash_addr, self.scratch_const(val3))))
            slots.append(("alu", (op2, val_hash_addr, tmp1, tmp2)))
            slots.append(("debug", ("compare", val_hash_addr, (round, i, "hash_stage", hi))))

        return slots
    
    def schedule_instructions_from_independent_streams(self, instructions_streams):
        SLOT_LIMITS = {
            "alu":   (12, 0),
            "valu":  (6,  1),
            "load":  (2,  2),
            "flow":  (1,  3),
            "store": (2,  4),
            "debug": (64, None),  # not tracked in total_slots
        }

        total_slots = [0, 0, 0, 0, 0]
        instrs = []

        while instructions_streams:
            cur_instr = {}

            for key, (limit, slot_index) in SLOT_LIMITS.items():
                remaining = limit
                for stream in instructions_streams:
                    cur = stream.instructions[stream.cur_pointer]
                    slots = cur.get(key)
                    if not slots or remaining == 0:
                        continue
                    while remaining > 0 and slots:
                        cur_instr.setdefault(key, []).append(slots.pop(0))
                        if slot_index is not None:
                            total_slots[slot_index] += 1
                        remaining -= 1
                    if remaining == 0:
                        break

            cur_instr = {k: v for k, v in cur_instr.items() if v}
            instrs.append(cur_instr)

            for stream in instructions_streams.copy():
                cur = stream.instructions[stream.cur_pointer]
                if all(len(v) == 0 for v in cur.values()):
                    stream.cur_pointer += 1
                    if stream.cur_pointer == stream.length:
                        instructions_streams.remove(stream)

        #print(f"alu = {total_slots[0] // 12}, valu = {total_slots[1] // 6}, load = {total_slots[2] // 2}, flow = {total_slots[3]}, store = {total_slots[4] // 2}")
        return instrs

    def get_my_hash_alu_valu_mix(self):
            
        # every batch and round has different alu/valu combination for hashing
        default = (0, 0, 1, 0, 0, 0, 0, 0, 1)

        overrides = {
            (0,  0):  (0, 0, 0, 0, 0, 0, 0, 0, 0),
            (2,  14): (0, 1, 0, 1, 0, 0, 0, 0, 0),
            (3,  3):  (0, 1, 0, 0, 1, 1, 0, 1, 1),
            (3,  8):  (0, 0, 0, 1, 1, 0, 0, 0, 1),
            (3,  14): (0, 0, 0, 1, 1, 1, 1, 1, 0),
            (15, 11): (0, 0, 0, 0, 0, 0, 1, 1, 1),
            (21, 14): (0, 0, 0, 0, 1, 0, 0, 0, 1),
            (23, 15): (0, 0, 0, 0, 0, 0, 1, 1, 0),
            (25, 12): (0, 0, 0, 0, 0, 0, 0, 0, 0),
            (28, 13): (0, 1, 0, 0, 1, 0, 0, 0, 0),
        }

        my_hash_alu_valu_mix = [
            [overrides.get((b, r), default) for r in range(16)]
            for b in range(32)
        ]

        return my_hash_alu_valu_mix

    def build_kernel(
        self, forest_height: int, n_nodes: int, batch_size: int, rounds: int
    ):
        """
        Like reference_kernel2 but building actual instructions.
        Scalar implementation using only scalar ALU and load/store.
        """

        # allocate all required scratch memory
        V_CONST_1 = self.alloc_scratch("V_CONST_1", 8)
        V_CONST_2 = self.alloc_scratch("V_CONST_2", 8)
        V_CONST_3 = self.alloc_scratch("V_CONST_3", 8)
        V_CONST_7 = self.alloc_scratch("V_CONST_7", 8)

        # vectorized constants required for hash function
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

        # vectorized forest values from 0 to 14 - from depth 0 to 3
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
        
        # vectorized forest value pointer that has address of the first forest value
        V_FOREST_VAL_P = self.alloc_scratch("V_FOREST_VALUE_P", 8)

        # temporary registers used per batch
        inp_val_ptr_batch = [self.alloc_scratch(f"inp_val_ptr_batch_{i}") for i in range(batch_size//8)]
        inp_idx_ptr_batch = [self.alloc_scratch(f"inp_idx_ptr_batch_{i}") for i in range(batch_size//8)]
        vhash_batch = [self.alloc_scratch(f"vhash_batch_{i}", 8) for i in range(batch_size//8)]
        vtree_idx_batch = [self.alloc_scratch(f"vtree_idx_batch_{i}", 8) for i in range(batch_size//8)]
        vtmp1_batch = [self.alloc_scratch(f"vtmp1_batch_{i}", 8) for i in range(batch_size//8)]
        vtmp2_batch = [self.alloc_scratch(f"vtmp2_batch_{i}", 8) for i in range(batch_size//8)]

        # consts varying from 0 to 248 with a stride of 8. 0, 8, 16 ... 248
        CONST_0_to_256 = [self.alloc_scratch(i * 8) for i in range(batch_size//8)]

        INP_VALUES_P = self.alloc_scratch("INP_VALUES_P")
        INP_INDICES_P = self.alloc_scratch("INP_INDICES_P")
        
        # temporary registers that are used for both setup code and later used in round 3 and round 14 
        # to replace load instructions
        tmp1_batch  = self.alloc_scratch("tmp1_batch",  38)
        vtmp3_batch = self.alloc_scratch("vtmp3_batch", 128)

        # aliases only used in setup code to set constants
        CONST_1        = tmp1_batch + 0
        CONST_2        = tmp1_batch + 1
        CONST_3        = tmp1_batch + 2
        CONST_4        = tmp1_batch + 3
        CONST_5        = tmp1_batch + 4
        CONST_6        = tmp1_batch + 5
        CONST_7        = tmp1_batch + 6
        CONST_33       = tmp1_batch + 7
        HASH_VALUE_1   = tmp1_batch + 8
        HASH_VALUE_2   = tmp1_batch + 9
        HASH_VALUE_3   = tmp1_batch + 10
        HASH_VALUE_4   = tmp1_batch + 11
        HASH_VALUE_5   = tmp1_batch + 12
        HASH_VALUE_6   = tmp1_batch + 13
        CONST_4097     = tmp1_batch + 14
        CONST_19       = tmp1_batch + 15
        CONST_9        = tmp1_batch + 16
        FOREST_VAL_8_P = tmp1_batch + 17
        FOREST_VAL_0_P = tmp1_batch + 18
        NUM_NODES      = tmp1_batch + 19
        FIRST_8_FOREST_VALUES  = vtmp3_batch + 0
        SECOND_8_FOREST_VALUES = vtmp3_batch + 8

        def make_stream(*instrs):
            return InstructionStream(list(instrs))

        def const_broadcast(reg, val, vreg):
            """Load a const into reg at slot, then vbroadcast into vreg."""
            return make_stream(
                {"load": [("const", reg, val)]},
                {"valu": [("vbroadcast", vreg, reg)]},
            )
        
        # load all the required constants and vectorize them
        instructions_streams = [
            # CONST_0_to_256[0] — no broadcast
            make_stream({"load": [("const", CONST_0_to_256[0], 0)]}),

            # CONST_1 — broadcast + load NUM_NODES
            make_stream(
                {"load": [("const", CONST_1, 1)]},
                {"valu": [("vbroadcast", V_CONST_1, CONST_1)], "load": [("load", NUM_NODES, CONST_1)]},
            ),

            # CONST_2, CONST_3 — simple broadcast
            const_broadcast(CONST_2, 2, V_CONST_2),
            const_broadcast(CONST_3, 3, V_CONST_3),

            # CONST_4 — forest value loading chain
            make_stream(
                {"load": [("const", CONST_4, 4), ("const", CONST_0_to_256[1], 8)]},
                {"load": [("load", FOREST_VAL_0_P, CONST_4)]},
                {"load": [("vload", FIRST_8_FOREST_VALUES, FOREST_VAL_0_P)],
                    "alu":  [('+', FOREST_VAL_8_P, FOREST_VAL_0_P, CONST_0_to_256[1])],
                    "valu": [("vbroadcast", V_FOREST_VAL_P, FOREST_VAL_0_P)]},
                {"load": [("vload", SECOND_8_FOREST_VALUES, FOREST_VAL_8_P)]},
                {"valu": [
                    ("vbroadcast", V_FOREST_VAL_1, FIRST_8_FOREST_VALUES + 1),
                    ("vbroadcast", V_FOREST_VAL_2, FIRST_8_FOREST_VALUES + 2),
                    ("vbroadcast", V_FOREST_VAL_3, FIRST_8_FOREST_VALUES + 3),
                    ("vbroadcast", V_FOREST_VAL_4, FIRST_8_FOREST_VALUES + 4),
                    ("vbroadcast", V_FOREST_VAL_5, FIRST_8_FOREST_VALUES + 5),
                    ("vbroadcast", V_FOREST_VAL_6, FIRST_8_FOREST_VALUES + 6),
                ]},
                {"valu": [
                    ("vbroadcast", V_FOREST_VAL_7,  FIRST_8_FOREST_VALUES + 7),
                    ("vbroadcast", V_FOREST_VAL_8,  SECOND_8_FOREST_VALUES),
                    ("vbroadcast", V_FOREST_VAL_9,  SECOND_8_FOREST_VALUES + 1),
                    ("vbroadcast", V_FOREST_VAL_10, SECOND_8_FOREST_VALUES + 2),
                    ("vbroadcast", V_FOREST_VAL_11, SECOND_8_FOREST_VALUES + 3),
                    ("vbroadcast", V_FOREST_VAL_12, SECOND_8_FOREST_VALUES + 4),
                ]},
                {"valu": [
                    ("vbroadcast", V_FOREST_VAL_13, SECOND_8_FOREST_VALUES + 5),
                    ("vbroadcast", V_FOREST_VAL_14, SECOND_8_FOREST_VALUES + 6),
                    ("vbroadcast", V_FOREST_VAL_0,  FIRST_8_FOREST_VALUES),
                ]},
            ),

            # CONST_5, CONST_6 — load into tmp registers (no broadcast)
            make_stream(
                {"load": [("const", CONST_5, 5)]},
                {"load": [("load", INP_INDICES_P, CONST_5)]},
            ),
            make_stream(
                {"load": [("const", CONST_6, 6)]},
                {"load": [("load", INP_VALUES_P, CONST_6)]},
            ),

            # CONST_7 — broadcast + load tmp1_batch+32
            make_stream(
                {"load": [("const", CONST_7, 7)]},
                {"valu": [("vbroadcast", V_CONST_7, CONST_7)], "load": [("load", tmp1_batch + 32, CONST_7)]},
            ),

            # Simple const→vbroadcast streams
            const_broadcast(CONST_33,          33,         V_33),
            const_broadcast(HASH_VALUE_1,      0x7ED55D16, V_7ED55D16),
            const_broadcast(HASH_VALUE_2,      0xC761C23C, V_C761C23C),
            const_broadcast(HASH_VALUE_3,      0x165667B1, V_165667B1),
            const_broadcast(HASH_VALUE_4,      0xD3A2646C, V_D3A2646C),
            const_broadcast(HASH_VALUE_5,      0xFD7046C5, V_FD7046C5),
            const_broadcast(HASH_VALUE_6,      0xB55A4F09, V_B55A4F09),
            const_broadcast(CONST_4097,        4097,       V_4097),
            const_broadcast(CONST_19,          19,         V_19),
            const_broadcast(CONST_9,           9,          V_9),
            const_broadcast(CONST_0_to_256[2], 16,         V_16),

            # Batch const loads (no broadcast)
            *[
                make_stream({"load": [("const", CONST_0_to_256[i], i * 8)]})
                for i in range(3, batch_size // 8)
            ],
        ]

        res = self.schedule_instructions_from_independent_streams(instructions_streams)
        self.instrs.extend(res)
        instructions_streams.clear()
        self.add("flow", ("pause",))

        def my_hash(instruction_stream, batch, my_hash_alu_valu_mix_per_batch_round):
            valu_alu_select_array = [
                [
                    [{"valu": [('multiply_add', vhash_batch[batch], vhash_batch[batch], V_4097, V_7ED55D16)]}],
                    [
                        {"alu": [
                            ('*', vhash_batch[batch],     vhash_batch[batch],     V_4097),
                            ('*', vhash_batch[batch] + 1, vhash_batch[batch] + 1, V_4097),
                            ('*', vhash_batch[batch] + 2, vhash_batch[batch] + 2, V_4097),
                            ('*', vhash_batch[batch] + 3, vhash_batch[batch] + 3, V_4097),
                            ('*', vhash_batch[batch] + 4, vhash_batch[batch] + 4, V_4097),
                            ('*', vhash_batch[batch] + 5, vhash_batch[batch] + 5, V_4097),
                            ('*', vhash_batch[batch] + 6, vhash_batch[batch] + 6, V_4097),
                            ('*', vhash_batch[batch] + 7, vhash_batch[batch] + 7, V_4097)
                        ]},
                        {"alu": [
                            ('+', vhash_batch[batch],     vhash_batch[batch],     V_7ED55D16),
                            ('+', vhash_batch[batch] + 1, vhash_batch[batch] + 1, V_7ED55D16),
                            ('+', vhash_batch[batch] + 2, vhash_batch[batch] + 2, V_7ED55D16),
                            ('+', vhash_batch[batch] + 3, vhash_batch[batch] + 3, V_7ED55D16),
                            ('+', vhash_batch[batch] + 4, vhash_batch[batch] + 4, V_7ED55D16),
                            ('+', vhash_batch[batch] + 5, vhash_batch[batch] + 5, V_7ED55D16),
                            ('+', vhash_batch[batch] + 6, vhash_batch[batch] + 6, V_7ED55D16),
                            ('+', vhash_batch[batch] + 7, vhash_batch[batch] + 7, V_7ED55D16)
                        ]},
                    ]
                ],
                [
                    [{"valu": [
                        ('^',  vtmp1_batch[batch], vhash_batch[batch], V_C761C23C),
                        ('>>', vtmp2_batch[batch], vhash_batch[batch], V_19),
                    ]}],
                    [
                        {"alu": [
                            ('^',  vtmp1_batch[batch],     vhash_batch[batch],     V_C761C23C),
                            ('^',  vtmp1_batch[batch] + 1, vhash_batch[batch] + 1, V_C761C23C),
                            ('^',  vtmp1_batch[batch] + 2, vhash_batch[batch] + 2, V_C761C23C),
                            ('^',  vtmp1_batch[batch] + 3, vhash_batch[batch] + 3, V_C761C23C),
                            ('^',  vtmp1_batch[batch] + 4, vhash_batch[batch] + 4, V_C761C23C),
                            ('^',  vtmp1_batch[batch] + 5, vhash_batch[batch] + 5, V_C761C23C),
                            ('^',  vtmp1_batch[batch] + 6, vhash_batch[batch] + 6, V_C761C23C),
                            ('^',  vtmp1_batch[batch] + 7, vhash_batch[batch] + 7, V_C761C23C),
                            ('>>', vtmp2_batch[batch],     vhash_batch[batch],     V_19),
                            ('>>', vtmp2_batch[batch] + 1, vhash_batch[batch] + 1, V_19),
                            ('>>', vtmp2_batch[batch] + 2, vhash_batch[batch] + 2, V_19),
                            ('>>', vtmp2_batch[batch] + 3, vhash_batch[batch] + 3, V_19),
                        ]},
                        {"alu": [
                            ('>>', vtmp2_batch[batch] + 4, vhash_batch[batch] + 4, V_19),
                            ('>>', vtmp2_batch[batch] + 5, vhash_batch[batch] + 5, V_19),
                            ('>>', vtmp2_batch[batch] + 6, vhash_batch[batch] + 6, V_19),
                            ('>>', vtmp2_batch[batch] + 7, vhash_batch[batch] + 7, V_19),
                        ]},
                    ]
                ],
                [
                    [{"valu": [('^', vhash_batch[batch], vtmp1_batch[batch], vtmp2_batch[batch])]}],
                    [{"alu": [
                        ('^', vhash_batch[batch],     vtmp1_batch[batch],     vtmp2_batch[batch]),
                        ('^', vhash_batch[batch] + 1, vtmp1_batch[batch] + 1, vtmp2_batch[batch] + 1),
                        ('^', vhash_batch[batch] + 2, vtmp1_batch[batch] + 2, vtmp2_batch[batch] + 2),
                        ('^', vhash_batch[batch] + 3, vtmp1_batch[batch] + 3, vtmp2_batch[batch] + 3),
                        ('^', vhash_batch[batch] + 4, vtmp1_batch[batch] + 4, vtmp2_batch[batch] + 4),
                        ('^', vhash_batch[batch] + 5, vtmp1_batch[batch] + 5, vtmp2_batch[batch] + 5),
                        ('^', vhash_batch[batch] + 6, vtmp1_batch[batch] + 6, vtmp2_batch[batch] + 6),
                        ('^', vhash_batch[batch] + 7, vtmp1_batch[batch] + 7, vtmp2_batch[batch] + 7),
                    ]}],
                ],
                [
                    [{"valu": [('multiply_add', vhash_batch[batch], vhash_batch[batch], V_33, V_165667B1)]}],
                    [
                        {"alu": [
                            ('*', vhash_batch[batch],     vhash_batch[batch],     V_33),
                            ('*', vhash_batch[batch] + 1, vhash_batch[batch] + 1, V_33),
                            ('*', vhash_batch[batch] + 2, vhash_batch[batch] + 2, V_33),
                            ('*', vhash_batch[batch] + 3, vhash_batch[batch] + 3, V_33),
                            ('*', vhash_batch[batch] + 4, vhash_batch[batch] + 4, V_33),
                            ('*', vhash_batch[batch] + 5, vhash_batch[batch] + 5, V_33),
                            ('*', vhash_batch[batch] + 6, vhash_batch[batch] + 6, V_33),
                            ('*', vhash_batch[batch] + 7, vhash_batch[batch] + 7, V_33)
                        ]},
                        {"alu": [
                            ('+', vhash_batch[batch],     vhash_batch[batch],     V_165667B1),
                            ('+', vhash_batch[batch] + 1, vhash_batch[batch] + 1, V_165667B1),
                            ('+', vhash_batch[batch] + 2, vhash_batch[batch] + 2, V_165667B1),
                            ('+', vhash_batch[batch] + 3, vhash_batch[batch] + 3, V_165667B1),
                            ('+', vhash_batch[batch] + 4, vhash_batch[batch] + 4, V_165667B1),
                            ('+', vhash_batch[batch] + 5, vhash_batch[batch] + 5, V_165667B1),
                            ('+', vhash_batch[batch] + 6, vhash_batch[batch] + 6, V_165667B1),
                            ('+', vhash_batch[batch] + 7, vhash_batch[batch] + 7, V_165667B1)
                        ]},
                    ]
                ],
                [
                    [{"valu": [
                        ('+',  vtmp1_batch[batch], vhash_batch[batch], V_D3A2646C),
                        ('<<', vtmp2_batch[batch], vhash_batch[batch], V_9),
                    ]}],
                    [
                        {"alu": [
                            ('+',  vtmp1_batch[batch],     vhash_batch[batch],     V_D3A2646C),
                            ('+',  vtmp1_batch[batch] + 1, vhash_batch[batch] + 1, V_D3A2646C),
                            ('+',  vtmp1_batch[batch] + 2, vhash_batch[batch] + 2, V_D3A2646C),
                            ('+',  vtmp1_batch[batch] + 3, vhash_batch[batch] + 3, V_D3A2646C),
                            ('+',  vtmp1_batch[batch] + 4, vhash_batch[batch] + 4, V_D3A2646C),
                            ('+',  vtmp1_batch[batch] + 5, vhash_batch[batch] + 5, V_D3A2646C),
                            ('+',  vtmp1_batch[batch] + 6, vhash_batch[batch] + 6, V_D3A2646C),
                            ('+',  vtmp1_batch[batch] + 7, vhash_batch[batch] + 7, V_D3A2646C),
                            ('<<', vtmp2_batch[batch],     vhash_batch[batch],     V_9),
                            ('<<', vtmp2_batch[batch] + 1, vhash_batch[batch] + 1, V_9),
                            ('<<', vtmp2_batch[batch] + 2, vhash_batch[batch] + 2, V_9),
                            ('<<', vtmp2_batch[batch] + 3, vhash_batch[batch] + 3, V_9),
                        ]},
                        {"alu": [
                            ('<<', vtmp2_batch[batch] + 4, vhash_batch[batch] + 4, V_9),
                            ('<<', vtmp2_batch[batch] + 5, vhash_batch[batch] + 5, V_9),
                            ('<<', vtmp2_batch[batch] + 6, vhash_batch[batch] + 6, V_9),
                            ('<<', vtmp2_batch[batch] + 7, vhash_batch[batch] + 7, V_9),
                        ]},
                    ],
                ],
                [
                    [{"valu": [('^', vhash_batch[batch], vtmp1_batch[batch], vtmp2_batch[batch])]}],
                    [{"alu": [
                        ('^', vhash_batch[batch],     vtmp1_batch[batch],     vtmp2_batch[batch]),
                        ('^', vhash_batch[batch] + 1, vtmp1_batch[batch] + 1, vtmp2_batch[batch] + 1),
                        ('^', vhash_batch[batch] + 2, vtmp1_batch[batch] + 2, vtmp2_batch[batch] + 2),
                        ('^', vhash_batch[batch] + 3, vtmp1_batch[batch] + 3, vtmp2_batch[batch] + 3),
                        ('^', vhash_batch[batch] + 4, vtmp1_batch[batch] + 4, vtmp2_batch[batch] + 4),
                        ('^', vhash_batch[batch] + 5, vtmp1_batch[batch] + 5, vtmp2_batch[batch] + 5),
                        ('^', vhash_batch[batch] + 6, vtmp1_batch[batch] + 6, vtmp2_batch[batch] + 6),
                        ('^', vhash_batch[batch] + 7, vtmp1_batch[batch] + 7, vtmp2_batch[batch] + 7),
                    ]}],
                ],
                [
                    [{"valu": [('multiply_add', vhash_batch[batch], vhash_batch[batch], V_9, V_FD7046C5)]}],
                    [
                        {"alu": [
                            ('*', vhash_batch[batch],     vhash_batch[batch],     V_9),
                            ('*', vhash_batch[batch] + 1, vhash_batch[batch] + 1, V_9),
                            ('*', vhash_batch[batch] + 2, vhash_batch[batch] + 2, V_9),
                            ('*', vhash_batch[batch] + 3, vhash_batch[batch] + 3, V_9),
                            ('*', vhash_batch[batch] + 4, vhash_batch[batch] + 4, V_9),
                            ('*', vhash_batch[batch] + 5, vhash_batch[batch] + 5, V_9),
                            ('*', vhash_batch[batch] + 6, vhash_batch[batch] + 6, V_9),
                            ('*', vhash_batch[batch] + 7, vhash_batch[batch] + 7, V_9)
                        ]},
                        {"alu": [
                            ('+', vhash_batch[batch],     vhash_batch[batch],     V_FD7046C5),
                            ('+', vhash_batch[batch] + 1, vhash_batch[batch] + 1, V_FD7046C5),
                            ('+', vhash_batch[batch] + 2, vhash_batch[batch] + 2, V_FD7046C5),
                            ('+', vhash_batch[batch] + 3, vhash_batch[batch] + 3, V_FD7046C5),
                            ('+', vhash_batch[batch] + 4, vhash_batch[batch] + 4, V_FD7046C5),
                            ('+', vhash_batch[batch] + 5, vhash_batch[batch] + 5, V_FD7046C5),
                            ('+', vhash_batch[batch] + 6, vhash_batch[batch] + 6, V_FD7046C5),
                            ('+', vhash_batch[batch] + 7, vhash_batch[batch] + 7, V_FD7046C5)
                        ]},
                    ]
                ],
                [
                    [{"valu": [
                        ('^',  vtmp1_batch[batch], vhash_batch[batch], V_B55A4F09),
                        ('>>', vtmp2_batch[batch], vhash_batch[batch], V_16),
                    ]}],
                    [
                        {"alu": [
                            ('^',  vtmp1_batch[batch],     vhash_batch[batch],     V_B55A4F09),
                            ('^',  vtmp1_batch[batch] + 1, vhash_batch[batch] + 1, V_B55A4F09),
                            ('^',  vtmp1_batch[batch] + 2, vhash_batch[batch] + 2, V_B55A4F09),
                            ('^',  vtmp1_batch[batch] + 3, vhash_batch[batch] + 3, V_B55A4F09),
                            ('^',  vtmp1_batch[batch] + 4, vhash_batch[batch] + 4, V_B55A4F09),
                            ('^',  vtmp1_batch[batch] + 5, vhash_batch[batch] + 5, V_B55A4F09),
                            ('^',  vtmp1_batch[batch] + 6, vhash_batch[batch] + 6, V_B55A4F09),
                            ('^',  vtmp1_batch[batch] + 7, vhash_batch[batch] + 7, V_B55A4F09),
                            ('>>', vtmp2_batch[batch],     vhash_batch[batch],     V_16),
                            ('>>', vtmp2_batch[batch] + 1, vhash_batch[batch] + 1, V_16),
                            ('>>', vtmp2_batch[batch] + 2, vhash_batch[batch] + 2, V_16),
                            ('>>', vtmp2_batch[batch] + 3, vhash_batch[batch] + 3, V_16),
                        ]},
                        {"alu": [
                            ('>>', vtmp2_batch[batch] + 4, vhash_batch[batch] + 4, V_16),
                            ('>>', vtmp2_batch[batch] + 5, vhash_batch[batch] + 5, V_16),
                            ('>>', vtmp2_batch[batch] + 6, vhash_batch[batch] + 6, V_16),
                            ('>>', vtmp2_batch[batch] + 7, vhash_batch[batch] + 7, V_16),
                        ]},
                    ],
                ],
                [
                    [{"valu": [('^', vhash_batch[batch], vtmp1_batch[batch], vtmp2_batch[batch])]}],
                    [{"alu": [
                        ('^', vhash_batch[batch],     vtmp1_batch[batch],     vtmp2_batch[batch]),
                        ('^', vhash_batch[batch] + 1, vtmp1_batch[batch] + 1, vtmp2_batch[batch] + 1),
                        ('^', vhash_batch[batch] + 2, vtmp1_batch[batch] + 2, vtmp2_batch[batch] + 2),
                        ('^', vhash_batch[batch] + 3, vtmp1_batch[batch] + 3, vtmp2_batch[batch] + 3),
                        ('^', vhash_batch[batch] + 4, vtmp1_batch[batch] + 4, vtmp2_batch[batch] + 4),
                        ('^', vhash_batch[batch] + 5, vtmp1_batch[batch] + 5, vtmp2_batch[batch] + 5),
                        ('^', vhash_batch[batch] + 6, vtmp1_batch[batch] + 6, vtmp2_batch[batch] + 6),
                        ('^', vhash_batch[batch] + 7, vtmp1_batch[batch] + 7, vtmp2_batch[batch] + 7),
                    ]}],
                ]
            ]
            for idx in range(9):
                instruction_stream.extend(valu_alu_select_array[idx][my_hash_alu_valu_mix_per_batch_round[idx]])
        
        def load_forest_values_for_round2_round13(batch, instruction_stream):
            instruction_stream.extend([
                        {"store": [('vstore', inp_idx_ptr_batch[batch], vtree_idx_batch[batch])]},
                        {"valu":  [('-', vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_3)]},
                        {"valu":  [('&', vtmp2_batch[batch], vtree_idx_batch[batch], V_CONST_1)]},
                        {"flow":  [("vselect", vtmp1_batch[batch], vtmp2_batch[batch], V_FOREST_VAL_4, V_FOREST_VAL_3)]},
                        {"flow":  [("vselect", vtmp2_batch[batch], vtmp2_batch[batch], V_FOREST_VAL_6, V_FOREST_VAL_5)]},
                        {"alu": [
                            ('>>', vtree_idx_batch[batch] + j, vtree_idx_batch[batch] + j, V_CONST_1 + j)
                            for j in range(8)
                        ]},
                        {"alu": [
                            ('&', vtree_idx_batch[batch] + j, vtree_idx_batch[batch] + j, V_CONST_1 + j)
                            for j in range(8)
                        ]},
                        {"flow": [("vselect", vtmp2_batch[batch], vtree_idx_batch[batch], vtmp2_batch[batch], vtmp1_batch[batch])]},
                        {"valu": [('^', vhash_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                    ])
        
        def load_forest_values_for_round3_round14_1(batch, instruction_stream):
            instruction_stream.extend([
                            {"store": [('vstore', inp_idx_ptr_batch[batch], vtree_idx_batch[batch]), ('vstore', inp_val_ptr_batch[batch], vhash_batch[batch])]},
                            {"valu":  [("-", vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_7)]},
                            {"valu":  [("&", vtmp1_batch[batch], vtree_idx_batch[batch], V_CONST_1)]},
                            {"flow":  [("vselect", vhash_batch[batch],            vtmp1_batch[batch], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                            {"flow":  [("vselect", vtmp2_batch[batch],            vtmp1_batch[batch], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow":  [("vselect", vtmp3_batch + (batch * 8),     vtmp1_batch[batch], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"store": [("vstore",  tmp1_batch + batch,            vtmp3_batch + (batch * 8))]},
                            {"flow":  [("vselect", vtmp3_batch + (batch * 8),     vtmp1_batch[batch], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                            {"valu":  [(">>", vtmp1_batch[batch], vtree_idx_batch[batch], V_CONST_1)]},
                            {"valu":  [("&",  vtmp1_batch[batch], vtmp1_batch[batch], V_CONST_1)]},
                            {"flow":  [("vselect", vhash_batch[batch], vtmp1_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                            {"load":  [("vload",   vtmp2_batch[batch], tmp1_batch + batch)]},
                            {"flow":  [("vselect", vtmp2_batch[batch], vtmp1_batch[batch], vtmp3_batch + (batch * 8), vtmp2_batch[batch])]},
                            {"valu":  [(">>", vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_2)]},
                            {"alu": [
                                ('&', vtree_idx_batch[batch] + j, vtree_idx_batch[batch] + j, V_CONST_1 + j)
                                for j in range(8)
                            ]},
                            {"flow": [("vselect", vtmp2_batch[batch], vtree_idx_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                            {"load": [('vload', vtree_idx_batch[batch], inp_idx_ptr_batch[batch]), ('vload', vhash_batch[batch], inp_val_ptr_batch[batch])]},
                        ])

        def load_forest_values_for_round3_round14_2(batch, instruction_stream):
            instruction_stream.extend([
                        {"store": [('vstore', inp_idx_ptr_batch[batch], vtree_idx_batch[batch]), ('vstore', inp_val_ptr_batch[batch], vhash_batch[batch])]},
                        {"valu":  [("-", vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_7)]},
                        {"valu":  [("&", vtmp1_batch[batch], vtree_idx_batch[batch], V_CONST_1)]},
                        {"flow":  [("vselect", vhash_batch[batch], vtmp1_batch[batch], V_FOREST_VAL_8,  V_FOREST_VAL_7)]},
                        {"flow":  [("vselect", vtmp2_batch[batch], vtmp1_batch[batch], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                        {"valu":  [(">>", vtmp1_batch[batch], vtree_idx_batch[batch], V_CONST_1)]},
                        {"valu":  [("&",  vtmp1_batch[batch], vtmp1_batch[batch], V_CONST_1)]},
                        {"flow":  [("vselect", vhash_batch[batch], vtmp1_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                        {"store": [("vstore",  tmp1_batch + batch, vhash_batch[batch])]},
                        {"valu":  [("&",  vtmp1_batch[batch], vtree_idx_batch[batch], V_CONST_1)]},
                        {"flow":  [("vselect", vhash_batch[batch], vtmp1_batch[batch], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                        {"flow":  [("vselect", vtmp2_batch[batch], vtmp1_batch[batch], V_FOREST_VAL_14, V_FOREST_VAL_13)]},
                        {"valu":  [(">>", vtmp1_batch[batch], vtree_idx_batch[batch], V_CONST_1)]},
                        {"valu":  [("&",  vtmp1_batch[batch], vtmp1_batch[batch], V_CONST_1)]},
                        {"flow":  [("vselect", vhash_batch[batch], vtmp1_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                        {"load":  [("vload",   vtmp2_batch[batch], tmp1_batch + batch)]},
                        {"valu":  [(">>", vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_2)]},
                        {"alu": [
                            ('&', vtree_idx_batch[batch] + j, vtree_idx_batch[batch] + j, V_CONST_1 + j)
                            for j in range(8)
                        ]},
                        {"flow": [("vselect", vtmp2_batch[batch], vtree_idx_batch[batch], vhash_batch[batch], vtmp2_batch[batch])]},
                        {"load": [('vload', vtree_idx_batch[batch], inp_idx_ptr_batch[batch]), ('vload', vhash_batch[batch], inp_val_ptr_batch[batch])]},
                    ])

        my_hash_alu_valu_mix = self.get_my_hash_alu_valu_mix()

        for batch in range(batch_size // VLEN):
            instruction_stream = []
            instruction_stream.extend([
                {"alu": [
                    ('+', inp_val_ptr_batch[batch],    INP_VALUES_P,      CONST_0_to_256[batch]),
                    ('+', inp_idx_ptr_batch[batch],    INP_INDICES_P,     CONST_0_to_256[batch]),
                    ('+', tmp1_batch + batch,   tmp1_batch + 32,   CONST_0_to_256[batch]),
                ]},
                {"load": [('vload', vhash_batch[batch], inp_val_ptr_batch[batch])]},
            ])

            for round in range(rounds):
                if round == 0:
                    instruction_stream.extend([
                        {"valu": [('^', vhash_batch[batch], V_FOREST_VAL_0, vhash_batch[batch])]},
                    ])
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])
                    instruction_stream.extend([
                        {"valu": [('%',       vtmp1_batch[batch], vhash_batch[batch], V_CONST_2)]},
                        {"flow": [('vselect', vtree_idx_batch[batch], vtmp1_batch[batch], V_CONST_2, V_CONST_1)]},
                    ])

                elif round == 1:
                    instruction_stream.extend([
                        {"flow": [('vselect', vtmp2_batch[batch], vtmp1_batch[batch], V_FOREST_VAL_2, V_FOREST_VAL_1)]},
                        {"valu": [('^', vhash_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                    ])
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp1_batch[batch], vhash_batch[batch],  V_CONST_2)]},
                        {"flow": [('vselect',    vtmp1_batch[batch], vtmp1_batch[batch],  V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_2, vtmp1_batch[batch])]},
                    ])

                elif round == 2:
                    load_forest_values_for_round2_round13(batch, instruction_stream)
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp1_batch[batch], vhash_batch[batch],  V_CONST_2)]},
                        {"flow": [('vselect',    vtmp1_batch[batch], vtmp1_batch[batch],  V_CONST_2, V_CONST_1)]},
                        {"load": [('vload',      vtree_idx_batch[batch], inp_idx_ptr_batch[batch])]},
                        {"valu": [('multiply_add', vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_2, vtmp1_batch[batch])]},
                    ])

                elif round == 3:
                    if batch < 16:
                        load_forest_values_for_round3_round14_1(batch, instruction_stream)
                    else:
                        load_forest_values_for_round3_round14_2(batch, instruction_stream)
                    instruction_stream.extend([
                        {"valu": [('^', vhash_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                    ])
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp1_batch[batch], vhash_batch[batch],  V_CONST_2)]},
                        {"flow": [('vselect',    vtmp1_batch[batch], vtmp1_batch[batch],  V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_2, vtmp1_batch[batch])]},
                    ])

                elif 4 <= round <= 9:
                    instruction_stream.extend([
                        {"valu": [('+', vtmp1_batch[batch], vtree_idx_batch[batch], V_FOREST_VAL_P)]},
                        {"load": [('load', vtmp2_batch[batch],     vtmp1_batch[batch]),     ('load', vtmp2_batch[batch] + 1, vtmp1_batch[batch] + 1)]},
                        {"load": [('load', vtmp2_batch[batch] + 2, vtmp1_batch[batch] + 2), ('load', vtmp2_batch[batch] + 3, vtmp1_batch[batch] + 3)]},
                        {"load": [('load', vtmp2_batch[batch] + 4, vtmp1_batch[batch] + 4), ('load', vtmp2_batch[batch] + 5, vtmp1_batch[batch] + 5)]},
                        {"load": [('load', vtmp2_batch[batch] + 6, vtmp1_batch[batch] + 6), ('load', vtmp2_batch[batch] + 7, vtmp1_batch[batch] + 7)]},
                        {"valu": [('^', vhash_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                    ])
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp1_batch[batch], vhash_batch[batch],  V_CONST_2)]},
                        {"flow": [('vselect',    vtmp1_batch[batch], vtmp1_batch[batch],  V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_2, vtmp1_batch[batch])]},
                    ])

                elif round == 10:
                    instruction_stream.extend([
                        {"valu": [('+', vtmp1_batch[batch], vtree_idx_batch[batch], V_FOREST_VAL_P)]},
                        {"load": [('load', vtmp2_batch[batch],     vtmp1_batch[batch]),     ('load', vtmp2_batch[batch] + 1, vtmp1_batch[batch] + 1)]},
                        {"load": [('load', vtmp2_batch[batch] + 2, vtmp1_batch[batch] + 2), ('load', vtmp2_batch[batch] + 3, vtmp1_batch[batch] + 3)]},
                        {"load": [('load', vtmp2_batch[batch] + 4, vtmp1_batch[batch] + 4), ('load', vtmp2_batch[batch] + 5, vtmp1_batch[batch] + 5)]},
                        {"load": [('load', vtmp2_batch[batch] + 6, vtmp1_batch[batch] + 6), ('load', vtmp2_batch[batch] + 7, vtmp1_batch[batch] + 7)]},
                        {"valu": [('^', vhash_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                    ])
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])

                elif round == 11:
                    instruction_stream.extend([
                        {"valu": [('^', vhash_batch[batch], V_FOREST_VAL_0, vhash_batch[batch])]},
                    ])
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])
                    instruction_stream.extend([
                        {"valu": [('%',       vtmp1_batch[batch], vhash_batch[batch], V_CONST_2)]},
                        {"flow": [('vselect', vtree_idx_batch[batch], vtmp1_batch[batch], V_CONST_2, V_CONST_1)]},
                    ])

                elif round == 12:
                    instruction_stream.extend([
                        {"flow": [('vselect', vtmp2_batch[batch], vtmp1_batch[batch], V_FOREST_VAL_2, V_FOREST_VAL_1)]},
                        {"valu": [('^', vhash_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                    ])
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp1_batch[batch], vhash_batch[batch],  V_CONST_2)]},
                        {"flow": [('vselect',    vtmp1_batch[batch], vtmp1_batch[batch],  V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_2, vtmp1_batch[batch])]},
                    ])

                elif round == 13:
                    load_forest_values_for_round2_round13(batch, instruction_stream)
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp1_batch[batch], vhash_batch[batch],  V_CONST_2)]},
                        {"flow": [('vselect',    vtmp1_batch[batch], vtmp1_batch[batch],  V_CONST_2, V_CONST_1)]},
                        {"load": [('vload',      vtree_idx_batch[batch], inp_idx_ptr_batch[batch])]},
                        {"valu": [('multiply_add', vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_2, vtmp1_batch[batch])]},
                    ])

                elif round == 14:
                    if batch < 16:
                        load_forest_values_for_round3_round14_1(batch, instruction_stream)
                    elif batch >= 16 and batch <= 27:
                        load_forest_values_for_round3_round14_2(batch, instruction_stream)
                    else:
                        instruction_stream.extend([
                            {"valu": [('+', vtmp1_batch[batch], vtree_idx_batch[batch], V_FOREST_VAL_P)]},
                            {"load": [('load', vtmp2_batch[batch],     vtmp1_batch[batch]),     ('load', vtmp2_batch[batch] + 1, vtmp1_batch[batch] + 1)]},
                            {"load": [('load', vtmp2_batch[batch] + 2, vtmp1_batch[batch] + 2), ('load', vtmp2_batch[batch] + 3, vtmp1_batch[batch] + 3)]},
                            {"load": [('load', vtmp2_batch[batch] + 4, vtmp1_batch[batch] + 4), ('load', vtmp2_batch[batch] + 5, vtmp1_batch[batch] + 5)]},
                            {"load": [('load', vtmp2_batch[batch] + 6, vtmp1_batch[batch] + 6), ('load', vtmp2_batch[batch] + 7, vtmp1_batch[batch] + 7)]},
                        ])
                    instruction_stream.extend([
                        {"valu": [('^', vhash_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                    ])
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])
                    instruction_stream.extend([
                        {"valu": [('%',          vtmp1_batch[batch], vhash_batch[batch],  V_CONST_2)]},
                        {"flow": [('vselect',    vtmp1_batch[batch], vtmp1_batch[batch],  V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtree_idx_batch[batch], vtree_idx_batch[batch], V_CONST_2, vtmp1_batch[batch])]},
                    ])

                else:  # round >= 15
                    instruction_stream.extend([
                        {"valu": [('+', vtmp1_batch[batch], vtree_idx_batch[batch], V_FOREST_VAL_P)]},
                        {"load": [('load', vtmp2_batch[batch],     vtmp1_batch[batch]),     ('load', vtmp2_batch[batch] + 1, vtmp1_batch[batch] + 1)]},
                        {"load": [('load', vtmp2_batch[batch] + 2, vtmp1_batch[batch] + 2), ('load', vtmp2_batch[batch] + 3, vtmp1_batch[batch] + 3)]},
                        {"load": [('load', vtmp2_batch[batch] + 4, vtmp1_batch[batch] + 4), ('load', vtmp2_batch[batch] + 5, vtmp1_batch[batch] + 5)]},
                        {"load": [('load', vtmp2_batch[batch] + 6, vtmp1_batch[batch] + 6), ('load', vtmp2_batch[batch] + 7, vtmp1_batch[batch] + 7)]},
                        {"valu": [('^', vhash_batch[batch], vtmp2_batch[batch], vhash_batch[batch])]},
                    ])
                    my_hash(instruction_stream, batch, my_hash_alu_valu_mix[batch][round])

            instruction_stream.extend([
                {"store": [('vstore', inp_val_ptr_batch[batch], vhash_batch[batch])]},
            ])
            instructions_streams.append(InstructionStream(instruction_stream))

        res = self.schedule_instructions_from_independent_streams(instructions_streams)

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
        do_kernel_test(10, 16, 256)


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
