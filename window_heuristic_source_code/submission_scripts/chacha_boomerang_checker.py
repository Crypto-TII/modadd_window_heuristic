import numpy as np
from os import urandom
import copy

word_size = 32

const1 = 1634760805
const2 = 857760878
const3 = 2036477234
const4 = 1797285236
rotations = [16,12,8,7]
mask_val = 2**word_size-1

def rol(a, r):
    return ((a<<r)&mask_val) | (a>>(word_size-r))

def ror(a, r):
    return rol(a, word_size-r)

def quarter_round(a, b, c, d):
    a = (a + b) & mask_val; d = d ^ a; d = rol(d, rotations[0]);
    c = (c + d) & mask_val; b = b ^ c; b = rol(b, rotations[1]);
    a = (a + b) & mask_val; d = d ^ a; d = rol(d, rotations[2]);
    c = (c + d) & mask_val; b = b ^ c; b = rol(b, rotations[3]);
    return a, b, c, d

def inverse_quarter_round(a, b, c, d):
    b = ror(b, rotations[3]); b = b ^ c; c = (c - d) & mask_val
    d = ror(d, rotations[2]); d = d ^ a; a = (a - b) & mask_val
    b = ror(b, rotations[1]); b = b ^ c; c = (c - d) & mask_val
    d = ror(d, rotations[0]); d = d ^ a; a = (a - b) & mask_val
    return a, b, c, d

def prepare_state(p, k):
    k1, k2, k3, k4, k5, k6, k7, k8 = k
    p1, p2, n1, n2 = p
    c1 = np.repeat(const1, len(k1))
    c2 = np.repeat(const2, len(k1))
    c3 = np.repeat(const3, len(k1))
    c4 = np.repeat(const4, len(k1))
    state = np.array([c1,c2,c3,c4,k1,k2,k3,k4,k5,k6,k7,k8,p1,p2,n1,n2], dtype = np.uint32)
    return state


def forward_permutation(p, k, r):
    state = prepare_state(p, k).copy()
    for rr in range(r):
        if rr%2 == 0:
            state[0], state[4], state[8], state[12] = quarter_round(state[0], state[4], state[8], state[12])
            state[1], state[5], state[9], state[13] = quarter_round(state[1], state[5], state[9], state[13])
            state[2], state[6], state[10], state[14] = quarter_round(state[2], state[6], state[10], state[14])
            state[3], state[7], state[11], state[15] =  quarter_round(state[3], state[7], state[11], state[15])
        else:
            state[0], state[5], state[10], state[15] = quarter_round(state[0], state[5], state[10], state[15])
            state[1], state[6], state[11], state[12] = quarter_round(state[1], state[6], state[11], state[12])
            state[2], state[7], state[8], state[13] = quarter_round(state[2], state[7], state[8], state[13])
            state[3], state[4], state[9], state[14] = quarter_round(state[3], state[4], state[9], state[14])
    return state

def forward_permutation_state(state, r):
    for rr in range(r):
        if rr%2 == 0:
            state[0], state[4], state[8], state[12] = quarter_round(state[0], state[4], state[8], state[12])
            state[1], state[5], state[9], state[13] = quarter_round(state[1], state[5], state[9], state[13])
            state[2], state[6], state[10], state[14] = quarter_round(state[2], state[6], state[10], state[14])
            state[3], state[7], state[11], state[15] =  quarter_round(state[3], state[7], state[11], state[15])
        else:
            state[0], state[5], state[10], state[15] = quarter_round(state[0], state[5], state[10], state[15])
            state[1], state[6], state[11], state[12] = quarter_round(state[1], state[6], state[11], state[12])
            state[2], state[7], state[8], state[13] = quarter_round(state[2], state[7], state[8], state[13])
            state[3], state[4], state[9], state[14] = quarter_round(state[3], state[4], state[9], state[14])
    return state

