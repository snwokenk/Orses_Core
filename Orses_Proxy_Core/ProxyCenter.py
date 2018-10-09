"""

Proxy center is used to load WalletProxy instances and call certain methods needed to to validate and execute
conditions of an assignment statement
"""
from Orses_Proxy_Core.WalletProxy import WalletProxy


class ProxyCenter:
    def __init__(self, admin_inst):

        self.admin_inst = admin_inst
        self.db_manager = self.admin_inst.get_db_manager()

        # dict_of_managing_bcw = {"wallet_id": WalletProxy Instance}
        self.dict_of_managing_bcw = dict()

    def initiate_new_proxy(self, bcw_wid: str, overwrite=False):

        # initiate walletProxy
        new_proxy = WalletProxy(
            proxy_center=self,
            bcw_wid=bcw_wid,
            new_proxy=True,
            overwrite=overwrite
        )

        pubkey = new_proxy.get_pubkey()

        # insert into dict_of_managing_bcw, if pubkey Truthy (not empty, false or None
        if pubkey:


            self.dict_of_managing_bcw[bcw_wid] = new_proxy
            bcw_administered_list = list(self.dict_of_managing_bcw.keys())
            self.admin_inst.fl.save_json_into_file(
                filename="list_of_administered_bcws",
                python_json_serializable_object=bcw_administered_list,
                in_folder=self.admin_inst.fl.get_proxy_folder_path()
            )

            # return pubkey
            return pubkey
        else:
            # will  not insert into dict and will return
            return {}

    def load_a_proxy(self, bcw_wid):

        loaded_proxy = WalletProxy(
            proxy_center=self,
            bcw_wid=bcw_wid,
            new_proxy=False,
            overwrite=False
        )
        pubkey = loaded_proxy.get_pubkey()
        if pubkey:
            return loaded_proxy

        else:
            print(f"in load_a_proxy, Could not load proxy pubkey/privkey. WID is {bcw_wid}")
            return None

    def load_administered_proxies(self):

        bcw_administered_list = self.admin_inst.fl.open_file_from_json(
            filename="list_of_administered_bcws",
            in_folder=self.admin_inst.fl.get_proxy_folder_path()
        )
        for bcw_wid in bcw_administered_list:
            loaded_proxy = self.load_a_proxy(bcw_wid=bcw_wid)
            if loaded_proxy:
                self.dict_of_managing_bcw[bcw_wid] = loaded_proxy

        if self.dict_of_managing_bcw:
            return True
        else:
            return False

    def execute_assignment_statement(self, asgn_stmt, q_obj):
        """

        :param q_obj: queue.Queue object to NetworkPropagtor.run_propagator_convo_initiator
        :param asgn_stmt: main assignment statement dict
        :return: bool, if able to execute or not
        """









