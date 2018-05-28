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

import json, multiprocessing
from queue import Empty
from Orses_Competitor_Core.CompetitorDataLoading import BlockChainData


class BlockChainPropagator:
    def __init__(self, q_object_connected_to_block_validator, q_object_to_competing_process,
                 q_object_for_propagator, reactor_instance):
        self.q_object_validator = q_object_connected_to_block_validator
        self.q_object_compete = q_object_to_competing_process
        self.q_object_for_propagator = q_object_for_propagator
        self.q_object_between_initiator_manager = multiprocessing.Queue()
        self.reactor_instance = reactor_instance
        self.conversations_dict = dict()
        self.convo_id = 0
        self.connected_protocols_dict = dict()
        self.locally_known_block = BlockChainData.get_current_known_block()[0]
        self.has_current_block = False
        self.protocol_with_most_recent_block = None  # [protocol id, block_no known]

    def add_protocol(self, protocol):

        # adds connected protocol, key as protocol_id,  value: list [protocol object, dict(speaker, hearer keys), number of convo(goes to 999 and resets)]
        self.connected_protocols_dict.update({protocol.proto_id: protocol})

    def remove_protocol(self, protocol):

        del self.connected_protocols_dict[protocol.proto_id]

    def initial_setup(self, recursive_count=0):
        """
        will run first to update block info
        :return:
        """
        if recursive_count >= 10:
            return [False, False]  # was_able_to_update, sent_signal_to_other_threads

        # first get most recent block
        lists_of_blocks_to_get = [-1, -1] if self.locally_known_block is None else [self.locally_known_block+1, -1]

        # keep track of the protocols you sent requests to, (in case a new node connects and sends message
        protocol_list = set(self.connected_protocols_dict)
        self.initiate_msg_to_protocol(RequestMostRecentBlockKnown, protocol_list) # find out which node has most recent block
        count = 0
        while count < len(self.connected_protocols_dict):
            try:
                rsp = self.q_object_for_propagator.get(timeout=15)  # will timeout in 15 seconds
            except Empty:
                count += 1
            else:
                count += 1 if rsp[0] in protocol_list else 0

        if self.locally_known_block <  self.protocol_with_most_recent_block[1]:
            self.initiate_msg_to_protocol(RequestNewBlock, [self.protocol_with_most_recent_block[0]],
                                          lists_of_blocks_to_get)  # ask for blocks from node
        else:
            self.has_current_block = True

        timeout_count = 0
        was_able_to_update = False
        while self.has_current_block is False or timeout_count < 3:
            try:
                rsp = self.q_object_for_propagator.get(timeout=15)
            except Empty:
                timeout_count += 1
                if self.conversations_dict[self.convo_id].end_convo is True:
                    if self.locally_known_block >= self.protocol_with_most_recent_block[1]:
                        was_able_to_update = [True, False]
                        break
                    else:
                        recursive_count += 1
                        was_able_to_update = self.initial_setup(recursive_count)
                        break
            else:
                try:
                    data = json.loads(rsp[-1])
                except ValueError:
                    pass
                else:
                    self.conversations_dict[data[0]].listen(data)  # data[0] is convo id, listen does the rest
                    if self.conversations_dict[data[0]].end_convo is True:
                        if self.locally_known_block >= self.protocol_with_most_recent_block[1]:
                            was_able_to_update = [True, False]
                            break
                    else:
                        recursive_count += 1
                        was_able_to_update = self.initial_setup(recursive_count)
                        break

        if was_able_to_update[0] and was_able_to_update[1] is False:
            for i in range(4): # four other threads to start, sends signal
                self.q_object_between_initiator_manager.put(True)
            return [True, True]
        elif was_able_to_update[1] is True:
            return [True, True]

        else:
            for i in range(4): # four other threads to start, sends signal to stop
                self.q_object_between_initiator_manager.put(False)
            return [False, False]




    def run_propagator_convo_initiator(self):
        """
        used to initiate a block request, send validated blocks
        Process is only used to INITIATE convo, any replies go to the run_propagator_convo_manager thread
        :return:
        """

        known_block_updated = self.q_object_between_initiator_manager.get()

        while True:

            break

        try:
            if self.q_object_compete:  # competing process, used to propagate self or other's blocks

                while True:

                    rsp = self.q_object_validator()
            else:
                pass

        except (KeyboardInterrupt, SystemExit):
            pass

    def run_propagator_convo_manager(self):

        known_block_updated = self.q_object_between_initiator_manager.get()
        pass

    def initiate_msg_to_protocol(self, type_of_msg_to_initiate, list_of_protocol_ids,*args):

        if type_of_msg_to_initiate == RequestNewBlock:
            for i in list_of_protocol_ids:
                convo_id = self.convo_id
                self.conversations_dict[convo_id] = RequestNewBlock(
                    args[0], self.connected_protocols_dict[i], convo_id
                )
                self.conversations_dict[convo_id].speak()
                if self.convo_id == convo_id:
                    self.convo_id+=1
        elif type_of_msg_to_initiate == RequestMostRecentBlockKnown:
            for i in self.connected_protocols_dict:
                convo_id = self.convo_id
                self.conversations_dict[convo_id] = RequestMostRecentBlockKnown(
                    protocol= self.connected_protocols_dict[i],
                    convo_id=convo_id,
                    protocol_id=i,
                    blockchainPropagatorInstance=self
                )
                self.conversations_dict[convo_id].speak()
                if self.convo_id == convo_id:
                    self.convo_id+=1






