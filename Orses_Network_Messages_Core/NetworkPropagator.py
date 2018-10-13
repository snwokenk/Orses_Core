"""
This module will be used  propagate messages to other verification nodes or admin nodes.
Messages are gotten from
"""
from Orses_Validator_Core import AssignmentStatementValidator, TokenTransferValidator, \
    TokenReservationRequestValidator, TokenReservationRevokeValidator, MiscMessagesValidator

from Orses_Dummy_Network_Core.DummyVeriNodeListener import DummyVeriNodeListener

import json, os, shutil


validator_dict = dict()
validator_dict['a'] = AssignmentStatementValidator.AssignmentStatementValidator
validator_dict['b'] = TokenTransferValidator.TokenTransferValidator
validator_dict['c'] = TokenReservationRequestValidator.TokenReservationRequestValidator
validator_dict['d'] = TokenReservationRevokeValidator.TokenReservationRevokeValidator
validator_dict['f'] = MiscMessagesValidator.MiscMessagesValidator


class NetworkPropagator:

    def __init__(self, mempool, q_object_connected_to_validator, q_for_propagate, reactor_instance,
                 q_object_between_initial_setup_propagators, is_sandbox=False, q_object_to_competing_process=None,
                 admin_inst=None):
        """

        :param q_object_connected_to_validator: q object used to get validated messages from Message validators
        :param q_object_to_competing_process: q object used to send new validated messages to competing process,
        if active
        """
        # set mempool object shared with BlockchainPropagator
        # contains dict with hash previews for valid msgs and invalid messages
        # contains a method to check
        self.mempool = mempool

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
        # self.validated_message_dict_with_hash_preview = dict()

        # self.invalidated_message_dict_with_hash_preview = dict()

        #message_from_other_veri_node_dict[protocol_id] = {hashpreviews}
        # dict with hash previews received from other nodes
        self.message_from_other_veri_node_dict = dict()
        self.reactor_instance = reactor_instance

        self.network_manager = None

        self.copy_main_default_address_to_admin()

    def copy_main_default_address_to_admin(self):

        if self.is_sandbox is True:
            addr_file_name = "Default_Addresses_Sandbox"
        else:
            addr_file_name = "Default_Addresses"

        path_of_main = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), addr_file_name)
        try:
            shutil.copy(src=path_of_main, dst=self.admin.fl.get_username_folder_path())
        except FileExistsError:
            print("In NetworkPropagator.py, __init__: Default Address Already folder already exists")
        else:
            self.admin.known_addresses = self.admin.fl.get_addresses()

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

        is_competing = self.q_object_compete is not None and self.admin.isCompetitor is True
        try:

            while True:
                # rsp['reason(a, b,c,d)+8charhashprev', snd_wallet_pubkey, main_message_dict, if valid(True or False)]
                # reason a=assignment statement, b=TokenTransfer, c=TokenReservationRequest, D=TokenReservationRevoke
                rsp = self.q_object_validator.get()
                print("in NetworkPropagator.py, convo initiator: ")
                [print(i) for i in rsp]

                try:
                    if isinstance(rsp, str) and rsp in {'exit', 'quit'}:
                        break
                    elif rsp[-1] is None:
                        pass
                    elif rsp[-1] is True:
                        print("in convo initiator, connected protocols", self.connected_protocols_dict)
                        # self.validated_message_dict_with_hash_preview[rsp[0]] = rsp[2]
                        self.mempool.insert_into_valid_msg_preview_hash(
                            hash_prev=rsp[0],
                            msg=rsp[2]
                        )
                        reason_msg = rsp[0][0]
                        # todo: create a process which handles proxy duties (if any) of BCW,
                        # send to compete process, if node is competing
                        # assignment statements are not included in block so no need to send to compete process
                        if is_competing and reason_msg != 'a':
                            print(f"in Networkpropagator, should be sending to compete process")
                            # rsp[0][0] = 0 index of reason msg which is either a, b, c or d
                            self.q_object_compete.put([reason_msg,rsp[2]]) if rsp[3] is True else None
                        elif reason_msg == "a":
                            print(f"Received an assignment statement, BCW logic not yet implemented")

                        # propagate
                        self.reactor_instance.callInThread(
                            msg_sender_creator,
                            rsp=rsp,
                            propagator_inst=self,
                            admin_inst=self.admin
                        )
                    else:
                        # self.invalidated_message_dict_with_hash_preview[rsp[0]] = rsp[2]
                        self.mempool.insert_into_invalid_msg_preview_hash(hash_prev=rsp[0], msg=rsp[2])

                except Exception as e:
                    print("Message: ", rsp, ": exception: ", e)
                    continue


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

                        # msg is python list = ['n', convo_id_list, msg], already json decoded in NetworkMessageSorter
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
                                del self.convo_dict[protocol_id][local_convo_id]

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
                            if msg != "end":
                                self.reactor_instance.callInThread(
                                    notify_of_ended_message,
                                    protocol=self.connected_protocols_dict[protocol_id][0],
                                    convo_id=msg[1],
                                    propagator_instance=self
                                )
                                print("did not find message in protocol's convo dictionary", msg)
                            else:
                                print(f"in {__file__}, message == end")

                except KeyboardInterrupt:
                    print("ending convo manager")
                    break

                except Exception as e:  # log error and continue, avoid stopping reactor process cuz of error
                    # todo: implement error logging, when message received causes error. for now print error and msg
                    print(f"\n-----\nError in {__file__}\nMessage causing Error: {rsp}\n"
                          f"Exception raised: {e}")
                    continue

        except (SystemExit, KeyboardInterrupt):
            reactor.stop()

        finally:
            # todo: implement a way to safely end current conversations before losing Connection and ending reactor
            # todo: use queue to notify send_stop_to_reactor() when done so reactor can be stopped

            for i in self.connected_protocols_dict:
                try:
                    self.connected_protocols_dict[i][0].transport.loseConnection()
                except Exception as e:
                    print("In NetworkPropagator.py, run_propagator_convo_manager, Exception occured")

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

    # a: assignment statement validator, b:token transfer validator, c:token reservation request validator,
    # d:token reservation request validator, e: BCW initiated token transfer
    if isinstance(msg[-1], str) and msg[-1] and msg[-1][0] in {'a', 'b', 'c', 'd', 'f', 'e'}:
        statement_validator = validator_dict[msg[-1][0]]

    else:  # send end message
        propagator_inst.reactor_instance.callInThread(
            notify_of_ended_message,
            protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
            convo_id=convo_id,
            propagator_instance=propagator_inst
        )
        return

    # todo: move this while loop into a function, which returns a convo id

    # get untaken convo_id for new message
    convo_id[0] = get_convo_id(protocol_id=protocol_id, propagator_inst=propagator_inst)

    prop_receiver = StatementReceiver(
        protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
        convo_id=convo_id,
        propagatorInst=propagator_inst,
        statement_validator=statement_validator,
        admin_instance=admin_inst
    )

    #  if msg[-1][0] != 'e' else NodeValidatorReceiver(
    #     protocol=propagator_inst.connected_protocols_dict[protocol_id][0],
    #     convo_id=convo_id,
    #     propagatorInst=propagator_inst,
    #     admin_instance=admin_inst,
    #     conn_node_validator=statement_validator
    # )

    # updates convo_dict of protocol with local convo id
    propagator_inst.convo_dict[protocol_id][convo_id[0]] = prop_receiver
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
    # a is assignment statement, b is token transfer transaction, c is token reservation request,
    # d is token reservation revoke, f is misc messages, e is BCW intiated tranfer transaction (btt)
    if reason not in {'a', 'b', 'c', 'd', 'f', 'e'}:
        return None

    # todo: check he message_from_other
    for i in propagator_inst.connected_protocols_dict:  # make sure not propagating to same node that sent it

        if i not in propagator_inst.message_from_other_veri_node_dict or \
                (i in propagator_inst.message_from_other_veri_node_dict and
                         rsp[0] not in propagator_inst.message_from_other_veri_node_dict[i]):
            print("in NetworkPropagator.py, RSP: ", rsp)
            convo_id = get_convo_id(protocol_id=i, propagator_inst=propagator_inst)

            prop_sender = StatementSender(
                protocol=propagator_inst.connected_protocols_dict[i][0],
                convo_id=convo_id,
                validated_message_list=rsp,
                propagator_inst=propagator_inst,
                admin_inst=admin_inst

            )

            # update protocol's convo dictionary with new convo
            propagator_inst.convo_dict[i][convo_id] = prop_sender

            prop_sender.speak()
        else:
            print(f"\nIn NetworkPropagator.py, protocol: {i} sent tx with preview of: {rsp[0]}\n"
                  f"so Will Not Send To it\n ")


def get_convo_id(protocol_id, propagator_inst: NetworkPropagator):

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
                if self.propagator_inst.mempool.check_valid_msg_hash_prev_dict(hash_prev=msg[-1]):
                    self.speak(rsp=True)
                # have seen and rejected transaction
                elif self.propagator_inst.mempool.check_invalid_msg_hash_prev_dict(hash_prev=msg[-1]):
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




