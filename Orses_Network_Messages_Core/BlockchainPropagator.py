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

import json, multiprocessing
from twisted.internet import reactor, defer, threads
from queue import Empty
from Orses_Competitor_Core.CompetitorDataLoading import BlockChainData
from Orses_Validator_Core.NonNewBlockValidator import NonNewBlockValidator


bk_validator_dict = dict()
bk_validator_dict["req_block"] = NonNewBlockValidator  # validator for non new blocks


blockchain_msg_reasons = {
    "knw_blk",  # request most recent block
    "req_block",
    "new_block",  # a newly created block

}


class BlockChainPropagator:
    def __init__(self, q_object_connected_to_block_validator, q_object_to_competing_process,
                 q_for_bk_propagate, q_object_between_initial_setup_propagators,reactor_instance,
                 admin_instance):
        # initiate Blockchain Data folder if not already created. If create_genesis_only is True, then
        BlockChainData(admin_instance, create_genesis_only=False)

        self.admin_instance = admin_instance
        self.q_object_connected_to_block_validator = q_object_connected_to_block_validator
        self.q_object_compete = q_object_to_competing_process
        self.q_for_bk_propagate = q_for_bk_propagate
        self.q_object_between_initial_setup_propagators = q_object_between_initial_setup_propagators
        self.q_object_to_receive_from_messages = multiprocessing.Queue()
        self.reactor_instance = reactor_instance
        self.convo_dict = dict()
        self.convo_id = 0
        self.connected_protocols_dict = dict()
        self.locally_known_block = BlockChainData.get_current_known_block(admin_instance)[0]
        self.has_current_block = False
        self.protocol_with_most_recent_block = None  # [protocol id, convo_id, block_no known]

    def add_protocol(self, protocol):

        # adds connected protocol, key as protocol_id,  value: list [protocol object, dict(speaker, hearer keys), number of convo(goes to 999 and resets)]
        self.connected_protocols_dict.update({protocol.proto_id: [protocol, 0]})
        self.convo_dict[protocol.proto_id] = dict()

    def remove_protocol(self, protocol):

        del self.connected_protocols_dict[protocol.proto_id]
        del self.convo_dict[protocol.proto_id]

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

        def wait_for_most_recent_block_response(prop_inst, protocol_list, count=0):

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
                    prop_inst.q_object_to_receive_from_messages.get(timeout=7)
                except Empty:

                    print("in Break has broken")
                    break
                else:
                    count1+=1

            return prop_inst.protocol_with_most_recent_block

        def send_response_to_other_threads(has_setup: bool, prop_inst: BlockChainPropagator, recent_block=None):
            for i in range(5):  # four other threads to start and 1 process to end, sends signal
                prop_inst.q_object_between_initial_setup_propagators.put(has_setup)

            if (prop_inst.admin_instance.isCompetitor is True and
                    isinstance(prop_inst.q_object_compete, multiprocessing.queues.Queue) and
                    recent_block):
                prop_inst.q_object_compete.put(recent_block)

        # START INITiAL SETUP
        self.reactor_instance.callInThread(
            first_initial_setup
        )


    def run_propagator_convo_initiator(self):
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

            while True:
                rsp = self.q_object_connected_to_block_validator.get()
                print(f"in blockchainPropagator Initiator, rsp: {rsp}")

                try:
                    if isinstance(rsp, str) and rsp in {'exit', 'quit'}:
                        raise KeyboardInterrupt

                    elif isinstance(rsp, list):
                        reason_msg = rsp[0]  # reason of message

                        if reason_msg == "nb":  # new block created locally
                            pass
                except KeyboardInterrupt:
                    print("ending convo initiator in BlockchainPropagator")
                    break
                except Exception as e:
                    print(f"\n-----\nError in {__file__}, in initiator\nMessage causing Error: {rsp}\n"
                          f"Exception raised: {e}")
                    continue

        except (KeyboardInterrupt, SystemExit):
            pass

    def run_propagator_convo_manager(self):

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
                q_from_prop_to_msg=propagator_inst.q_object_to_receive_from_messages
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
            propagator_inst.reactor_instance.callInThread(
                msg_sender_creator,
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

    # instantiate a validator, if needed
    if isinstance(reason_msg, str) and reason_msg in blockchain_msg_reasons:

        if reason_msg not in {"knw_blk"}:  # if it is in, then no need for a validator
            statement_validator = bk_validator_dict[reason_msg]
    elif isinstance(reason_msg, list) and len(reason_msg) >= 2:

        # req_block message
        if isinstance(reason_msg[0], str) and reason_msg[0] in blockchain_msg_reasons:
            statement_validator = bk_validator_dict[reason_msg[0]]

    else:  # send end message
        propagator_inst.reactor_instance.callInThread(
            notify_of_ended_message,
            protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
            convo_id=convo_id,
            propagator_instance=propagator_inst
        )
        return

    # todo: move this while loop into a function, which returns a convo id

    convo_id[0] = get_convo_id(protocol_id=protocol_id, propagator_inst=propagator_inst)

    prop_receiver = get_message_receiver(
        reason_msg=reason_msg,
        convo_id=convo_id,
        protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
        protocol_id=protocol_id,
        propagator_inst=propagator_inst
    )

    propagator_inst.convo_dict[protocol_id].update({convo_id[0]: prop_receiver})
    prop_receiver.listen(msg=msg)

    if reason_msg == "new_block":
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
    admin_inst = propagator_inst.admin_instance

    # a request most recent block known message/
    # receiver is to send most recent block known (int block number is sent NOT whole block)

    if reason_msg == "knw_blk":
        msg_rcv = SendMostRecentBlockKnown(
            protocol=protocol,
            convo_id=convo_id,
            propagator_inst = propagator_inst
        )
    # request new blocks
    # receiver is SendNewBlockRequested, this sends actual blocks requested
    elif isinstance(reason_msg, list) and reason_msg[0] == "req_block":  # todo: have a way of safely sending blocks without loss of data

        msg_rcv = SendNewBlocksRequested(
            protocol=protocol,
            convo_id=convo_id,
            blockchainPropagatorInstance=propagator_inst
        )

    else:
        print(f"in {__file__}: get_message_receiver, reason msg {reason_msg}")
        msg_rcv = None

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

        self.propagator_inst.reactor_instance.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, self.convo_id, msg]).encode()
        )


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



