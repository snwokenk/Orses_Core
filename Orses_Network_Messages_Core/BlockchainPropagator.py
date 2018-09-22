"""
used to propagate messages about the blockchain. This includes:
1. new blocks
    send new blocks
    receive new blocks
    request for blocks (if restarting a node)
2. Validate blocks
    new blocks are passed through the Block Validator
    new blocks from competitors are passed through a winner validator, which stores blocks from competitors and
    determines the winner, the winner is then chosen based on the rules. if a node is a proxy for a blockchain-Connected
    wallet, it broadcasts to the network the block which will be used by the wallet,
2. New competitor
    new competitors are stored on the blockchain through a new competitor message. the msg_hash, client id,
    timestamp, pubkey and ip address are stored in this message. other competitors are able to get these information an

3. average timestamp

"""

"""
initial setup runs 
initial_setup runs first and request for blocks from a node
Once known_block is updated to be current, then convo_manager and convo initiator starts running
also, message propagator and initiator will also wait for initial setup

"""

"""
current messages defined:
1: message to find out the highest block number known/message to send highest block number known when requested

2: message to request for new blocks, if not up to date, message to send new blocks requested

3. to define: message_to_propagate validated blocks, message to receive blocks being propagated and validating it
"""

import json, multiprocessing, time
from multiprocessing import queues
from twisted.internet import threads
from queue import Empty
from Orses_Competitor_Core.CompetitorDataLoading import BlockChainData
from Orses_Validator_Core.NonNewBlockValidator import NonNewBlockValidator
from Orses_Validator_Core.NewBlockOneValidator import NewBlockOneValidator
from Orses_Validator_Core.NewBlockValidator import NewBlockValidator
from Orses_Competitor_Core.CompetitionHelperFunctions import get_prime_char, get_prime_char_for_block_one, \
    get_addl_chars_exp_leading, get_addl_chars_exp_leading_block_one


from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator



bk_validator_dict = dict()
bk_validator_dict["req_block"] = NonNewBlockValidator  # validator for non new blocks
bk_validator_dict["nb"] = NewBlockValidator
bk_validator_dict["nb1"] = NewBlockOneValidator


blockchain_msg_reasons = {
    "knw_blk",  # request most recent block
    "req_block",
    "pb", # propagated block
    "nb",  # a newly created block
    "nb1",
    "bc" # block choice
}


