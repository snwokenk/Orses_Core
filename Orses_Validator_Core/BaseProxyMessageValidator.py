

class BaseProxyMessageValidator:
    def __init__(self, proxy_msg_tx_dict, admin_instance, wallet_pubkey=None,  timelimit=300, q_object=None):

        self.admin_instance = admin_instance
        self.mempool = admin_instance.get_mempool()
        self.db_manager = self.admin_instance.get_db_manager()

        # to maintain compatibility argument is called wallet_pubkey but should be bcw_proxy_pubkey
        self.bcw_proxy_pubkey = wallet_pubkey
        self.non_json_proxy_pubkey = None

