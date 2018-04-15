import json, time
from hashlib import sha256


def encode_datastructure(datastructure):
    return json.dumps(datastructure).encode()


def competitive_hasher(enc_d):
    return sha256(sha256(enc_d).digest()).hexdigest()


def get_qualified_hashes(prime_char,  hash_hex, len_prime_char, dict_of_valid_hash, nonce):
    """
    used to get hash meetimg maximum probability using prime char and addl character
    :param prime_char: a string of repeating hex character string of 0-9 or A-F
    :type prime_char: str
    :param hash_hex: sha256 hex
    :type hash_hex: sha256 hex
    :param len_prime_char: length of prime_char parameter string
    :type len_prime_char: int
    :return:
    """
    print(hash_hex, prime_char, hash_hex[:len_prime_char])

    if prime_char == hash_hex[:len_prime_char]:
        dict_of_valid_hash[str(nonce)] = hash_hex


def compete(single_prime_char, exp_leading, block_header, len_competition=30):

    prime_char = single_prime_char.lower() * exp_leading
    block_header["nonce"] = 0
    dict_of_valid_nonce_hash = dict()
    end_time = time.time() + len_competition

    while time.time() < end_time:
        get_qualified_hashes(
            prime_char=prime_char,
            hash_hex=competitive_hasher(encode_datastructure(block_header)),
            dict_of_valid_hash=dict_of_valid_nonce_hash,
            len_prime_char=exp_leading,
            nonce=block_header["nonce"]
        )
        block_header["nonce"] += 1

    return dict_of_valid_nonce_hash


if __name__ == '__main__':

    data = {"tx": "Sam", "time": 14590}

    v = compete(single_prime_char="f", exp_leading=4, block_header=data)

    print(v)
    print("-")
    print(data)