class BlockChainPropagator:
    def __init__(self, mempool, q_object_connected_to_block_validator, q_object_to_competing_process,
                 q_for_bk_propagate, q_object_between_initial_setup_propagators,reactor_instance,
                 admin_instance,  is_program_running):
        # initiate Blockchain Data folder if not already created. If create_genesis_only is True, then
        BlockChainData(admin_instance, create_genesis_only=False)

        # set mempool shared with networkPropagtor
        self.mempool = mempool

        self.admin_instance = admin_instance

        # ***multiprocessing.Queue objects used to communicated between threads and processes***


        # this is used by validator to pass block to  convo initiator for further propagation
        # OR by compete process to pass locally newly created block to convo initiator for propagation and
        # launching of block winner chosing process
        self.q_object_connected_to_block_validator = q_object_connected_to_block_validator
        self.q_object_compete = q_object_to_competing_process
        self.q_for_bk_propagate = q_for_bk_propagate
        self.q_object_between_initial_setup_propagators = q_object_between_initial_setup_propagators
        self.q_object_to_receive_from_messages_initial_setup = multiprocessing.Queue()
        self.q_object_for_winning_block_process = multiprocessing.Queue()

        # goes to run_block_winner_chooser_process(),
        # and passed to a validator when a newly created block is meant to be sent there
        # this is used in the process of block competition and creation
        self.q_object_from_block_validator_for_newly_created_blocks = multiprocessing.Queue()

        # ***reactor from start_node.py passed as a parameter***
        self.reactor_instance = reactor_instance

        # ***dictionaries used for communication between nodes and block propagation***
        self.convo_dict = dict()
        # self.convo_id = 0
        self.connected_protocols_dict = dict()
        self.connected_protocols_dict_of_pubkey = dict()

        # This is used by initial setup BUT
        # It is updated every time a new block is accepted by node
        self.locally_known_block = BlockChainData.get_current_known_block(admin_instance)[0]

        # used by initial setup
        self.has_current_block = False

        # used by initial setup
        self.protocol_with_most_recent_block = None  # [protocol id, convo_id, block_no known]

        # ***attributes used in block creation and consensus formation***
        self.dict_of_potential_blocks = {
            "prev": dict(),
            "full_hash": dict()
        }

        self.dict_of_potential_indirect_blocks = dict()

        # this dictionary stores block hash which was endorsed by another node but was not received on time
        # A block from here is only used, when it turns out the it received a plurality (not necessarily a majority)
        # of endorsements
        self.dict_of_hash_not_rcv_directly = dict()


        # dict storing endorsements for use in determining the winning block
        # hashes stored here were received on time.
        # if a hash is endorsed but not received on time, it is stored in self.dict_of_hash_not_rcv_directly
        # ie {"SHA256 hash": number of endorsements (later will be endorsements based on tokens)
        self.dict_of_endorsed_hash = dict()

        # same as dict of endorsed but for hashes not received on time but endorsed
        self.dict_of_indirect_endorsed_hash = dict()

        # multiprocessing.Event that tells when accepting blocks then when accepting block choice
        self.is_accepting_blocks = multiprocessing.Event()
        self.is_accepting_block_choices = multiprocessing.Event()

        # dict of deferred convo key is convo reason, value is list index 0 as message obj method index 1 as msg
        # ie {'bc': [[SendBlockWinnerChoice_instance.listen_deffered, msg received from peer], [...]] }
        self.dict_of_deferred_convo = dict()

        # attribute storing winning block. This is attribute stores a block when block choice winner is being determined
        # and become None when it's not
        self.winning_block_choice = None


        # multiprocessing.Event object which keeps track of if program is running or Not
        # (if user has requested program to exit or quit
        self.is_program_running = is_program_running


    def add_protocol(self, protocol):

        # adds connected protocol, key as protocol_id,  value: list [protocol object, dict(speaker, hearer keys), number of convo(goes to 999 and resets)]
        self.connected_protocols_dict.update({protocol.proto_id: [protocol, 0]})
        self.convo_dict[protocol.proto_id] = dict()
        self.connected_protocols_dict_of_pubkey[protocol.proto_id] = None

    def remove_protocol(self, protocol):

        del self.connected_protocols_dict[protocol.proto_id]
        del self.convo_dict[protocol.proto_id]
        del self.connected_protocols_dict_of_pubkey[protocol.proto_id]

    def get_pubkey_of_node_with_protocol(self, protocol):
        try:
            return self.connected_protocols_dict_of_pubkey[protocol.proto_id]
        except KeyError:
            print(f"In get_pubkey_of_node_with_protocol, blockchainPropagator, protocol id not in dict. BUT SHOULD BE")
            return None


    def initial_setup(self, recursive_count=0, no_connected_peers_ok=True):
        """
        Meant to run before Blockchain Propagator, Network Propagator and Compete processes
        :param recursive_count:
        :param no_connected_peers_ok: if have no connected peer is ok, should be true for testing.
        :return:
        """

        def first_initial_setup(recursive_count=0, prop_inst=self, no_connected_peers_ok=True):

            protocol_list = set(self.connected_protocols_dict)

            # check to see if connected to any node, if not check if it is ok to not be connected to a node and return
            if not protocol_list and no_connected_peers_ok is True:  # no connected protocols
                send_response_to_other_threads(
                    has_setup=True,
                    prop_inst=prop_inst,
                    recent_block=BlockChainData.get_current_known_block(prop_inst.admin_instance)[1]
                )
                return
            elif not protocol_list and no_connected_peers_ok is False:
                print(f"in {__file__}: No connection, admin {self.admin_instance.admin_name}")
                send_response_to_other_threads(has_setup=False, prop_inst=prop_inst)
                return

            if recursive_count >= 3:
                return [False, False]  # was not able to update and did not send

            # first get most recent block [-1, -1] will get from genesis to recent
            # else [oldest block to get, newest block to get. to get most recent [oldest block to get, -1]
            list_of_blocks_to_get = [-1, -1] if self.locally_known_block is None else [self.locally_known_block+1, -1]


            # get most recent block known by connected nodes. Will only get an int
            # uses separate thread for each protocol message

            msg_sender_creator_for_multiple(
                set_of_excluded_protocol_id={},
                msg=["knw_blk"],
                protocol_list=protocol_list,
                propagator_inst=self
            )

            # to move forward information about most recent block must be received.
            # A good way of doing this with twisted is using deferred

            response_thread = threads.deferToThread(
                wait_for_most_recent_block_response,
                prop_inst=prop_inst,
                protocol_list=protocol_list
            )

            response_thread.addCallback(
                lambda protocol_with_recent_block:
                prop_inst.reactor_instance.callInThread(
                    second_initial_setup,
                    protocol_with_most_recent_block=protocol_with_recent_block,
                    list_of_blocks_to_get=list_of_blocks_to_get,
                    prop_inst=prop_inst
                )
            )
            response_thread.addErrback(lambda x: print(f"in {__file__}: in deferToThread:\n{x}\n"))

        def second_initial_setup(protocol_with_most_recent_block, list_of_blocks_to_get, prop_inst):

            """
            request for actual blocks from node with the most recent block
            :param protocol_with_most_recent_block:
            :return:
            """

            if isinstance(protocol_with_most_recent_block, list) and len(protocol_with_most_recent_block) == 3 and \
                    prop_inst.locally_known_block < protocol_with_most_recent_block[2]:
                print("reached here, in second inital, create req_block")
                msg_sender_creator_for_one(
                    protocol_id=protocol_with_most_recent_block[0],  # [protocol id, convo_id, block_no known]
                    msg=["req_block"],
                    propagator_inst=prop_inst,
                    blocks_to_receive=list_of_blocks_to_get,
                    expected_recent_block=protocol_with_most_recent_block[2]
                )
            elif prop_inst.locally_known_block >= protocol_with_most_recent_block[2]:
                send_response_to_other_threads(
                    has_setup=True,
                    prop_inst=prop_inst,
                    recent_block=BlockChainData.get_current_known_block(prop_inst.admin_instance)[1])
            else:
                send_response_to_other_threads(has_setup=False, prop_inst=prop_inst)

            # wait for blocks to download, then end
            response_thread = threads.deferToThread(
                wait_for_blocks_to_be_received,
                prop_inst=prop_inst,
            )
            response_thread.addCallback(
                lambda is_setup:
                send_response_to_other_threads(
                    has_setup=is_setup,
                    prop_inst=prop_inst,
                    recent_block=BlockChainData.get_current_known_block(prop_inst.admin_instance)[1] if is_setup is True else None

                )
            )
            response_thread.addErrback(lambda err: print("Error happened in second initial defferea", err))

        def wait_for_blocks_to_be_received(prop_inst: BlockChainPropagator):

            while prop_inst.has_current_block is False:
                try:
                    rsp = prop_inst.q_for_bk_propagate.get(timeout=10)

                    print(f"in {__file__}: wait for blocks: rsp: {rsp}")
                except Empty:
                    break
                else:
                    protocol_id = rsp[0]
                    msg = rsp[1]
                    local_convo_id = msg[1][0]
                    prop_inst.convo_dict[protocol_id][local_convo_id].listen(msg)

            if prop_inst.has_current_block is True:
                return True
            elif prop_inst.has_current_block is None:
                print(f"in {__file__}: in wait for blocks:\nDid not receive all blocks from peer")

            return False

        def wait_for_most_recent_block_response(prop_inst: BlockChainPropagator, protocol_list, count=0) -> list:

            """
            used to wait for responses from peer nodes.
            These responses tells us about the most recent block known.
            An ideal discrepancy between responses should be 1 block.
            meaning. if chain is on block 100, most blocks should know about block 100 or at least block 99
            :param prop_inst: propagator instance(blockchainpropagator
            :param protocol_list: (set containing protocols in which message was sent)
            :param count:
            :return:
            """

            while count < len(protocol_list):
                try:
                    rsp = prop_inst.q_for_bk_propagate.get(timeout=10)  # will timeout in 7 seconds
                except Empty:  # queue exception
                    print(
                        f"Timed out in initial_setup, blockchain propagator, admin : "
                        f"{prop_inst.admin_instance.admin_name}"
                    )
                    count += 1
                    continue
                else:
                    protocol_id = rsp[0]
                    msg = rsp[1]
                    local_convo_id = msg[1][0]  # convo_id for incoming msg [local convo id, other convo id]
                    count += 1 if rsp[0] in protocol_list else 0

                    prop_inst.reactor_instance.callFromThread(prop_inst.convo_dict[protocol_id][local_convo_id].listen, msg)

            # Must wait till prop_inst.protocol_with_most_recent_block is set, using Queue as signal
            count1 = 0
            while count1 < count:
                try:
                    prop_inst.q_object_to_receive_from_messages_initial_setup.get(timeout=7)
                except Empty:

                    print("in Break has broken")
                    break
                else:
                    count1+=1

            return prop_inst.protocol_with_most_recent_block

        def send_response_to_other_threads(has_setup: bool, prop_inst: BlockChainPropagator, recent_block=None) -> None:
            """
            Used to send signal for other processes to start
            :param has_setup:
            :param prop_inst:
            :param recent_block:
            :return:
            """
            for i in range(5):  # four other threads to start and 1 process to end, sends signal
                prop_inst.q_object_between_initial_setup_propagators.put(has_setup)

            if recent_block:
                self.mempool.update_mempool(winning_block=recent_block)
                if (prop_inst.admin_instance.isCompetitor is True and
                        isinstance(prop_inst.q_object_compete, multiprocessing.queues.Queue)):
                    prop_inst.q_object_compete.put(recent_block)

        # START INITiAL SETUP
        self.reactor_instance.callInThread(
            first_initial_setup
        )

    def run_propagator_convo_initiator(self) -> None:
        """
        used to initiate a block request, send validated blocks
        Process is only used to INITIATE convo, any replies go to the run_propagator_convo_manager thread
        :return:
        """

        initial_setup_done = self.q_object_between_initial_setup_propagators.get()  # returns bool

        if initial_setup_done is False:
            print("ending block initiator, Setup Not Able")
            return

        is_competing = self.q_object_compete is not None and self.admin_instance.isCompetitor is True

        try:

            while self.is_program_running.is_set():
                rsp = self.q_object_connected_to_block_validator.get()
                print(f"in blockchainPropagator Initiator, rsp: {rsp}")

                try:
                    if isinstance(rsp, str) and rsp in {'exit', 'quit'}:
                        raise KeyboardInterrupt

                    elif isinstance(rsp, list):
                        reason_msg = rsp[0]  # reason of message

                        if reason_msg in {"nb", "nb1"}:  # new block created locally nb1 block one created

                            # rsp == ["nb', end_time_for_winner chooser process, block]
                            # startup winner chooser process
                            # the data is received from handle_new_block of Orses_Compete_Algo.py
                            self.reactor_instance.callInThread(
                                self.run_block_winner_chooser_process,
                                block=rsp[-1],
                                end_time=rsp[1],
                            )

                            # send newly created blocks to other nodes
                            msg_sender_creator_for_multiple(
                                set_of_excluded_protocol_id={},
                                msg=rsp,
                                protocol_list=list(self.connected_protocols_dict),
                                propagator_inst=self

                            )
                        elif reason_msg == "new_round":  # if node is a non_competitor, this is sent
                            # rsp == ["nb', end_time_for_winner chooser process, block]
                            # startup winner chooser process
                            # the data is received from handle_new_block of Orses_Compete_Algo.py
                            self.reactor_instance.callInThread(
                                self.run_block_winner_chooser_process,
                                block=rsp[-1],
                                end_time=rsp[1],
                            )
                except KeyboardInterrupt:
                    print("ending convo initiator in BlockchainPropagator")
                    break
                except Exception as e:
                    print(f"\n-----\nError in {__file__}, in initiator\nMessage causing Error: {rsp}\n"
                          f"Exception raised: {e}")
                    continue

        except (KeyboardInterrupt, SystemExit):
            pass

    def run_propagator_convo_manager(self) -> None:

        initial_setup_done = self.q_object_between_initial_setup_propagators.get()  # returns bool

        print(f"Initial setup done , in blockchain propagator convo manager, {initial_setup_done}, "
              f"admin {self.admin_instance.admin_name}")
        if initial_setup_done is False:
            print("ending block manager, Setup Not Able")
            return
        reactor = self.reactor_instance
        try:
            while True:
                rsp = self.q_for_bk_propagate.get()  # [protocol_id, data_list],  data_list=['b', convo_id, etc]
                print("in convo manager, blockchainprop: message", rsp)

                try:
                    if isinstance(rsp, str) and rsp in {'exit', 'quit'}:
                        raise KeyboardInterrupt

                    elif isinstance(rsp, list) and len(rsp) == 2:

                        # protocol id
                        protocol_id = rsp[0]

                        # msg is python list = ['b', convo_id_list, msg], already json decoded in NetworkMessageSorter
                        msg = rsp[1]

                        # convo_id_list == [local convo id, other convo id]
                        local_convo_id = msg[1][0]

                        if local_convo_id is not None and local_convo_id in self.convo_dict[protocol_id]:

                            if self.convo_dict[protocol_id][local_convo_id].end_convo is not True:
                                self.reactor_instance.callInThread(
                                    self.convo_dict[protocol_id][local_convo_id].listen,
                                    msg=msg
                                )
                        elif local_convo_id is None:
                            self.reactor_instance.callInThread(
                                msg_receiver_creator,
                                protocol_id=protocol_id,
                                msg=msg,
                                propagator_inst=self,

                            )
                        else:
                            pass

                except KeyboardInterrupt:
                    print("ending convo manager in BlockchainPropagator")
                    break

                except Exception as e:  # log error and continue, avoid stopping reactor process cuz of error
                    # todo: implement error logging, when message received causes error. for now print error and msg
                    print(f"\n-----\nError in {__file__} in convo manager\nMessage causing Error: {rsp}\n"
                          f"Exception raised: {e}")
                    continue
        except (SystemExit, KeyboardInterrupt):
            reactor.stop()

        finally:
            # shutdown instructions go here
            pass

        print("In BlockchainPropagator.py convo manager ended")

    def run_block_winner_chooser_process(self, block: (dict, list), end_time: (int, float)) -> None:
        """
        A new instance of this function is run in a separate thread by the blockchainpropagator process
        Each new instance represents a new round, The aim of this process is to find the winning block based on the
        rules set forth. Once the block is found , it is returned along with the secondary signatories to use.

        Winning block hash is then sent to other nodes, who can then determine block with the most endorsements

        Blocks might be sent to other processes waiting for or needing current block info
        :param block: the first block received from the competition
        :param end_time: the time when a block is decided (also known as 7 second window
        :return:
        """
        # start accepting blocks
        self.is_accepting_blocks.set()

        if isinstance(block, dict):
            block_header = block["bh"]
            block_no = int(block_header["block_no"])
            block_before_recent_no = block_no - 2
            self.dict_of_potential_blocks["full_hash"][block_header["block_hash"]] = block
            self.dict_of_potential_blocks["prev"][block_header["block_hash"][-8:]] = block_header["block_hash"]

            # get the parameters used for competition
            if block_no == 1:
                prime_char = get_prime_char_for_block_one()
                exp_leading_prime, addl_chars = get_addl_chars_exp_leading_block_one()
            else:
                block_before_recent = BlockChainData.get_block(
                    admin_instance=self.admin_instance,
                    block_no=block_before_recent_no
                )

                block_before_recent_header = block_before_recent["bh"]

                prime_char = get_prime_char(block={}, block_header=block_before_recent_header)
                exp_leading_prime, addl_chars = get_addl_chars_exp_leading(block={}, block_header=block_before_recent_header)

            # check first block received and get score
            winning_score, winning_hash, determined_with_tiebreaker = choose_winning_hash_from_two(
                prime_char=prime_char,
                addl_chars=addl_chars,
                curr_winning_hash="",
                hash_of_new_block=block_header["block_hash"],
                exp_leading=exp_leading_prime,
                current_winning_score=0
            )
        else:
            # block is list [block_no, prime char, addl_chars, exp_leading_prime]
            block_no = block[0]
            block_before_recent_no = block_no - 2
            winning_score = 0
            prime_char = block[1]
            addl_chars = block[2]
            exp_leading_prime = block[3]
            winning_hash = ""

        while self.is_program_running.is_set() and time.time() <= end_time:
            try:
                # blocks are received from NewBlockValidator.
                # this function, is meant to determine the winning block from valid blocks received
                # it is not meant to validate a block, blocks should already be validated
                new_block = self.q_object_from_block_validator_for_newly_created_blocks.get(timeout=0.25)
            except Empty:
                continue
            else:

                print(f"new block {new_block} in admin {self.admin_instance.admin_name}")
                if isinstance(new_block, str) and new_block in {'exit', 'quit'}:
                    # rather than using usual break return so check_winning_block_from_network() does not exec
                    return

                new_block_header = new_block["bh"]

                self.dict_of_potential_blocks["full_hash"][new_block_header["block_hash"]] = block
                self.dict_of_potential_blocks["prev"][new_block_header["block_hash"][-8:]] = \
                    new_block_header["block_hash"]

                winning_score, winning_hash, determined_with_tiebreaker = choose_winning_hash_from_two(
                    prime_char=prime_char,
                    addl_chars=addl_chars,
                    curr_winning_hash=winning_hash,
                    hash_of_new_block=new_block_header["block_hash"],
                    exp_leading=exp_leading_prime,
                    current_winning_score=winning_score
                )

        # stop accepting blocks
        self.is_accepting_blocks.clear()

        self.check_winning_block_from_network(
            winning_hash=winning_hash,
            winning_score=winning_score,
            block_no=block_no
        )

    def check_winning_block_from_network(self,  winning_hash, block_no, winning_score):
        """
        This function will use the locally determined winning block and check for endorsements from proxy nodes.
        The block with endorsements representing the most tokens is used as the next block. (as long as it is valid)
        :return:
        """

        # start accepting block choices
        self.is_accepting_block_choices.set()

        winning_block = self.dict_of_potential_blocks["full_hash"][winning_hash]
        self.winning_block_choice = winning_block

        self.dict_of_endorsed_hash[winning_hash] = 1

        # variable will be used to compare total endorsements to all available endorsements
        total_endorsements = 0

        winning_block_header = winning_block['bh']

        # todo: for now use the absolute number of endorsements from nodes
        # todo: but once BCW logic is added, the winning node should be the block(which is valid)
        # todo: endorsed by proxy nodes REPRENSENTING THE LARGEST AMOUNT OF TOKENS RESERVED(WITH A TIME DISCOUNT)

        # send winning hash to others who have asked
        # this is done by checking the deferred dict of propagator inst
        deffered_list = self.dict_of_deferred_convo.pop('bc', [])  # this will delete 'bc' key. return [] if no 'bc'
        for list_of_deffered in deffered_list:
            # list_of_deffered = [SendBlockWinner.listen_deffered callable, msg of rsp]
            self.reactor_instance.callInThread(
                callable=list_of_deffered[0],
                msg=list_of_deffered[1],
                block_choice_prev=winning_block_header['block_hash'][-8:]
            )

        # once the deferred have been dealt with, send a request for block choice
        msg_sender_creator_for_multiple(
            set_of_excluded_protocol_id={},
            msg=["bc"],
            protocol_list=set(self.connected_protocols_dict),
            propagator_inst=self,
            q_object_to_winner_process=self.q_object_for_winning_block_process
        )

        # todo: check propagators deffered dict using "bc" as a key, any deferred convo should be continued with block choice provided

        # check for response
        no_of_protocols = len(self.connected_protocols_dict)
        len_of_check = time.time() + 20
        while self.is_program_running.is_set() and no_of_protocols > 0 and time.time() <= len_of_check:
            try:
                winning_hash_rsp = self.q_object_for_winning_block_process.get(timeout=0.2)
            except Empty:
                print(f"in check_winning_network {time.time()} - len_to_wait {len_of_check}")
                pass
            else:
                if isinstance(winning_hash_rsp, str) and winning_hash_rsp in {'exit', 'quit'}:
                    break

                elif isinstance(winning_hash_rsp, list):  # [winning hash, signature]
                    # todo: log and save signature and hashes
                    # todo: use absolute number of endorsements. Later endorsements will be based on tokens represented
                    block_hash = winning_hash_rsp[0]
                    signature = winning_hash_rsp[1]
                    if block_hash in self.dict_of_potential_blocks["full_hash"]:
                        try:
                            self.dict_of_endorsed_hash[winning_hash_rsp[0]] += 1
                        except KeyError:
                            self.dict_of_endorsed_hash[winning_hash_rsp[0]] = 1
                    else:
                        # hash is endorsed by other non_malicious node but was not received by this node
                        try:
                            self.dict_of_indirect_endorsed_hash[winning_hash_rsp[0]] += 1
                        except KeyError:
                            self.dict_of_indirect_endorsed_hash[winning_hash_rsp[0]] = 1

                    total_endorsements += 1

        # stop accepting block choices
        self.is_accepting_block_choices.clear()
        self.winning_block_choice = None
        list_of_direct_hash = sorted(self.dict_of_endorsed_hash, key=lambda x: self.dict_of_endorsed_hash[x])
        list_of_indirect_hash = sorted(self.dict_of_indirect_endorsed_hash, key=lambda x: self.dict_of_indirect_endorsed_hash[x])
        # decide winning block
        direct_winner = list_of_direct_hash[-1]
        if list_of_indirect_hash:
            indirect_winner = list_of_indirect_hash[-1]
            block_winner_hash = direct_winner if self.dict_of_endorsed_hash[direct_winner] >= self.dict_of_indirect_endorsed_hash[indirect_winner] else indirect_winner
        else:
            block_winner_hash = direct_winner

        # get block winner from potential blocks (direct), if not then from indirect

        # todo: get block from indirect if not in dict_of_potential_blocks
        block_of_winner = self.dict_of_potential_blocks["full_hash"].get(block_winner_hash, None)

        counter = -1
        while self.is_program_running.is_set():

            if block_of_winner:
                self.locally_known_block = block_of_winner

                # todo: update mempool to move transactions from unconfirmed to confirmed that were included in block
                self.mempool.update_mempool(winning_block=self.locally_known_block)

                if self.admin_instance.currenty_competing is True:
                    self.q_object_compete.put(['bcb', self.locally_known_block])
                elif self.admin_instance.is_validator is True:
                    # use this to re lauch noncompete process
                    # todo: competitor.non_compete_process should pass itself allow with block data
                    pass

                break
            elif block_winner_hash in self.dict_of_potential_indirect_blocks:

                # validate block received after
                # blocks received indirectly aren't validated until after
                validator = NewBlockValidator(
                    admin_inst=self.admin_instance,
                    block=self.dict_of_potential_indirect_blocks[block_winner_hash],
                    block_propagator_inst=self

                ) if block_no > 1 else\
                NewBlockOneValidator(
                    admin_inst=self.admin_instance,
                    block=self.dict_of_potential_indirect_blocks[block_winner_hash],
                    block_propagator_inst=self
                )

                is_validated = validator.validate()

                if is_validated:
                    block_of_winner = self.dict_of_potential_indirect_blocks[block_winner_hash]
                    self.locally_known_block = block_of_winner
                    self.mempool.update_mempool(winning_block=self.locally_known_block)
                    if self.admin_instance.currenty_competing is True:
                        self.q_object_compete.put(
                            ['bcb', self.locally_known_block])
                    elif self.admin_instance.is_validator is True:
                        pass
                    break
                else:  # indirect block isn't valid
                    counter -= 1

                    # choose a new winner from main direct winner and second indirect winner
                    # because first indirect winner's block is invalid
                    if len(list_of_indirect_hash) >= abs(counter):
                        block_winner_hash = direct_winner if self.dict_of_endorsed_hash[direct_winner] > \
                        self.dict_of_indirect_endorsed_hash[list_of_indirect_hash[counter]] else list_of_indirect_hash[counter]
                        block_of_winner = self.dict_of_potential_blocks.get(block_winner_hash, None)
                        continue
                    else:
                        # no more blocks from indirectly received so. The winning block from directly received
                        # and validated blocks is chosen
                        block_of_winner = self.dict_of_potential_blocks[direct_winner]
                        self.locally_known_block = block_of_winner
                        self.mempool.update_mempool(winning_block=self.locally_known_block)
                        if self.admin_instance.currenty_competing is True:
                            self.q_object_compete.put(['bcb', self.locally_known_block])
                        elif self.admin_instance.is_validator is True:
                            pass
                        break
            else:
                print(f"in check_winning_block_from_network, BlockchainPropagator. Error, no block winner")

        if block_of_winner and self.is_program_running.is_set():

            BlockChainData.save_a_newly_created_block(
                block_no=block_no,
                block=block_of_winner,
                admin_instance=self.admin_instance
            )


