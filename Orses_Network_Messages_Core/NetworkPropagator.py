"""
This module will be used  propagate messages to other verification nodes or admin nodes.
Messages are gotten from
"""
from Orses_Validator_Core import AssignmentStatementValidator, TokenTransferValidator, \
    TokenReservationRequestValidator, TokenReservationRevokeValidator

import json


class NetworkPropagator:

    def __init__(self, q_object_connected_to_validator, q_for_propagate, q_object_to_competing_process=None):
        """

        :param q_object_connected_to_validator: q object used to get validated messages from Message validators
        :param q_object_to_competing_process: q object used to send new validated messages to competing process,
        if active
        """
        self.q_object_validator = q_object_connected_to_validator
        self.q_object_compete = q_object_to_competing_process
        self.validated_message_dict = dict()

        # dict with hash previews as dict keys ( this can be updated using binary search Tree) will do for now
        self.validated_message_dict_with_hash_preview = dict()

    def run_propagator(self):

        # this method will be run in in another process using multiprocessing.Process
        # plan is to run NetworkPropagatorHearer
        while True:
            pass


class NetworkPropagatorSpeaker:

    def __init__(self, validated_message_list):
        """
        this list is passed from message validators ie AssignmentStatementValidator, TokenTransferValidator etc
        reason message for propagating message is:
        a for assignment statement, b for token transfer, c for token reservation and d for token revoke. different from
        non admin to admin which is "tx_asg" etc (should harmonize)
        :param validated_message_list: [reason, msg hash, pubkey of wallet or admin (if new competitor msg), msg dict]
        """

        self.reason = validated_message_list[0]
        self.tx_hash_preview = validated_message_list[1][:8] # first 8 characters of hash
        self.tx_hash_preview_with_reason = f'{self.reason}{self.tx_hash_preview}'
        self.msg_pubkey = validated_message_list[2]
        self.main_msg = json.dumps(validated_message_list[3])
        self.messages_to_be_spoken = iter([self.tx_hash_preview_with_reason.encode(), self.main_msg.encode()])
        self.messages_heard = set()
        self.end_convo = False
        self.sent_pubkey = False
        self.last_msg = b'end'
        self.need_pubkey = b'wpk'

    def speak(self):

        if self.end_convo is True:
            return self.last_msg
        elif self.last_msg in self.messages_heard:
            self.end_convo = True
            return self.last_msg
        elif self.sent_pubkey is False and self.need_pubkey in self.messages_heard:
            self.sent_pubkey = True
            return self.msg_pubkey.encode()
        else:
            return next(self.messages_to_be_spoken)

    def listen(self, msg):

        self.messages_heard.update(msg)


class NetworkPropagatorHearer:
    def __init__(self, q_object_for_validator, NetworkPropagatorInstance):
        self.NetworkPropagatorInstance = NetworkPropagatorInstance
        self.q_object_for_validator = q_object_for_validator
        self.reason_validator_dict = {
            b'a': AssignmentStatementValidator.AssignmentStatementValidator,
            b'b': TokenTransferValidator.TokenTransferValidator,
            b'c': TokenReservationRequestValidator.TokenReservationRequestValidator,
            b'd': TokenReservationRevokeValidator.TokenReservationRevokeValidator
        }
        self.firstmessage = b''  # first message is reason message/reason key for validator dict
        self.hash_preview = ''

        # if none then no check yet, false: node does not have (will receive it), True: Node Has (will not receive it
        self.has_tx = None
        self.message_heard = set()
        self.validator_response = None
        self.end_convo = False
        self.last_msg = b'end'
        self.verified_msg = b'ver'
        self.send_tx_msg = b'snd'
        self.need_pubkey = b'wpk'
        self.main_message = ""
        self.valid_main_message = ''  # can be None, False, True. None means need pubkey. empty string default

    def listen(self, msg):
        if self.last_msg in self.message_heard:
            pass

        elif not self.firstmessage:
            if msg[0:1] not in self.reason_validator_dict:
                self.message_heard.update(self.last_msg)
            else:
                self.firstmessage = msg[0:1]
                self.hash_preview = msg[1:].decode()

        # has_tx is false and main_message empty then next message should be main message
        elif not self.main_message and self.has_tx is False:

            # tries to turn into python dictionary, if not then ends convo
            try:
                self.main_message = json.loads(msg.decode())
            except ValueError:
                self.message_heard.update(self.last_msg)
            else:

                # tries to run python dictionary of transaction through validator, if KeyError then wrong tx sent
                try:
                    self.valid_main_message = self.reason_validator_dict[self.firstmessage](
                        self.main_message,
                        wallet_pubkey=None,
                        q_object=self.q_object_for_validator,
                    ).check_validity()
                except KeyError:  # transaction sent not same as tx_reason stored in self.firstmessage
                    self.message_heard.update(self.last_msg)

                else:

                    # None means node does not have wallet pubkey of client
                    if self.valid_main_message is True:
                        self.message_heard.update(self.verified_msg)
                    elif self.valid_main_message is None:
                        self.message_heard.update(self.need_pubkey)
                    elif self.valid_main_message is False:
                        self.message_heard.update(self.last_msg)

        # means main msg was not able to be validated because of lack of pubkey, current msg should be pubkey
        elif self.main_message and self.valid_main_message is None:

            self.valid_main_message = self.reason_validator_dict[self.firstmessage](
                self.main_message,
                wallet_pubkey=bytes.fromhex(msg.decode()),
                q_object=self.q_object_for_validator,
            ).check_validity()

            # can't be None this time because wallet pubkey provided
            if self.valid_main_message is True:
                self.message_heard.update(self.verified_msg)
            elif self.valid_main_message is False:
                self.message_heard.update(self.last_msg)

        else:
            self.message_heard.update(msg)

    def speak(self):
        if self.last_msg in self.message_heard:
            # setting this to true will cause NetworkPropagator to delete this instance
            self.end_convo = True
            return self.last_msg
        elif self.verified_msg in self.message_heard:
            self.end_convo = True
            return self.verified_msg
        elif self.valid_main_message is None and self.need_pubkey in self.message_heard:
            return self.need_pubkey

        elif self.has_tx is None and self.hash_preview:
            self.has_tx = self.hash_preview in self.NetworkPropagatorInstance.validated_message_dict_with_hash_preview

            if self.has_tx is True:
                self.end_convo = True
                return self.verified_msg  # instructs NetworkPropagator to delete this instance
            elif self.has_tx is False:
                return self.send_tx_msg
        else:
            print(self.message_heard)
            return self.last_msg







