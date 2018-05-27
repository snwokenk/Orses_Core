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

import json


class BlockChainPropagator:
    def __init__(self, q_object_connected_to_block_validator, q_object_to_competing_process, reactor_instance):
        self.q_object_validator = q_object_connected_to_block_validator
        self.q_object_compete = q_object_to_competing_process
        self.reactor_instance = reactor_instance
        self.conversations_dict = dict()
        self.connected_protocols_dict = dict()

    def add_protocol(self, protocol):

        # adds connected protocol, key as protocol_id,  value: list [protocol object, dict(speaker, hearer keys), number of convo(goes to 999 and resets)]
        self.connected_protocols_dict.update({protocol.proto_id: [protocol, {"speaker": {}, "hearer": {}}, 0]})

    def remove_protocol(self, protocol):

        del self.connected_protocols_dict[protocol.proto_id]

    def run_propagator_convo_initiator(self):
        """
        used to initiate a block request, send validated blocks
        Process is only used to INITIATE convo, any replies go to the run_propagator_convo_manager thread
        :return:
        """

        try:
            if self.q_object_compete:

                while True:

                    rsp = self.q_object_validator()
        except (KeyboardInterrupt, SystemExit):
            pass



# request for new block
class RequestNewBlock:
    def __init__(self, blocks_to_receive: list, protocol, convo_id):

        # index 0, first block to send, index 1, last block to receive, if index 1 is -1 then send till the most
        # recent block, if index 0 is 0 and index 1 are -1 then send the whole blockchain (speaker has option of send
        # only a part of request
        self.blocks_to_receive = blocks_to_receive
        self.last_msg = b'end'
        self.verified_msg = b'ver'
        self.end_convo = False
        self.messages_heard = set()
        self.protocol = protocol
        self.convo_id = convo_id
        self.first_msg = True

    def speak(self, msg=None):

        if self.end_convo is False:

            if self.first_msg is True:
                self.first_msg = False
                rsp = json.dumps([self.convo_id, "req_block", self.blocks_to_receive]).encode()
                self.protocol.transport.write(rsp)
        elif msg:
            self.protocol.transport.write(msg)
        else:
            pass

    def listen(self, msg):

        if self.end_convo is False:
            if isinstance(msg, list):
                if msg[-1] is True:
                    self.end_convo = True
                    # send blockDict to blockValidator
            # message to receive should be [convo_id, blockNo, blockDict, isEndOfMsg (True or False)]
        else:
            pass

# send requested block
class SendNewBlocksRequested:
    def __init__(self, protocol, convo_id):
        self.last_msg = 'end'
        self.verified_msg = 'ver'
        self.need_pubkey = 'wpk'
        self.messages_heard = set()
        self.protocol = protocol
        self.convo_id = convo_id
        self.first_msg = False

    def listen(self, msg):

        if self.first_msg is False:
            self.first_msg = True

    def speak(self):
        pass

