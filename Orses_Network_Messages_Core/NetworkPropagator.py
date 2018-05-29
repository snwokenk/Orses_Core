"""
This module will be used  propagate messages to other verification nodes or admin nodes.
Messages are gotten from
"""
from Orses_Validator_Core import AssignmentStatementValidator, TokenTransferValidator, \
    TokenReservationRequestValidator, TokenReservationRevokeValidator
# from twisted.internet.protocol import Protocol

import json


class NetworkPropagator:

    def __init__(self, q_object_connected_to_validator, q_for_propagate, reactor_instance,
                 q_object_between_initial_setup_propagators, q_object_to_competing_process=None):
        """

        :param q_object_connected_to_validator: q object used to get validated messages from Message validators
        :param q_object_to_competing_process: q object used to send new validated messages to competing process,
        if active
        """
        self.q_object_validator = q_object_connected_to_validator
        self.q_object_compete = q_object_to_competing_process
        self.q_object_propagate = q_for_propagate
        self.q_object_between_initial_setup_propagators = q_object_between_initial_setup_propagators
        self.validated_message_dict = dict()  # being used to store validate messages
        self.connected_protocols_dict = dict()

        # dict with reason+hash previews as dict keys( this can be updated using binary search Tree) will do for now
        # main tx dict as value
        self.validated_message_dict_with_hash_preview = dict()

        self.invalidated_message_dict_with_hash_preview = dict()

        # dict with hash previews received from other nodes
        self.message_from_other_veri_node_dict = dict()
        self.reactor_instance = reactor_instance

        self.network_manager = None

    def add_protocol(self, protocol):

        # adds connected protocol, key as protocol_id,  value: list [protocol object, dict(speaker, hearer keys), number of convo(goes to 999 and resets)]
        self.connected_protocols_dict.update({protocol.proto_id: [protocol, {"speaker": {}, "hearer": {}}, 0]})

    def remove_protocol(self, protocol):

        del self.connected_protocols_dict[protocol.proto_id]

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
            if self.q_object_compete:

                while True:

                    # rsp['reason(a, b,c,d)+8charhashprev', sending_wallet_pubkey, main_message_dict, if valid(True or False)]
                    rsp = self.q_object_validator.get()

                    try:
                        print("in compete, convo initiator: ", rsp)
                        if isinstance(rsp, str) and rsp in {'exit', 'quit'}:
                            break

                        elif rsp[3] is None:  # msg is network or blockchain related (ie, asking for updates etc)
                            pass

                        elif rsp[3] is True:
                            # send to
                            self.q_object_compete.put(rsp[2])
                            self.validated_message_dict_with_hash_preview[rsp[0]] = rsp[2]
                            self.check_speak_send(validated_message_list=rsp)
                        else:
                            self.invalidated_message_dict_with_hash_preview[rsp[0]] = rsp[2]
                    except Exception as e:
                        # todo: implement error logging, when message received causes error. for now print error and msg
                        print("Message: ", rsp, ": exception: ", e)
                        continue

            else:  # node not competing

                while True:

                    # rsp['reason(a, b,c,d)+8charhashprev', sending_wallet_pubkey, main_message_dict, if valid(True or False)]
                    rsp = self.q_object_validator.get()
                    try:

                        print("in propagator initiator: ", rsp)
                        print(self.connected_protocols_dict)
                        if isinstance(rsp, str) and rsp in {'exit', 'quit'}:
                            print("received exit signal in propagator")
                            raise KeyboardInterrupt

                        elif rsp[3] is True:
                            self.validated_message_dict_with_hash_preview[rsp[0]] = rsp[2]
                            self.check_speak_send(validated_message_list=rsp)
                        else:
                            self.invalidated_message_dict_with_hash_preview[rsp[0]] = rsp[2]
                    except KeyboardInterrupt:
                        print("Ending convo Iniiator")
                        break
                    except Exception as e:
                        # todo: implement error logging, when message received causes error. for now print error and msg
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
                rsp = self.q_object_propagate.get()
                print("in propagator: ", rsp)
                try:
                    if isinstance(rsp, str) and rsp in {'exit', 'quit'}:
                        raise KeyboardInterrupt

                    elif isinstance(rsp, list) and len(rsp) == 2:
                        # rsp == [protocol_instance_id, data]
                        # data is json encoded python list (encoded into bytes)
                        # data == [propagator type('s', 'h' or 'n'), convo id(3 dit from 0-999), convo (main convo)]
                        data = json.loads(rsp[1].decode())

                        # prop_type = data[0]
                        # convo_id = data[1]
                        # convo = data[2]

                        if data[0] == 'n':

                            # stops from creating convo when message already broadcasted (avoids using more cpu/mem resource
                            if data[2] in self.message_from_other_veri_node_dict:
                                json.dumps(['h', data[1], 'ver']).encode()

                            self.connected_protocols_dict[rsp[0]][1]["hearer"][data[1]] = NetworkPropagatorHearer(
                                convo_id=data[1],
                                NetworkPropagatorInstance=self,
                                q_object_for_validator=self.q_object_validator,

                            )

                            reactor.callInThread(self.listen_speak_send, rsp[0], 'hearer', data[1], data[2])
                            # self.connected_protocols_dict[rsp[0]]["hearer"][data[1]].listen(data[2])

                        elif data[0] == 's':
                            reactor.callInThread(self.listen_speak_send, rsp[0], 'hearer', data[1], data[2])
                            # self.connected_protocols_dict[rsp[0]]["hearer"][data[1]].listen(data[2])

                        elif data[0] == "h":
                            reactor.callInThread(self.listen_speak_send, rsp[0], 'speaker', data[1], data[2])
                            # self.connected_protocols_dict[rsp[0]]["speaker"][data[1]].listen(data[2])
                except KeyboardInterrupt:
                    print("ending convo manager")
                    break

                except Exception as e:
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

    def listen_speak_send(self, protocol_id, hearer_or_speaker, convo_id, data2):
        """
        used to listen to ongoing conversation, speak and send what is spoken
        :param protocol_id:
        :param hearer_or_speaker:
        :param convo_id:
        :param data2:
        :return:
        """
        try:
            speaker_or_hearer_dict = self.connected_protocols_dict[protocol_id][1][hearer_or_speaker]
        except KeyError:
            speaker_or_hearer_dict = None

        if speaker_or_hearer_dict and convo_id in speaker_or_hearer_dict and speaker_or_hearer_dict[convo_id]:
            if speaker_or_hearer_dict[convo_id].end_convo is True:
                print(speaker_or_hearer_dict[convo_id].end_convo_reason)
                self.connected_protocols_dict[protocol_id][1][hearer_or_speaker][convo_id] = None

            else:
                self.connected_protocols_dict[protocol_id][1][hearer_or_speaker][convo_id].listen(data2)

                # use protocol's transport.write to send response
                rsp = self.connected_protocols_dict[protocol_id][1][hearer_or_speaker][convo_id].speak()

                # if after listening and speaking end convo is True then snd message to speaker(if speaker will not snd)
                if self.connected_protocols_dict[protocol_id][1][hearer_or_speaker][convo_id].end_convo is True:
                    reason = self.connected_protocols_dict[protocol_id][1][hearer_or_speaker][convo_id].end_convo_reason
                    print("reason in listen_speak: ", reason, hearer_or_speaker)

                    if hearer_or_speaker == "hearer" and reason == "received and validated message":

                        # if message is validated, add hash preview and protocol id to dict
                        # this dict will be used to avoid resending message to node that sent it
                        self.message_from_other_veri_node_dict.update(
                            {
                                self.connected_protocols_dict[protocol_id][1][hearer_or_speaker][convo_id].hash_preview_with_reason: protocol_id
                            }
                        )
                    if hearer_or_speaker == "hearer":
                        self.connected_protocols_dict[protocol_id][0].transport.write(
                            rsp
                        )
                    self.connected_protocols_dict[protocol_id][1][hearer_or_speaker][convo_id] = None

                else:
                    self.connected_protocols_dict[protocol_id][0].transport.write(
                        rsp
                    )

    def check_speak_send(self, validated_message_list):

        if validated_message_list[0] in self.message_from_other_veri_node_dict:

            # connected_protocols_dict = [protocol id: [protocol obj, {'speaker':{convoid: networkspeaker class},
            # 'hearer': {}}, # of convo < 1000]

            for protocol_id in self.connected_protocols_dict:

                if protocol_id != self.message_from_other_veri_node_dict[validated_message_list[0]]:

                    convo_id = self.connected_protocols_dict[protocol_id][2]
                    self.connected_protocols_dict[protocol_id][2]+=1

                    self.connected_protocols_dict[protocol_id][1]["speaker"][convo_id] = NetworkPropagatorSpeaker(
                        validated_message_list=validated_message_list,
                        convo_id=convo_id,

                    )

                    self.connected_protocols_dict[protocol_id][0].transport.write(
                        self.connected_protocols_dict[protocol_id][1]["speaker"][convo_id].speak()
                    )
        else:

            # propagating message received from regular and not received from other nodes
            for protocol_id in self.connected_protocols_dict:

                convo_id = self.connected_protocols_dict[protocol_id][2]
                self.connected_protocols_dict[protocol_id][2]+=1

                self.connected_protocols_dict[protocol_id][1]["speaker"][convo_id] = NetworkPropagatorSpeaker(
                    validated_message_list=validated_message_list,
                    convo_id=convo_id,

                )

                self.connected_protocols_dict[protocol_id][0].transport.write(
                    self.connected_protocols_dict[protocol_id][1]["speaker"][convo_id].speak()
                )


