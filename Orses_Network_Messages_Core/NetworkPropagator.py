"""
This module will be used  propagate messages to other verification nodes or admin nodes.
Messages are gotten from
"""
from Orses_Validator_Core import AssignmentStatementValidator, TokenTransferValidator, \
    TokenReservationRequestValidator, TokenReservationRevokeValidator, ConnectedNodeValidator
# from twisted.internet.protocol import Protocol

import json, os, shutil


validator_dict = dict()
validator_dict['a'] = AssignmentStatementValidator.AssignmentStatementValidator
validator_dict['b'] = TokenTransferValidator.TokenTransferValidator
validator_dict['c'] = TokenReservationRequestValidator.TokenReservationRequestValidator
validator_dict['d'] = TokenReservationRevokeValidator.TokenReservationRevokeValidator
validator_dict['e'] = ConnectedNodeValidator.ConnectedNodeValidator


class NetworkPropagator:

    def __init__(self, q_object_connected_to_validator, q_for_propagate, reactor_instance,
                 q_object_between_initial_setup_propagators, is_sandbox=False, q_object_to_competing_process=None,
                 admin_inst=None):
        """

        :param q_object_connected_to_validator: q object used to get validated messages from Message validators
        :param q_object_to_competing_process: q object used to send new validated messages to competing process,
        if active
        """
        self.admin = admin_inst
        self.is_sandbox = is_sandbox
        self.q_object_validator = q_object_connected_to_validator
        self.q_object_compete = q_object_to_competing_process
        self.q_object_propagate = q_for_propagate
        self.q_object_between_initial_setup_propagators = q_object_between_initial_setup_propagators

        # convo_dict[protocol_id] = {convo_id: statementsender/statementreceiver}
        self.convo_dict = dict()
        self.connected_protocols_dict = dict()


        # dict with reason+hash previews as dict keys( this can be updated using binary search Tree) will do for now
        # main tx dict as value
        self.validated_message_dict_with_hash_preview = dict()

        self.invalidated_message_dict_with_hash_preview = dict()

        #message_from_other_veri_node_dict[protocol_id] = {hashpreviews}
        # dict with hash previews received from other nodes
        self.message_from_other_veri_node_dict = dict()
        self.reactor_instance = reactor_instance

        self.network_manager = None

    def copy_main_default_address_to_admin(self, admin_instance):

        if self.is_sandbox is True:
            addr_file_name = "Default_Addresses_Sandbox"
        else:
            addr_file_name = "Default_Addresses"

        path_of_main = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), addr_file_name)
        try:
            shutil.copy(src=path_of_main, dst=admin_instance.fl.get_username_folder_path())
        except FileExistsError:
            print("In NetworkPropagator.py, __init__: Blockchain_Data folder already exists")

    def copy_or_created_banned_admin_list(self):
        pass


    def add_protocol(self, protocol):

        # adds connected protocol, key as protocol_id,  value: list [protocol object, number of convo(goes to 20000 and resets)]
        self.connected_protocols_dict.update({protocol.proto_id: [protocol, 0]})
        self.convo_dict[protocol.proto_id] = dict()

    def remove_protocol(self, protocol):

        del self.connected_protocols_dict[protocol.proto_id]
        del self.convo_dict[protocol.proto_id]

    def run_propagator_convo_initiator(self):
        """
        used to send validated messages to other veri nodes. These validated messages could come first hand from
        regular client nodes or propagted messages from other nodes.
        Process is only used to INITIATE convo, any replies go to the run_propagator_convo_manager thread
        :return:
        """
        initial_setup_done = self.q_object_between_initial_setup_propagators.get()  # returns bool

        if initial_setup_done is False:
            print("ending initiator, Setup Not Able")
            return

        try:

            while True:
                # rsp['reason(a, b,c,d)+8charhashprev', snd_wallet_pubkey, main_message_dict, if valid(True or False)]
                # reason a=assignment statement, b=TokenTransfer, c=TokenReservationRequest, D=TokenReservationRevoke
                rsp = self.q_object_validator.get()
                print("in compete, convo initiator: ", rsp)

                try:
                    if isinstance(rsp, str) and rsp in {'exit', 'quit'}:
                        break
                    elif rsp[3] is None:
                        pass
                    elif rsp[3] is True:
                        print("in convo initiator, reached here", self.connected_protocols_dict)
                        self.validated_message_dict_with_hash_preview[rsp[0]] = rsp[2]
                        self.reactor_instance.callInThread(
                            msg_sender_creator,
                            rsp=rsp,
                            propagator_inst=self,
                            admin_inst=self.admin
                        )
                    else:
                        self.invalidated_message_dict_with_hash_preview[rsp[0]] = rsp[2]

                except Exception as e:
                    print("Message: ", rsp, ": exception: ", e)
                    continue

                else:
                    if self.q_object_compete:
                        self.q_object_compete.put(rsp[2])

        except (KeyboardInterrupt, SystemExit):
            pass

        finally:
            print("Convo Initiator Ended")

    def run_propagator_convo_manager(self):
        """
        This method listens for new messages from connected protocols.
        This connected protocols are stored in the self.connected_protocols_dict
        conversations are tracked using convo id
        :return:
        """

        # this method will be run in in another process using reactor.callInThread
        # plan is to run NetworkPropagatorHearer

        # thread to

        initial_setup_done = self.q_object_between_initial_setup_propagators.get()  # returns bool

        if initial_setup_done is False:
            print("ending convo, Setup Not Able")
            return
        reactor = self.reactor_instance
        try:

            while True:
                # rsp == [protocol_instance_id, data]
                rsp = self.q_object_propagate.get()

                print("in propagator: ", rsp)
                try:
                    if isinstance(rsp, str) and rsp in {'exit', 'quit'}:
                        raise KeyboardInterrupt

                    elif isinstance(rsp, list) and len(rsp) == 2:

                        # protocol id
                        protocol_id = rsp[0]

                        # data is python list = ['n', convo_id_list, msg], already json decoded in NetworkMessageSorter

                        msg = rsp[1]

                        # convo_id_list == [local convo id, other convo id]
                        local_convo_id = msg[1][0]

                        # prop_type = data[0]
                        # convo_id = msg[1] / convo_id for incoming message = [local convo id, other convo id]
                        # main msg = msg[2]

                        if local_convo_id is not None and local_convo_id in self.convo_dict[protocol_id]:
                            # check if convo has ended
                            if self.convo_dict[protocol_id][local_convo_id].end_convo:
                                # notify other node about ended convo
                                self.reactor_instance.callInThread(
                                    notify_of_ended_message,
                                    protocol=self.connected_protocols_dict[protocol_id][0],
                                    convo_id=msg[1],
                                    propagator_instance=self
                                )

                            else:
                                # convo is still on, call listen() in another thread
                                self.reactor_instance.callInThread(
                                    self.convo_dict[protocol_id][local_convo_id].listen,
                                    msg=msg
                                )

                        elif local_convo_id is None: # new convo
                            self.reactor_instance.callInThread(
                                msg_receiver_creator,
                                protocol_id=protocol_id,
                                msg=msg,
                                propagator_inst=self,
                                admin_inst=self.admin

                            )

                        else:
                            # end convo in other node, since it can't be found locally
                            self.reactor_instance.callInThread(
                                notify_of_ended_message,
                                protocol=self.connected_protocols_dict[protocol_id][0],
                                convo_id=msg[1],
                                propagator_instance=self
                            )
                            print("did not find message in protocol's convo dictionary", msg)

                except KeyboardInterrupt:
                    print("ending convo manager")
                    break

                except Exception as e:  # log error and continue, avoid stopping reactor process cuz of error
                    # todo: implement error logging, when message received causes error. for now print error and msg
                    print("Message: ", rsp, ": exception: ", e)
                    continue

        except (SystemExit, KeyboardInterrupt):
            reactor.stop()

        finally:
            # todo: implement a way to safely end current conversations before losing Connection and ending reactor
            # todo: use queue to notify send_stop_to_reactor() when done so reactor can be stopped

            for i in self.connected_protocols_dict:
                self.connected_protocols_dict[i][0].transport.loseConnection()

            self.network_manager.close_all_ports()  # stop listening on ports

            print("Convo Manager Ended")


