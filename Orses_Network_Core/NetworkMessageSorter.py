"""
sorts the messages received from connected protocols' dataReceived
determines if message should go to blockchain propagator or Network propagator.

Messages for Blockchain Propagator are messages sending new blocks, or wallet_hash states

Messges for Network Propagator are transaction messages and assignment statement messages (if proxy of
bk_connected wallet being used)

"""
import json, copy

from Orses_Dummy_Network_Core.DummyVeriNodeConnector import DummyVeriNodeConnector
from Orses_Network_Core.VeriNodeConnector import VeriNodeConnector
from Orses_Validator_Core.ConnectedNodeValidator import ConnectedNodeValidator
from Orses_Network_Messages_Core.NetworkQuery import NetworkQuery
from Orses_Proxy_Core.ProxyNetworkCommunicator import ProxyMessageSender, ProxyMessageResponder


class NetworkMessageSorter:
    def __init__(self, q_object_from_protocol, q_for_bk_propagate, q_for_propagate, n_propagator_inst,
                 b_propagator_inst, node=None, admin=None):
        self.node = node
        self.admin_inst = admin if admin is not None else self.node.admin
        self.network_prop_inst = n_propagator_inst
        self.blockchain_prop_inst = b_propagator_inst
        self.q_for_propagate = q_for_propagate
        self.q_for_bk_propagate = q_for_bk_propagate
        self.q_object_from_protocol = q_object_from_protocol
        self.convo_dict = dict()  # a little different from others
        self.non_validated_connected_protocols_dict = dict()
        self.validated_conn_protocols_dict = dict()

    def add_protocol(self, protocol, peer_admin_id=None):
        # todo: rather than connecting to protocols dict,
        # todo: add to a preliminary dict until validated, then add to protocols dict
        # adds connected protocol, key as protocol_id,  value:
        # list [protocol object, number of convo(goes to 20000 and resets)]
        self.non_validated_connected_protocols_dict.update({protocol.proto_id: [protocol, 0]})
        self.convo_dict[protocol.proto_id] = dict()

        # # add to blockchain propagator connected dict
        # self.blockchain_prop_inst.connected_protocols_dict.update({protocol.proto_id: [protocol, 0]})
        # self.blockchain_prop_inst.convo_dict[protocol.proto_id] = dict()

        # # add to network propagaor
        # self.network_prop_inst.connected_protocols_dict.update({protocol.proto_id: [protocol, 0]})
        # self.network_prop_inst.convo_dict[protocol.proto_id] = dict()

        if isinstance(protocol, (DummyVeriNodeConnector, VeriNodeConnector)):
            # must send a validator message to complete connection on both ends
            self.network_prop_inst.reactor_instance.callInThread(
                self.create_sender_message,
                protocol=protocol,
                admin_inst=self.admin_inst,
                peer_admin_id=peer_admin_id
            )

            print(f"in NetworkMessageSorter.py Listener Protocol Created When Connected {protocol}")

    def remove_protocol(self, protocol):
        self.blockchain_prop_inst.remove_protocol(protocol=protocol)
        self.network_prop_inst.remove_protocol(protocol=protocol)

    def add_protocol_to_all(self, protocol, admin_id_for_protocol):
        """
        when node validated add it to
        :param protocol:
        :param admin_id_for_protocol: admin_id of protocol
        :return:
        """

        # set admin_id in VeriNodeListener class (or resets for connector)
        protocol.peer_admin_id = admin_id_for_protocol

        # add to blockchain propagator connected dict
        self.blockchain_prop_inst.add_protocol(protocol=protocol, peer_admin_id=admin_id_for_protocol)

        # add to network propagaor
        self.network_prop_inst.add_protocol(protocol=protocol, peer_admin_id=admin_id_for_protocol)

    def run_sorter(self):
        """
        :return:
        """

        # todo: add message receiver for Node Validator
        while True:
            msg = self.q_object_from_protocol.get()  # msg = [protocol id, data], data = [type(b or n), convo id, etc]

            try:
                msg[1] = json.loads(msg[1].decode())  # decode data bytes to string, then json decode
            except ValueError:
                print("in NetworkMessageSorter, json message error")
                continue
            except AttributeError as e:  # not able to decode() probably a string
                if isinstance(msg, str) and msg in {"quit", "exit", "force exit"}:
                    break
                else:
                    print(f"\n-----\nError in {__file__}\nMessage causing Error: {msg}\n"
                          f"Exception raised: {e}")
                    continue

            # *** This handles getting connected protocol validated ***
            if msg[0] in self.non_validated_connected_protocols_dict:  # if in it, then peer node not yet validated
                protocol_id = msg[0]
                msg_data = msg[1]  # [type(b or n), convo id, etc]
                local_convo_id = msg_data[1][0]

                if local_convo_id is not None and local_convo_id in self.convo_dict[protocol_id]:
                    self.network_prop_inst.reactor_instance.callInThread(
                        self.convo_dict[protocol_id][local_convo_id].listen,
                        msg=msg_data
                    )
                elif local_convo_id is None:
                    self.network_prop_inst.reactor_instance.callInThread(
                        self.create_receiver_message,
                        msg=msg_data,
                        protocol=self.non_validated_connected_protocols_dict[protocol_id][0],
                        admin_inst=self.admin_inst,

                    )

                else:
                    print(f"in NetworkMessageSorter, Node Not Validated and No Options Available")
                    pass

            # *** This handles validated connected protocol ***
            elif msg[0] in self.validated_conn_protocols_dict:

                try:  # check what type of message, if 'n' then networkpropagator, if 'b' then blockchainpropagator
                    try:
                        print(f"in message sorter, admin:{self.node.admin.admin_name if self.node else None}, msg: {msg}, "
                              f"")
                    except AttributeError:
                        pass

                    if msg[1][0] == 'n':
                        self.q_for_propagate.put(msg)  # goes to NetworkPropagator.py, run_propagator_convo_manager
                    elif msg[1][0] == 'b':
                        self.q_for_bk_propagate.put(msg)  # goes to BlockchainPropagator.py, run_propagator_convo_manager
                    elif msg[1][0] == 'q':  # msg = [protocol id, ['q', convo id, type of msg (req OR rsp), msg]

                        self.network_prop_inst.reactor_instance.callInThread(
                            self.handle_query,
                            msg=msg
                        )
                        continue
                    elif msg[1][0] == 'p':  # msg = [protocol id, ['p', convo id, type of msg (req OR rsp), msg]
                        self.network_prop_inst.reactor_instance.callInThread(
                            self.handle_proxy_convo,
                            msg=msg
                        )

                    else:
                        print("in NetworkMessageSorter.py, msg could not be sent to any process", msg)
                except IndexError as e:
                    print(f"\n-----\nError in {__file__}\nMessage causing Error: {msg}\n"
                          f"Exception raised: {e}")
                    continue
            else:
                print(f"in NetworkMessageSorter.py, protocol id not in validated Or Non Validated")

        print("in NetworkMessageSorter.py Sorter Ended")

    def create_sender_message(self, protocol, admin_inst, peer_admin_id):

        if protocol.proto_id in self.convo_dict and self.convo_dict[protocol.proto_id]:
            # only one convo should be had which is validatorMessage
            return
        else:
            convo_id = -1
            host_addr = protocol.transport.getHost()
            peer_addr = protocol.transport.getPeer()
            knw_addr = copy.deepcopy(admin_inst.known_addresses)
            try:
                knw_addr.pop(self.admin_inst.admin_id, None)
            except KeyError:
                pass
            try:
                knw_addr.pop(peer_admin_id, None)
            except KeyError:
                pass

            sender = NodeValidatorSender(
                protocol=protocol,
                convo_id=convo_id,
                propagator_inst=self.network_prop_inst,
                msg_sorter_inst=self,
                admin_inst=admin_inst,
                message_list=[
                    {"1": ConnectedNodeValidator.get_hash_of_important_files(admin_inst),
                     "2": {self.admin_inst.admin_id: [host_addr.host, host_addr.port]},
                     "3": len(knw_addr)
                     },
                    knw_addr
                ],
                peer_admin_id=peer_admin_id

            )

            self.convo_dict[protocol.proto_id] = {convo_id: sender}
            sender.speak()

    def create_receiver_message(self, msg, protocol, admin_inst):

        if protocol.proto_id in self.convo_dict and self.convo_dict[protocol.proto_id]:
            # only one convo should be had which is validatorMessage
            return
        else:
            convo_id = msg[1]
            convo_id[0] = -1

            host_addr = protocol.transport.getHost()
            peer_addr = protocol.transport.getPeer()
            knw_addr = copy.deepcopy(admin_inst.known_addresses)
            try:
                knw_addr.pop(host_addr.host)
            except KeyError:
                pass
            try:
                knw_addr.pop(peer_addr.host)
            except KeyError:
                pass

            receiver = NodeValidatorReceiver(
                protocol=protocol,
                convo_id=convo_id,
                propagatorInst=self.network_prop_inst,
                msg_sorter_inst=self,
                admin_instance=admin_inst,
                conn_node_validator=ConnectedNodeValidator,
                known_addr=knw_addr
            )

            self.convo_dict[protocol.proto_id] = {convo_id[0]: receiver}
            receiver.listen(msg=msg)

    def handle_query(self, msg):
        """
        Should be run in non reactor thread using callInThread
        :param msg: [protocol id, ['q', convo id, type of msg (req OR rsp), msg]
        :return:
        """

        # get protocol
        protocol = self.validated_conn_protocols_dict.get(msg[0], None)
        if protocol is None:
            return
        main_msg = msg[1]
        type_of_msg = main_msg[2]
        req_or_response_msg = main_msg[3]

        if type_of_msg == 'req':  # a request
            NetworkQuery.respond_to_a_query(
                query_msg=req_or_response_msg,
                admin_inst=self.admin_inst,
                protocol=protocol
            )
        elif type_of_msg == 'rsp':

            NetworkQuery.receive_query_response(
                query_msg=main_msg
            )

    def handle_proxy_convo(self, msg):
        """
        SHOULD BE RUN IN A NON REACTOR THREAD USING callInThread
        Should be run in non reactor thread using callInThread
        :param msg: [protocol id, ['q', convo id, type of msg (snd OR rcv), msg]
        :return:
        """

        # get protocol
        protocol = self.validated_conn_protocols_dict.get(msg[0], None)
        if protocol is None:
            return

        main_msg = msg[1]
        convo_id = main_msg[1]
        type_of_msg = main_msg[2]
        snd_or_rcv_msg = main_msg[3]

        if type_of_msg == "snd":
            proxy_center = self.admin_inst.get_proxy_center()

            # respond to a send message
            ProxyMessageResponder(
                msg=main_msg,
                protocol=protocol,
                proxy_communicator_inst=proxy_center.get_proxy_communicator()

            )
            pass
        elif type_of_msg == "rsp":

            # receive a response
            instance_of_pms: ProxyMessageSender = ProxyMessageSender.get_instance_of_class(convo_id=convo_id)

            if isinstance(instance_of_pms, ProxyMessageSender):
                instance_of_pms.listen(
                    response=snd_or_rcv_msg
                )
            pass


