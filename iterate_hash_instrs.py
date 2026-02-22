from typing import Any, Literal
from itertools import product, islice
from multiprocessing import Pool
from copy import deepcopy
from test_python import schedule_instructions, initial_setup, hash_instrs, Engine, Instruction, InstructionStream, round_2_alu_valu_select, round_3_alu_valu_select

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


#round2_perm = (0, 0, 0, 0)
round3_perm = (0, 0, 0, 0, 0, 1)

perm_hash_instructions = [[(0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0)] * 16 for _ in range(32)]

def construct_31_IS(batch):
    batch_idx = 0
    InstructionStreams = []
    for i in range(0, batch_size//8, 1):
        if i != batch:
            instruction_stream = []
            instruction_stream.extend([{"alu":[('+', tmp4_batch[i], tmp1, CONST[i]), ('+', tmp5_batch[i], tmp2, CONST[i])]},
                                {"load":[('vload', vtmp1_batch[i], tmp4_batch[i])]}])
            for round in range(rounds):
                if round == 0:
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], V_FOREST_VAL_0, vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    
                    instruction_stream.extend([
                        {"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect', vtmp2_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                    ])

                elif round == 1:
                    instruction_stream.extend([
                        
                        {"flow": [('vselect', vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_2, V_FOREST_VAL_1)]}])
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    
                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]}])
                    
                elif round == 2:
                    round_2_alu_valu_select(instruction_stream, i, perm_hash_instructions[i][round][9:])
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

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
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

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
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

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
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

                elif round == 11:
                    
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], V_FOREST_VAL_0, vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    
                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect', vtmp2_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                    ])

                elif round == 12:
                    instruction_stream.extend([
                        
                        {"flow": [('vselect', vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_2, V_FOREST_VAL_1)]}])
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    
                    instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                        {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                        {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]}])
                
                elif round == 13:

                    round_2_alu_valu_select(instruction_stream, i, perm_hash_instructions[i][round][9:])
                    
                    instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    
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
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                    
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
                    hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

            instruction_stream.extend([{"store": [('vstore', tmp4_batch[i], vtmp1_batch[i])]}])
            InstructionStreams.append(InstructionStream(instruction_stream))
    return InstructionStreams

def construct_15_rounds(i, r):
    final_instruction_stream = []
    final_instruction_stream.append([{"alu":[('+', tmp4_batch[i], tmp1, CONST[i]), ('+', tmp5_batch[i], tmp2, CONST[i])]},
                                {"load":[('vload', vtmp1_batch[i], tmp4_batch[i])]}])
    batch_idx = 0
    for round in range(rounds):
        if round != r:
            instruction_stream = []
            if round == 0:
                instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], V_FOREST_VAL_0, vtmp1_batch[i])]}])
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                
                instruction_stream.extend([
                    {"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                    {"flow": [('vselect', vtmp2_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                ])

            elif round == 1:
                instruction_stream.extend([
                    
                    {"flow": [('vselect', vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_2, V_FOREST_VAL_1)]}])
                
                instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                
                instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                    {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                    {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]}])
                
            elif round == 2:

                round_2_alu_valu_select(instruction_stream, i, perm_hash_instructions[i][round][9:])
                
                instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

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
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

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
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

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
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])

            elif round == 11:
                
                
                instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], V_FOREST_VAL_0, vtmp1_batch[i])]}])
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                
                instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                    {"flow": [('vselect', vtmp2_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                ])

            elif round == 12:
                instruction_stream.extend([
                    
                    {"flow": [('vselect', vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_2, V_FOREST_VAL_1)]}])
                
                instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                
                instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
                    {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
                    {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]}])
            
            elif round == 13:

                round_2_alu_valu_select(instruction_stream, i, perm_hash_instructions[i][round][9:])
                
                instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                
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
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
                
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
                hash_instrs(instruction_stream, i, perm_hash_instructions[i][round])
            final_instruction_stream.append(instruction_stream)

    final_instruction_stream.append([{"store": [('vstore', tmp4_batch[i], vtmp1_batch[i])]}])
    return final_instruction_stream

