from hashlib import sha256
import time, multiprocessing, os,  queue, json, math
from multiprocessing.queues import Queue
from multiprocessing import synchronize
from queue import Empty # Exception
from Orses_Competitor_Core.BlockCreator import GenesisBlockCreator, BlockOneCreator, RegularBlockCreator
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Orses_Util_Core.FileAction import FileAction
from Orses_Cryptography_Core.Hasher import Hasher
from Orses_Competitor_Core.CompetitorDataLoading import BlockChainData
from Orses_Competitor_Core.CompetitionHelperFunctions import get_prime_char, get_addl_chars_exp_leading, \
    get_prime_char_for_block_one, get_addl_chars_exp_leading_block_one


"""
This file can be used to generate a genesis block for test, beta or live network
And also contains compete algorithm
"""


def round_down_4_places(dec_num):

    return math.floor(dec_num*10000)/10000


def competitive_hasher(enc_d):
    return sha256(sha256(enc_d).digest()).hexdigest()


def get_qualified_hashes(prime_char,  hash_hex, len_prime_char, nonce, extra_nonce,  dict_of_valid_hash=None,
                         check_if_valid=None):
    """
    used to get hash meetimg maximum probability using prime char and addl character
    :param prime_char: a string of repeating hex character string of 0-9 or A-F
    :type prime_char: str
    :param hash_hex: sha256 hex
    :type hash_hex: sha256 hex str
    :param len_prime_char: length of prime_char parameter string
    :type len_prime_char: int
    :param dict_of_valid_hash:
    :param check_if_valid:
    :return:
    """
    if prime_char == hash_hex[:len_prime_char]:
        if check_if_valid:
            return True
        dict_of_valid_hash[hash_hex] = [nonce, extra_nonce]

    else:
        return False


def compete_improved(single_prime_char, exp_leading, block_header, dict_of_valid_nonce_hash,  q,
                     extra_nonce_index, max_nonce_value, end_time, prev_hash, is_program_running):
    prime_char = single_prime_char.lower() * exp_leading
    nonce = 0
    x_nonce = 0
    merkle_root = block_header.mrh
    print("starting nonce", nonce)
    extra_nonce = f"{extra_nonce_index}_{x_nonce}"
    combined_merkle = f'{extra_nonce}{merkle_root}{prev_hash}'

    if is_program_running is None or is_program_running.is_set():
        while time.time() < end_time:

            # check if nonce greater than max number (which is highest number of unsigned 64 bit integer or ((2**64) - 1)
            if nonce > max_nonce_value:
                nonce = 0
                x_nonce += 1
                extra_nonce = f"{extra_nonce_index}_{x_nonce}"
                # if extra nonce is needed then add in combined merkle
                combined_merkle = f'{extra_nonce}{merkle_root}{prev_hash}'

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


def threaded_compete_improved(
        single_prime_char,
        addl_chars,
        exp_leading,
        block_header,
        prev_hash,
        is_program_running,
        len_competition=60
):
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
                                                                   end_time,prev_hash, is_program_running)))
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
        for j in hash[exp_leading:]:  # this is from eligible hashes so start from exp leading index
            if j == prime_char and leading_prime is True:
                # if j is prime and previous value was prime then j value is added n in 16^n.
                ini_pr_ch += 1
            elif j == prime_char and leading_prime is False:  # prime character still an eligible addl char
                temp_extra += 16

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
def start_competing(block_header, prev_hash, is_program_running, exp_leading=6, len_competition=30,
                    single_prime_char="f", addl_chars=""):

    winning_hash = threaded_compete_improved(
        single_prime_char=single_prime_char,
        exp_leading=exp_leading,
        block_header=block_header,
        len_competition=len_competition,
        addl_chars=addl_chars,
        prev_hash=prev_hash,
        is_program_running=is_program_running

    )

    print(f"The winning hash and nonce is {winning_hash}")

    if winning_hash:

        block_header.block_hash = winning_hash["nonce"][1]
        block_header.n = format(winning_hash["nonce"][0][0], "x")
        block_header.x_n = winning_hash["nonce"][0][1]
        block_header.set_block_time()
        print(block_header.get_block_header())

    return block_header.get_block_header()


