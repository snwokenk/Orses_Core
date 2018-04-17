"""
This module will be used connect propagate messages to other verification nodes or admin nodes.
Before propagating
"""

import json


class NetworkPropagator:
    def __init__(self, q_object_connected_to_validator, q_object_to_competing_process=None):
        """

        :param q_object_connected_to_validator:
        :param q_object_to_competing_process:
        """
        self.q_object_validator = q_object_connected_to_validator
        self.q_object_compete = q_object_to_competing_process


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
        self.last_msg = b'end'

    def speak(self):

        if self.end_convo is True:
            return self.last_msg
        elif self.last_msg in self.messages_heard:
            self.end_convo = True
            return self.last_msg
        else:
            return next(self.messages_to_be_spoken)

    def listen(self, msg):

        self.messages_heard.update(msg)