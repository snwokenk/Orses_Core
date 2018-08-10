from hashlib import sha256
import time, multiprocessing, os,  copy, queue
from multiprocessing.queues import Queue
from Orses_Competitor_Core.BlockCreator import GenesisBlockCreator
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
"""
This file can be used to generate a genesis block for test, beta or live network
And also contains compete algorithm
"""


def competitive_hasher(enc_d):
    return sha256(sha256(enc_d).digest()).hexdigest()


def get_qualified_hashes(prime_char,  hash_hex, len_prime_char, dict_of_valid_hash, nonce, extra_nonce):
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

        dict_of_valid_hash[hash_hex] = [nonce, extra_nonce]


def compete_improved(single_prime_char, exp_leading, block_header, dict_of_valid_nonce_hash,  q,
                     extra_nonce_index, max_nonce_value, end_time):
    prime_char = single_prime_char.lower() * exp_leading
    nonce = 0
    x_nonce = 0
    primary_signatory = block_header.p_s
    merkle_root = block_header.mrh
    print("starting nonce", nonce)
    extra_nonce = f"{extra_nonce_index}_{x_nonce}"
    combined_merkle = f'{extra_nonce}{merkle_root}+{primary_signatory}'
    while time.time() < end_time:

        # check if nonce greater than max number (which is highest number of unsigned 64 bit integer or ((2**64) - 1)
        if nonce > max_nonce_value:
            nonce = 0
            x_nonce += 1
            extra_nonce = f"{extra_nonce_index}_{x_nonce}"
            # if extra nonce is needed then add in combined merkle
            combined_merkle = f'{extra_nonce}{merkle_root}+{primary_signatory}'

        get_qualified_hashes(
            prime_char=prime_char,
            hash_hex=competitive_hasher(f'{combined_merkle}{nonce}'.encode()),
            dict_of_valid_hash=dict_of_valid_nonce_hash,
            len_prime_char=exp_leading,
            nonce=nonce,
            extra_nonce=extra_nonce
        )
        nonce += 1

    total_hashes = nonce if x_nonce is None else nonce + (max_nonce_value * x_nonce)
    print("done", os.getpid())
    q.put(total_hashes)
    return dict_of_valid_nonce_hash


def threaded_compete_improved(single_prime_char, addl_chars, exp_leading, block_header, len_competition=60):
    """

    :param single_prime_char: the prime character
    :param addl_chars: additional characters that can be used after the exp_leading
    :param exp_leading: the expected number of times the single_prime_char appears
    :param block_header: instance of GenesisBlockHeader
    :param len_competition: int number of seconds for competition
    :return:
    """
    # check number of cpu cores
    num_cpu = multiprocessing.cpu_count()

    # create 2 threads per cpu
    # todo: allow individual to set number of threads using intensity
    num_cpu = num_cpu * 2 if num_cpu >= 2 else num_cpu

    Process = multiprocessing.Process

    # instantiate a manager class, for use in creating data structures that can be shared
    manager = multiprocessing.Manager()

    # create a q object, this will block in main thread and receive the total number of hashes
    q = multiprocessing.Queue()
    total_hashes = 0

    process_list = []
    dict_of_valid_nonce_hash = manager.dict()
    starting_nonce = 0

    # this is the difference between each thread/process's starting nonce
    starting_nonce_multiples = 20_000_000

    max_nonce_value = 18_446_744_073_709_551_615  # max  number of 64 bit number of unsigned long long
    end_time = time.time() + len_competition + 0.1  # add one tenth second for delay
    for extra_nonce_index in range(num_cpu):

        process_list.append(Process(target=compete_improved, args=(single_prime_char,exp_leading, block_header,
                                                                   dict_of_valid_nonce_hash, q,
                                                                   extra_nonce_index, max_nonce_value,
                                                                   end_time,)))
        starting_nonce += starting_nonce_multiples

    for process in process_list:
        process.daemon = True
        process.start()
    total_hashes += q.get()  # first hash process to be finished
    for i in range(num_cpu-1):
        print(i)
        total_hashes += q.get()  # remaining hashes

    dict_of_valid_nonce_hash = dict(dict_of_valid_nonce_hash)
    print("hash Per Second: ", total_hashes/len_competition)
    print("total hashes: ", total_hashes)
    print("number of valid hashes: ", len(dict_of_valid_nonce_hash))
    # print(dict_of_valid_nonce_hash)

    return choose_top_scoring_hash(single_prime_char, addl_chars, dict_of_valid_nonce_hash, exp_leading)


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
    for hash in dict_of_valid_hashes:
        print(hash)
        temp_score = 0
        temp_extra = 0
        ini_pr_ch = initial_prime_char
        leading_prime = True
        for j in hash[exp_leading:]:
            if j == prime_char and leading_prime:
                # if j is prime and previous value was prime then j value is added n in 16^n.
                ini_pr_ch += 1
            elif j in addl_chars:
                # add the value, if j is prime char and previous char was not prime , then f value is added score
                leading_prime = False
                # temp_score = 16 ** ini_pr_ch if not score else score
                temp_extra += 15 - addl_chars.find(j)  # addl_chars string sorted from hi value char(15) to lowest.
            else:
                temp_score = 16 ** ini_pr_ch
                temp_score += temp_extra
                break
        # print("temp_score", temp_score, "score", score, "\n---")
        if temp_score > score:
            score = temp_score
            leading_dict = {"nonce": [dict_of_valid_hashes[hash], hash], "score": "16/{}/{}".format(ini_pr_ch, temp_extra)}

    return leading_dict