def get_reward_txs(
        primary_sig_wallet,
        secondary_sig_wallets: list,  # todo: create secondary reward. for now skip
        block_no: int,
        fees: int,
        len_of_comp: int,
        include_foundation_reward=True,
        block_one_reward_per_second=15854895991,
        wsh=None

):
    # todo: retrieve wallet's
    # number of blocks before reward is reduced by 2% == 525600

    base = 0.98
    exponent = block_no // 525600

    reward_discount_from_base = base ** exponent
    reward_per_second = math.floor(block_one_reward_per_second * reward_discount_from_base)

    main_reward = reward_per_second * len_of_comp

    foundation_reward = math.floor(main_reward * 0.15) if include_foundation_reward is True else 0
    extra_reward = foundation_reward // 2

    primary_signatory_reward = main_reward + extra_reward
    primary_rwd_tx = {primary_sig_wallet: [primary_signatory_reward, fees, primary_signatory_reward+fees]}
    foundation_rwd_tx = {"fnd_rwd": foundation_reward}

    list_of_hashes = [Hasher.sha_hasher(json.dumps(primary_rwd_tx)), Hasher.sha_hasher(json.dumps(foundation_rwd_tx))]
    primary_reward_hash, fnd_reward_hash = list_of_hashes
    rwd_txs = [
        [primary_reward_hash, primary_rwd_tx],
        [fnd_reward_hash, foundation_rwd_tx],

    ]

    return rwd_txs


def generate_regular_block(block_no: int, admin_inst, combined_list: list,
                           wsh: dict, fees: int, no_of_txs: int, no_of_asgns: int, primary_sig_wallet: str,
                           prev_hash, addl_chars, is_program_running, len_competiion=60, exp_leading_prime=7,
                           single_prime_char='f', should_save=False, include_foundation=True):

    # primary wallet_for test"W884c07be004ee2a8bc14fb89201bbc607e75258d"
    if block_no == 1:

        # pass
        new_block = generate_block_one(
            admin_inst=admin_inst,
            combined_list=combined_list,
            wsh=wsh,
            fees=fees,
            no_of_txs=no_of_txs,
            no_of_asgns=no_of_asgns,
            primary_sig_wallet=primary_sig_wallet,
            len_competiion=len_competiion,
            exp_leading_prime=exp_leading_prime,
            single_prime_char=single_prime_char,
            should_save=should_save,
            include_foundation=include_foundation,
            genesis_block_hash=prev_hash,
            is_program_running=is_program_running



        )
    else:


        # todo: get list of previous 2 hashes. have a way of getting previous 2 blocks hashes probably using fileaction
        list_of_prev_2_hashes=None

        # insert reward transactions into transaction dict
        list_of_hashes = get_reward_txs(
            primary_sig_wallet=primary_sig_wallet,
            block_no=block_no,
            fees=fees,
            len_of_comp=len_competiion,
            include_foundation_reward=include_foundation,
            secondary_sig_wallets=[],  # todo: add secondary rewards to reward transactions. for now, skip
            wsh=wsh
        )

        # insert reward transactions hash into combined hash list [prim signatory rwd hash, foundation reward hash]
        combined_list.extend(list_of_hashes)

        # instantiate block one creator
        new_block_creator_inst = RegularBlockCreator(
            primary_sig_wallet_id=primary_sig_wallet,
            combined_list=combined_list
        )





        # set misc messages with top 10 signatories
        # todo: secondary signatories reward should be added into reward tx

        new_block_creator_inst.set_block_before_competing(
            combined_list=combined_list,
            secondary_signatories=[],  # is blank, pro
            wsh=wsh
        )

        block_header = new_block_creator_inst.block_header_callable()

        print(f"in Orses compete, generate_regula_block:\n"
              f"block header {block_header}\n"
              f"new_block_creator {new_block_creator_inst}"
              f"merkle root fo block {block_no}: {new_block_creator_inst.merkle_root}")
        block_header.set_header_before_compete(
            primary_sig_wallet_id=primary_sig_wallet,
            merkle_root=new_block_creator_inst.merkle_root,
            no_of_txs=no_of_txs,
            no_of_asgns=no_of_asgns,
            list_of_prev_2_hashes=list_of_prev_2_hashes,  # todo: this list should get
            list_of_maximum_prob=['p6+0', "p7+0", "p6+0", "p7+0", "p6+0"],
            prev_hash=prev_hash,
            block_no=block_no
        )

        final_block_header = start_competing(
            block_header=block_header,
            len_competition=len_competiion,
            exp_leading=exp_leading_prime,
            single_prime_char=single_prime_char,
            addl_chars=addl_chars,
            prev_hash=prev_hash,
            is_program_running=is_program_running
        )

        block_object = new_block_creator_inst.get_block()
        block_object.set_after_competing(
            block_header=final_block_header
        )

        new_block = block_object.get_block()

        if should_save:
            folder = admin_inst.fl.get_block_data_folder_path()
            admin_inst.fl.save_json_into_file(
                filename=str(block_no),
                python_json_serializable_object=new_block,
                in_folder=folder
            )

    return new_block


