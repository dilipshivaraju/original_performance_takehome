from typing import Any, Literal
from copy import deepcopy, copy
from itertools import product

Engine = Literal["alu", "load", "store", "flow"]
Instruction = dict[Engine, list[tuple]]


class InstructionStream:
    def __init__(self, instructions: list[Instruction]) -> None:
        self.instructions: list[Instruction] = instructions
        self.length: int = len(instructions)
        self.cur_pointer: int = 0

def generate_instructions(InstructionStreams):
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

tmp4_batch = [i for i in range(32)]
tmp5_batch = [i for i in range(32, 64, 1)]
vtmp1_batch = [i for i in range(64, 320, 8)]
vtmp2_batch = [i for i in range(320, 576, 8)]
vtmp4_batch = [i for i in range(320, 576, 8)]
vtmp5_batch = [i for i in range(832, 1088, 8)]
CONST = [i for i in range(1088,1120,1)]
tmp1 = 1120
tmp2 = 1121
V_FOREST_VALUE_P = 1122
V_7ED55D16 = 1130
V_12 = 1138
V_C761C23C = 1146
V_19 = 1154
V_165667B1 = 1162
V_5 = 1170
V_D3A2646C = 1178
V_9 = 1186
V_FD7046C5 = 1194
V_3 = 1202
V_B55A4F09 = 1210
V_16 = 1218
V_CONST_2 = 1226
V_CONST_0 = 1234
V_CONST_1 = 1242
V_NUM_NODES = 1250
batch_size = 256
rounds = 16

"""print(tmp4_batch)
print(tmp5_batch)
print(vtmp1_batch)
print(vtmp2_batch)
print(vtmp4_batch)
print(vtmp5_batch)
print(CONST)"""