# run this function to start competing, to run, feed it the prime character, addl_chars, block header_dict,
# expected leading prime chars and len of competition
def start_competing(block_header, exp_leading=6, len_competition=30, single_prime_char="f", addl_chars=""):

    winning_hash = threaded_compete_improved(
        single_prime_char=single_prime_char,
        exp_leading=exp_leading,
        block_header=block_header,
        len_competition=len_competition,
        addl_chars=addl_chars
    )

    print(f"The winning hash and nonce is {winning_hash}")

    block_header.block_hash = winning_hash["nonce"][1]
    block_header.n = format(winning_hash["nonce"][0][0], "x")
    block_header.x_n = winning_hash["nonce"][0][1]
    print(block_header.get_block_header())

    return block_header


def generate_genesis_block(len_of_competition=30, exp_leading_prime=6, single_prime_char="f"):
    gen_block_creator_inst = GenesisBlockCreator(primary_sig_wallet_id="W884c07be004ee2a8bc14fb89201bbc607e75258d")
    gen_block_creator_inst.set_before_competing()

    merkle_root = gen_block_creator_inst.merkle_root

    gen_block_obj = gen_block_creator_inst.get_block()

    block_header = gen_block_creator_inst.block_header_callable()
    block_header.set_header_before_comepete(
        primary_sig_wallet_id=gen_block_creator_inst.primary_sig_wallet_id,
        merkle_root=merkle_root
    )

    print(f"in Orses_compete_algo: merkle root:  {merkle_root}")
    print(f"in Orses_compete_algo: block: {gen_block_obj.get_block()}")

    print(f"in Orses_compete_algo: block_header: {block_header.get_block_header()}")

    final_block_header = start_competing(
        block_header=block_header,
        len_competition=len_of_competition,
        exp_leading=exp_leading_prime,
        single_prime_char=single_prime_char
    )

    gen_block_obj.set_after_compete(
        block_header=final_block_header.get_block_header(),
        signature=DigitalSigner.sign_with_provided_privkey(
            dict_of_privkey_numbers={
                'x': 60785994004755780541968889462742035955235637618029604119657448498380482761088,
                'y': 100309319245511545150569175878829989424599308092677960010907323326738383429364,
                'd': 29950300400169917180358605208938775880760212514399944926857005417377480590100
            },
            message=final_block_header.block_hash
        ),
        list_of_secondary_signatories=["Wf2f140a956cec5cd6a1a6f7763378b239a007ac0",
                                       "Wc8f7cc3576244c915e50e4410b988dfb6946f036"]


    )

    return gen_block_obj.get_block()


class Competitor:
    def __init__(self, reward_wallet, admin_inst):
        self.admin_inst = admin_inst
        self.reward_wallet = reward_wallet

    def get_recent_block(self):
        """
        get recent block fromm CompetitorDataloading.py
        This should have been updated and being updated by Blockchainpropagator
        :return:
        """

    def compete(
            self,
            q_for_compete: (multiprocessing.queues.Queue, queue.Queue),
            q_from_bk_propagator: (multiprocessing.queues.Queue, queue.Queue),
            q_for_validator: (multiprocessing.queues.Queue, queue.Queue),
    ):

        print(f"in Orses_compete_alog, Started Compete Process For admin: {self.admin_inst.admin_name}")
        recent_blk = q_for_compete.get()
        print(f"in Orses_compete_Algo, recent block:\n{recent_blk} admin: {self.admin_inst.admin_name}")
        rwd_wallet = self.reward_wallet

        while True:
            rsp = q_for_compete.get()

            # rsp should be dictionary of transaction ie
            if isinstance(rsp, str) and rsp in {"exit", "quit"}:
                break


if __name__ == '__main__':
    genesis_block = generate_genesis_block()

    print("\n\n")
    for x, y in genesis_block.items():
        print(x, ": ", y)