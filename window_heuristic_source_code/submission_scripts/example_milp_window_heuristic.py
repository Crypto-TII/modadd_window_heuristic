from claasp.ciphers.block_ciphers.speck_block_cipher import SpeckBlockCipher
from claasp.cipher_modules.models.minizinc.minizinc_models.minizinc_xor_differential_model import MinizincXorDifferentialModel
speck = SpeckBlockCipher(number_of_rounds=5, block_bit_size=32, key_bit_size=64)
minizinc = MinizincXorDifferentialModel(speck)
bit_positions = list(range(32))
bit_positions_key = list(range(64))
fixed_variables = [{ 'component_id': 'plaintext',
    'constraint_type': 'sum',
    'bit_positions': bit_positions,
    'operator': '>',
    'value': '0' }]
fixed_variables.append({ 'component_id': 'key',
    'constraint_type': 'sum',
    'bit_positions': bit_positions_key,
    'operator': '=',
    'value': '0' })
result = minizinc.find_lowest_weight_xor_differential_trail(
    solver_name='Xor', fixed_values=fixed_variables
)
# searching for a differential trail with the lowest weightos Speck32/64 reduced to 5 rounds using MILP techniques. Also, here we are using the window size 0 for every round 
minizinc = MinizincXorDifferentialModel(speck, [0, 0, 0, 0, 0])
result = minizinc.find_lowest_weight_xor_differential_trail(solver_name='Xor', fixed_values=fixed_variables)
print(result["total_weight"])