class NetworkPropagatorSpeaker:
    created = 0

    def __init__(self, validated_message_list, convo_id):
        """
        this list is passed from message validators ie AssignmentStatementValidator, TokenTransferValidator etc
        reason message for propagating message is:
        a for assignment statement, b for token transfer, c for token reservation and d for token revoke. different from
        non admin to admin which is "tx_asg" etc (should harmonize)
        :param validated_message_list: [reason, msg hash, pubkey of wallet or admin (if new competitor msg), msg dict]
        """

        # self.reason = validated_message_list[0]
        # self.tx_hash_preview = validated_message_list[1][:8] # first 8 characters of hash
        self.tx_hash_preview_with_reason = validated_message_list[0]  # string with reason letter-8char hash preview
        self.msg_pubkey = validated_message_list[1]
        self.main_msg = validated_message_list[2]  # this will be serialized at later stage
        self.messages_to_be_spoken = iter([self.tx_hash_preview_with_reason, self.main_msg])
        self.messages_heard = set()
        self.end_convo = False
        self.end_convo_reason = ""
        self.sent_pubkey = False
        self.last_msg = 'end'
        self.verified_msg = 'ver'
        self.need_pubkey = 'wpk'
        self.convo_id = convo_id
        self.propagator_type = 's'  # h for hearer
        self.first_msg = True

        NetworkPropagatorSpeaker.created += 1
        self.id = NetworkPropagatorSpeaker.created

    def speak(self):
        print("message in speaker: ", self.messages_heard)

        if self.end_convo is True:
            return self.speaker_helper(self.last_msg)

        elif self.first_msg is True:

            self.first_msg = False
            return json.dumps(['n', self.convo_id, next(self.messages_to_be_spoken)]).encode()

        elif self.verified_msg in self.messages_heard:
            self.end_convo = True
            self.end_convo_reason = "Other side has msg already"
            return self.speaker_helper(self.verified_msg)  # this will not be sent because it is a speaker

        elif self.last_msg in self.messages_heard:
            self.end_convo = True
            self.end_convo_reason = 'other node ended convo'
            return self.speaker_helper(self.last_msg)

        elif self.sent_pubkey is False and self.need_pubkey in self.messages_heard:
            self.sent_pubkey = True
            return self.speaker_helper(self.msg_pubkey)

        else:

            # todo: exception handing if iterator empty
            return self.speaker_helper(next(self.messages_to_be_spoken))

    def listen(self, msg):

        self.messages_heard.add(msg)

    def speaker_helper(self, msg):

        return json.dumps([self.propagator_type, self.convo_id, msg]).encode()