def backwards_permutation(state, r):
    for i in range(r):
       rr = r - i - 1
       if rr%2 == 0:
            state[0], state[4], state[8], state[12] = inverse_quarter_round(state[0], state[4], state[8], state[12])
            state[1], state[5], state[9], state[13] = inverse_quarter_round(state[1], state[5], state[9], state[13])
            state[2], state[6], state[10], state[14] = inverse_quarter_round(state[2], state[6], state[10], state[14])
            state[3], state[7], state[11], state[15] =  inverse_quarter_round(state[3], state[7], state[11], state[15])
       else:
            state[0], state[5], state[10], state[15] = inverse_quarter_round(state[0], state[5], state[10], state[15])
            state[1], state[6], state[11], state[12] = inverse_quarter_round(state[1], state[6], state[11], state[12])
            state[2], state[7], state[8], state[13] = inverse_quarter_round(state[2], state[7], state[8], state[13])
            state[3], state[4], state[9], state[14] = inverse_quarter_round(state[3], state[4], state[9], state[14])
    return state

def encrypt(p, k, r):
    initial_state = prepare_state(p, k)
    final_state = forward_permutation_state(initial_state.copy(), r)
    return initial_state + final_state


def check_testvector():
    k = np.array([[0x03020100], [0x07060504], [0x0b0a0908], [0x0f0e0d0c], [0x13121110], [0x17161514], [0x1b1a1918], [0x1f1e1d1c]], dtype=np.uint32).reshape(8,1)
    p = np.array([[0x00000001], [0x09000000], [0x4a000000], [0x00000000]], dtype=np.uint32).reshape(4,1)
    stream = np.array([
        [0xe4e7f110], [0x15593bd1], [0x1fdd0f50], [0xc47120a3],
        [0xc7f4d1c7], [0x0368c033], [0x9aaa2204], [0x4e6cd4c3],
        [0x466482d2], [0x09aa9f07], [0x05d7c214], [0xa2028bd9],
        [0xd19c12b5], [0xb94e16de], [0xe883d0cb], [0x4e3c50a2]
    ], dtype=np.uint32)

    # Inversion test

    P = prepare_state(p, k)
    forward   = forward_permutation(p, k, 2)
    backwards = backwards_permutation(forward.copy(), 2)
    assert np.all(P.flatten() == backwards.flatten())

    expected = [hex(x) for x in stream.flatten()]
    produced = [hex(x) for x in encrypt(p, k, 20).flatten()]
    assert expected == produced



def verify(nabla, delta, nr, n=10**6):
    K0 = np.frombuffer(urandom(n*32), dtype=np.uint32).reshape(8, n)
    K1 = K0^np.uint32(nabla[:8]).reshape(8, 1)
    P0 = np.frombuffer(urandom(n*16), dtype=np.uint32).reshape(4, n)
    P1 = P0^np.uint32(nabla[8:]).reshape(4, 1)

    S0 = prepare_state(P0, K0)
    S1 = prepare_state(P1, K1)
    nabla_init = S0 ^ S1
    C0 = forward_permutation_state(S0, nr)
    C1 = forward_permutation_state(S1, nr)
    C0 ^= delta.reshape(16,1)
    C1 ^= delta.reshape(16,1)

    S2 = backwards_permutation(C0, nr)
    S3 = backwards_permutation(C1, nr)

    nabla_prime = S2 ^ S3
    num = np.sum((nabla_prime == nabla_init).all(axis = 0))
    return num/n

check_testvector()

# 2-round boomerang distinguisher
nr = 2
# Input difference
nabla = np.uint32([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 32768])
# Output difference
delta = np.uint32([2147483648, 2147483648, 2147483648, 2147483648, 64, 64, 64, 64, 0, 0, 0, 0, 0, 0, 0, 0])
probability = verify(nabla, delta, nr)
print(f'The probability for the boomerang {[hex(x) for x in nabla]} <-{nr}-> {[hex(x) for x in delta]} is 2^{np.log2(probability)}')
# 3-round boomerang distinguisher
# Input difference
nr = 3
nabla = np.uint32([0, 0, 0, 0, 0, 0, 0, 0, 32768, 0, 0, 0])
# Output difference
delta = np.uint32([0, 0, 0, 0, 0, 64, 0, 64, 0, 2147483648, 0, 2147483648, 0, 0, 0, 0])
probability = verify(nabla, delta, nr)
print(f'The probability for the boomerang {[hex(x) for x in nabla]} <-{nr}-> {[hex(x) for x in delta]} is 2^{np.log2(probability)}')