def generate_block_one(admin_inst, combined_list: list,  wsh: dict, fees: int, no_of_txs,
                       no_of_asgns, primary_sig_wallet: str, genesis_block_hash, is_program_running, len_competiion=60, exp_leading_prime=7,
                       single_prime_char='f',should_save=False, include_foundation=True):
    """

    1 Orses Token = 10,000,000,000 ntakiri
    default primary sig reward is 2.5 billion * 0.02 == 50 million Orses Token
    assuming number of minutes  in a year (365 * 1440) ~ 525600
    and number of seconds is 525600 * 60  == 31536000

    reward per second is (50,000,000 * 10,000,000,000)/31536000 = 15854895991 ntakiri   # rounded down

    block one will have a set length of 60 seconds (because it has no block before recent) so
    block one reward is = 951293759460 Orses ntakiri or 95.129375946 Orses' token

    misc message structure:

    {
        “Client id”:{
            “Hash”:{
                purpose(optional): “”
                Signature: “”,
                Public key: “”,
                Message: “”,
                Time: int
            }
        }
    }


    :param reward: amount to reward primary signatories
    :param len_competiion:
    :param exp_leading_prime:
    :param single_prime_char:
    :param should_save:
    :return:
    """

    # create reward transactions
    list_of_hashes = get_reward_txs(
        primary_sig_wallet=primary_sig_wallet,
        block_no=1,
        fees=fees,
        len_of_comp=len_competiion,
        include_foundation_reward=include_foundation,
        secondary_sig_wallets=[]  # todo: add secondary rewards to reward transactions for now, skip
    )

    # insert reward transactions hash into combined hash list [prim signatory rwd hash, foundation reward hash]
    combined_list.extend(list_of_hashes)

    # instantiate block one creator
    block_one_creator_inst = BlockOneCreator(
        primary_sig_wallet_id=primary_sig_wallet,
        combined_list=combined_list
    )

    # set misc messages with top 10 signatories
    # todo: secondary signatories reward should be added into reward tx

    block_one_creator_inst.set_block_before_competing(
        combined_list=combined_list,
        secondary_signatories=[],  # is blank, pro
        wsh=wsh
    )

    block_header = block_one_creator_inst.block_header_callable()
    block_header.set_header_before_compete(
        primary_sig_wallet_id=block_one_creator_inst.primary_sig_wallet_id,
        merkle_root=block_one_creator_inst.merkle_root,
        no_of_txs=no_of_txs,
        no_of_asgns=no_of_asgns,
        prev_hash=genesis_block_hash
    )

    final_block_header = start_competing(
        block_header=block_header,
        len_competition=len_competiion,
        exp_leading=exp_leading_prime,
        single_prime_char=single_prime_char,
        prev_hash=genesis_block_hash,
        is_program_running=is_program_running
    )

    block_object = block_one_creator_inst.get_block()
    block_object.set_after_competing(
        block_header=final_block_header
    )

    new_block = block_object.get_block()

    if should_save:
        folder = admin_inst.fl.get_block_data_folder_path()
        admin_inst.fl.save_json_into_file(
            filename="1",
            python_json_serializable_object=new_block,
            in_folder=folder
        )

    return new_block


def generate_genesis_block(len_of_competition=90, exp_leading_prime=6, single_prime_char='f', should_save=False):
    gen_block_creator_inst = GenesisBlockCreator(primary_sig_wallet_id="W884c07be004ee2a8bc14fb89201bbc607e75258d")
    gen_block_creator_inst.set_before_competing()

    merkle_root = gen_block_creator_inst.merkle_root

    gen_block_obj = gen_block_creator_inst.get_block()

    block_header = gen_block_creator_inst.block_header_callable()
    block_header.set_header_before_compete(
        primary_sig_wallet_id=gen_block_creator_inst.primary_sig_wallet_id,
        merkle_root=merkle_root
    )



    final_block_header: dict = start_competing(
        block_header=block_header,
        len_competition=len_of_competition,
        exp_leading=exp_leading_prime,
        single_prime_char=single_prime_char,
        is_program_running=None,
        prev_hash='0'
    )

    gen_block_obj.set_after_compete(
        block_header=final_block_header,
        signature=DigitalSigner.sign_with_provided_privkey(
            dict_of_privkey_numbers={
                'x': 60785994004755780541968889462742035955235637618029604119657448498380482761088,
                'y': 100309319245511545150569175878829989424599308092677960010907323326738383429364,
                'd': 29950300400169917180358605208938775880760212514399944926857005417377480590100
            },
            message=final_block_header.get("block_hash")
        ),
        list_of_secondary_signatories=["Wf2f140a956cec5cd6a1a6f7763378b239a007ac0",
                                       "Wc8f7cc3576244c915e50e4410b988dfb6946f036"]
    )

    gen_block = gen_block_obj.get_block()

    filename = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Blockchain_Data", "0")

    if should_save:
        FileAction.save_json_into_file(
            filename=filename,
            python_json_serializable_object=gen_block,
        )

    print(f"Newly Generated Block is:\n")
    print(gen_block)

    return gen_block