class NetworkPropagatorHearer:

    def __init__(self, q_object_for_validator, NetworkPropagatorInstance, convo_id):

        self.NetworkPropagatorInstance = NetworkPropagatorInstance
        self.q_object_for_validator = q_object_for_validator
        self.reason_validator_dict = {
            'a': AssignmentStatementValidator.AssignmentStatementValidator,
            'b': TokenTransferValidator.TokenTransferValidator,
            'c': TokenReservationRequestValidator.TokenReservationRequestValidator,
            'd': TokenReservationRevokeValidator.TokenReservationRevokeValidator
        }
        self.firstmessage = ''  # first message is reason message/reason key for validator dict
        self.hash_preview = ''
        self.hash_preview_with_reason = ''

        # if none then no check yet, false: node does not have (will receive it), True: Node Has (will not receive it
        self.has_tx = None
        self.message_heard = set()
        self.validator_response = None
        self.end_convo = False
        self.end_convo_reason = ""
        self.last_msg = 'end'
        self.verified_msg = 'ver'
        self.send_tx_msg = 'snd'
        self.need_pubkey = 'wpk'
        self.main_message = ""
        self.is_main_message_valid = ''  # can be None, False, True. None means need pubkey. empty string default

        self.convo_id = convo_id
        self.propagator_type = 'h'  # h for hearer

    def listen(self, msg):
        if self.last_msg in self.message_heard:
            pass

        elif not self.firstmessage:
            if msg[0:1] not in self.reason_validator_dict:
                self.message_heard.add(self.last_msg)
                self.end_convo_reason = "message reason not a valid reason"
                print(self.end_convo_reason)
            else:
                self.firstmessage = msg[0:1]
                self.hash_preview = msg[1:]
                self.hash_preview_with_reason = msg
                self.has_tx = self.hash_preview_with_reason in \
                              self.NetworkPropagatorInstance.validated_message_dict_with_hash_preview


        # has_tx is false and main_message empty then next message should be main message
        elif not self.main_message and self.has_tx is False:

            # tries to turn into python dictionary, if not then ends convo
            try:
                self.main_message = msg
            except ValueError:
                self.message_heard.add(self.last_msg)
            else:

                # tries to run python dictionary of transaction through validator, if KeyError then wrong tx sent
                try:
                    self.is_main_message_valid = self.reason_validator_dict[self.firstmessage](
                        self.main_message,
                        wallet_pubkey=None,
                        q_object=self.q_object_for_validator,
                    ).check_validity()
                except KeyError:  # transaction sent not same as tx_reason stored in self.firstmessage
                    self.message_heard.add(self.last_msg)

                else:

                    # None means node does not have wallet pubkey of client
                    if self.is_main_message_valid is True:
                        self.message_heard.add(self.verified_msg)
                        self.end_convo_reason = "received and validated message"
                    elif self.is_main_message_valid is None:
                        self.message_heard.add(self.need_pubkey)
                    elif self.is_main_message_valid is False:
                        self.message_heard.add(self.last_msg)
                        self.end_convo_reason = "message not valid"

        # means main msg was not able to be validated because of lack of pubkey, current msg should be pubkey
        elif self.main_message and self.is_main_message_valid is None:

            self.is_main_message_valid = self.reason_validator_dict[self.firstmessage](
                self.main_message,
                wallet_pubkey=bytes.fromhex(msg),
                q_object=self.q_object_for_validator,
            ).check_validity()

            # can't be None this time because wallet pubkey provided
            if self.is_main_message_valid is True:
                self.message_heard.add(self.verified_msg)
                self.end_convo_reason = "received and validated message"
            elif self.is_main_message_valid is False:
                self.end_convo_reason = "message not valid"
                self.message_heard.add(self.last_msg)

        else:
            print("MAIN MESSAGE: ", self.main_message)
            print("IS MAIN MESSAGE VALID: ", self.is_main_message_valid)
            print("HAS TRANSACTION: ", self.has_tx)
            self.message_heard.add(msg)

    def speak(self):
        print("message heard in hearer: ",self.message_heard)
        if self.last_msg in self.message_heard:

            # setting this to true will cause NetworkPropagator to delete this instance
            self.end_convo = True
            self.end_convo_reason = "end message heard"
            return self.speaker_helper(self.last_msg)

        elif self.verified_msg in self.message_heard:
            self.end_convo = True
            self.end_convo_reason = "Verified message heard"
            return self.speaker_helper(self.verified_msg)

        elif self.has_tx is True:
            self.end_convo = True
            self.end_convo_reason = "already have message, no need to receive it"
            return self.speaker_helper(self.verified_msg)

        elif self.has_tx is False:
            return self.speaker_helper(self.send_tx_msg)

        elif self.is_main_message_valid is None and self.need_pubkey in self.message_heard:
            return self.speaker_helper(self.need_pubkey)


        else:
            print(self.message_heard)
            self.end_convo_reason = "not able to decide what to speak"
            return self.speaker_helper(self.last_msg)

    def speaker_helper(self, msg):

        return json.dumps([self.propagator_type, self.convo_id, msg]).encode()







