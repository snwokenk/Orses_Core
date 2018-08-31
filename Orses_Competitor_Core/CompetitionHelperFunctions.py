

def get_prime_char(block:  dict, block_header=None) -> str:
    if block_header:
        prime_char: str = block_header["shv"]['16']
    else:
        prime_char: str = block["bh"]["shv"]['16']

    return prime_char


def get_prime_char_for_block_one() -> str:
    return 'f'


def get_addl_chars_exp_leading(block: dict, block_header=None) -> list:

    block_header = block_header if block_header else block["bh"]
    # get the number of times single prime char shows up in front of hash
    mpt_split = block_header["mpt"].split(sep="+")  # "P7+0"  == ['P7', '0']
    exp_leading_prime = int(mpt_split[0][1:])
    number_of_addl_chars = int(mpt_split[1])

    # get addl_chars if needed (if number after plus is >  ie p7+2 or p7+3 no after + can never be 1 (p7+1 == p8+0)
    # additional characters are choosen from biggest to smallest key
    addl_chars = ""
    for i in range(1, number_of_addl_chars):

        # addl_chars = "value at key '15', value at key '14',....etc" value at key '1' is never used
        # value at key '16' is the prime char and is automatically assumed as the first addl char
        addl_chars = f"{addl_chars}{block_header['shv'][str(16-i)]}"

    return [exp_leading_prime, addl_chars]


def get_addl_chars_exp_leading_block_one():

    return [5, ""]  # [exp_leading_prime, addl chars]