class TxMiscWsh:

    def __init__(self, txs, fees: int):

        self.number_of_transactions = 0
        self.number_of_assignment_statements = 0
        self.txs = txs
        self.misc_msgs = dict()  # misc messages dictionary
        self.wsh = dict()  # wallet hash states
        self.fees = fees
        self.combined_list_of_hashes = list()
        self.list_for_merkle = list()

    def append_to_combined_list(self, a_hash, main_msg):
        comb_index = self.number_of_transactions
        self.combined_list_of_hashes.append([a_hash, main_msg])
        self.list_for_merkle.append(a_hash)
        self.number_of_transactions += 1

        return comb_index

    def create_empty_tx_dict(self):

        transactions = dict()
        transactions["ttx"] = dict()
        transactions["rsv_req"] = dict()
        transactions["rvk_req"] = dict()

        return transactions

    def add_to_misc_msg(self, msg_hash, msg: list, fees: int):

        self.append_to_combined_list(msg_hash, msg)
        self.fees += fees

    def add_to_txs(self, type_of_tx, tx_hash, tx: list, fees: int):
        if type_of_tx in {"ttx", "rsv_req", "rvk_req"}:

            self.append_to_combined_list(tx_hash, tx)
            self.fees += fees
        else:
            print(f"in Orses_Compete_Algo.py: in add_to_txs, type_of_tx NOT VALID")

    def add_to_wsh(self, wsh_hash, wsh_list: list, no_of_asgn_stmt: int, fees: int):
        wsh_index = self.append_to_combined_list(wsh_hash, wsh_list)
        wsh_list.append(wsh_index)
        self.number_of_assignment_statements += no_of_asgn_stmt

        self.wsh[wsh_hash] = wsh_list

        self.fees += fees