def choose_winning_hash_from_two(prime_char: str, addl_chars: str, curr_winning_hash: str, hash_of_new_block: str,
                                 exp_leading: int, current_winning_score=0) -> list:  # return a list
    """
    :param prime_char: hex character that must be leading in a hash
    :param addl_chars: addl characters (if any) used after the leading hash
    :param curr_winning_hash: current hash of winning block
    :param hash_of_new_block: hash of new block to determine
    :param exp_leading: expected amount of leading prime char in a hash
    :param current_winning_score: winning score of winning hash
    :return: returns  list : [winning score, winning hash, True/False if winner determined using tiebreaker]
    """
    initial_prime_char = exp_leading

    temp_score = 0
    temp_extra = 0
    ini_pr_ch = initial_prime_char
    leading_prime = True
    for j in hash_of_new_block[exp_leading:]:  # this is from eligible hashes so start from exp leading index
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
    if temp_score > current_winning_score:
        current_winning_score = temp_score
        curr_winning_hash = hash_of_new_block
        determined_with_tiebreaker = False
    elif temp_score == current_winning_score:
        # todo: institute tie breaker according to whitepaper and protocols written
        determined_with_tiebreaker = True
    else:
        determined_with_tiebreaker = False

    return [current_winning_score, curr_winning_hash, determined_with_tiebreaker]