# helper functions


class NodeValidatorSender:
    def __init__(self, protocol, convo_id, message_list, propagator_inst, msg_sorter_inst: NetworkMessageSorter,
                 admin_inst, peer_admin_id):
        # {"1": software_hash_list, "2": ip address, "3": number of known address}
        self.msg_sorter_inst = msg_sorter_inst
        self.main_msg = message_list[0]
        self.addr_dict = message_list[1]  # {admin_id: [ip addr, port]}
        self.not_compatible_msg = "ntc"
        self.admin_inst = admin_inst
        self.propagator_inst = propagator_inst
        self.last_msg = 'end'
        self.verified_msg = 'ver'
        self.rejected_msg = 'rej'
        self.send_tx_msg = 'snd'
        self.need_pubkey = 'wpk'
        self.prop_type = 'n'
        self.end_convo = False
        self.end_convo_reason = None
        self.protocol = protocol
        self.local_convo_id = convo_id
        self.other_convo_id = None  # in listen() get other convo_id
        self.convo_id = [self.other_convo_id, self.local_convo_id]
        self.sent_first_msg = False
        self.peer_admin_id = peer_admin_id

    def speak(self, rsp=None):

        if self.end_convo is False:
            if self.sent_first_msg is False and rsp is None:
                self.sent_first_msg = True
                self.speaker(msg=f'e{self.admin_inst.admin_id}')
            elif rsp is not None:
                self.speaker(msg=rsp)

    def listen(self, msg):
        print(f"in Networkmessagesorter.py, listen, networkmessagesender msg\n"
              f"{msg}")
        if self.end_convo is False:
            if isinstance(msg[-1], str) and msg[-1] in {self.verified_msg, self.rejected_msg, self.last_msg}:
                self.end_convo = True
                self.end_convo_reason = msg[-1]
                try:
                    del self.msg_sorter_inst.non_validated_connected_protocols_dict[self.protocol.proto_id]
                    if msg[-1] == self.last_msg:
                        self.msg_sorter_inst.validated_conn_protocols_dict[self.protocol.proto_id] = self.protocol
                        self.msg_sorter_inst.add_protocol_to_all(
                            protocol=self.protocol,
                            admin_id_for_protocol=self.peer_admin_id
                        )
                except KeyError:
                    pass
                return
            if self.other_convo_id is None:
                self.other_convo_id = msg[1][1]  # msg = ['n', [your convo id, other convo id], main_msg]
                self.convo_id = [self.other_convo_id, self.local_convo_id]

            if msg[-1] == self.send_tx_msg:  # msg[-1] == "snd"
                self.speak(self.main_msg)

            elif msg == self.not_compatible_msg:
                # todo: find a way to note nodes not running compatible software for now end convo
                self.end_convo = True
                self.end_convo_reason = msg[-1]
                try:
                    del self.msg_sorter_inst.non_validated_connected_protocols_dict[self.protocol.proto_id]
                except KeyError:
                    pass

            elif isinstance(msg[-1], dict):  # peer node running compatible software, dict is to decide if to snd addr

                msg_dict = msg[-1]

                if isinstance(msg_dict["2"], (list, dict)):  # addresses of peer node
                    self.admin_inst.fl.update_addresses(address_dict=msg_dict["2"])

                if msg_dict["1"] is True:  # other node wants tocal address list
                    self.speak(self.addr_dict)
                else:
                    try:
                        del self.msg_sorter_inst.non_validated_connected_protocols_dict[self.protocol.proto_id]
                        self.msg_sorter_inst.validated_conn_protocols_dict[self.protocol.proto_id] = self.protocol
                        self.msg_sorter_inst.add_protocol_to_all(
                            protocol=self.protocol,
                            admin_id_for_protocol=self.peer_admin_id
                        )
                    except KeyError:
                        pass

    def speaker(self, msg):

        self.propagator_inst.reactor_instance.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, self.convo_id, msg]).encode()
        )


