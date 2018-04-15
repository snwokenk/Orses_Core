

class BalanceRetriever:
    """
    class used to retrieve balance of provided wallet id
    """

    def __init__(self, wid, associated_bk_conn_wid):

        self.wallet_id = wid
        self.balance = 0
        self.assc_bk_wid = associated_bk_conn_wid

    def search_blockchain_ttx(self):
        "used to search transfer transaction in blockchian"
        pass

    def search_blockchain_tat(self):
        """
        used to search Token Association Transaction found only in blockchain Genesis Block 0
        :return:
        """
        pass