from hashlib import sha256
import time, multiprocessing, os,  copy
from Orses_Competitor_Core.Compete_Process import genesis_block


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
    if prime_char == hash_hex[:len_prime_char]:
        dict_of_valid_hash[hash_hex] = nonce


def compete(single_prime_char, exp_leading, block_header, dict_of_valid_nonce_hash, starting_nonce, q,
            len_competition=60):
    prime_char = single_prime_char.lower() * exp_leading
    block_header["nonce"] = starting_nonce
    # dict_of_valid_nonce_hash = dict()
    end_time = time.time() + len_competition
    combined_merkle = f'{block_header["merkle_root"]}+{block_header["primary_signatory"]}'
    while time.time() < end_time:
        get_qualified_hashes(
            prime_char=prime_char,
            hash_hex=competitive_hasher(f'{combined_merkle}{block_header["nonce"]}'.encode()),
            dict_of_valid_hash=dict_of_valid_nonce_hash,
            len_prime_char=exp_leading,
            nonce=block_header["nonce"]
        )
        block_header["nonce"] += 1
        # print(block_header["nonce"])
    total_hashes = block_header["nonce"] - starting_nonce
    print("done", os.getpid())
    q.put(total_hashes)

    return dict_of_valid_nonce_hash


def threaded_compete(single_prime_char, addl_chars, exp_leading, block_header, len_competition=60):
    num_cpu = multiprocessing.cpu_count()
    num_cpu = num_cpu * 2 if num_cpu >= 2 else num_cpu
    Process = multiprocessing.Process
    manager = multiprocessing.Manager()
    q = multiprocessing.Queue()
    total_hashes = 0

    process_list = []
    dict_of_valid_nonce_hash = manager.dict()
    starting_nonce = 0
    for i in range(num_cpu):
        process_list.append(Process(target=compete, args=(single_prime_char,exp_leading, copy.deepcopy(block_header),
                                                          dict_of_valid_nonce_hash, starting_nonce, q,
                                                          len_competition),))
        starting_nonce += 10_000_000
    for process in process_list:
        process.daemon= True
        process.start()
    total_hashes += q.get()  # first hash process to be finished
    for i in range(num_cpu-1):
        print(i)
        total_hashes += q.get()  # remaining hashes

    print("hash Per Second", total_hashes/len_competition)
    # print(dict_of_valid_nonce_hash)

    return choose_top_scoring_hash(single_prime_char, addl_chars, dict(dict_of_valid_nonce_hash), exp_leading)


def choose_top_scoring_hash(prime_char, addl_chars, dict_of_valid_hashes, exp_leading):
    """

    :param prime_char: hex character that must be leading in a hash
    :param addl_chars: addl characters (if any) used after the leading hash
    :param dict_of_valid_hashes: a dictionary of valid hashes with enough leading prime characters
    :param exp_leading: expected amount of leading prime char in a hash
    :return: returns the hash and nonce with highes score
    """
    initial_prime_char = exp_leading
    score = 0
    leading_dict = None
    print("type", type(dict_of_valid_hashes), dict_of_valid_hashes)
    for i in dict_of_valid_hashes:
        print(i)
        temp_score = 0
        temp_extra = 0
        ini_pr_ch = initial_prime_char
        leading_prime = True
        for j in i[exp_leading:]:
            if j == prime_char and leading_prime:
                # if j is prime and previous value was prime then j value is added n in 16^n.
                ini_pr_ch += 1
            elif j in addl_chars:
                # add the value, if j is prime char and previous char was not prime , then f value is added score
                leading_prime = False
                # temp_score = 16 ** ini_pr_ch if not score else score
                temp_extra += 15 - addl_chars.find(j) # addl_chars string sorted from hi value char(15) to lowest.
            else:
                temp_score = 16 ** ini_pr_ch
                temp_score += temp_extra
                break
        print("temp_score", temp_score, "score", score, "\n---")
        if temp_score > score:
            score = temp_score
            leading_dict = {"nonce": [dict_of_valid_hashes[i], i], "score": "16/{}/{}".format(ini_pr_ch, temp_extra)}

    return leading_dict


# run this function to start competing, to run, feed it the prime character, addl_chars, block header_dict,
# expected leading prime chars and len of competition
def start_competing(prime_char, addl_chars, block_header, exp_leading, len_competition):

    v = threaded_compete(single_prime_char=prime_char,
                         exp_leading=exp_leading, block_header=block_header, len_competition=len_competition,
                         addl_chars=addl_chars)

    block_header["nonce"] = v["nonce"][0]

    return block_header

if __name__ == '__main__':
    pass