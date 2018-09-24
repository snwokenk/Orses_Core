"""
used to check the wallet information of any wallet id.

This class can be used to get a wallet balance
"""



class WalletInfo:



    @staticmethod
    def get_wallet_balance(admin_inst, wallet_id):

        # returns [available tokens, reserved tokens, total tokens]
        return admin_inst.get_db_manager().get_from_wallet_balances_db(wallet_id=wallet_id)


    @staticmethod
    def get_if_wallet_a_bcw(admin_inst, wallet_id):