def notify_of_ended_message(protocol, convo_id: list, propagator_instance: NetworkPropagator):
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


def msg_receiver_creator(protocol_id, msg, propagator_inst: NetworkPropagator, admin_inst):
    convo_id = msg[1]
    print(f"in NetworkPropagtor.py, message receiver creator, msg {msg}")

    # todo: limit protocol to only sending connectorvalidator messages if not yet validated

    # a: assignment statement validator, b:token transfer validator, c:token reservation request validator,
    # d:token reservation request validator, e: ConnectedNodeValidator
    if isinstance(msg[-1], str) and msg[-1] and msg[-1][0] in {'a', 'b', 'c', 'd', 'e'}:
        statement_validator = validator_dict[msg[-1][0]]

    else:  # send end message
        propagator_inst.reactor_instance.callInThread(
            notify_of_ended_message,
            protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
            convo_id=convo_id,
            propagator_instance=propagator_inst
        )
        return

    while True:  # gives new convo a convo_id that is not taken
        convo_id[0] = propagator_inst.connected_protocols_dict[protocol_id][1]
        if convo_id[0] in propagator_inst.convo_dict[protocol_id] and \
                propagator_inst.convo_dict[protocol_id][convo_id].end_convo is False:
            propagator_inst.connected_protocols_dict[protocol_id][1] += 1
            continue
        elif convo_id[0] >= 20000:
            propagator_inst.connected_protocols_dict[protocol_id][1] = 0
            continue
        propagator_inst.connected_protocols_dict[protocol_id][1] += 1
        break

    prop_receiver = StatementReceiver(
        protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
        convo_id=convo_id,
        propagatorInst=propagator_inst,
        statement_validator=statement_validator,
        admin_instance=admin_inst
    ) if msg[-1][0] != 'e' else NodeValidatorReceiver(
        protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
        convo_id=convo_id,
        propagatorInst=propagator_inst,
        admin_instance=admin_inst,
        conn_node_validator=statement_validator
    )

    # updates convo_dict of protocol with local convo id
    propagator_inst.convo_dict[protocol_id].update({convo_id[0]: prop_receiver})
    prop_receiver.listen(msg=msg)
    if protocol_id in propagator_inst.message_from_other_veri_node_dict:

        propagator_inst.message_from_other_veri_node_dict[protocol_id].add(msg[-1])
    else:
        propagator_inst.message_from_other_veri_node_dict[protocol_id] = {msg[-1], }