def valu_alu_select(i, index, perm):
    valu_alu_select_array = [
        [
            [{"valu": [('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]}],
            [{"alu": [
                ('+', vtmp4_batch[i],     vtmp2_batch[i],     V_FOREST_VALUE_P),
                ('+', vtmp4_batch[i] + 1, vtmp2_batch[i] + 1, V_FOREST_VALUE_P),
                ('+', vtmp4_batch[i] + 2, vtmp2_batch[i] + 2, V_FOREST_VALUE_P),
                ('+', vtmp4_batch[i] + 3, vtmp2_batch[i] + 3, V_FOREST_VALUE_P),
                ('+', vtmp4_batch[i] + 4, vtmp2_batch[i] + 4, V_FOREST_VALUE_P),
                ('+', vtmp4_batch[i] + 5, vtmp2_batch[i] + 5, V_FOREST_VALUE_P),
                ('+', vtmp4_batch[i] + 6, vtmp2_batch[i] + 6, V_FOREST_VALUE_P),
                ('+', vtmp4_batch[i] + 7, vtmp2_batch[i] + 7, V_FOREST_VALUE_P),
            ]}],
        ],
        [
            [{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}],
            [{"alu": [
                ('^', vtmp1_batch[i],     vtmp5_batch[i],     vtmp1_batch[i]),
                ('^', vtmp1_batch[i] + 1, vtmp5_batch[i] + 1, vtmp1_batch[i] + 1),
                ('^', vtmp1_batch[i] + 2, vtmp5_batch[i] + 2, vtmp1_batch[i] + 2),
                ('^', vtmp1_batch[i] + 3, vtmp5_batch[i] + 3, vtmp1_batch[i] + 3),
                ('^', vtmp1_batch[i] + 4, vtmp5_batch[i] + 4, vtmp1_batch[i] + 4),
                ('^', vtmp1_batch[i] + 5, vtmp5_batch[i] + 5, vtmp1_batch[i] + 5),
                ('^', vtmp1_batch[i] + 6, vtmp5_batch[i] + 6, vtmp1_batch[i] + 6),
                ('^', vtmp1_batch[i] + 7, vtmp5_batch[i] + 7, vtmp1_batch[i] + 7),
            ]}],
        ],
        [
            [{"valu": [
                ('+',  vtmp4_batch[i], vtmp1_batch[i], V_7ED55D16),
                ('<<', vtmp5_batch[i], vtmp1_batch[i], V_12),
            ]}],
            [
                {"alu": [
                    ('+',  vtmp4_batch[i],     vtmp1_batch[i],     V_7ED55D16),
                    ('+',  vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_7ED55D16),
                    ('+',  vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_7ED55D16),
                    ('+',  vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_7ED55D16),
                    ('+',  vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_7ED55D16),
                    ('+',  vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_7ED55D16),
                    ('+',  vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_7ED55D16),
                    ('+',  vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_7ED55D16),
                    ('<<', vtmp5_batch[i],     vtmp1_batch[i],     V_12),
                    ('<<', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_12),
                    ('<<', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_12),
                    ('<<', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_12),
                ]},
                {"alu": [
                    ('<<', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_12),
                    ('<<', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_12),
                    ('<<', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_12),
                    ('<<', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_12),
                ]},
            ],
        ],
        [
            [{"valu": [('+', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]}],
            [{"alu": [
                ('+', vtmp1_batch[i],     vtmp4_batch[i],     vtmp5_batch[i]),
                ('+', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
                ('+', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2),
                ('+', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
                ('+', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4),
                ('+', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
                ('+', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6),
                ('+', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7),
            ]}],
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
            [{"valu": [
                ('+',  vtmp4_batch[i], vtmp1_batch[i], V_165667B1),
                ('<<', vtmp5_batch[i], vtmp1_batch[i], V_5),
            ]}],
            [
                {"alu": [
                    ('+',  vtmp4_batch[i],     vtmp1_batch[i],     V_165667B1),
                    ('+',  vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_165667B1),
                    ('+',  vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_165667B1),
                    ('+',  vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_165667B1),
                    ('+',  vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_165667B1),
                    ('+',  vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_165667B1),
                    ('+',  vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_165667B1),
                    ('+',  vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_165667B1),
                    ('<<', vtmp5_batch[i],     vtmp1_batch[i],     V_5),
                    ('<<', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_5),
                    ('<<', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_5),
                    ('<<', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_5),
                ]},
                {"alu": [
                    ('<<', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_5),
                    ('<<', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_5),
                    ('<<', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_5),
                    ('<<', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_5),
                ]},
            ],
        ],
        [
            [{"valu": [('+', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]}],
            [{"alu": [
                ('+', vtmp1_batch[i],     vtmp4_batch[i],     vtmp5_batch[i]),
                ('+', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
                ('+', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2),
                ('+', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
                ('+', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4),
                ('+', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
                ('+', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6),
                ('+', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7),
            ]}],
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
            [{"valu": [
                ('+',  vtmp4_batch[i], vtmp1_batch[i], V_FD7046C5),
                ('<<', vtmp5_batch[i], vtmp1_batch[i], V_3),
            ]}],
            [
                {"alu": [
                    ('+',  vtmp4_batch[i],     vtmp1_batch[i],     V_FD7046C5),
                    ('+',  vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_FD7046C5),
                    ('+',  vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_FD7046C5),
                    ('+',  vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_FD7046C5),
                    ('+',  vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_FD7046C5),
                    ('+',  vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_FD7046C5),
                    ('+',  vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_FD7046C5),
                    ('+',  vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_FD7046C5),
                    ('<<', vtmp5_batch[i],     vtmp1_batch[i],     V_3),
                    ('<<', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_3),
                    ('<<', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_3),
                    ('<<', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_3),
                ]},
                {"alu": [
                    ('<<', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_3),
                    ('<<', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_3),
                    ('<<', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_3),
                    ('<<', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_3),
                ]},
            ],
        ],
        [
            [{"valu": [('+', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]}],
            [{"alu": [
                ('+', vtmp1_batch[i],     vtmp4_batch[i],     vtmp5_batch[i]),
                ('+', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
                ('+', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2),
                ('+', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
                ('+', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4),
                ('+', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
                ('+', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6),
                ('+', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7),
            ]}],
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
        ],
        [
            [{"valu": [('%', vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]}],
            [{"alu": [
                ('%', vtmp4_batch[i],     vtmp1_batch[i],     V_CONST_2),
                ('%', vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_CONST_2),
                ('%', vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_CONST_2),
                ('%', vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_CONST_2),
                ('%', vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_CONST_2),
                ('%', vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_CONST_2),
                ('%', vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_CONST_2),
                ('%', vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_CONST_2),
            ]}],
        ],
        [
            [{"valu": [('==', vtmp4_batch[i], vtmp4_batch[i], V_CONST_0)]}],
            [{"alu": [
                ('==', vtmp4_batch[i],     vtmp4_batch[i],     V_CONST_0),
                ('==', vtmp4_batch[i] + 1, vtmp4_batch[i] + 1, V_CONST_0),
                ('==', vtmp4_batch[i] + 2, vtmp4_batch[i] + 2, V_CONST_0),
                ('==', vtmp4_batch[i] + 3, vtmp4_batch[i] + 3, V_CONST_0),
                ('==', vtmp4_batch[i] + 4, vtmp4_batch[i] + 4, V_CONST_0),
                ('==', vtmp4_batch[i] + 5, vtmp4_batch[i] + 5, V_CONST_0),
                ('==', vtmp4_batch[i] + 6, vtmp4_batch[i] + 6, V_CONST_0),
                ('==', vtmp4_batch[i] + 7, vtmp4_batch[i] + 7, V_CONST_0),
            ]}],
        ],
        [
            [{"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]}],
            [
                {"alu": [
                    ('*', vtmp2_batch[i],     vtmp2_batch[i],     V_CONST_2),
                    ('*', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, V_CONST_2),
                    ('*', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, V_CONST_2),
                    ('*', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, V_CONST_2),
                    ('*', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, V_CONST_2),
                    ('*', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, V_CONST_2),
                    ('*', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, V_CONST_2),
                    ('*', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, V_CONST_2),
                ]},
                {"alu": [
                    ('+', vtmp2_batch[i],     vtmp2_batch[i],     vtmp4_batch[i]),
                    ('+', vtmp2_batch[i] + 1, vtmp2_batch[i] + 1, vtmp4_batch[i] + 1),
                    ('+', vtmp2_batch[i] + 2, vtmp2_batch[i] + 2, vtmp4_batch[i] + 2),
                    ('+', vtmp2_batch[i] + 3, vtmp2_batch[i] + 3, vtmp4_batch[i] + 3),
                    ('+', vtmp2_batch[i] + 4, vtmp2_batch[i] + 4, vtmp4_batch[i] + 4),
                    ('+', vtmp2_batch[i] + 5, vtmp2_batch[i] + 5, vtmp4_batch[i] + 5),
                    ('+', vtmp2_batch[i] + 6, vtmp2_batch[i] + 6, vtmp4_batch[i] + 6),
                    ('+', vtmp2_batch[i] + 7, vtmp2_batch[i] + 7, vtmp4_batch[i] + 7),
                ]},
            ],
        ],
        [
            [{"valu": [('<', vtmp4_batch[i], vtmp2_batch[i], V_NUM_NODES)]}],
            [{"alu": [
                ('<', vtmp4_batch[i],     vtmp2_batch[i],     V_NUM_NODES),
                ('<', vtmp4_batch[i] + 1, vtmp2_batch[i] + 1, V_NUM_NODES),
                ('<', vtmp4_batch[i] + 2, vtmp2_batch[i] + 2, V_NUM_NODES),
                ('<', vtmp4_batch[i] + 3, vtmp2_batch[i] + 3, V_NUM_NODES),
                ('<', vtmp4_batch[i] + 4, vtmp2_batch[i] + 4, V_NUM_NODES),
                ('<', vtmp4_batch[i] + 5, vtmp2_batch[i] + 5, V_NUM_NODES),
                ('<', vtmp4_batch[i] + 6, vtmp2_batch[i] + 6, V_NUM_NODES),
                ('<', vtmp4_batch[i] + 7, vtmp2_batch[i] + 7, V_NUM_NODES),
            ]}],
        ],
    ]

    #print(len(valu_alu_select_array))
    return valu_alu_select_array[index][perm[index]]

log_file = open("output.txt", "w")

def log(msg):
    print(msg, file=log_file, flush=True)

min = 150000
perm_idx = 0
for idx, perm in enumerate(product([0, 1], repeat=18)):
    #valu_alu_select(0, 1, perm)
    #print(perm[0])
    InstructionStreams = []
    for i in range(0, batch_size//8, 1):
        instruction_stream = []
        instruction_stream.extend([
                {
                    "alu": [
                        ('+', tmp4_batch[i], tmp1, CONST[i]), 
                        ('+', tmp5_batch[i], tmp2, CONST[i])
                    ]
                },
                {
                    "load": [
                        ('vload', vtmp1_batch[i], tmp4_batch[i]), 
                        ('vload', vtmp2_batch[i], tmp5_batch[i])
                    ]
                }
            ])
        for round in range(rounds):
            valu_index = 0
            

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1
            #print(instruction_stream)

            instruction_stream.extend([
                                {"load":[('load', vtmp5_batch[i], vtmp4_batch[i]), ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                                {"load":[('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                                {"load":[('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                                {"load":[('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]}])
            
            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            #hash
            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1
            #end hash

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend([{"flow":[('vselect', vtmp4_batch[i], vtmp4_batch[i], V_CONST_1, V_CONST_2)]}])

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend(valu_alu_select(i, valu_index, perm))
            valu_index += 1

            instruction_stream.extend([{"flow":[('vselect', vtmp2_batch[i], vtmp4_batch[i], vtmp2_batch[i], V_CONST_0)]}])

        instruction_stream.extend([{"store":[('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]}])
        InstructionStreams.append(InstructionStream(instruction_stream))
    instrs = generate_instructions(InstructionStreams)
    #print(perm)
    instr_len = len(instrs)
    log(idx)

    if(instr_len < min):
        #print("minimum_value so far")
        min = instr_len
        print(perm)
        print(min)



"""for i in range(0, batch_size//8, 1):
    instruction_stream = []
    instruction_stream.extend([{"alu":[('+', tmp4_batch[i], tmp1, CONST[i]), ('+', tmp5_batch[i], tmp2, CONST[i])]},
                        {"load":[('vload', vtmp1_batch[i], tmp4_batch[i]), ('vload', vtmp2_batch[i], tmp5_batch[i])]}])
    for round in range(rounds):
        if i >= 16 and round < 8:
            instruction_stream.extend([{"valu":[('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P)]}
                                    ])
        else:
            instruction_stream.extend([{"alu":[('+', vtmp4_batch[i], vtmp2_batch[i], V_FOREST_VALUE_P), ('+', vtmp4_batch[i] + 1, vtmp2_batch[i] + 1, V_FOREST_VALUE_P + 1),
                                            ('+', vtmp4_batch[i] + 2, vtmp2_batch[i] + 2, V_FOREST_VALUE_P + 2), ('+', vtmp4_batch[i] + 3, vtmp2_batch[i] + 3, V_FOREST_VALUE_P + 3),
                                            ('+', vtmp4_batch[i] + 4, vtmp2_batch[i] + 4, V_FOREST_VALUE_P + 4), ('+', vtmp4_batch[i] + 5, vtmp2_batch[i] + 5, V_FOREST_VALUE_P + 5),
                                            ('+', vtmp4_batch[i] + 6, vtmp2_batch[i] + 6, V_FOREST_VALUE_P + 6), ('+', vtmp4_batch[i] + 7, vtmp2_batch[i] + 7, V_FOREST_VALUE_P + 7)]}]
                                )
        instruction_stream.extend([
                                {"load":[('load', vtmp5_batch[i], vtmp4_batch[i]), ('load', vtmp5_batch[i] + 1, vtmp4_batch[i] + 1)]},
                                {"load":[('load', vtmp5_batch[i] + 2, vtmp4_batch[i] + 2), ('load', vtmp5_batch[i] + 3, vtmp4_batch[i] + 3)]},
                                {"load":[('load', vtmp5_batch[i] + 4, vtmp4_batch[i] + 4), ('load', vtmp5_batch[i] + 5, vtmp4_batch[i] + 5)]},
                                {"load":[('load', vtmp5_batch[i] + 6, vtmp4_batch[i] + 6), ('load', vtmp5_batch[i] + 7, vtmp4_batch[i] + 7)]},
                                {"valu":[('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
        
        
                                
        
        instruction_stream.extend([{"valu":[('+', vtmp4_batch[i], vtmp1_batch[i], V_7ED55D16),('<<', vtmp5_batch[i], vtmp1_batch[i], V_12)]},
                                    {"valu":[('+', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]},
                                    {"valu":[('^', vtmp4_batch[i], vtmp1_batch[i], V_C761C23C),('>>', vtmp5_batch[i], vtmp1_batch[i], V_19)]},
                                    {"valu":[('^', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]},
                                    {"valu":[('+', vtmp4_batch[i], vtmp1_batch[i], V_165667B1),('<<', vtmp5_batch[i], vtmp1_batch[i], V_5)]},
                                    {"valu":[('+', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]},
                                    {"valu":[('+', vtmp4_batch[i], vtmp1_batch[i], V_D3A2646C),('<<', vtmp5_batch[i], vtmp1_batch[i], V_9)]},
                                    {"valu":[('^', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]},
                                    {"valu":[('+', vtmp4_batch[i], vtmp1_batch[i], V_FD7046C5),('<<', vtmp5_batch[i], vtmp1_batch[i], V_3)]},
                                    {"valu":[('+', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]},
                                    {"valu":[('^', vtmp4_batch[i], vtmp1_batch[i], V_B55A4F09),('>>', vtmp5_batch[i], vtmp1_batch[i], V_16)]},
                                    {"valu":[('^', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]},
                                    {"valu":[('%', vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                                {"valu":[('==', vtmp4_batch[i], vtmp4_batch[i], V_CONST_0)]},
                                {"flow":[('vselect', vtmp4_batch[i], vtmp4_batch[i], V_CONST_1, V_CONST_2)]},
                                {"valu":[('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]},
                                {"valu":[('<', vtmp4_batch[i], vtmp2_batch[i], V_NUM_NODES)]},
                                {"flow":[('vselect', vtmp2_batch[i], vtmp4_batch[i], vtmp2_batch[i], V_CONST_0)]}])
    
    instruction_stream.extend([{"store":[('vstore', tmp5_batch[i], vtmp2_batch[i]), ('vstore', tmp4_batch[i], vtmp1_batch[i])]}])
    #print(instruction_stream)
    InstructionStreams.append(InstructionStream(instruction_stream))

for stream in InstructionStreams:
    for instr in stream.instructions:
        print(instr)
    #print(stream.instructions)
    print("\n\n")"""

#instrs = generate_instructions(InstructionStreams)
#print(len(instrs))

#for instr in instrs:
    #print(instr)



"""
{"valu":[('+', vtmp4_batch[i], vtmp1_batch[i], V_7ED55D16),('<<', vtmp5_batch[i], vtmp1_batch[i], V_12)]}

{"alu":[('+', vtmp4_batch[i], vtmp1_batch[i], V_7ED55D16), ('+', vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_7ED55D16), 
        ('+', vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_7ED55D16), ('+', vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_7ED55D16), 
        ('+', vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_7ED55D16), ('+', vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_7ED55D16)
        ('+', vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_7ED55D16), ('+', vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_7ED55D16), 
        ('<<', vtmp5_batch[i], vtmp1_batch[i], V_12), ('<<', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_12),
        ('<<', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_12), ('<<', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_12)]},
{"alu":[('<<', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_12), ('<<', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_12),
        ('<<', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_12), ('<<', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_12)]},

{"valu":[('+', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i])]}

{"alu":[('+', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i]), ('+', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
        ('+', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2), ('+', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
        ('+', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4), ('+', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
        ('+', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6), ('+', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7)]},

{"valu":[('+', vtmp4_batch[i], vtmp1_batch[i], V_165667B1),('<<', vtmp5_batch[i], vtmp1_batch[i], V_5)]}

{"alu":[('^', vtmp4_batch[i], vtmp1_batch[i], V_C761C23C), ('^', vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_C761C23C), 
        ('^', vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_C761C23C), ('^', vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_C761C23C), 
        ('^', vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_C761C23C), ('^', vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_C761C23C)
        ('^', vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_C761C23C), ('^', vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_C761C23C), 
        ('>>', vtmp5_batch[i], vtmp1_batch[i], V_19), ('>>', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_19),
        ('>>', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_19), ('>>', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_19)]},
{"alu":[('>>', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_19), ('>>', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_19),
        ('>>', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_19), ('>>', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_19)]},

{"alu":[('^', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i]), ('^', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
        ('^', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2), ('^', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
        ('^', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4), ('^', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
        ('^', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6), ('^', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7)]},


{"alu":[('+', vtmp4_batch[i], vtmp1_batch[i], V_165667B1), ('+', vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_165667B1), 
        ('+', vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_165667B1), ('+', vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_165667B1), 
        ('+', vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_165667B1), ('+', vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_165667B1)
        ('+', vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_165667B1), ('+', vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_165667B1), 
        ('<<', vtmp5_batch[i], vtmp1_batch[i], V_5), ('<<', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_5),
        ('<<', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_5), ('<<', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_5)]},
{"alu":[('<<', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_5), ('<<', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_5),
        ('<<', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_5), ('<<', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_5)]},

{"alu":[('+', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i]), ('+', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
        ('+', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2), ('+', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
        ('+', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4), ('+', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
        ('+', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6), ('+', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7)]},

{"alu":[('+', vtmp4_batch[i], vtmp1_batch[i], V_D3A2646C), ('+', vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_D3A2646C), 
        ('+', vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_D3A2646C), ('+', vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_D3A2646C), 
        ('+', vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_D3A2646C), ('+', vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_D3A2646C)
        ('+', vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_D3A2646C), ('+', vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_D3A2646C), 
        ('<<', vtmp5_batch[i], vtmp1_batch[i], V_9), ('<<', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_9),
        ('<<', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_9), ('<<', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_9)]},
{"alu":[('<<', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_9), ('<<', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_9),
        ('<<', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_9), ('<<', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_9)]},

{"alu":[('^', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i]), ('^', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
        ('^', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2), ('^', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
        ('^', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4), ('^', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
        ('^', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6), ('^', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7)]},

{"alu":[('+', vtmp4_batch[i], vtmp1_batch[i], V_FD7046C5), ('+', vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_FD7046C5), 
        ('+', vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_FD7046C5), ('+', vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_FD7046C5), 
        ('+', vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_FD7046C5), ('+', vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_FD7046C5)
        ('+', vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_FD7046C5), ('+', vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_FD7046C5), 
        ('<<', vtmp5_batch[i], vtmp1_batch[i], V_3), ('<<', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_3),
        ('<<', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_3), ('<<', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_3)]},
{"alu":[('<<', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_3), ('<<', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_3),
        ('<<', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_3), ('<<', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_3)]},

{"alu":[('+', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i]), ('+', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
        ('+', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2), ('+', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
        ('+', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4), ('+', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
        ('+', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6), ('+', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7)]},

{"alu":[('^', vtmp4_batch[i], vtmp1_batch[i], V_B55A4F09), ('^', vtmp4_batch[i] + 1, vtmp1_batch[i] + 1, V_B55A4F09), 
        ('^', vtmp4_batch[i] + 2, vtmp1_batch[i] + 2, V_B55A4F09), ('^', vtmp4_batch[i] + 3, vtmp1_batch[i] + 3, V_B55A4F09), 
        ('^', vtmp4_batch[i] + 4, vtmp1_batch[i] + 4, V_B55A4F09), ('^', vtmp4_batch[i] + 5, vtmp1_batch[i] + 5, V_B55A4F09)
        ('^', vtmp4_batch[i] + 6, vtmp1_batch[i] + 6, V_B55A4F09), ('^', vtmp4_batch[i] + 7, vtmp1_batch[i] + 7, V_B55A4F09), 
        ('>>', vtmp5_batch[i], vtmp1_batch[i], V_16), ('>>', vtmp5_batch[i] + 1, vtmp1_batch[i] + 1, V_16),
        ('>>', vtmp5_batch[i] + 2, vtmp1_batch[i] + 2, V_16), ('>>', vtmp5_batch[i] + 3, vtmp1_batch[i] + 3, V_16)]},

{"alu":[('>>', vtmp5_batch[i] + 4, vtmp1_batch[i] + 4, V_16), ('>>', vtmp5_batch[i] + 5, vtmp1_batch[i] + 5, V_16),
        ('>>', vtmp5_batch[i] + 6, vtmp1_batch[i] + 6, V_16), ('>>', vtmp5_batch[i] + 7, vtmp1_batch[i] + 7, V_16)]},

{"alu":[('^', vtmp1_batch[i], vtmp4_batch[i], vtmp5_batch[i]), ('^', vtmp1_batch[i] + 1, vtmp4_batch[i] + 1, vtmp5_batch[i] + 1),
        ('^', vtmp1_batch[i] + 2, vtmp4_batch[i] + 2, vtmp5_batch[i] + 2), ('^', vtmp1_batch[i] + 3, vtmp4_batch[i] + 3, vtmp5_batch[i] + 3),
        ('^', vtmp1_batch[i] + 4, vtmp4_batch[i] + 4, vtmp5_batch[i] + 4), ('^', vtmp1_batch[i] + 5, vtmp4_batch[i] + 5, vtmp5_batch[i] + 5),
        ('^', vtmp1_batch[i] + 6, vtmp4_batch[i] + 6, vtmp5_batch[i] + 6), ('^', vtmp1_batch[i] + 7, vtmp4_batch[i] + 7, vtmp5_batch[i] + 7)]}"""