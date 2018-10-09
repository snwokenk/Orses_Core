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

    def generate_random_bytes_for_competition(self, length_of_bytes=5):
        """
        will generate random 5 bytes to be sent to competitors as timing trigger
        :param length_of_bytes:
        :return:
        """

    def execute_assignment_statement(self, asgn_stmt_dict, q_obj):
        """

        :param q_obj: queue.Queue object to NetworkPropagtor.run_propagator_convo_initiator
        :param asgn_stmt_dict: main assignment statement dict
        :return: bool, if able to execute or not
        """

        # first verify assignment statement is using a BCW administered by local node
        assignment_statement = asgn_stmt_dict["asgn_stmt"]

        # asgn_stmt_list = [snd_wid, rcv_wid, bcw wid, amt, fee, timestamp, timelimit]
        # timelimit is seconds after timestamp in which an asgn_stmt is considered stale
        asgn_stmt_list = assignment_statement.split(sep='|')

        # query bcw_wid not in self.dict_of_managing_bcw return false and end execution
        # This is then used by ListenerMessages class to relay a 'rej' message to sender
        if not asgn_stmt_list[2] in self.dict_of_managing_bcw:
            return False

        # todo: assignment statement should then be propagated to other proxies of the same BCW (if they don't have it)

        # Now that it's been established that local node manages BCW, check to see if the two
        # if the rcv wallet was newly created then it is managed by the BCW being used by the sender.
        # each local node should have a db oll all wallets of the network, this is done using log messages for
        # assignment statements
        # once queried should

        # query for sender/receiver wallet id balance [available, reserved, total]
        snd_balance = self.admin_inst.get_db_manager().get_from_wallet_balances_db(wallet_id=asgn_stmt_list[0])
        rcv_balance = self.admin_inst.get_db_manager().get_from_wallet_balances_db(wallet_id=asgn_stmt_list[1])

        if len(snd_balance) == 3:
            snd_managed = [False, "blockchain"]
        elif len(snd_balance) > 3 and isinstance(snd_balance[-1], str):
            snd_managed = [True, snd_balance[-1]] if snd_balance[-1] == asgn_stmt_list[2] else [False, snd_balance[-1]]

        else:
            print(f"in ProxyCenter, Execute Assignment statement, could not determine sender wallet manager, debug")
            return False

        if len(rcv_balance) == 3 or rcv_balance[-1] is None:
            rcv_managed = [False, "blockchain"] if rcv_balance[2] > 0 else [True, asgn_stmt_list[2]]
        elif len(rcv_balance) > 3 and isinstance(rcv_balance[-1], str):
            rcv_managed = [True, snd_balance[-1]] if snd_balance[-1] == asgn_stmt_list[2] else [False, snd_balance[-1]]

        else:
            print(f"in ProxyCenter, Execute Assignment statement, could not determine receiver wallet manager, debug")
            return False

        # first and easiest to accomplish is if both receiving and sending wallets managed by same BCW



        wallet_proxy = self.dict_of_managing_bcw[asgn_stmt_list[2]]

        if snd_managed[0] is True and rcv_managed[0] is True:
            # todo: fulfill the easiest, which is when rcving
            pass
        elif snd_managed[0] is True and rcv_managed[0] is False:
            pass
        elif snd_managed[0] is False and rcv_managed[0] is False:
            pass
        elif snd_managed[0] is False and rcv_managed[0] is True:
            pass