def msg_sender_creator(rsp, propagator_inst: NetworkPropagator, admin_inst):
    """

    :param rsp: ['reason(a, b,c,d)+8charhashprev', snd_wallet_pubkey, main_message_dict, if valid(True or False)]
    :param propagator_inst:
    :return:
    """
    reason = rsp[0][0]
    if reason not in {'a', 'b', 'c', 'd'}:
        return None

    for i in propagator_inst.connected_protocols_dict:  # make sure not propagating to same node that sent it

        if i not in propagator_inst.message_from_other_veri_node_dict or \
                (i in propagator_inst.message_from_other_veri_node_dict and
                         rsp[0] not in propagator_inst.message_from_other_veri_node_dict[i]):

            while True:  # gets a convo id that is not in use
                convo_id=propagator_inst.connected_protocols_dict[i][1]
                if convo_id in propagator_inst.convo_dict[i] and propagator_inst.convo_dict[i][convo_id].end_convo is False:
                    propagator_inst.connected_protocols_dict[i][1] += 1
                    continue
                elif convo_id >= 20000:
                    propagator_inst.connected_protocols_dict[i][1] = 0
                    continue
                propagator_inst.connected_protocols_dict[i][1] += 1
                break

            prop_sender = StatementSender(
                protocol=propagator_inst.connected_protocols_dict[i][0],
                convo_id=convo_id,
                validated_message_list=rsp,
                propagator_inst=propagator_inst,
                admin_inst=admin_inst

            )

            # update protocol's convo dictionary with new convo
            propagator_inst.convo_dict[i].update({convo_id: prop_sender})
            prop_sender.speak()
        else:
            print(f"In NetworkPropagator.py, protocol: {i} sent tx with preview of: {rsp[0]} ")


