
"""
used to initiate a Balance Transfer Request. This transaction message is used to transfer a managed wallet's balance
from one BCW to another. The current BCW waits for all transactions relating to the managed wallets account to be done
before executing this request which transfers the management/balance of a wallet to the new BCW

'Transfering a balance' involves transferring the payable balance of one BCW to another.


main btr dict should have keys:
asgn_stmt_dict  # receiving wid is found in asgn_stmt_dict
sending bcw



final btr dict keys:

btr
tx_hash (using json encoded btr
asgn_stmt hash
signature
admin id

"""
import time, json
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Crypto.Hash import SHA256

from Orses_Proxy_Core.BaseProxyMessage import BaseProxyMessage


class BalanceTransferRequest(BaseProxyMessage):

    def __init__(self, wallet_proxy, asgn_stmt_dict, bcw_with_balance, asgn_sender_pubkey):

        super().__init__(wallet_proxy=wallet_proxy, asgn_stmt_dict=asgn_stmt_dict)
        self.bcw_with_balance = bcw_with_balance  # The BCW transferring the balance
        self.asgn_sender_pubkey = asgn_sender_pubkey

    def create_main_transaction(self):
        btr = {
            "asgn_stmt": self.asgn_stmt_dict,
            'snd_bcw': self.bcw_with_balance,  # the BCW that is being requested to transfer balance

        }

        return btr

    def sign_and_return_balance_transfer_request(self, bcw_proxy_privkey):

        btr_dict, main_dict = self.sign_and_return_main_transaction(bcw_proxy_privkey=bcw_proxy_privkey)

        if btr_dict:
            btr_dict['btr'] = main_dict
            btr_dict['a_snd_pubkey'] = self.asgn_sender_pubkey  # pubkey of wallet that sent assignment stmt

        return btr_dict

