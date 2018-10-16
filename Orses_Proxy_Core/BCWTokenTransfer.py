"""

used to initiate a BCW token transfer.

This is necessary when needing to transfer tokens management from a wallet

When added to the blockchain, the balance of the sender is added to 'payables" of the BCW

The wallet info for the sender then indicates it is managed by the BCW it is managed by
(amounts aren't deducted, deducting/adding of token balances is now managed by the BCW's proxies


Finding the total tokens available on the network is done by summing the total of all Wallets managed by the
blockchain (not all wallets but only wallets directly managed b).
"""
import time, json
from Orses_Cryptography_Core.DigitalSigner import DigitalSigner
from Crypto.Hash import SHA256


class BCWTokenTransfer:

    """
    BCWTokenTransfer = {
        'btt':{
            asgn_stmt: asgn_stmt_dict,
            timestamp: utc timestamp
            proxy_id: admin id of proxy
        }
        'sig': base85 signature string
        'tx_hash': hash of btt (derived by json encoding btt dict and getting SHA256 hash of string"

    }
    """

    def __init__(self, wallet_proxy, asgn_stmt_dict, fee=0.0000000001):
        self.wallet_proxy = wallet_proxy
        self.admin_inst = wallet_proxy.admin_inst
        self.asgn_stmt_dict = asgn_stmt_dict
        self.fee = fee

    def create_btt(self):

        btt = {
            'asgn_stmt': self.asgn_stmt_dict,
            'proxy_id': self.admin_inst.admin_id,
            'timestamp': int(time.time()),
            'fee': self.fee
        }

        return btt

    def sign_and_return_bcw_initiated_token_transfer(self, bcw_proxy_privkey):

        if bcw_proxy_privkey:

            btt = self.create_btt()
            btt_json = json.dumps(btt)
            signature = DigitalSigner.sign_with_provided_privkey(
                dict_of_privkey_numbers=bcw_proxy_privkey,
                message=btt_json
            )
            tx_hash = SHA256.new(btt_json.encode()).hexdigest()

            btt_dict = {
                'btt': btt,
                'sig': signature,
                'tx_hash': tx_hash,
                'asgn_hash': self.asgn_stmt_dict["stmt_hsh"],
                'admin_id': self.admin_inst.admin_id
            }

            return btt_dict
        else:
            return {}



