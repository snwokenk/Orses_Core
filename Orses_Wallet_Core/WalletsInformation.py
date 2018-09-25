"""
used to check the wallet information of any wallet id.

This class can be used to get a wallet balance
"""

import time

class WalletInfo:


    @staticmethod
    def get_wallet_balance(admin_inst, wallet_id):

        # returns [available tokens, reserved tokens, total tokens]
        return admin_inst.get_db_manager().get_from_wallet_balances_db(wallet_id=wallet_id)

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