def msg_sender_creator(protocol_id, msg, propagator_inst: BlockChainPropagator, **kwargs):

    reason_msg = msg[0]  # [reason, main message(if applicable)]

    if reason_msg in blockchain_msg_reasons:

        convo_id = get_convo_id(protocol_id=protocol_id, propagator_inst=propagator_inst)

        if reason_msg == "knw_blk":
            msg_snd = RequestMostRecentBlockKnown(
                protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
                convo_id=convo_id,
                protocol_id=protocol_id,
                blockchainPropagatorInstance=propagator_inst,
                q_from_prop_to_msg=propagator_inst.q_object_to_receive_from_messages_initial_setup
            )
        elif reason_msg in {"nb", "nb1"}:
            msg_snd = SendNewlyCreatedBlock(
                protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
                convo_id=convo_id,
                msg=msg,
                propagator_inst=propagator_inst

            )
        elif reason_msg == "req_block":
            if "blocks_to_receive" in kwargs and "expected_recent_block" in kwargs:

                msg_snd = RequestNewBlock(
                    blocks_to_receive=kwargs["blocks_to_receive"],
                    protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
                    convo_id=convo_id,
                    blockchainPropagatorInstance=propagator_inst,
                    expected_recent_block=kwargs["expected_recent_block"]
                )
            else:
                msg_snd = None
        elif reason_msg == "bc": # block choice
            local_block_winner_prev = kwargs.get("local_block_winner_choice_prev", None)
            q_object = kwargs.get("q_object_to_winner_process", None)
            if isinstance(q_object, multiprocessing.queues.Queue):
                msg_snd = RequestBlockWinnerChoice(
                    protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
                    convo_id=convo_id,
                    propagator_inst=propagator_inst,
                    local_block_winner_choice_prev=local_block_winner_prev,
                    q_object=q_object
                )
            else:
                print(f"troubleshoot, q_object None is msg_sender_creator, blockchainpropagator, reason='bc'")
                msg_snd = None
        else:
            msg_snd = None

        if msg_snd:
            propagator_inst.convo_dict[protocol_id][convo_id] = msg_snd
            msg_snd.speak()


