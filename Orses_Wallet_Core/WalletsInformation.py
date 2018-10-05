"""
used to check the wallet information of any wallet id.

This class can be used to get a wallet balance
"""

import time

class WalletInfo:


    @staticmethod
    def get_wallet_balance_info(admin_inst, wallet_id):
        """
        Is sent to client when requesting for  balance
        :param admin_inst:
        :param wallet_id:
        :return:
        """

        # returns [available tokens, reserved tokens, total tokens]
        confirmed_balance = admin_inst.get_db_manager().get_from_wallet_balances_db(wallet_id=wallet_id)

        # {tx_hash: [tx_type, "sender" or "receiver, main_tx, sig,fee,  amt_tokens(sender=neg., receiver=pos.]}
        pending_txs = WalletInfo.get_pending_transactions(admin_inst=admin_inst, wallet_id=wallet_id)

        return [confirmed_balance, pending_txs]




    @staticmethod
    def get_pending_transactions(admin_inst, wallet_id):

        # {tx_hash: [tx_type, "sender" or "receiver, main_tx, sig,fee,  amt_tokens(sender=neg., receiver=pos.]}
        return admin_inst.get_db_manager().get_from_unconfirmed_db_wid(
            wallet_id=wallet_id
        )


    @staticmethod
    def get_lesser_of_wallet_balance(admin_inst, wallet_id):
        """
        This is used internally to get the lesser of balance.

        Either the balance found on the blockchain is used OR balance of blockchain + tokens sent/received

        lesser_of_bal = confirmed_bal if confirmed_bal < pending_bal else pending_bal

        :param admin_inst:
        :param wallet_id:
        :return:
        """

        confirmed_bal, pending_txs= WalletInfo.get_wallet_balance_info(admin_inst, wallet_id)
        confirmed_bal = confirmed_bal[0]  # select only available bal
        token_change = 0
        for activity in pending_txs.values():
            #              tkn amount     fee  These will be negative if wallet_id was sender and positive if receiver
            token_change += activity[-1]+activity[-2]

        pending_bal = confirmed_bal + token_change

        return confirmed_bal if confirmed_bal < pending_bal else pending_bal

    @staticmethod
    def get_wallet_bcw_info(admin_inst, wallet_id):


        # [hash of rsv_req tx, rsv req dict, signature, amount reserved, timestamp of reservation exp]
        wallet_bcw = admin_inst.get_db_manager().get_from_bcw_db(wallet_id=wallet_id)
        return wallet_bcw

    @staticmethod
    def get_if_wallet_a_bcw(admin_inst, wallet_id):

        """
        Check if wallet is a blockchain connected wallet
        :param admin_inst:
        :param wallet_id:
        :return:
        """
        wallet_bcw = WalletInfo.get_wallet_bcw_info(admin_inst=admin_inst, wallet_id=wallet_id)

        return True if wallet_bcw else False


    @staticmethod
    def check_remaining_reservation_time(admin_inst, wallet_id):
        """

        :param admin_inst:
        :param wallet_id:
        :return: int: representing remaining time Or None if wallet is not a BCW
        """

        wallet_bcw_entry = WalletInfo.get_wallet_bcw_info(admin_inst, wallet_id)

        if wallet_bcw_entry:
            return wallet_bcw_entry[-1] - int(time.time())

        else:
            return None