# *** base message sender class ***
class BlockChainMessageSender:
    def __init__(self, protocol, convo_id):
        """

        :param protocol: the protocol class representing a connection, use as self.protocol.transport.write()
        :param convo_id: the convo id used by propagator to keep track of message
        """
        self.last_msg = b'end'
        self.verified_msg = b'ver'
        self.messages_heard = set()
        self.end_convo = False
        self.protocol = protocol
        self.convo_id = convo_id
        self.sent_first_msg = True

    def speak(self):
        """ override """

    def listen(self, msg):
        """override"""


# *** base  message receiver class ***
class BlockChainMessageReceiver:
    def __init__(self, protocol, convo_id):
        """

        :param protocol: the protocol class representing a connection, use as self.protocol.transport.write()
        :param convo_id: the convo id used by propagator to keep track of message
        """
        self.last_msg = 'end'
        self.verified_msg = 'ver'
        self.need_pubkey = 'wpk'
        self.messages_heard = set()
        self.protocol = protocol
        self.convo_id = convo_id
        self.end_convo = False
        self.received_first_msg = False

    def speak(self):
        """ override """

    def listen(self, msg):
        """override"""


class RequestMostRecentBlockKnown(BlockChainMessageSender):
    """
    use this to first find out which node has the most recent block before calling RequestNewBlock

    """
    def __init__(self, protocol, convo_id, blockchainPropagatorInstance, protocol_id):
        super().__init__(protocol, convo_id)
        self.blockchainPropagator = blockchainPropagatorInstance
        self.protocolId = protocol_id

    def speak(self):

        msg = json.dumps([self.convo_id, "knw_blk"]).encode()
        self.protocol.transport.write(msg)

    def listen(self, msg):
        """
        :param msg: [convo_id, most_recent_blockNo]
        :return:
        """
        self.end_convo = True
        if self.blockchainPropagator.protocol_with_most_recent_block is not None and \
                        self.blockchainPropagator.protocol_with_most_recent_block < msg[-1]:
                self.blockchainPropagator.protocol_with_most_recent_block = [self.protocolId, msg[-1]]


