
"""
used to initiate a Balance Transfer Request. This transaction message is used to transfer a managed wallet's balance
from one BCW to another. The current BCW waits for all transactions relating to the managed wallets account to be done
before executing this request which transfers the management/balance of a wallet to the new BCW

'Transfering a balance' involves transferring the payable balance of one BCW to another.

"""
import time, json
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Crypto.Hash import SHA256


class BalanceTransferRequest:

    def __init__(self, wallet_proxy, asgn_stmt_dict):
        self.wallet_proxy = wallet_proxy
        self.admin_inst = wallet_proxy.admin_inst
        self.asgn_stmt_dict = asgn_stmt_dict

    def create_btr(self):
        pass

    def sign_and_return_balance_transfer_request(self, bcw_proxy_privkey):
        pass