def msg_sender_creator_for_one(protocol_id, msg, propagator_inst: BlockChainPropagator, **kwargs):

    propagator_inst.reactor_instance.callInThread(
        msg_sender_creator,
        protocol_id=protocol_id,
        msg=msg,
        propagator_inst=propagator_inst,
        **kwargs
    )


def msg_sender_creator_for_multiple(set_of_excluded_protocol_id, msg, protocol_list, propagator_inst: BlockChainPropagator, **kwargs):

    # todo: this can be used to make an ordered request, in which multiple protocols send different parts of data

    for protocol_id in protocol_list:
        if protocol_id not in set_of_excluded_protocol_id:

            msg_sender_creator_for_one(
                protocol_id=protocol_id,
                msg=msg,
                propagator_inst=propagator_inst,
                **kwargs
            )


def msg_receiver_creator(protocol_id, msg, propagator_inst: BlockChainPropagator):
    """
    msg = ['b', convo_id_list, main_msg]
    :param protocol_id:
    :param msg:
    :param propagator_inst:
    :return:
    """

    convo_id = msg[1]
    reason_msg = msg[2]

    convo_id[0] = get_convo_id(protocol_id=protocol_id, propagator_inst=propagator_inst)
    kw_dict = dict()
    prop_receiver = get_message_receiver(
        reason_msg=reason_msg,
        convo_id=convo_id,
        protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
        protocol_id=protocol_id,
        propagator_inst=propagator_inst
    )

    propagator_inst.convo_dict[protocol_id].update({convo_id[0]: prop_receiver})
    prop_receiver.listen(msg=msg)

    if isinstance(reason_msg, list):
        pass
    else:
        if reason_msg == "nb":  # new block reason
            pass  # store hash in message_from_other_veri_node_dict to keep track of where it was received


def notify_of_ended_message(protocol, convo_id: list, propagator_instance: BlockChainPropagator):
    """
    used to notify other node of ended message, if it tries to communicate with ended message
    :param protocol: connected protocol of other node
    :param convo_id: convo id list [local convo id, other convo id] this is switched
    :param propagator_instance: instance of NetworkPropagator class
    :return:
    """
    convo_id[0], convo_id[1] = convo_id[1], convo_id[0]  # switch convo id to [other convo id, local convo id]
    msg = json.dumps(["n", convo_id, 'end']).encode()

    # call this from the reactor thread o be thread safe
    propagator_instance.reactor_instance.callFromThread(protocol.transport.write, msg)


def get_message_receiver(reason_msg, convo_id, protocol, protocol_id, propagator_inst, *args, **kwargs):
    """
    Used to return to proper Message receiver class for reason msg
    :param reason_msg:
    :param convo_id:
    :param protocol:
    :param protocol_id:
    :param propagator_inst:
    :param args:
    :param kwargs:
    :return:
    """


    # a request most recent block known message/
    # receiver is to send most recent block known (int block number is sent NOT whole block)

    if reason_msg == "knw_blk":
        msg_rcv = SendMostRecentBlockKnown(
            protocol=protocol,
            convo_id=convo_id,
            propagator_inst = propagator_inst
        )
    # request for new blocks
    # receiver is SendNewBlockRequested, this sends actual blocks requested
    elif isinstance(reason_msg, list):
        if reason_msg[0] == "req_block":  # todo: have a way of safely sending blocks without loss of data
            msg_rcv = SendNewBlocksRequested(
                protocol=protocol,
                convo_id=convo_id,
                blockchainPropagatorInstance=propagator_inst
            )

        # new creator blog being propagated from peer
        # reason_msg == ["nb", block]
        elif reason_msg[0] in {"nb", "nb1"}:

            msg_rcv = ReceiveNewlyCreatedBlock(
                protocol=protocol,
                convo_id=convo_id,
                propagator_inst=propagator_inst,
                is_block_one=False if reason_msg[0] == "nb" else True
            )
        elif reason_msg[0] == "bc":  # block choice

            msg_rcv = SendBlockWinnerChoice(
                protocol=protocol,
                convo_id=convo_id,
                propagator_inst=propagator_inst,
                local_block_winner_choice_full_block=propagator_inst.winning_block_choice,
            )

        else:
            msg_rcv = DefaultMessageReceiver(
                protocol=protocol,
                convo_id=convo_id,
                propagator_inst=propagator_inst
            )

    else:
        print(f"in {__file__}: get_message_receiver, reason msg {reason_msg}")
        msg_rcv = None

    if msg_rcv is None:

        DefaultMessageReceiver(
            protocol=protocol,
            convo_id=convo_id,
            propagator_inst=propagator_inst
        )

    return msg_rcv


def get_convo_id(protocol_id, propagator_inst: BlockChainPropagator):

    while True:  # gets a convo id that is not in use
        convo_id = propagator_inst.connected_protocols_dict[protocol_id][1]
        if convo_id in propagator_inst.convo_dict[protocol_id] and propagator_inst.convo_dict[protocol_id][convo_id].end_convo is False:
            propagator_inst.connected_protocols_dict[protocol_id][1] += 1
            continue
        elif convo_id >= 20000:
            propagator_inst.connected_protocols_dict[protocol_id][1] = 0
            continue
        propagator_inst.connected_protocols_dict[protocol_id][1] += 1
        return convo_id


# *** base message sender class ***
class BlockChainMessageSender:
    def __init__(self, protocol, convo_id, propagator_inst):
        """

        :param protocol: the protocol class representing a connection, use as self.protocol.transport.write()
        :param convo_id: the convo id used by propagator to keep track of message
        """
        self.propagator_inst = propagator_inst
        self.last_msg = 'end'
        self.verified_msg = 'ver'
        self.prop_type = 'b'
        self.messages_heard = set()
        self.end_convo = False
        self.protocol = protocol
        self.local_convo_id = convo_id
        self.other_convo_id = None  # in listen() get other convo_id
        self.convo_id = [self.other_convo_id, self.local_convo_id]
        self.sent_first_msg = False
        self.need_admin_pubkey_msg = 'apk'
        self.need_pubkey_msg = 'wpk'

    def speak(self):
        """ override """

    def listen(self, msg):
        """override"""

    def speaker(self, msg):

        self.propagator_inst.reactor_instance.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, self.convo_id, msg]).encode()
        )


