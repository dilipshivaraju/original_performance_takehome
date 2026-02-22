from typing import Any, Literal
from itertools import product, islice
from multiprocessing import Pool
from copy import deepcopy

Engine = Literal["alu", "load", "store", "flow"]
Instruction = dict[Engine, list[tuple]]


class InstructionStream:
    def __init__(self, instructions: list[Instruction]) -> None:
        self.instructions: list[Instruction] = deepcopy(instructions)
        self.length: int = len(instructions)
        self.cur_pointer: int = 0

def schedule_instructions(InstructionStreams):
    instrs = []
    while len(InstructionStreams) > 0:
        cur_instr: dict = {}
        valu_slots: int = 6

        for stream in InstructionStreams:
            cur = stream.instructions[stream.cur_pointer]

            if "valu" in cur:
                current_value_slot = len(cur["valu"])

                while valu_slots > 0 and current_value_slot > 0:
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
                    slot = cur["flow"].pop(0)
                    cur_instr["flow"] = cur_instr.get("flow", [])
                    cur_instr["flow"].append(slot)
                    flow_slots -= 1
                    current_value_slot -= 1

            if flow_slots == 0:
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

batch_size = 256
rounds = 16

V_CONST_1 = 0
V_CONST_2 = 8
V_CONST_3 = 16
V_CONST_7 = 24
FIRST_8_VALUES = 32
SECOND_8_VALUES = 40

V_7ED55D16 = 48
V_C761C23C = 56
V_165667B1 = 64
V_D3A2646C = 72
V_FD7046C5 = 80
V_B55A4F09 = 88

V_4097 = 96
V_19 = 104
V_33 = 112
V_9 = 120
V_16 = 128

V_FOREST_VAL_0 = 136
V_FOREST_VAL_1 = 144
V_FOREST_VAL_2 = 152
V_FOREST_VAL_3 = 160
V_FOREST_VAL_4 = 168
V_FOREST_VAL_5 = 176
V_FOREST_VAL_6 = 184

V_FOREST_VAL_7 = 192
V_FOREST_VAL_8 = 200
V_FOREST_VAL_9 = 208
V_FOREST_VAL_10 = 216
V_FOREST_VAL_11 = 224
V_FOREST_VAL_12 = 232
V_FOREST_VAL_13 = 240
V_FOREST_VAL_14 = 248

V_NUM_NODES = 256
V_FOREST_VALUE_P = 264