class SendMostRecentBlockKnown(BlockChainMessageReceiver):
    def __init__(self, protocol, convo_id):
        super().__init__(protocol, convo_id)

    def listen(self, msg):
        self.speak()

    def speak(self):
        self.end_convo = True
        curr_block = BlockChainData.get_current_known_block()
        if isinstance(curr_block, list):
            curr_block_no = curr_block[0]
            msg = json.dumps([self.convo_id, curr_block_no]).encode()
        else:
            msg = json.dumps([self.convo_id, 0]).encode()
        self.protocol.transport.write(msg)






# request for new block
class RequestNewBlock(BlockChainMessageSender):
    def __init__(self, blocks_to_receive: list, protocol, convo_id, blockchainPropagatorInstance):

        # index 0, first block to send, index 1, last block to receive, if index 1 is -1 then send till the most
        # recent block, if index 0 is 0 and index 1 are -1 then send the whole blockchain (speaker has option of send
        # only a part of request
        super().__init__(protocol, convo_id)
        self.blocks_to_receive = blocks_to_receive
        self.blockchainPropagator = blockchainPropagatorInstance

    def speak(self, rsp=None):

        if self.end_convo is False:

            if self.sent_first_msg is False and rsp is None:
                self.sent_first_msg = True
                msg = json.dumps([self.convo_id, "req_block", self.blocks_to_receive]).encode()
                self.protocol.transport.write(msg)
            elif rsp is True:
                msg = json.dumps([self.convo_id, self.verified_msg]).encode()
                self.protocol.transport.write(msg)
            elif rsp is False or (self.sent_first_msg is True and rsp is None):
                msg = json.dumps([self.convo_id, self.end_convo]).encode()
                self.end_convo = True
                self.protocol.transport.write(msg)

    def listen(self, msg):

        if self.end_convo is False:
            if isinstance(msg, list):
                if msg[-1] is True:  # no need to speak, convo already ended on other side
                    self.end_convo = True  # end convo
                    self.save_block(msg[1], msg[2]) if len(msg) == 4 else False  # save last block
                else:
                    rsp = self.save_block(msg[1], msg[2]) if len(msg) == 4 else False
                    self.speak(rsp=rsp)
            else:
                self.speak(rsp=False)
            # message to receive should be [convo_id, blockNo, blockDict, isEndOfConvo (True or False)]
        else:
            pass

    def save_block(self, block_no, block):

        # the block is validated in BlockchainData
        if isinstance(block_no, int) and isinstance(block, dict):
            return BlockChainData.save_a_propagated_block(block_no, block)
        else:
            return False


# send requested block
class SendNewBlocksRequested(BlockChainMessageReceiver):
    def __init__(self, protocol, convo_id):
        super().__init__(protocol, convo_id)
        self.blocks_to_send = None  # becomes an iterator when first message sent
        self.last_known_block = BlockChainData.get_current_known_block()
        self.cur_block_no = None

    def listen(self, msg):
        """
        :param msg: list with [convo_id, main msg] if first message then [convo_id, "req_block", list of blocks to send]
        :return: None, invokes the self.speak() method which writes directly to other node
        """

        if self.end_convo is False:
            if msg[-1] == self.last_msg:
                self.end_convo = True
            elif self.received_first_msg is False:
                self.received_first_msg = True
                self.convo_id = msg[0]
                self.create_iterator_of_blocks_to_send(msg[-1])
                self.speak()
            else:
                self.speak()

    def speak(self):

        block = self.get_block()

        if block:
            msg = [self.convo_id, self.cur_block_no, block, False]
        else:
            self.end_convo = True
            msg = [self.convo_id, self.end_convo, True]  # tells other node that end of convo is True

        self.protocol.transport.write(json.dumps(msg).encode())

    def create_iterator_of_blocks_to_send(self, list_of_blocks_to_send):
        """

        :param list_of_blocks_to_send: [first block to send, last_block_to send] if last_block_to_send is -1
                                        send till the most recent block, if len=1 [block_to_send]
        :return: returns None
        """

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
            return BlockChainData.get_block(self.cur_block_no)
        except StopIteration:
            return None