# *** base  message receiver class ***
class BlockChainMessageReceiver:
    def __init__(self, protocol, convo_id: list, propagator_inst: BlockChainPropagator):
        """

        :param protocol: the protocol class representing a connection, use as self.protocol.transport.write()
        :param convo_id: the convo id used by propagator to keep track of message
        """
        self.last_msg = 'end'
        self.verified_msg = 'ver'
        self.prop_type = 'b'
        self.need_pubkey = 'wpk'
        self.need_admin_pubkey = 'apk'
        self.messages_heard = set()
        self.protocol = protocol
        self.local_convo_id = convo_id[0]
        self.other_convo_id = convo_id[1]  # when receiving from other, the other's local id is added here
        self.convo_id = [self.other_convo_id, self.local_convo_id]
        self.end_convo = False
        self.received_first_msg = False
        self.propagator_inst = propagator_inst
        self.last_known_block = propagator_inst.locally_known_block

    def speak(self):
        """ override """

    def listen(self, msg):
        """override"""

    def speaker(self, msg):

        # speaker will always call transport.write from main thread
        self.propagator_inst.reactor_instance.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, self.convo_id, msg]).encode()
        )


class DefaultMessageReceiver(BlockChainMessageReceiver):
    """
    Use to send an end message,
    this is done when reason msg from peer node does not have a corresponding message receiver class
    """

    def listen(self, msg):
        if self.end_convo is False:
            self.speak()

    def speak(self):
        self.end_convo = True
        self.speaker(msg=self.last_msg)


class RequestMostRecentBlockKnown(BlockChainMessageSender):
    """
    use this to first find out which node has the most recent block before calling RequestNewBlock

    """
    def __init__(self, protocol, convo_id, blockchainPropagatorInstance, protocol_id, q_from_prop_to_msg=None):
        super().__init__(protocol, convo_id, blockchainPropagatorInstance)
        self.prop_type = 'b'
        self.protocolId = protocol_id
        self.q_from_prop_to_msg = q_from_prop_to_msg

    def speak(self):

        msg = "knw_blk"
        self.speaker(msg=msg)

    def listen(self, msg):
        """
        :param msg: [convo_id, most_recent_blockNo]
        :return:
        """
        self.end_convo = True
        if self.propagator_inst.protocol_with_most_recent_block is not None and \
                        self.propagator_inst.protocol_with_most_recent_block < msg[-1]:
                self.propagator_inst.protocol_with_most_recent_block = [self.protocolId,
                                                                        self.local_convo_id, msg[-1]]
        elif self.propagator_inst.protocol_with_most_recent_block is None:
            print(f"in {__file__}: in Listen of request most recent block, msg:\n{msg}")
            self.propagator_inst.protocol_with_most_recent_block = [self.protocolId,
                                                                    self.local_convo_id, msg[-1]]

        if isinstance(self.q_from_prop_to_msg, multiprocessing.queues.Queue):
            self.q_from_prop_to_msg.put(None)  # this is just meant to send a signal, actual value not used


class SendMostRecentBlockKnown(BlockChainMessageReceiver):
    def __init__(self, protocol, convo_id, propagator_inst):
        super().__init__(protocol, convo_id, propagator_inst)

    def listen(self, msg):
        self.speak()

    def speak(self):
        self.end_convo = True
        curr_block = self.last_known_block
        print(f"in {__file__}: current block is {curr_block}")
        if isinstance(curr_block, int):
            # msg = json.dumps([self.prop_type, self.convo_id, curr_block_no]).encode()
            msg = curr_block
        else:
            # msg = json.dumps([self.prop_type, self.convo_id, 0]).encode()
            msg = 0
        self.speaker(msg=msg)
        # self.protocol.transport.write(msg)


# request for new block
class RequestNewBlock(BlockChainMessageSender):
    def __init__(self, blocks_to_receive: list, protocol, convo_id, blockchainPropagatorInstance: BlockChainPropagator,
                 expected_recent_block):

        # index 0, first block to send, index 1, last block to receive, if index 1 is -1 then send till the most
        # recent block, if index 0 is 0 and index 1 are -1 then send the whole blockchain (speaker has option of send
        # only a part of request
        super().__init__(protocol, convo_id, blockchainPropagatorInstance)
        self.blocks_to_receive = ["req_block", blocks_to_receive]
        self.last_block_received = None
        self.expected_recent_block = expected_recent_block

    def speak(self, rsp=None):

        if self.end_convo is False:

            if self.sent_first_msg is False and rsp is None:
                self.sent_first_msg = True
                msg = json.dumps([self.prop_type, self.convo_id, self.blocks_to_receive]).encode()
                self.protocol.transport.write(msg)
            elif rsp is True:
                msg = json.dumps([self.prop_type, self.convo_id, self.verified_msg]).encode()
                self.protocol.transport.write(msg)
            elif rsp is False or (self.sent_first_msg is True and rsp is None):
                msg = json.dumps([self.prop_type, self.convo_id, self.end_convo]).encode()
                self.end_convo = True
                self.protocol.transport.write(msg)

    def listen(self, msg):

        if self.end_convo is False:
            if isinstance(msg, list):
                if self.other_convo_id is None:
                    self.other_convo_id = msg[1][1]  # msg = ['b', [your convo id, other convo id], main_msg]
                    self.convo_id = [self.other_convo_id, self.local_convo_id]

                if msg[-1] is True:  # no need to speak, convo already ended on other side
                    self.end_convo = True  # end convo

                    # when convo is checked make sure
                    if (isinstance(self.last_block_received, int) and isinstance(self.expected_recent_block, int)) and \
                            self.last_block_received >= self.expected_recent_block:
                        self.propagator_inst.has_current_block = True
                    else:
                        self.propagator_inst.has_current_block = None

                elif len(msg) == 5 and msg[-1] is False and isinstance(msg[-2], dict):


                    # receiving a block
                    block_no = msg[-3]
                    block = msg[-2]


                    rsp =self.save_block(
                        block_no=block_no,
                        block=block
                    )
                    if rsp:
                        self.last_block_received = block_no
                        self.propagator_inst.locally_known_block = block_no
                        self.speak(rsp=rsp)

                else:
                    rsp = self.save_block(msg[1], msg[2]) if len(msg) == 4 else False
                    # written twice because self.speak() actually sends data to peer. want to update before that
                    if rsp is True:
                        self.propagator_inst.locally_known_block = msg[1]
                    self.speak(rsp=rsp)

            else:
                self.speak(rsp=False)
            # message to receive should be [convo_id, blockNo, blockDict, isEndOfConvo (True or False)]
        else:
            pass

    def save_block(self, block_no, block):

        # the block is validated in BlockchainData
        if isinstance(block_no, int) and isinstance(block, dict):
            return BlockChainData.save_a_propagated_block(block_no, block, self.propagator_inst.admin_instance)
        else:
            return False