# *** base message sender class ***
class PropagatorMessageSender:
    def __init__(self, protocol, convo_id, propagator_inst: NetworkPropagator, admin_inst):
        """

        :param protocol: the protocol class representing a connection, use as self.protocol.transport.write()
        :param convo_id: the convo id used by propagator to keep track of message
        """
        self.admin_inst = admin_inst
        self.propagator_inst = propagator_inst
        self.last_msg = 'end'
        self.verified_msg = 'ver'
        self.rejected_msg = 'rej'
        self.send_tx_msg = 'snd'
        self.need_pubkey = 'wpk'
        self.prop_type = 'n'
        self.messages_heard = set()
        self.end_convo = False
        self.end_convo_reason = None
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
class PropagatorMessageReceiver:
    def __init__(self, protocol, convo_id, propagator_inst: NetworkPropagator, admin_instance):
        """

        :param protocol: the protocol class representing a connection, use as self.protocol.transport.write()
        :param convo_id: the convo id used by propagator to keep track of message
        """
        self.admin_instance = admin_instance
        self.last_msg = 'end'
        self.verified_msg = 'ver'
        self.rejected_msg = 'rej'
        self.send_tx_msg = 'snd'
        self.prop_type = 'n'
        self.need_pubkey = 'wpk'
        self.q_object = propagator_inst.q_object_validator
        self.messages_heard = set()
        self.protocol = protocol
        self.local_convo_id = convo_id[0]
        self.other_convo_id = convo_id[1]  # when receiving from other, the other's local id is added here
        self.convo_id = [self.other_convo_id, self.local_convo_id]
        self.propagator_inst = propagator_inst
        self.end_convo = False
        self.received_first_msg = False
        self.received_tx_msg = False
        self.main_message = None
        self.received_tx_msg_but_pubkey_needed = None

    def speak(self):
        """ override """

    def listen(self, msg):
        """override"""

    def speaker(self, msg):
        self.propagator_inst.reactor_instance.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, self.convo_id, msg]).encode()
        )


class StatementSender(PropagatorMessageSender):
    def __init__(self, protocol, convo_id, validated_message_list, propagator_inst, admin_inst):
        super().__init__(protocol, convo_id, propagator_inst, admin_inst)
        self.tx_hash_preview_with_reason = validated_message_list[0]  # string with reason letter-8char hash preview
        self.msg_pubkey = validated_message_list[1]
        self.main_msg = validated_message_list[2]  # this will be serialized at later stage

    def speak(self, rsp=None):

        if self.end_convo is False:
            if self.sent_first_msg is False and rsp is None:
                self.sent_first_msg = True
                self.speaker(msg=self.tx_hash_preview_with_reason)  # send to other node
            elif rsp is not None:
                self.speaker(msg=rsp)

    def listen(self, msg):
        if self.end_convo is False:
            if msg[-1] in {self.verified_msg, self.rejected_msg, self.last_msg}:
                self.end_convo = True
                self.end_convo_reason = msg[-1]
                return

            if self.other_convo_id is None:
                self.other_convo_id = msg[1][1]  # msg = ['n', [your convo id, other convo id], main_msg]
                self.convo_id = [self.other_convo_id, self.local_convo_id]

            if msg[-1] == self.send_tx_msg:
                self.speak(self.main_msg)
            elif msg[-1] == self.need_pubkey:
                self.speak(self.msg_pubkey)


class StatementReceiver(PropagatorMessageReceiver):
    def __init__(self, protocol, convo_id, propagatorInst, statement_validator, admin_instance):
        super().__init__(protocol, convo_id, propagatorInst, admin_instance)
        self.statement_validator = statement_validator

    def listen(self, msg):

        if self.end_convo is False:
            if isinstance(msg[-1], str) and msg[-1] in {self.verified_msg, self.rejected_msg, self.last_msg}:
                self.end_convo = True

            # will be turned to true in self.speak()
            elif self.received_first_msg is False and isinstance(msg[-1], str):
                # have seen and accepted transaction
                if msg[-1] in self.propagator_inst.validated_message_dict_with_hash_preview:
                    self.speak(rsp=True)
                # have seen and rejected transaction
                elif msg[-1] in self.propagator_inst.invalidated_message_dict_with_hash_preview:
                    self.speak(rsp=False)
                # has not seen transaction
                else:
                    self.speak()

            # expecting tx message
            elif self.received_tx_msg is False and isinstance(msg[-1], dict):
                try:
                    rsp = self.statement_validator(
                        msg[-1],
                        wallet_pubkey=None,
                        q_object=self.q_object,
                        admin_instance=self.admin_instance
                    ).check_validity()
                except KeyError:  # wrong tx message sent (or invalid format maybe using different version)
                    rsp = False

                print("rsp of validator, ", rsp)
                self.main_message = msg[-1] if rsp is True or rsp is None else None
                self.speak(rsp=rsp)
            elif self.received_tx_msg_but_pubkey_needed is True:  # needed pubkey to validate transaction
                print(f"needed pubkey, {msg}")
                try:
                    rsp = self.statement_validator(
                        self.main_message,
                        wallet_pubkey=msg[-1],
                        q_object=self.q_object,
                        admin_instance=self.admin_instance
                    ).check_validity()
                except KeyError:  # wrong tx message sent (or invalid format maybe using different version)
                    rsp = False

                self.speak(rsp=rsp)
            else:
                print("in NetworkPropagator, statementreceiver, No option available")
                self.speak(rsp=self.last_msg)

    def speak(self, rsp=None):
        if self.end_convo is False:
            if self.received_first_msg is False:
                self.received_first_msg = True
                msg = self.verified_msg if rsp is True else(self.rejected_msg if rsp is False else self.send_tx_msg)
                self.end_convo = True if (rsp is True) or (rsp is False) else False
                self.speaker(msg=msg)

            elif self.received_tx_msg is False:
                self.received_tx_msg = True
                msg = self.verified_msg if rsp is True else(self.rejected_msg if rsp is False else self.need_pubkey)
                self.received_tx_msg_but_pubkey_needed = True if rsp is None else None
                self.end_convo = True if (rsp is True) or (rsp is False) else False
                self.speaker(msg=msg)

            elif self.received_tx_msg_but_pubkey_needed is True:
                self.end_convo = True
                msg = self.verified_msg if rsp is True else self.rejected_msg
                self.speaker(msg=msg)
            elif rsp == self.last_msg:
                self.end_convo = True
                self.speaker(msg=rsp)


