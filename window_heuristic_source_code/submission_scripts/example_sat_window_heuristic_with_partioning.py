from claasp.ciphers.block_ciphers.speck_block_cipher import SpeckBlockCipher
from claasp.cipher_modules.models.sat.sat_models.sat_xor_differential_model import SatXorDifferentialModel
from claasp.cipher_modules.models.utils import set_fixed_variables, integer_to_bit_list


speck = SpeckBlockCipher(number_of_rounds=9)
sat = SatXorDifferentialModel(speck)
sat.set_window_size_heuristic_by_round(
    [2 for i in range(9)], number_of_full_windows=1, full_window_operator='at_least'
)
plaintext = set_fixed_variables(component_id='plaintext', constraint_type='not_equal',
                                bit_positions=range(32), bit_values=(0,) * 32)
key = set_fixed_variables(component_id='key', constraint_type='equal',
                          bit_positions=range(64), bit_values=(0,) * 64)
result = sat.find_one_xor_differential_trail_with_fixed_weight(30, fixed_values=[plaintext, key], solver_name='CADICAL_EXT')

print(result['total_weight'])
print(result)
