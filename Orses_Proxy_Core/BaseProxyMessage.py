import time, json
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Crypto.Hash import SHA256


class BaseProxyMessage:

    def __init__(self, wallet_proxy, asgn_stmt_dict):

        self.wallet_proxy = wallet_proxy
        self.admin_inst = wallet_proxy.admin_inst
        self.asgn_stmt_dict = asgn_stmt_dict

    def create_main_transaction(self):
        # Override
        pass

    def sign_and_return_main_transaction(self, bcw_proxy_privkey):

        main_tx = self.create_main_transaction()

        if bcw_proxy_privkey and main_tx:

            btt_json = json.dumps(main_tx)
            signature = DigitalSigner.sign_with_provided_privkey(
                dict_of_privkey_numbers=None,
                message=btt_json,
                key=bcw_proxy_privkey
            )
            tx_hash = SHA256.new(btt_json.encode()).hexdigest()

            btt_dict = {
                'sig': signature,
                'tx_hash': tx_hash,
                'asgn_hash': self.asgn_stmt_dict["stmt_hsh"],
                'admin_id': self.admin_inst.admin_id
            }

            return btt_dict, main_tx
        else:
            return {}, {}