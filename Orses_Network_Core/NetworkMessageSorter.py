"""
sorts the messages received from connected protocols' dataReceived
determines if message should go to blockchain propagator or Network propagator.

Messages for Blockchain Propagator are messages sending new blocks, or wallet_hash states

Messges for Network Propagator are transaction messages and assignment statement messages (if proxy of
bk_connected wallet being used)

"""
import json


class NetworkMessageSorter:
    def __init__(self, q_object_from_protocol, q_for_bk_propagate, q_for_propagate):
        self.q_for_propagate = q_for_propagate
        self.q_for_bk_propagate = q_for_bk_propagate
        self.q_object_from_protocol = q_object_from_protocol

    def run_sorter(self):
        """
        :return:
        """
        while True:
            msg = self.q_object_from_protocol.get()  # msg = [protocol id, data], data = [type(b or n), convo id, etc]

            try:
                msg[1] = json.loads(msg[1].decode())
            except ValueError:
                print("in NetworkMessageSorter, json message error")
                continue

            try:
                if msg[1][0] == 'n':
                    self.q_for_propagate.put(msg)
                elif msg[1][0] == 'b':
                    self.q_for_bk_propagate.put(msg)
                else:
                    print("msg could not be sent to any process", msg)
            except IndexError:
                continue