tmp4_batch = [272 + i * 1 for i in range(batch_size//8)]
tmp5_batch = [272 + (batch_size//8) + i * 1 for i in range(batch_size//8)]
vtmp1_batch = [272 + 2*(batch_size//8) + i * 8 for i in range(batch_size//8)]
vtmp2_batch = [272 + 2*(batch_size//8) + (batch_size//8)*8 + i * 8 for i in range(batch_size//8)]
vtmp4_batch = [272 + 2*(batch_size//8) + 2*(batch_size//8)*8 + i * 8 for i in range(batch_size//8)]
vtmp5_batch = [272 + 2*(batch_size//8) + 3*(batch_size//8)*8 + i * 8 for i in range(batch_size//8)]

_vtmp5_end = 272 + 2*(batch_size//8) + 4*(batch_size//8)*8

vtmp6 = [_vtmp5_end + i * 8 for i in range(7)]
vtmp7 = [_vtmp5_end + 56 + i * 8 for i in range(7)]

CONST = [_vtmp5_end + 112 + i * 1 for i in range(batch_size//8)]

_const_end = _vtmp5_end + 112 + (batch_size//8)

CONST_1 = _const_end
CONST_2 = _const_end + 1
CONST_3 = _const_end + 2
CONST_4 = _const_end + 3
CONST_5 = _const_end + 4
CONST_6 = _const_end + 5
CONST_7 = _const_end + 6

batches = [0, 1, 2, 3, 4, 5, 6]

HASH_VALUE_1 = _const_end + 7
HASH_VALUE_2 = _const_end + 8
HASH_VALUE_3 = _const_end + 9
HASH_VALUE_4 = _const_end + 10
HASH_VALUE_5 = _const_end + 11
HASH_VALUE_6 = _const_end + 12
CONST_4097 = _const_end + 13
CONST_19 = _const_end + 14
CONST_9 = _const_end + 15
CONST_33 = _const_end + 16

tmp1 = _const_end + 17
tmp2 = _const_end + 18
forest_val_8_p = _const_end + 19
FOREST_VALUE_P = _const_end + 20
NUM_NODES = _const_end + 21
vtmp8 = _const_end + 22


def initial_setup():
    InstructionStreams = []
    instrs = []

    instrs[:] = [{"load":[("const", CONST[0], 0)]}]

    InstructionStreams.append(InstructionStream(instrs))

    instrs[:] = [{"load":[("const", CONST_1, 1)]},
                {"valu":[('vbroadcast', V_CONST_1, CONST_1)], "load":[("load", NUM_NODES, CONST_1)]},
                {"valu":[('vbroadcast', V_NUM_NODES, NUM_NODES)]}]

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
                    {"valu":[('vbroadcast', V_CONST_7, CONST_7)]}]

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
    res = schedule_instructions(InstructionStreams)

    a.extend(res)
    instrs.extend(a)
    #print(a)
    #instrs = deepcopy(self.instrs)
    #print(len(self.instrs))
    InstructionStreams.clear()
    return a
    #self.add("flow", ("pause",))

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

def round_3_alu_valu_select(instruction_stream, i, perm):
    valu_alu_select_array = [
        [
            [{"valu": [("-", vtmp2_batch[i], vtmp2_batch[i], V_CONST_7)]}],
            [
                {"alu": [
                    ('-', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_7),
                    ('-', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_7 + 1),
                    ('-', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_7 + 2),
                    ('-', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_7 + 3),
                    ('-', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_7 + 4),
                    ('-', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_7 + 5),
                    ('-', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_7 + 6),
                    ('-', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_7 + 7),
                ]}
            ]
        ],
        [   
            [{"valu": [("&", vtmp4_batch[i], vtmp2_batch[i], V_CONST_1)]}],
            [
                {"alu": [
                    ('&', vtmp4_batch[i],     vtmp2_batch[i],     V_CONST_1),
                    ('&', vtmp4_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                    ('&', vtmp4_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                    ('&', vtmp4_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                    ('&', vtmp4_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                    ('&', vtmp4_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                    ('&', vtmp4_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                    ('&', vtmp4_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                ]}
            ]
        ],
        [
            [{"valu": [(">>", vtmp7[batches[0]], vtmp2_batch[i], V_CONST_1)]}],
            [
                {"alu": [
                    ('>>', vtmp7[batches[0]],     vtmp2_batch[i],     V_CONST_1),
                    ('>>', vtmp7[batches[0]] + 1, vtmp2_batch[i] + 1, V_CONST_1 + 1),
                    ('>>', vtmp7[batches[0]] + 2, vtmp2_batch[i] + 2, V_CONST_1 + 2),
                    ('>>', vtmp7[batches[0]] + 3, vtmp2_batch[i] + 3, V_CONST_1 + 3),
                    ('>>', vtmp7[batches[0]] + 4, vtmp2_batch[i] + 4, V_CONST_1 + 4),
                    ('>>', vtmp7[batches[0]] + 5, vtmp2_batch[i] + 5, V_CONST_1 + 5),
                    ('>>', vtmp7[batches[0]] + 6, vtmp2_batch[i] + 6, V_CONST_1 + 6),
                    ('>>', vtmp7[batches[0]] + 7, vtmp2_batch[i] + 7, V_CONST_1 + 7),
                ]}
            ]
        ],
        [
            [{"valu": [("&", vtmp7[batches[0]], vtmp7[batches[0]], V_CONST_1)]}],
            [
                {"alu": [
                    ('&', vtmp7[batches[0]],     vtmp7[batches[0]],     V_CONST_1),
                    ('&', vtmp7[batches[0]] + 1, vtmp7[batches[0]] + 1, V_CONST_1 + 1),
                    ('&', vtmp7[batches[0]] + 2, vtmp7[batches[0]] + 2, V_CONST_1 + 2),
                    ('&', vtmp7[batches[0]] + 3, vtmp7[batches[0]] + 3, V_CONST_1 + 3),
                    ('&', vtmp7[batches[0]] + 4, vtmp7[batches[0]] + 4, V_CONST_1 + 4),
                    ('&', vtmp7[batches[0]] + 5, vtmp7[batches[0]] + 5, V_CONST_1 + 5),
                    ('&', vtmp7[batches[0]] + 6, vtmp7[batches[0]] + 6, V_CONST_1 + 6),
                    ('&', vtmp7[batches[0]] + 7, vtmp7[batches[0]] + 7, V_CONST_1 + 7),
                ]}
            ]
        ],
        [
            [{"valu": [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_2)]}],
            [
                {"alu": [
                    ('>>', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_2),
                    ('>>', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_2 + 1),
                    ('>>', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_2 + 2),
                    ('>>', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_2 + 3),
                    ('>>', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_2 + 4),
                    ('>>', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_2 + 5),
                    ('>>', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_2 + 6),
                    ('>>', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_2 + 7),
                ]}
            ]
        ],
        [
            [{"valu": [("&", vtmp2_batch[i], vtmp2_batch[i], V_CONST_1)]}],
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
                {"store":[('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]}])


    for _ in range(2):
        instruction_stream.extend(valu_alu_select_array[idx][perm[idx]])
        idx += 1
    
    instruction_stream.extend([{"flow": [("vselect", vtmp1_batch[i], vtmp4_batch[i], V_FOREST_VAL_8, V_FOREST_VAL_7)]},
                            {"flow": [("vselect", vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_10, V_FOREST_VAL_9)]},
                            {"flow": [("vselect", vtmp6[batches[0]], vtmp4_batch[i], V_FOREST_VAL_12, V_FOREST_VAL_11)]},
                            {"flow": [("vselect", vtmp4_batch[i], vtmp4_batch[i], V_FOREST_VAL_14, V_FOREST_VAL_13)]}])

    for _ in range(2):
        instruction_stream.extend(valu_alu_select_array[idx][perm[idx]])
        idx += 1
    
    instruction_stream.extend([{"flow": [("vselect", vtmp1_batch[i], vtmp7[batches[0]], vtmp5_batch[i], vtmp1_batch[i])]},
                            {"flow": [("vselect", vtmp5_batch[i], vtmp7[batches[0]], vtmp4_batch[i], vtmp6[batches[0]])]}])

    for _ in range(2):
        instruction_stream.extend(valu_alu_select_array[idx][perm[idx]])
        idx += 1
    
    instruction_stream.extend([{"flow": [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp1_batch[i])]},
                               {"load": [('vload', vtmp2_batch[i], tmp5_batch[i]), ('vload', vtmp1_batch[i], tmp4_batch[i])]}])

def hash_instrs(instruction_stream, batch, perm):
    """instruction_stream.extend([{"alu": [
                ('^', vtmp1_batch[i],     vtmp5_batch[i],     vtmp1_batch[i]),
                ('^', vtmp1_batch[i] + 1, vtmp5_batch[i] + 1, vtmp1_batch[i] + 1),
                ('^', vtmp1_batch[i] + 2, vtmp5_batch[i] + 2, vtmp1_batch[i] + 2),
                ('^', vtmp1_batch[i] + 3, vtmp5_batch[i] + 3, vtmp1_batch[i] + 3),
                ('^', vtmp1_batch[i] + 4, vtmp5_batch[i] + 4, vtmp1_batch[i] + 4),
                ('^', vtmp1_batch[i] + 5, vtmp5_batch[i] + 5, vtmp1_batch[i] + 5),
                ('^', vtmp1_batch[i] + 6, vtmp5_batch[i] + 6, vtmp1_batch[i] + 6),
                ('^', vtmp1_batch[i] + 7, vtmp5_batch[i] + 7, vtmp1_batch[i] + 7),
            ]},
                {"valu": [('multiply_add', vtmp1_batch[i], vtmp1_batch[i], V_4097, V_7ED55D16)]},
                {"valu": [('^',  vtmp4_batch[i], vtmp1_batch[i], V_C761C23C),  ('>>', vtmp5_batch[i], vtmp1_batch[i], V_19)]},
                {"alu": [
                ('^', vtmp1_batch[i],     vtmp4_batch[i],     vtmp5_batch[i]),
                ('^', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
                ('^', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2),
                ('^', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
                ('^', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4),
                ('^', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
                ('^', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6),
                ('^', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7),
            ]},
                {"valu": [('multiply_add', vtmp1_batch[i], vtmp1_batch[i], V_33, V_165667B1)]},
                {"valu": [('+',  vtmp4_batch[i], vtmp1_batch[i], V_D3A2646C), ('<<', vtmp5_batch[i], vtmp1_batch[i], V_9)]},
                {"valu": [('^',  vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]},
                {"valu": [('multiply_add', vtmp1_batch[i], vtmp1_batch[i], V_9, V_FD7046C5)]},
                {"valu": [('^',  vtmp4_batch[i], vtmp1_batch[i], V_B55A4F09),  ('>>', vtmp5_batch[i], vtmp1_batch[i], V_16)]},
                {"valu": [('^',  vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]}
                ])"""
    #perm = (1, 0, 0, 1, 0, 0, 0, 0, 0, 0)
    #perm = list(perm)
    for idx in range(9):
        instruction_stream.extend(valu_alu_select(batch, idx, perm))

def get_block_range(block_idx, total=2**19, num_blocks=24):
    block_size = total // num_blocks
    start = block_idx * block_size
    # last block picks up the remainder
    #print(start)
    end = total if block_idx == num_blocks - 1 else start + block_size
    #print(f"{start}====={end}")
    return start, end

def process_block(args):
    block_idx, a = args
    start, end = get_block_range(block_idx)
    gen = product([0, 1], repeat=19)
    min = 1500
    log_file = open(f"output_19_permute_{block_idx}.txt", "w")

    def log(msg):
        print(msg, file=log_file, flush=True)
    
    for idx, perm in enumerate(islice(gen, start, end)):
        global_idx = start + idx
        # do your work here

        batch_idx = 0
        #perm = (0, 0, 1, 0, 0, 1, 0, 0, 0)
        #perm = (0, 0, 1, 0, 0, 1, 0, 0, 0)
        #perm_hash_instrs = (0, 0, 1, 0, 0, 1, 0, 0, 0)
        #perm = (1, 1, 0, 1)
        perm_hash_instrs, round2_perm, round3_perm = perm[:9], perm[9:13], perm[13:] 
        InstructionStreams = []
        for i in range(0, batch_size//8, 1):
            instruction_stream = []
            instruction_stream.extend([{"alu":[('+', tmp4_batch[i], tmp1, CONST[i]), ('+', tmp5_batch[i], tmp2, CONST[i])]},
                                {"load":[('vload', vtmp1_batch[i], tmp4_batch[i])]}])
            for round in range(rounds):
                if round == 0:
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], V_FOREST_VAL_0, vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)
                    
                    instruction_stream.extend([
                        {"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect', vtmp2_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                    ])

                elif round == 1:
                    instruction_stream.extend([
                        
                        {"flow": [('vselect', vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_2, V_FOREST_VAL_1)]}])
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)
                    
                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]}])
                    
                elif round == 2:
                    
                    """instruction_stream.extend([
                        {"store":[('vstore', tmp5_batch[i], vtmp2_batch[i])]},
                        {"valu": [("-", vtmp2_batch[i], vtmp2_batch[i], V_CONST_3)]},
                        {"valu": [("&", vtmp5_batch[i], vtmp2_batch[i], V_CONST_1)]},
                        {"flow": [("vselect", vtmp4_batch[i], vtmp5_batch[i], V_FOREST_VAL_4, V_FOREST_VAL_3)]},
                        {"flow": [("vselect", vtmp5_batch[i], vtmp5_batch[i], V_FOREST_VAL_6, V_FOREST_VAL_5)]},
                        {"valu": [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_1)]},
                        {"valu": [("&", vtmp2_batch[i], vtmp2_batch[i], V_CONST_1)]},
                        {"flow": [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp4_batch[i])]}
                    ])"""

                    round_2_alu_valu_select(instruction_stream, i, round2_perm)
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)

                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',  vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"load": [('vload', vtmp2_batch[i], tmp5_batch[i])]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])
                
                elif round == 3:
                    if i in {1, 3, 5, 7, 9, 11, 13}:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    elif i == 15:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    elif i == 17:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    elif i == 19:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    elif i == 21:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    elif i == 23:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    else:
                        instruction_stream.extend([
                        {"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]},
                        {"load": [('load', vtmp5_batch[i],     vtmp4_batch[i]),     ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                        {"load": [('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                        {"load": [('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                        {"load": [('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]}])
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)

                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])
                
                elif 4 <= round <= 9:
                    instruction_stream.extend([
                        {"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]},
                        {"load": [('load', vtmp5_batch[i],     vtmp4_batch[i]),     ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                        {"load": [('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                        {"load": [('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                        {"load": [('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]}])
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)

                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])

                elif round == 10:
                    instruction_stream.extend([
                        {"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]},
                        {"load": [('load', vtmp5_batch[i],     vtmp4_batch[i]),     ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                        {"load": [('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                        {"load": [('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                        {"load": [('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]}])
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)

                elif round == 11:
                    
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], V_FOREST_VAL_0, vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)
                    
                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect', vtmp2_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                    ])

                elif round == 12:
                    instruction_stream.extend([
                        
                        {"flow": [('vselect', vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_2, V_FOREST_VAL_1)]}])
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)
                    
                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]}])
                
                elif round == 13:
                    
                    """instruction_stream.extend([
                        {"store":[('vstore', tmp5_batch[i], vtmp2_batch[i])]},
                        {"valu": [("-", vtmp2_batch[i], vtmp2_batch[i], V_CONST_3)]},
                        {"valu": [("&", vtmp5_batch[i], vtmp2_batch[i], V_CONST_1)]},
                        {"flow": [("vselect", vtmp4_batch[i], vtmp5_batch[i], V_FOREST_VAL_4, V_FOREST_VAL_3)]},
                        {"flow": [("vselect", vtmp5_batch[i], vtmp5_batch[i], V_FOREST_VAL_6, V_FOREST_VAL_5)]},
                        {"valu": [(">>", vtmp2_batch[i], vtmp2_batch[i], V_CONST_1)]},
                        {"valu": [("&", vtmp2_batch[i], vtmp2_batch[i], V_CONST_1)]},
                        {"flow": [("vselect", vtmp5_batch[i], vtmp2_batch[i], vtmp5_batch[i], vtmp4_batch[i])]}
                    ])"""

                    round_2_alu_valu_select(instruction_stream, i, round2_perm)
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)
                    
                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"load": [('vload', vtmp2_batch[i], tmp5_batch[i])]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])

                elif round == 14:
                    if i in {1, 3, 5, 7, 9, 11, 13}:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                        batch_idx += 1
                    elif i == 15:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    elif i == 17:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    elif i == 19:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    elif i == 21:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    elif i == 23:
                        round_3_alu_valu_select(instruction_stream, i, round3_perm)
                    else:
                        instruction_stream.extend([
                        {"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]},
                        {"load": [('load', vtmp5_batch[i],     vtmp4_batch[i]),     ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                        {"load": [('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                        {"load": [('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                        {"load": [('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]}])
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)
                    
                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                    ])

                else:  # round >= 15
                    instruction_stream.extend([
                        {"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]},
                        {"load": [('load', vtmp5_batch[i],     vtmp4_batch[i]),     ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                        {"load": [('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                        {"load": [('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                        {"load": [('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]}])
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instrs)

            instruction_stream.extend([{"store": [('vstore', tmp4_batch[i], vtmp1_batch[i])]}])
            InstructionStreams.append(InstructionStream(instruction_stream))
        res = schedule_instructions(InstructionStreams)
        instr_len = len(res) + len(a)
        log(global_idx)

        if(instr_len < min):
            #print("minimum_value so far")
            min = instr_len
            log(perm_hash_instrs)
            log(round2_perm)
            log(round3_perm)
            log(min)


if __name__ == "__main__":
    setup_data = initial_setup()
    with Pool(24) as p:
        p.map(process_block, [(i, setup_data) for i in range(24)])