# send requested block
class SendNewBlocksRequested(BlockChainMessageReceiver):
    def __init__(self, protocol, convo_id, blockchainPropagatorInstance: BlockChainPropagator):
        super().__init__(protocol, convo_id, blockchainPropagatorInstance)
        self.blocks_to_send = None  # becomes an iterator when first message sent
        self.admin_inst = blockchainPropagatorInstance.admin_instance
        self.last_known_block = BlockChainData.get_current_known_block(admin_instance=self.admin_inst)
        self.cur_block_no = None

    def listen(self, msg):
        """
        :param msg: list with ['b', convo_id, main msg]
            if first message then ['b', convo_id, ["req_block", list of blocks to send]]
        :return: None, invokes the self.speak() method which writes directly to other node
        """
        print(f"here here, msg {msg}")
        if self.end_convo is False:
            if msg[-1] == self.last_msg:
                self.end_convo = True
            elif self.received_first_msg is False:
                self.received_first_msg = True
                self.create_iterator_of_blocks_to_send(msg[-1][-1])
                self.speak()
            else:

                self.speak()

    def speak(self):

        block = self.get_block()
        print(f"in {__file__}: speak: self.get_block: {block}, blocks to send {self.blocks_to_send}")

        if block:  # few times that len(msg) is != 3
            msg = [self.prop_type, self.convo_id, self.cur_block_no, block, False]
        else:
            self.end_convo = True
            msg = [self.prop_type, self.convo_id, self.end_convo, True]  # tells other node that end of convo is True

        self.protocol.transport.write(json.dumps(msg).encode())  # use this not the speaker() method

    def create_iterator_of_blocks_to_send(self, list_of_blocks_to_send):
        """

        :param list_of_blocks_to_send: [first block to send, last_block_to send] if last_block_to_send is -1
                                        send till the most recent block, if len=1 [block_to_send]
        :return: returns None
        """
        print(f"in {__file__}: list of blocks to send {list_of_blocks_to_send}")
        def create_generator(starting_point):
            if starting_point == -1: # from genesis block
                starting_point = 0
            while True:
                yield starting_point
                starting_point += 1

        # creating a generator that continues yielding incremental block until block not found allows to send
        # blocks that come in after this request was made
        if len(list_of_blocks_to_send) == 1:
            self.blocks_to_send = iter(list_of_blocks_to_send)
        elif list_of_blocks_to_send[1] == -1:
            self.blocks_to_send = create_generator(list_of_blocks_to_send[0])
        elif list_of_blocks_to_send[1] != -1:
            self.blocks_to_send = iter(range(list_of_blocks_to_send[0], list_of_blocks_to_send[1] + 1))
        else:
            self.blocks_to_send = iter([])

    def get_block(self):
        try:
            self.cur_block_no = next(self.blocks_to_send)
            bk_data = BlockChainData.get_block(self.cur_block_no, admin_instance=self.propagator_inst.admin_instance)
            print(f"in {__file__}: get_block: bk data: {bk_data}")
            return bk_data

        except StopIteration:
            return None


class PropagateValidatedBlock(BlockChainMessageSender):
    """
    used to send blocks to others IF they do not already have it
    """
    def __init__(self, protocol, convo_id, propagator_inst):
        super().__init__(protocol, convo_id, propagator_inst)


class ReceivePropagatatedBlock(BlockChainMessageReceiver):
    """
    This is used to receive block (once the node is up and running.
    NOT used to receive blocks during setup,
    """

    def __init__(self, protocol, convo_id, propagator_inst):
        super().__init__(protocol, convo_id,propagator_inst)


class SendNewlyCreatedBlock(BlockChainMessageSender):

    def __init__(self, msg, protocol, convo_id, propagator_inst):
        super().__init__(protocol, convo_id, propagator_inst)

        self.msg = msg

    def speak(self):
        """
        Just speak and end conversation
        :return:
        """
        self.speaker(msg=self.msg)
        self.end_convo = True


class ReceiveNewlyCreatedBlock(BlockChainMessageReceiver):
    def __init__(self, protocol, convo_id, propagator_inst, is_block_one):
        super().__init__(protocol, convo_id,propagator_inst)
        self.is_block_one = is_block_one

    def listen(self, msg):
        """
        listen for new block and then validate new block
        :param msg:
        :return:
        """

        # only when node is accepting new blocks,
        # block number will be validated to make sure not sending stale blocks
        if self.propagator_inst.is_accepting_blocks.is_set():
            # msg = ['b', [convo id, convo id], ['nb'

            # end the convo
            self.end_convo = True
            validator = NewBlockValidator if not self.is_block_one else NewBlockOneValidator
            block = msg[2][1]


            # the block validator will check the block to make sure it meets the requirement needed to be
            #  considedered a valid block
            block_validated = validator(
                admin_inst=self.propagator_inst.admin_instance,
                block=block,
                block_propagator_inst=self.propagator_inst,
                is_newly_created=True,
                q_object=self.propagator_inst.q_object_from_block_validator_for_newly_created_blocks

            ).validate()
            print(f"in ReceiveNewlyCreatedBlock", msg)
            print(f"in ReceiveNewlyCreatedBlock, is block valid", block_validated)
            # self.propagator_inst.reactor_instance.callInThread(
            #
            # )

        else:
            self.end_convo = True


class RequestBlockWinnerChoice(BlockChainMessageSender):
    """
    class is used to send choice of block winner to other competing/proxy nodes
    convo diagram:

    send a message requesting for winner choice, if pubkey of peer node is not known, add that to the message:
    msg = ['bc'], if need pubkey msg = ['bc', 'apk']

    response from other node might be immediate or delayed: so a defferal must be created to end the conversation
    if response is too late.

    response from other node:

    [last 8 char prev of block hash, signature of full block hash]

    the preview is used to find block hash and the digitalsignervalidator is used to verify signature


    if block hash is not found then preview is stored in dict of hash not received directly. and full hash message is
    sent. Peer node sends the full hash and full hash is stored as the value to the dict of hash not received directly
    end messages are then sent and convo's end_convo flag is set to True

    if block hash is found, then end message is sent and end_convo flag set to True by both nodes

    Even though a block hash is ignored, it is stored, if this ignored hash has the most endorsements then local node
    should request for block and validate the block and use it as the official block for that particular block number
    """

    def __init__(self, protocol, convo_id, propagator_inst, local_block_winner_choice_prev, q_object):

        super().__init__(protocol=protocol, convo_id=convo_id, propagator_inst=propagator_inst)

        self.q_object_to_winner_process = q_object
        self.local_block_winner_choice_prev = local_block_winner_choice_prev
        self.peer_node_winner_prev = None
        self.peer_node_winner_pubkey = None
        self.peer_node_winner_sig = None
        self.has_pubkey_of_peer_node = True if self.protocol.proto_id in self.propagator_inst.connected_protocols_dict_of_pubkey \
            else False
        self.received_first_message = False

    def speak(self, rsp=None):

        if self.sent_first_msg is False and rsp is None:
            self.sent_first_msg = True
            msg = ["bc"] if self.has_pubkey_of_peer_node is True else ["bc", self.need_admin_pubkey_msg]

            self.speaker(msg=msg)
        elif rsp:
            self.speaker(msg=rsp)

    def listen(self, msg):

        if self.end_convo is False and self.propagator_inst.is_accepting_block_choices.is_set():
            if isinstance(msg, list):
                if self.other_convo_id is None:
                    self.other_convo_id = msg[1][1]  # msg = ['b', [your convo id, other convo id], main_msg]
                    self.convo_id = [self.other_convo_id, self.local_convo_id]

                main_msg = msg[-1]
                if main_msg == self.last_msg:
                    self.end_convo = True

                elif isinstance(main_msg, list):
                    if len(main_msg) > 1 and self.received_first_message is False:
                        # main message should be [hash prev, signature using full hash]
                        # OR [hash prev, signature using full hash, peer node pubkey dict]
                        self.received_first_message = True
                        rsp = self.check_peer_node_choice(
                            main_msg=main_msg
                        )

                        if rsp is False:  # need hash of block ( will be stored in propagator.inst.dict_of_potential_blocks
                            msg = ["nd_h"]  # need hash message
                        else:
                            self.end_convo = True
                            msg = self.last_msg
                        self.speak(rsp=msg)
                    elif len(main_msg) == 1 and self.received_first_message:
                        # main message list with one element: full block choice of peer node.
                        # initial message's hash prev could not find hash, so full block is sent
                        # this block is stored in separate dictionary for blocks received after the local node's time
                        # todo: add logic which stores the hash in
                        block = main_msg[-1]
                        block_hash = block["bh"]["block_hash"]
                        self.check_peer_node_choice(
                            main_msg=block,
                            full_hash=block_hash

                        )
                        self.end_convo = True
                        self.speak(rsp=self.last_msg)
        elif self.end_convo is False and not self.propagator_inst.is_accepting_block_choices.is_set():
            self.end_convo = True
            self.speak(rsp=self.last_msg)

    def check_peer_node_choice(self, main_msg, full_hash=None):
        """
        check prev for full hash and verify by checking signature of other node, if pubkey not present,
        return none for req of pubkey
        :param main_msg:
        :param full_hash: if full hash is provided (usually when requested)
        :return:
        """

        if full_hash is None:
            preview = main_msg[0]
            signature = main_msg[1]

            pubkey_of_protocol = self.propagator_inst.connected_protocols_dict_of_pubkey[self.protocol] if \
                self.has_pubkey_of_peer_node else (main_msg[2] if len(main_msg) > 2 and isinstance(main_msg[2], dict) else None)

            if not pubkey_of_protocol:
                print(f"in check_peer_node_choice, BlockchainPropagato:\n"
                      f"Did not receive pubkey from protocol even though it was need. Troubleshoot")

                # todo: when connecting to a node, get admin data and signature
                return None

            try:
                # get hash choice from prev
                peer_node_hash_choice = self.propagator_inst.dict_of_potential_blocks["prev"][preview]


            except KeyError:
                # if KeyError then local node never received particular block hash.
                # It is stored in a dict in BlockchainPropagator class called Blocks_Not_received_On_Time
                # Blocks stored here are only used if it turns out that it received a majority of the endorsements

                if preview in self.propagator_inst.dict_of_hash_not_rcv_directly:

                    # if hash not received directly has already being received check this dict
                    peer_node_hash_choice = self.propagator_inst.dict_of_hash_not_rcv_directly[preview]

                else:

                    # if hash never received store info and return False, full hash will be sent by peer node
                    self.peer_node_winner_prev = preview
                    self.peer_node_winner_pubkey = pubkey_of_protocol
                    self.peer_node_winner_sig = signature
                    return False
        else:
            peer_node_hash_choice = full_hash
            pubkey_of_protocol = self.peer_node_winner_pubkey
            signature = self.peer_node_winner_sig

            #main_msg is a block
            self.propagator_inst.dict_of_potential_indirect_blocks[peer_node_hash_choice] = main_msg

        # validate signature
        is_valid = DigitalSignerValidator.validate(
            msg=peer_node_hash_choice,
            pubkey=pubkey_of_protocol,
            signature=signature
        )

        print(f"for testing in check_peer_node_choice, blockchainpropagator.py, is signature valid: {is_valid}")
        if is_valid:
            # todo set block when you for all possibilities
            self.propagator_inst.dict_of_hash_not_rcv_directly[self.peer_node_winner_prev] = peer_node_hash_choice
            self.q_object_to_winner_process.put([peer_node_hash_choice, signature])
        else:

            return None