class NodeValidatorReceiver:
    def __init__(self, protocol, convo_id, propagatorInst, msg_sorter_inst: NetworkMessageSorter, admin_instance,
                 conn_node_validator, known_addr):
        """
        FIRST message should be a string with message[1:] == admin ID, this is then checked to verify that admin not
        blacklisted. A "snd" message ie self.send_tx_msg is sent.

        SECOND message should then be a dictionary with three keys "1","2", "3".
        key "1" is == peer_software_hash_list AND peer_software_hash_list[-1] == combined_hash
        key "2" is the ip address of the node..
        key "3" is an int number of known addresses.
        This second message is passed to ConnectNodeValidator. the validator checks to make sure the peer is running a
        compatible software and also stores/updates the ip address of the node, if not already stored/updated
        if the peer node is NOT running a compatible software an "ntc" message ie self.not_compatible_msg is sent
        if peer node IS running compatible software:
        If the local and peer node has more than 3 ip addresses of nodes, then an end message is sent

        Otherwise a dictionary is sent. In this dictionary
        '1': True if the local node needs addresses else False
        '2': [list of addresses] if the peer node has 3 or less addresses else None


        THIRD  message is received only if the local node requested for peer's address list. Third message is a list of
        ip addresses. length of list is <= 20. Once this is received, local node stores these addresses in address list.

        :param protocol:
        :param convo_id:
        :param propagatorInst:
        :param admin_instance:
        :param conn_node_validator:
        """
        # TODO: after storing new addresses, find a way to trigger connection in which node can be connected to at
        # TODO: least 4 nodes IF not already connected
        self.known_addr = known_addr
        self.msg_sorter_inst = msg_sorter_inst
        self.connected_node_validator = conn_node_validator
        self.not_compatible_msg = "ntc"
        self.need_addr_msg = "ndr"
        self.need_to_receive_addr = None
        self.admin_instance = admin_instance
        self.last_msg = 'end'
        self.verified_msg = 'ver'
        self.rejected_msg = 'rej'
        self.send_tx_msg = 'snd'
        self.prop_type = 'n'
        self.local_convo_id = convo_id[0]
        self.other_convo_id = convo_id[1]  # when receiving from other, the other's local id is added here
        self.convo_id = [self.other_convo_id, self.local_convo_id]
        self.end_convo = False
        self.received_first_msg = False
        self.received_tx_msg = False
        self.main_message = None
        self.propagator_inst = propagatorInst
        self.protocol = protocol
        self.end_convo_reason = None
        self.peer_admin_id = None

    def listen(self, msg):
        print(f"in Networkmessagesorter.py, listen, networkmessagereceiver msg\n"
              f"{msg}\n")
        if self.end_convo is False:
            if isinstance(msg[-1], str) and msg[-1] in {self.verified_msg, self.rejected_msg, self.last_msg}:
                self.end_convo = True
                self.end_convo_reason = msg[-1]
                try:
                    del self.msg_sorter_inst.non_validated_connected_protocols_dict[self.protocol.proto_id]
                except KeyError:
                    pass
            elif self.received_first_msg is False and isinstance(msg[-1], str):  # "e{adminId}" ie. "e"
                self.peer_admin_id = msg[-1][1:]
                if self.peer_admin_id in self.admin_instance.fl.get_blacklisted_admin():
                    self.speak(rsp=False)
                else:
                    self.speak()

            # expecting dict of hashes/ second message
            elif self.received_tx_msg is False and isinstance(msg[-1], dict):
                try:
                    rsp = self.connected_node_validator(
                        peer_node_info_dict=msg[-1],
                        wallet_pubkey=None,
                        q_object=None,
                        admin_inst=self.admin_instance
                    ).check_validity()
                except KeyError:  # wrong tx message sent (or invalid format maybe using different version)
                    rsp = False
                print(f"message_sorter, in receive, rsp {rsp}")
                if rsp is True:
                    known_addr_peer = msg[-1]["3"]  # number of addresses known by peer
                    known_addr_local = len(self.known_addr)

                    # check if other node should send known addresses list
                    if known_addr_peer > 3 and known_addr_local > 3:  # no need to send
                        self.speak(rsp=self.last_msg)

                    else:  # more addresses needed
                        rsp_dict = dict()
                        rsp_dict['1'] = self.need_to_receive_addr = known_addr_local <= 3
                        try:
                            rsp_dict['2'] = list(self.known_addr) if known_addr_local <= 3 else {}
                        except TypeError:
                            rsp_dict['2'] = {}

                        self.speak(rsp_dict)

                else:  # rsp is False / non compatible software being run by peer node
                    self.speak(self.not_compatible_msg)

            elif self.need_to_receive_addr is True:
                if isinstance(msg[-1], (dict, list)):
                    self.admin_instance.fl.update_addresses(msg[-1])

                self.speak(self.last_msg)
            else:
                print("in NetworkMessageSorter, NodeValidatorReceiver, No option available")

    def speak(self, rsp=None):
        if self.end_convo is False:

            if self.received_first_msg is False:
                self.received_first_msg = True
                msg = self.verified_msg if rsp is True else(self.rejected_msg if rsp is False else self.send_tx_msg)
                self.end_convo = True if (rsp is True) or (rsp is False) else False
                if self.end_convo is True:
                    try:
                        del self.msg_sorter_inst.non_validated_connected_protocols_dict[self.protocol.proto_id]
                    except KeyError:
                        pass
                self.speaker(msg=msg)

            elif self.received_tx_msg is False:
                self.received_tx_msg = True
                if rsp == self.not_compatible_msg or isinstance(rsp, dict):
                    if rsp == self.not_compatible_msg:
                        try:
                            del self.msg_sorter_inst.non_validated_connected_protocols_dict[self.protocol.proto_id]
                        except KeyError:
                            pass
                        self.end_convo = True
                        self.end_convo_reason = self.not_compatible_msg
                    else:  # its a dict, and therefore compatible
                        if self.need_to_receive_addr is False:
                            try:
                                del self.msg_sorter_inst.non_validated_connected_protocols_dict[self.protocol.proto_id]
                                self.msg_sorter_inst.validated_conn_protocols_dict[self.protocol.proto_id] = self.protocol
                                self.msg_sorter_inst.add_protocol_to_all(
                                    protocol=self.protocol,
                                    admin_id_for_protocol=self.peer_admin_id
                                )
                            except KeyError:
                                pass
                        else:
                            pass

                    self.speaker(msg=rsp)

            elif rsp == self.last_msg:  # peer running compatible software
                self.end_convo = True
                try:
                    del self.msg_sorter_inst.non_validated_connected_protocols_dict[self.protocol.proto_id]
                    self.msg_sorter_inst.validated_conn_protocols_dict[self.protocol.proto_id] = self.protocol
                    self.msg_sorter_inst.add_protocol_to_all(
                        protocol=self.protocol,
                        admin_id_for_protocol=self.peer_admin_id
                    )
                except KeyError:
                    pass
                self.end_convo = True
                self.end_convo_reason = self.last_msg
                self.speaker(msg=rsp)

    def speaker(self, msg):
        self.propagator_inst.reactor_instance.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, self.convo_id, msg]).encode()
        )