class Competitor:
    def __init__(self, reward_wallet, admin_inst, is_program_running, just_launched=False):
        self.admin_inst = admin_inst
        self.just_launched = just_launched
        self.reward_wallet = reward_wallet
        self.block_creator = None
        self.hex_value_to_time = self.set_hex_value_to_seconds()
        self.is_program_running = is_program_running

    @staticmethod
    def set_hex_value_to_seconds():
        return {
            '0': 30,
            '1': 30,
            '2': 30,
            '3': 30,
            '4': 45,
            '5': 45,
            '6': 45,
            '7': 45,
            '8': 60,
            '9': 60,
            'a': 60,
            'b': 60,
            'c': 90,
            'd': 90,
            "e": 90,
            'f': 90
        }

    def determine_time(self, block_before_recent_block_no: int, block_before_recent_block_header):
        # to determine the time of current competition, must

        if block_before_recent_block_no > 0:

            try:
                hex_value = block_before_recent_block_header["block_hash"][-1]
            except TypeError:
                print(f"in determine_time(), block_before_recent is not a dict but of type "
                      f"{type(block_before_recent_block_header)}")
            except KeyError:
                print(f"block_before_recent is not a dict but of type "
                      f"{type(block_before_recent_block_header)}")

            else:
                return self.hex_value_to_time[hex_value]

        else:  # recent block is genesis block
            return 60

        return None

    def determine_competition_len(self, block_before_recent_block_no: int, block_before_recent_block_header: dict):
        time_len = self.determine_time(
            block_before_recent_block_no=block_before_recent_block_no,
            block_before_recent_block_header=block_before_recent_block_header
        )
        return time_len

    def competitor_get_block(self, block_no):
        """
        get recent block fromm CompetitorDataloading.py
        This should have been updated and being updated by Blockchainpropagator
        :return:
        """
        return BlockChainData.get_block(
            admin_instance=self.admin_inst,
            block_no=block_no
        )

    def create_empty_tx_dict(self):

        transactions = dict()
        transactions["ttx"] = dict()
        transactions["rsv_req"] = dict()
        transactions["rvk_req"] = dict()

        return transactions

    def get_new_block_arguments(self, rsp, pause_time=60):
        recent_blk = rsp[1]
        block_header = recent_blk["bh"]
        last_block_time = block_header["time"]
        # start_time = time.time() + pause_time  # 7 second proxy window
        start_time = last_block_time + pause_time  # 7 second proxy window

        # get single prime, exp leading prime, addl chars, len of competition from block before recent
        block_before_recent_block_no = int(block_header["block_no"], 16) - 1
        block_before_recent = self.competitor_get_block(
            block_no=block_before_recent_block_no
        )
        block_before_recent_block_header = block_before_recent["bh"]
        len_competition = self.determine_competition_len(
            block_before_recent_block_no=block_before_recent_block_no,
            block_before_recent_block_header=block_before_recent_block_header
        )

        # single character of this competition is value of key '16' in shuffled hex value dict
        single_prime_char = get_prime_char(block={}, block_header=block_before_recent_block_header) # char at shuffled he


        # get exp_leading_prime and addl chars
        exp_leading_prime, addl_chars = get_addl_chars_exp_leading(
            block={},
            block_header=block_before_recent_block_header
        )

        return start_time, len_competition, single_prime_char, exp_leading_prime, block_before_recent_block_no + 2, \
               addl_chars, block_header["block_hash"]

    def get_block_one_arguments(self):
        start_time = int(time.time())  # start immediately for block one but 2 second pause
        len_competition = 30
        single_prime_char = get_prime_char_for_block_one()
        exp_leading_prime, addl_chars = get_addl_chars_exp_leading_block_one()
        new_block_no = 1
        gen_block_header = self.competitor_get_block(block_no=0)["bh"]

        return start_time, len_competition, single_prime_char, exp_leading_prime, new_block_no, addl_chars, \
               gen_block_header["block_hash"]

    def non_compete_process(self, q_for_block_validator, reactor_inst, last_block=None, pause_time=60):
        """
        Will be run if by non competitor/ no proxy nodes
        The aim of this process is to be in sync with the competition schedule (of most of the nodes)
        THis process is called and either sends block arguments for validation or creates a reactor.CallLater to
        which sends the arguments at the appropriate time

        :param q_for_block_validator:
        :param reactor_inst: instance of reactor passed from main() function in start_node.py
        :param last_block: previous block, it's none at start of program but subsequent calles from
                            blockchainpropgator.check_winning_block_from_network puts the previous block
        :return:
        """
        print(f"In Non_compete() admin {self.admin_inst.admin_name}")

        # first get the last block to decide the timing (if last_block_is_none)
        # later each node will be started by random bytes from proxy nodes
        if last_block is None:
            last_block = BlockChainData.get_current_known_block(admin_instance=self.admin_inst)
            if last_block:
                last_block_no = int(last_block[0])
                last_block = last_block[1]
            else:
                print(f"in non_compete_process, last block is None ending process")
                return
        else:
            try:
                last_block_no = int(last_block['bh']['block_no'], 16)

            except (KeyError, TypeError) as e:
                print(f"in non_compete_process error occured and ending process: {e}")
                return

        if last_block_no > 0:
            block_argument = self.get_new_block_arguments(rsp=[last_block_no, last_block], pause_time=pause_time)
            start_time = block_argument[0]
            len_competition = block_argument[1]
            new_block_no = block_argument[4]
        else:
            block_argument = self.get_block_one_arguments()
            start_time = block_argument[0]
            len_competition = block_argument[1]
            new_block_no = block_argument[4]

        time_to_end_of_competition = start_time + len_competition  # 10 second slack
        print(f"in non_compete_process(), time to end of competition {time_to_end_of_competition}")

        # how long the time to receive blocks from other nodes should last


        # define a function to callback this function non_compete_process
        def callback_non_compete(prev_block):
            reactor_inst.callInThread(
                self.non_compete_process,
                q_for_block_validator=q_for_block_validator,
                reactor_inst=reactor_inst,
                last_block=prev_block
            )

        # set this callable to admin miscellaneous util dict, can then be called after new block is chosen
        self.admin_inst.util_dict["callback_non_compete"] = callback_non_compete

        # todo: because call back function includes reactor, it can't be sent using q

        # decide reason message
        reason_msg = "new_round"
        if time.time() >= time_to_end_of_competition:
            # [block_no, prime char, addl_chars, exp_leading_prime,]
            # [reason_msg, end_time, new_block]
            q_for_block_validator.put(
                [
                    reason_msg,
                    time.time() + (pause_time/2),  # end time
                    [
                        new_block_no,
                        block_argument[2],
                        block_argument[-2],
                        block_argument[3],

                    ]
                ]
            )
        else:
            # list of args = [block_no, prime char, addl_chars, exp_leading_prime]
            # [reason_msg, end_time, new_block or list of args]
            reactor_inst.callLater(
                abs(int(time_to_end_of_competition-time.time())),  # the delay
                lambda: q_for_block_validator.put(
                    [
                        reason_msg,
                        time.time() + (pause_time/2),  # end time
                        [
                            new_block_no,
                            block_argument[2],
                            block_argument[-2],
                            block_argument[3],

                        ]
                    ]
                )
            )

    def proxy_node_new_block_chooser(self):
        # used a node that is a proxy node to choose a block. process sends signed bytes, signs valid blocks
        # process is run by the main proxy node process which deals with receiving and satisfying
        # valid assignment statements
        pass

    def handle_new_block(self, q_object_from_compete_process_to_mining, q_for_block_validator,
                         is_generating_block: multiprocessing.synchronize.Event,
                         has_received_new_block: multiprocessing.synchronize.Event,
                         is_not_in_process_of_creating_new_block: multiprocessing.synchronize.Event,
                         is_program_running: multiprocessing.synchronize.Event, pause_time=60):

        # todo: a queue object should wait for 5 random signed bytes in a beta version, for now not needed
        # todo: for now q object will wait for 7 seconds
        # todo: get transactions, misc messages, wallet hash state dicts
        # todo: receive any extra messages and add to appropriated dict before start time
        # todo: while generating block, allow for receiving of transactions/msgs for next competition

        start_time, len_of_competition, single_prime_char, exp_leading_prime, new_block_no, prev_hash = \
            None, None, None, None, None, None
        addl_chars = None
        tx_misc_wsh = None

        # None == has not generated block or Just finished generating
        # False == received a recent block and is waiting for start time, during will received random signed bytes
        # True means

        while is_program_running.is_set():
            try:
                rsp = q_object_from_compete_process_to_mining.get(timeout=0.25)
                print("received rsp in Handle new block")
            except Empty:
                if is_program_running.is_set() is False:
                    print("Program should end")
                pass
            else:

                if isinstance(rsp, str) and rsp in {'exit', 'quit'}:  # exit signal to stop program
                    print("Exiting From Mining Process")
                    break
                elif isinstance(rsp, list) and len(rsp) >= 2:

                    if rsp[0] == "bcb":  # new block! new arguments  ['bcb', block, class_holding tx_misc, wsh]

                        has_received_new_block.set()
                        start_time, len_of_competition, single_prime_char, exp_leading_prime, new_block_no,\
                        addl_chars, prev_hash = self.get_new_block_arguments(rsp=rsp, pause_time=pause_time)

                        tx_misc_wsh = rsp[2]

                        print(f"In Handle blocks, {start_time}, {time.time()}")

                    elif rsp[0] == 'f':  # rsp == ['m', msg_hash, [main_msg, sig], msg_fee]
                        try:
                            tx_misc_wsh.add_to_misc_msg(
                                msg_hash=rsp[1],
                                msg=rsp[2],
                                fees=rsp[3]
                            )
                        except AttributeError as e:  # tx_misc_wsh is still None
                            print(f"tx_misc_wsh is still none: {e}")

                    elif rsp[0] == "wsh":  # for wallet state hash
                        # todo: wallet hash state key is the wallet and a dict
                        # todo: this dict has keys {"w_hash": str, "start": int amount, "end": int amount, "act": set of hashes of activities found in block activity }
                        pass

                    elif rsp[0] == "bk0":  # sending genesis block, network just launched
                        start_time, len_of_competition, single_prime_char, exp_leading_prime, new_block_no, \
                        addl_chars, prev_hash = self.get_block_one_arguments()
                        tx_misc_wsh = rsp[2]
                        has_received_new_block.set()

                        print(f"In Handle blocks, {start_time}, {time.time()}")

                    elif rsp[0] == 'e':  # btt
                        pass

                    else:  # rsp SHOULD represent a transaction rsp == [tx_type, tx_hash, [main_msg, sig]]

                        tx_misc_wsh.add_to_txs(
                            type_of_tx=rsp[0],
                            tx_hash=rsp[1],
                            tx=rsp[2],
                            fees=rsp[2][0]['fee']  # rsp[2] = [main_msg, sig] in main_msg 'fee' key
                        )

            # todo: implement this later:
            # todo: if 5 random bytes already received changed to and (time.time() >= start_time or random_received => 5)
            try:
                if is_generating_block.is_set() is False and has_received_new_block.is_set() is True and time.time() >= start_time:

                    # set this to false
                    # at compete it is set to true, when a new block has been received
                    # used by exit process to determine when to exit, it waits for process not to be creating blocks
                    is_not_in_process_of_creating_new_block.clear()

                    print("in handle_new_block, Orses_Compete_Algo.py, Bout To Start Competing")

                    # generating block is and instance of multiprocessing.Event()
                    is_generating_block.set()

                    # ***** this is a blocking code  **** #
                    new_block = generate_regular_block(
                        exp_leading_prime=exp_leading_prime,
                        len_competiion=len_of_competition,
                        single_prime_char=single_prime_char,
                        wsh=tx_misc_wsh.wsh,
                        block_no=new_block_no,
                        fees=tx_misc_wsh.fees,
                        combined_list=tx_misc_wsh.combined_list_of_hashes,
                        admin_inst=self.admin_inst,
                        primary_sig_wallet=self.reward_wallet,
                        addl_chars=addl_chars,
                        no_of_txs=tx_misc_wsh.number_of_transactions,
                        no_of_asgns=tx_misc_wsh.number_of_assignment_statements,
                        prev_hash=prev_hash,
                        is_program_running=is_program_running
                    )

                    # once done clear event object (becomes false) to notify compete_process
                    is_generating_block.clear()
                    has_received_new_block.clear()

                    # todo: when new block is created, send block to blockchainPropagatorInitiator process
                    # todo: this is done by sending using validator to blockchain queue ie q_for_block_validator

                    print(f"just created block: {new_block}, is generating block: {is_generating_block.is_set()}")

                    reason_msg = "nb" if new_block_no > 1 else "nb1"

                    # how long the time to receive blocks from other nodes should last
                    end_time = time.time() + (pause_time/2)

                    # To account for the fact that there might not be a valid hash
                    # if not a valid has, then block_hash will be None
                    if new_block["bh"]["block_hash"]:
                        # this goes to block initiator method process of BlockchainPropagator
                        end_time = time.time() + (pause_time/2)
                        q_for_block_validator.put([reason_msg, end_time, new_block])
                    else:

                        # todo: send list similar to non_compete process, when valid hash not found
                        # list of args = [block_no, prime char, addl_chars, exp_leading_prime]
                        # [reason_msg, end_time, new_block or list of args]

                        # set to true, if no hash was found, no need to wait if trying to exit.
                        # because there is no likely hood a monetary loss
                        is_not_in_process_of_creating_new_block.set()

                        q_for_block_validator.put(
                            [
                                "new_round",  # reason message
                                time.time() + (pause_time/2),  # end time
                                [
                                    new_block_no,
                                    single_prime_char,
                                    addl_chars,
                                    exp_leading_prime
                                ],


                            ]
                        )

            except TypeError as e:
                print(f"in Orses Compete error: {e}")
                continue

    def compete(
            self,
            q_for_compete: (multiprocessing.queues.Queue, queue.Queue),
            q_object_from_compete_process_to_mining: (multiprocessing.queues.Queue, queue.Queue),
            is_generating_block: multiprocessing.synchronize.Event,
            has_received_new_block: multiprocessing.synchronize.Event,
            is_not_in_process_of_creating_new_block: multiprocessing.synchronize.Event
    ):

        print(f"in Orses_compete_alog, Started Compete Process For admin: {self.admin_inst.admin_name}")
        recent_blk = q_for_compete.get()
        print(f"in Orses_compete_Algo, recent block:\n{recent_blk} admin: {self.admin_inst.admin_name}")

        reason_dict = dict()
        reason_dict['b'] = "ttx"
        reason_dict['c'] = "rsv_req"
        reason_dict['d'] = "rvk_req"
        reason_dict['f'] = "misc_msg"
        reason_dict['e'] = 'btt'


        if "bh" in recent_blk and recent_blk["bh"]:
            recent_block_no = int(recent_blk['bh']["block_no"], 16)
        else:
            return

        # instantiate class with existing txs, misc_msg and wsh. this is passed to self.handle_new_block()
        tx_misc_wsh = TxMiscWsh(
            txs=self.create_empty_tx_dict(),
            fees=0
        )

        # if genesis block is most recent and network was just launched then run this
        if self.just_launched and recent_block_no == 0:
            print(f"in {__file__}: Just launched so should be mining")
            q_object_from_compete_process_to_mining.put(['bk0', recent_blk, tx_misc_wsh])
        else:
            print(f"Not mining {recent_blk}, {recent_block_no}")

        msg_count = 0
        while self.is_program_running.is_set():
            rsp = q_for_compete.get()  # [reason letter, main tx dict OR main block dict]

            if self.is_program_running.is_set():
                msg_count += 1

                print(f"in Orses_compete, msg sent, msg count is {msg_count}: {rsp}")

                # rsp should be dictionary of transaction ie
                if isinstance(rsp, str) and rsp in {"exit", "quit"}:
                    q_object_from_compete_process_to_mining.put(rsp)
                    if is_generating_block:
                        print("Currently Generating Block. Program Will End After")
                    break

                elif rsp[0] == 'bcb':  # rsp is a block  bcb == blockchain block, rsp = ['bcb', block]
                    received_block_no = int(rsp[1]['bh']["block_no"], 16)
                    try:
                        print(f"received block no {received_block_no}, recent block +1 = {recent_block_no+1}")
                        assert received_block_no == recent_block_no+1
                    except AssertionError as e:
                        print(f'Assertion_error in compete(), Orses_compete_algo.py {e}')
                        break

                    recent_block_no = received_block_no

                    # add previous tx_misc_wsh
                    rsp.append(tx_misc_wsh)  # rsp == ['bcb', block, tx_misc_wsh]


                    # this is set to True, if exit process waiting for when not creating block to exit
                    is_not_in_process_of_creating_new_block.set()

                    #  has_received_new_block is set to true in mining process
                    q_object_from_compete_process_to_mining.put(rsp)

                    # instantiate a new  tx_misc_wsh
                    tx_misc_wsh = TxMiscWsh(
                        txs=self.create_empty_tx_dict(),
                        fees=0
                    )

                else:
                    if rsp[0] == "a":  # assignment statements are not included directly

                        print(f"received an assignment statement in compete, SHOULD NOT RECEIVE IN COMPETE\n{rsp}")
                        pass

                    elif rsp[0] == "f":  # misc messages

                        main_msg = rsp[1]["misc_msg"]
                        sig = rsp[1]['sig']
                        msg_hash = rsp[1]["msg_hash"]
                        msg_fee = main_msg['fee']

                        # if new block has been received but next block not being generated,
                        if has_received_new_block.is_set() is True and is_generating_block.is_set() is False:

                            # this goes to process being run self.handle_new_block Competitor method
                            q_object_from_compete_process_to_mining.put(['m', msg_hash, [main_msg, sig], msg_fee])

                        else:
                            tx_misc_wsh.add_to_misc_msg(
                                msg_hash=msg_hash,
                                msg=[main_msg, sig],
                                fees=msg_fee
                            )

                    else:  # transaction message
                        # todo: when checking transaction messages, check for fees

                        try:
                            # rsp[0] either b,c,d
                            # tx_dict_key either 'ttx', 'rsv_req' or 'rvk_req'
                            tx_dict_key = reason_dict.get(rsp[0], None)
                            if tx_dict_key:
                                main_msg = rsp[1][tx_dict_key]
                                sig = rsp[1]['sig']
                                tx_hash = rsp[1]["tx_hash"]

                                if has_received_new_block.is_set() is True and is_generating_block.is_set() is False:

                                    # print("is here 111")
                                    q_object_from_compete_process_to_mining.put(
                                        [tx_dict_key, tx_hash, [main_msg, sig]]
                                    )
                                else:

                                    tx_misc_wsh.add_to_txs(
                                        type_of_tx=tx_dict_key,
                                        tx_hash=tx_hash,
                                        tx=[main_msg, sig],
                                        fees=main_msg['fee']
                                    )
                        except KeyError as e:
                            print(f"In Orses_compete_algo: compete(), Key Error: {e},\nmsg: {rsp}\n")
                            continue

                        print(f"In Orses_Compete_Algo.py, this is tx_misc_wsh {vars(tx_misc_wsh)}")

        print("in Orses_Compete_Algo: Compete, process done")


if __name__ == '__main__':

    genesis_block = generate_genesis_block(should_save=True)

    print(genesis_block)


    print("\n\n")
    for x, y in genesis_block.items():
        print(x, ": ", y)