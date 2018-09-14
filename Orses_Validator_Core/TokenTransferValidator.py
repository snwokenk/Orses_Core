from Crypto.Hash import SHA256, RIPEMD160

from Orses_Cryptography_Core.DigitalSignerValidator import DigitalSignerValidator
from Orses_Cryptography_Core.PKIGeneration import WalletPKI
from Orses_Database_Core import RetrieveData, StoreData
import time, json


class TokenTransferValidator:
    def __init__(self, transfer_tx_dict, admin_instance, wallet_pubkey=None,  timelimit=300, q_object=None):
        self.admin_instance = admin_instance
        self.mempool = admin_instance.get_mempool()
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
        self.ntakri_amount = int(float(self.amt) * 10_000_000_000)
        self.fee = transfer_tx_dict["ttx"]["fee"]
        self.ntakri_fee = int(float(self.fee) * 10_000_000_000)
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
        elif (self.check_client_id_owner_of_wallet() is True and
                self.check_signature_valid() is True and
                self.check_timestamp() is True):
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

    def verify_and_modify_wallet_balance(self):
        """
        used to verify token sent has enough balance and then to update temp wallet balances
        these balances move into the main wallet balances when

        :param amount:
        :param fee:
        :return:
        """

        # get wallet balance
        db_manager = self.admin_instance.get_db_manager()

        # wallet balance [int, int, int] = [free token balance, reserved_token_balance, total token]
        # balance in ntakiri ie 1 orses token = 10,000,000,000 (10 billion) ntakiris
        available_tokens, reserved, total = db_manager.get_from_wallet_balances_db(
            wallet_id=self.sending_wid,
            only_value=True
        )

        # check if any for any intermediate balances, and use the lesser of the two
        # this tries to stop double spending of tokens before it is included in the blockchain

        recent_avail_bal, reserved_p, total_p = db_manager.get_from_temp_wallet_balances_prefixed_db(
            wallet_id=self.sending_wid,
            prefix=f'{self.admin_instance.get_mempool.next_block_no}-',
            only_value=True
        )

        # use the less of

        balance_to_use = recent_avail_bal if recent_avail_bal is not None and \
                                             recent_avail_bal < available_tokens else available_tokens

        if balance_to_use >= (self.ntakri_amount+self.ntakri_fee):
            if recent_avail_bal:
                db_manager.insert_into_wallet_balances_prefixed_db(
                    wallet_id=self.sending_wid,
                    wallet_data=[recent_avail_bal - self.ntakri_amount - self.ntakri_fee, reserved_p, total_p],
                    prefix=f'{self.admin_instance.get_mempool.next_block_no}-'
                )

            return True
        else:
            return False

    def calculate_unconfirmed_balance(self, balance_from_blockchain, db_manager):

        db_manager


