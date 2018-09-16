from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.PKIGeneration import WalletPKI
from Orses_Database_Core import RetrieveData, StoreData
import time, json


class TokenTransferValidator:
    def __init__(self, transfer_tx_dict, admin_instance, wallet_pubkey=None,  timelimit=300, q_object=None):
        self.admin_instance = admin_instance
        self.mempool = admin_instance.get_mempool()
        self.db_manager = self.admin_instance.get_db_manager()
        self.transfer_tx_dict = transfer_tx_dict
        self.transfer_tx_dict_json = json.dumps(transfer_tx_dict["ttx"])
        self.sending_wallet_pubkey = wallet_pubkey
        self.non_json_wallet_pubkey = None
        self.sending_wid = transfer_tx_dict["ttx"]["snd_wid"]
        self.sending_client_id = transfer_tx_dict["client_id"]
        self.receiving_wid = transfer_tx_dict["ttx"]["rcv_wid"]
        self.signature = transfer_tx_dict["sig"]
        self.tx_hash = transfer_tx_dict["tx_hash"]
        self.timestamp = transfer_tx_dict["ttx"]["time"]
        self.amt = transfer_tx_dict["ttx"]["amt"]
        self.ntakiri_amount = int(float(self.amt) * 10_000_000_000)
        self.fee = transfer_tx_dict["ttx"]["fee"]
        self.ntakiri_fee = int(float(self.fee) * 10_000_000_000)
        self.timelimit = timelimit
        self.unknown_wallet = True if wallet_pubkey else False
        self.q_object = q_object
        self.set_sending_wallet_pubkey()

    def set_sending_wallet_pubkey(self):
        """
        used to retrieve the wallet's pubkey from storage
        :return:
        """
        if self.sending_wallet_pubkey is None:
            snd_wid = self.sending_wid

            self.sending_wallet_pubkey = RetrieveData.RetrieveData.get_pubkey_of_wallet(
                wid=snd_wid,
                user_instance=self.admin_instance
            )
            self.non_json_wallet_pubkey = None if not self.sending_wallet_pubkey else \
                json.loads(self.sending_wallet_pubkey)
            # print(len(snd_wid))
            # print("sending pubkey: ", self.sending_wallet_pubkey)
        else:
            self.non_json_wallet_pubkey = json.loads(self.sending_wallet_pubkey)

    def check_validity(self):
        if self.sending_wallet_pubkey == "":
            return None
        elif (self.check_wallet_balance() is True and
                self.check_client_id_owner_of_wallet() is True and
                self.check_signature_valid() is True and
                self.check_timestamp() is True):

            # store info into unconfirmed leveldb
            rsp = self.db_manager.insert_into_unconfirmed_db(
                tx_type="ttx",
                sending_wid=self.sending_wid,
                tx_hash=self.tx_hash,
                signature=self.signature,
                main_tx=self.transfer_tx_dict,
                amt=self.ntakiri_amount,
                fee=self.ntakiri_fee,
                rcv_wid=self.receiving_wid
            )
            if rsp is False:
                print(f"in TokenTransferValidator, check_validity, not able to insert ttx into unconfirmed db")

            if self.unknown_wallet:
                StoreData.StoreData.store_wallet_info_in_db(
                    wallet_id=self.sending_wid,
                    wallet_owner=self.sending_client_id,
                    wallet_pubkey=self.sending_wallet_pubkey,
                    user_instance=self.admin_instance
                )

            StoreData.StoreData.store_token_transfer_tx_info_in_db(
                amt=self.amt,
                fee=self.fee,
                snd_wid=self.sending_wid,
                rcv_wid=self.receiving_wid,
                time=self.timestamp,
                sig=self.signature,
                json_ttx_dict=self.transfer_tx_dict_json,
                tx_hash=self.tx_hash,
                user_instance=self.admin_instance


            )

            # pass validated message to network propagator and competing process(if active)
            # 'b' reason message for token transfer msg
            if self.q_object:
                try:
                    self.q_object.put([f'b{self.tx_hash[:8]}', self.sending_wallet_pubkey, self.transfer_tx_dict, True])
                except Exception as e:
                    print("in TokenTransferValidator.py, exception in check_validity: ", e)
            return True
        else:
            if self.q_object:
                self.q_object.put([f'b{self.tx_hash[:8]}', self.sending_wallet_pubkey, self.transfer_tx_dict, False])
            return False

    def check_client_id_owner_of_wallet(self):
        step1 = SHA256.new(
            WalletPKI.generate_key_from_parts(
                x=self.non_json_wallet_pubkey["x"],
                y=self.non_json_wallet_pubkey["y"],
                in_bytes=True
            ) + self.sending_client_id.encode()
        ).digest()

        derived_wid = "W" + RIPEMD160.new(step1).hexdigest()

        print("owner check: ", derived_wid == self.sending_wid)

        return derived_wid == self.sending_wid

    def check_signature_valid(self):
        response = DigitalSignerValidator.validate_wallet_signature(msg=self.transfer_tx_dict_json,
                                                                    wallet_pubkey=self.non_json_wallet_pubkey,
                                                                    signature=self.signature)
        print("sig check: ", response)
        if response is True:
            return True
        else:
            return False

    def check_timestamp(self):
        rsp = int(time.time()) < int(self.timestamp + self.timelimit)

        print("time check", rsp)
        return rsp

    def check_inputs(self):
        """
        checks inputs to make sure they of the proper data type ie amount is
        :return: True if inputs are of write data type else False
        """

        try:
            amt = float(self.amt)
            fee = float(self.fee)
        except ValueError:
            print("inputs Check: ", False)
            return False
        else:
            if amt > 0.0 and fee > 0.0: # verify amt and fee is not negative
                print("inputs Check: ", True)
                return True
            else:
                print("inputs Check: ", False)
                return False

    def check_wallet_balance(self):

        # get wallet balance

        # wallet balance [int, int, int] = [free token balance, reserved_token_balance, total token]
        # balance in ntakiri ie 1 orses token = 10,000,000,000 (10 billion) ntakiris
        # balance gotten from blockchain
        available_bal, reserved, total = self.db_manager.get_from_wallet_balances_db(
            wallet_id=self.sending_wid,
            only_value=True
        )

        unconfirmed_bal = available_bal + self.get_token_change_from_unconfirmed()

        # will choose the less of the balance
        if self.ntakiri_amount >= (unconfirmed_bal if unconfirmed_bal < available_bal else available_bal):
            print("in TokenTransfer, Balance Validated")
            return True
        else:
            print("in TokenTransfer, Balance NOT Validated")
            return False

    def get_token_change_from_unconfirmed(self):

        token_change = 0
        # [[tx_type, "sender" or "receiver, main_tx, sig, tx_hash,fee,  amt_tokens(sender=neg., receiver=pos. ],...]
        unconfirmed_wallet_activities = self.db_manager.get_from_unconfirmed_db_wid(
            wallet_id=self.sending_wid,
            only_value=True
        )

        for activity in unconfirmed_wallet_activities:
            #              tkn amount     fee  These will be negative if wallet_id was sender and positive if receiver
            token_change += activity[-1]+activity[-2]

        return token_change

    # def verify_and_modify_wallet_balance(self):
    #
    #     """
    #     used to verify token sent has enough balance and then to update temp wallet balances
    #     these balances move into the main wallet balances when
    #
    #     :param amount:
    #     :param fee:
    #     :return:
    #     """
    #
    #     # get wallet balance
    #     db_manager = self.admin_instance.get_db_manager()
    #
    #     # wallet balance [int, int, int] = [free token balance, reserved_token_balance, total token]
    #     # balance in ntakiri ie 1 orses token = 10,000,000,000 (10 billion) ntakiris
    #     available_tokens, reserved, total = db_manager.get_from_wallet_balances_db(
    #         wallet_id=self.sending_wid,
    #         only_value=True
    #     )
    #
    #     # check if any for any intermediate balances, and use the lesser of the two
    #     # this tries to stop double spending of tokens before it is included in the blockchain
    #
    #     recent_avail_bal, reserved_p, total_p = db_manager.get_from_temp_wallet_balances_prefixed_db(
    #         wallet_id=self.sending_wid,
    #         prefix=f'{self.admin_instance.get_mempool.next_block_no}-',
    #         only_value=True
    #     )
    #
    #     balance_to_use = recent_avail_bal if recent_avail_bal is not None and \
    #                                          recent_avail_bal < available_tokens else available_tokens
    #
    #     if balance_to_use >= (self.ntakiri_amount + self.ntakiri_fee):
    #         if recent_avail_bal:
    #             db_manager.insert_into_wallet_balances_prefixed_db(
    #                 wallet_id=self.sending_wid,
    #                 wallet_data=[recent_avail_bal - self.ntakiri_amount - self.ntakiri_fee, reserved_p, total_p],
    #                 prefix=f'{self.admin_instance.get_mempool.next_block_no}-'
    #             )
    #
    #         return True
    #     else:
    #         return False
    #
    # def calculate_unconfirmed_balance(self, wallet_id,  blockchain_bal, reserved_bal,  db_manager):
    #
    #     # [[tx_type, "sender" or "receiver, main_tx, sig, tx_hash, fee, amt_tokens(sender=neg., receiver=pos. ], ....]
    #     recent_activity = db_manager.get_from_unconfirmed_db_wid(
    #         wallet_id=wallet_id,
    #         only_value=True
    #     )
    #     for snd_act in recent_activity:
    #         if snd_act[0] == "ttx":
    #
    #             # if not "sender" negate negative with a -, this will mean bal is added to not taken away from
    #             blockchain_bal += (snd_act[-1]+snd_act[-2]) if snd_act[1] == "sender" else -(snd_act[-1]+snd_act[-2])
    #
    #         elif snd_act[0] in {"rvk_req", "rsv_req"}:
    #             blockchain_bal += (snd_act[-1]+snd_act[-2]) if snd_act[0] == "rsv_req" else -snd_act[-1]
    #             reserved_bal += -snd_act[-1]
    #
    #
    #     return blockchain_bal