def cur_round(i, round, perm):
    final_instruction_stream = []
    instruction_stream = []
    batch_idx = 0
    if round == 0:
        instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], V_FOREST_VAL_0, vtmp1_batch[i])]}])
        hash_instrs(instruction_stream, i, perm)
        
        instruction_stream.extend([
            {"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
            {"flow": [('vselect', vtmp2_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
        ])

    elif round == 1:
        instruction_stream.extend([
            
            {"flow": [('vselect', vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_2, V_FOREST_VAL_1)]}])
        
        instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
        hash_instrs(instruction_stream, i, perm)
        
        instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
            {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
            {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]}])
        
    elif round == 2:

        round_2_alu_valu_select(instruction_stream, i, perm_hash_instructions[i][round][9:])
        
        instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
        hash_instrs(instruction_stream, i, perm)

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
        hash_instrs(instruction_stream, i, perm)

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
        hash_instrs(instruction_stream, i, perm)

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
        hash_instrs(instruction_stream, i, perm)

    elif round == 11:
        
        
        instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], V_FOREST_VAL_0, vtmp1_batch[i])]}])
        hash_instrs(instruction_stream, i, perm)
        
        instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
            {"flow": [('vselect', vtmp2_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
        ])

    elif round == 12:
        instruction_stream.extend([
            
            {"flow": [('vselect', vtmp5_batch[i], vtmp4_batch[i], V_FOREST_VAL_2, V_FOREST_VAL_1)]}])
        
        instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
        hash_instrs(instruction_stream, i, perm)
        
        instruction_stream.extend([{"valu": [('%',  vtmp4_batch[i], vtmp1_batch[i], V_CONST_2)]},
            {"flow": [('vselect',      vtmp4_batch[i], vtmp4_batch[i], V_CONST_2, V_CONST_1)]},
            {"valu": [('multiply_add', vtmp2_batch[i], vtmp2_batch[i], V_CONST_2, vtmp4_batch[i])]}])
    
    elif round == 13:

        round_2_alu_valu_select(instruction_stream, i, perm_hash_instructions[i][round][9:])
        
        instruction_stream.extend([{"valu": [('^', vtmp1_batch[i], vtmp5_batch[i], vtmp1_batch[i])]}])
        hash_instrs(instruction_stream, i, perm)
        
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
        hash_instrs(instruction_stream, i, perm)
        
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
        hash_instrs(instruction_stream, i, perm)
    #final_instruction_stream.append(instruction_stream)
    return instruction_stream
    

def process(a):
    print(len(a))
    min = 1430
    log_file = open(f"output_across_batches_13_permute.txt", "w")

    def log(msg):
        print(msg, file=log_file, flush=True)
    
    for i in range(0, batch_size//8, 1):
        InstructionStreams = construct_31_IS(i)
        print(len(InstructionStreams))
        for round in range(rounds):
            instr_rounds = construct_15_rounds(i, round) #instr_round = [[],[]..[]]
            print(len(instr_rounds))
            gen = product([0, 1], repeat=13)
            for idx, perm in enumerate(gen):
                strided = (i * (rounds * 8192)) + (round * 8192) + idx
                log(strided)
                curr_round_instrutions = cur_round(i, round, perm)
                instr_rounds.insert(round + 1, curr_round_instrutions)
                instruction_stream = [item for sublist in instr_rounds for item in sublist]
                InstructionStreams.insert(i, InstructionStream(instruction_stream))
                res = schedule_instructions(deepcopy(InstructionStreams))
                instr_len = len(res) + len(a)
                #print(instr_len)
                #print(perm)
                if instr_len < min:
                    min = instr_len
                    perm_hash_instructions[i][round] = perm
                    log(f"batch = {i}, round = {round}, instr_len = {min}, perm = {perm}")
                InstructionStreams.pop(i)
                instr_rounds.pop(round + 1)



if __name__ == "__main__":
    setup_data = initial_setup()
    process(setup_data)