class SendBlockWinnerChoice(BlockChainMessageReceiver):
    """
    class is used to receive another competing/proxy node's choice of block winner
    """

    def __init__(self, protocol, convo_id, propagator_inst,  local_block_winner_choice_full_block):
        super().__init__(protocol=protocol, convo_id=convo_id, propagator_inst=propagator_inst)
        self.local_block_winner_choice_full_block = local_block_winner_choice_full_block
        self.local_block_winner_choice_hash = local_block_winner_choice_full_block["bh"]["block_hash"] if \
        local_block_winner_choice_full_block else None
        self.local_block_winner_choice_prev = self.local_block_winner_choice_hash[-8: ] if \
        self.local_block_winner_choice_hash else None
        self.have_sent_full_block = False


    def listen(self, msg):
        if self.end_convo is False:
            if msg[-1] == self.last_msg:
                self.end_convo = True
            elif self.received_first_msg is False:

                # msg[2] == ['bc'] OR ['bc', 'apk'] if admin pubkey needed
                # msg[1] == convo id list
                # msg[0] == 'b' shows its from blockchainpropagator logic
                main_msg = msg[-1]

                # already have block winner
                if self.local_block_winner_choice_full_block:

                    self.received_first_msg = True

                    signature_of_choice = DigitalSigner.sign_with_provided_privkey(
                        dict_of_privkey_numbers={
                            'x': self.propagator_inst.admin_instance.privkey.pointQ.x,
                            'y': self.propagator_inst.admin_instance.privkey.pointQ.y,
                            'd': self.propagator_inst.admin_instance.privkey.d
                        },
                        message=self.local_block_winner_choice_hash
                    )
                    # only requires blockchain choice
                    if main_msg[-1] == "bc":
                        rsp = [self.local_block_winner_choice_prev, signature_of_choice]

                    # block choice along with pubkey needed
                    elif main_msg[-1] == "apk":  # main_msg[-1] == "apk", main_msg = ['bc', 'apk'
                        # todo: send admin id also, to let peer node verify registration of local node
                        # prev of hash, pubkey with x and y as base85 encoded string
                        rsp = [self.local_block_winner_choice_prev, signature_of_choice,
                               self.propagator_inst.admin_instance.get_pubkey(x_y_only=True)]
                    else:  # main_msg[-1] should be 'nd_h'. other node does not have

                        # send [local block chosen as winner) to peer node
                        rsp = [self.local_block_winner_choice_full_block]

                    self.speak(rsp=rsp,
                               sending_full_block=True if
                               (main_msg[-1] == "nd_h" and self.have_sent_full_block is False) else False)

                # block winner not yet found
                else:
                    # this will add original message to dict,
                    # once block choice is determined self.listen_deferred is called
                    print(f"In SendBlockWinnerChoice, {self.propagator_inst.admin_instance.admin_name} adding to deffered")
                    self.add_to_deferred_convo(msg=msg)

    def listen_deffered(self, msg, block_choice_full_block):

        try:
            # if end message has been sent by other node, then this conversation is sended
            if self.end_convo is False:
                self.local_block_winner_choice_full_block = block_choice_full_block
                self.local_block_winner_choice_hash = block_choice_full_block["bh"]["block_hash"]
                self.local_block_winner_choice_prev = self.local_block_winner_choice_hash[-8: ]
                self.listen(msg=msg)
        except (TypeError, KeyError) as e:
            print(f" Trouble shoot in listen_deferred:\n"
                  f"listen_deferred being called without full block choice or proper block\n"
                  f"error is {e}\n"
                  f"block_choice_full_block is {block_choice_full_block}")
            if self.end_convo is False:
                self.speak(rsp=self.last_msg, sending_full_block=False)


    def speak(self, rsp=None, sending_full_block=False):


        if (self.end_convo is False and rsp) or (sending_full_block is True and self.have_sent_full_block is False):
            self.end_convo = True

            # set have sent full block to true to avoid resending again
            if sending_full_block is True:
                self.have_sent_full_block = True
            self.end_convo = True
            self.speaker(msg=rsp)

    def add_to_deferred_convo(self, msg):

        try:
            # append to list containing self.listen_deffered method callable object and message
            self.propagator_inst.dict_of_deferred_convo["bc"].append([self.listen_deffered, msg])
        except KeyError:
            # no "bc" so create one with new list
            self.propagator_inst.dict_of_deferred_convo["bc"] = [[self.listen_deffered, msg]]


class SendNetworkWinnerChoice(BlockChainMessageSender):
    """
    after determining the block with the most endorsement, network winner is chosen.
    This is to broadcast to others about this choice,
    """

    pass


class ReceiveNetworkWinnerChoice(BlockChainMessageReceiver):
    """
    receive network winner choice from other nodes. This will first check the last five chars and 32-35 (inclusive)
    characters. If current node also has the same
    """
    pass
