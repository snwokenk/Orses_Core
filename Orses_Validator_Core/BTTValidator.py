
from Orses_Validator_Core import BaseProxyMessageValidator, AssignmentStatementValidator



import time, json


class BTTValidator(BaseProxyMessageValidator.BaseProxyMessageValidator):

    def __init__(self, btt_dict, admin_instance, wallet_pubkey=None, time_limit=300, q_object=None, asgn_validated=False):

        self.btt_dict = btt_dict
        self.btt = btt_dict['btt']

        # required by base class
        self.snd_admin_id = btt_dict["admin_id"]

        self.signature = btt_dict["sig"]

        # required by validate_asgn_stmt() method in base class
        self.asgn_sender_pubkey = btt_dict["a_snd_pubkey"]

        self.btt_hash = btt_dict['tx_hash']
        self.related_asgn_stmt_dict = self.btt['asgn_stmt']

        # related_list = [snd_wid, rcv_wid, bcw wid, amt, fee, timestamp, timelimit]
        self.related_asgn_stmt_list = self.related_asgn_stmt_dict['asgn_stmt'].split(sep='|')

        # bcw wid
        self.bcw_wid = self.related_asgn_stmt_list[2]

        self.asgn_stmt_sndr = self.related_asgn_stmt_list[0]

        # required by method
        self.main_dict_json = json.dumps(self.btt)

        self.btt_fee = self.btt["fee"]

        # call init of BaseClass
        super().__init__(
            admin_instance=admin_instance,
            wallet_pubkey=wallet_pubkey,
            time_limit=time_limit,
            q_object=q_object,
            asgn_validated=asgn_validated

        )

        # inherited from Baseclass
        self.set_sending_wallet_pubkey()

    def check_validity(self):
        if not self.non_json_proxy_pubkey:  # if empty dict {}
            return None
        elif self.non_json_proxy_pubkey is False:
            return False

        if self.check_signature_valid() is True and self.check_node_is_valid_proxy() and self.validate_asgn_stmt():

            # refactor this, to allow for inclusion into wallet of sender and BCW_WID wallet
            # sending_wid is the BCW and receiving id is the asgn stmt senders wid
            self.db_manager.insert_into_unconfirmed_db(
                tx_type="btt",
                sending_wid=self.bcw_wid,
                tx_hash=self.btt_hash,
                signature=self.signature,
                main_tx=self.btt_dict,
                amt=0.0,
                fee=self.btt_fee,
                rcv_wid=self.asgn_stmt_sndr
            )

            # send btt to NetworkPropagator.run_propagator_convo_initiator
            self.q_object.put([f'e{self.btt_hash[:8]}', json.dumps(self.non_json_proxy_pubkey), self.btt_dict, True])
            return True
        else:
            self.q_object.put([f'e{self.btt_hash[:8]}', json.dumps(self.non_json_proxy_pubkey), self.btt_dict, False])
            return False