class NodeValidatorSender(PropagatorMessageSender):
    def __init__(self, protocol, convo_id, message_list, propagator_inst, admin_inst):
        super().__init__(protocol, convo_id, propagator_inst, admin_inst)
        # {"1": software_hash_list, "2": ip address, "3": number of known address}
        self.main_msg = message_list[0]
        self.addr_list = message_list[1]

    def speak(self, rsp=None):

        if self.end_convo is False:
            if self.sent_first_msg is False and rsp is None:
                self.sent_first_msg = True
                self.speaker(msg=f'e{self.admin_inst.admin_name}')
            elif rsp is not None:
                self.speaker(msg=rsp)

    def listen(self, msg):
        if self.end_convo is False:
            if msg[-1] in {self.verified_msg, self.rejected_msg, self.last_msg}:
                self.end_convo = True
                self.end_convo_reason = msg[-1]
                return
            if self.other_convo_id is None:
                self.other_convo_id = msg[1][1]  # msg = ['n', [your convo id, other convo id], main_msg]
                self.convo_id = [self.other_convo_id, self.local_convo_id]

            if msg[-1] == self.send_tx_msg:  # msg[-1] == "snd"
                self.speak(self.main_msg)
            elif isinstance(msg[-1], dict):
                msg_dict = msg[-1]

                if isinstance(msg_dict["2"], list):  # addresses of peer node
                    self.admin_inst.fl.update_addresses(address_list=msg_dict)

                if msg_dict["1"] is True:  # other node wants tocal address list
                    self.speak(self.addr_list)


class NodeValidatorReceiver(PropagatorMessageReceiver):
    def __init__(self, protocol, convo_id, propagatorInst, admin_instance, conn_node_validator):
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
        '2': [list of addresses] if the peer node has 3 or less addresses


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

        super().__init__(protocol, convo_id, propagatorInst, admin_instance)
        self.connected_node_validator = conn_node_validator
        self.not_compatible_msg = "ntc"
        self.need_addr_msg = "ndr"
        self.need_to_send_addr = None
        self.need_to_receive_addr = None

    def listen(self, msg):

        if self.end_convo is False:
            if isinstance(msg[-1], str) and msg[-1] in {self.verified_msg, self.rejected_msg, self.last_msg}:
                self.end_convo = True
            elif self.received_first_msg is False and isinstance(msg[-1], str):  # "e{adminId}" ie. "e"
                # TODO: check adminId  to see if banned list, if banned self.speak(false)
                self.speak()

            # expecting dict of hashes
            elif self.received_tx_msg is False and isinstance(msg[-1], dict):
                pass
            elif self.need_to_send_addr is True:
                pass
            elif self.need_to_receive_addr is True:
                pass
            else:
                print("in NetworkPropagator, NodeValidatorReceiver, No option available")

    def speak(self, rsp=None):
        if self.end_convo is False:
            if self.received_first_msg is False:
                self.received_first_msg = True
                msg = self.verified_msg if rsp is True else(self.rejected_msg if rsp is False else self.send_tx_msg)
                self.end_convo = True if (rsp is True) or (rsp is False) else False
                self.speaker(msg=msg)