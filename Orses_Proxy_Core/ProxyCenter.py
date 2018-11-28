"""

Proxy center is used to load WalletProxy instances and call certain methods needed to to validate and execute
conditions of an assignment statement
"""
from Orses_Proxy_Core.WalletProxy import WalletProxy
from  Orses_Proxy_Core.ProxyNetworkCommunicator import ProxyNetworkCommunicator
from Orses_Wallet_Core.WalletsInformation import WalletInfo
from Orses_Validator_Core import BTTValidator, BTRValidator
import json, time


class ProxyCenter:
    def __init__(self, admin_inst, is_program_running):

        self.admin_inst = admin_inst
        self.is_program_running = is_program_running
        self.db_manager = self.admin_inst.db_manager

        # dict_of_managing_bcw = {"wallet_id": WalletProxy Instance}
        self.dict_of_managing_bcw = dict()

        # dict of messages, is updated by networkPropagator as a way to communicate with proxy center
        self.dict_of_expected_messages = dict()

        # dict of callables
        self.dict_of_callables = dict()

        # message sent by protocol center telling peer node to wait
        self.wait_msg = b'wait'

        self.proxy_communicator = ProxyNetworkCommunicator(
            proxy_center_inst=self
        )

    def __load_proxy_center(self):

        bcw_administered_list = self.admin_inst.fl.open_file_from_json(
            filename="list_of_administered_bcws",
            in_folder=self.admin_inst.fl.get_proxy_center_folder_path()
        )

        for bcw_wid in bcw_administered_list:
            self.dict_of_managing_bcw[bcw_wid] = WalletProxy(
                proxy_center=self,
                bcw_wid=bcw_wid,
                new_proxy=False,
                overwrite=False
            )

    def get_db_manager(self):

        return self.admin_inst.get_db_manager()

    def get_proxy_communicator(self):
        return self.proxy_communicator

    def get_a_proxy_pubkey(self, bcw_wid, admin_id_of_proxy):
        bcw_proxy_id = f"{bcw_wid}{admin_id_of_proxy}"

        proxy_pubkey = self.db_manager.get_proxy_pubkey(proxy_id=bcw_proxy_id)

        return proxy_pubkey

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
                in_folder=self.admin_inst.fl.get_proxy_center_folder_path()
            )

            # return pubkey
            return pubkey
        else:
            # will  not insert into dict and will return
            print(f"Proxycenter.initiate_new_proxy pubkey not able to load {pubkey}")
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
            self.dict_of_managing_bcw[bcw_wid] = loaded_proxy
            return loaded_proxy

        else:
            print(f"in load_a_proxy, Could not load proxy pubkey/privkey. WID is {bcw_wid}")
            return None

    def get_a_proxy(self, bcw_wid):

        return self.dict_of_managing_bcw.get(bcw_wid, None)

    def load_administered_proxies(self):

        # todo: later, logic involving syncing of data among other proxies will be added,
        # todo: this might be on the Proxycenter level or individual WalletProxy level. ind. proxies preferred

        bcw_administered_list = self.admin_inst.fl.open_file_from_json(
            filename="list_of_administered_bcws",
            in_folder=self.admin_inst.fl.get_proxy_center_folder_path()
        )
        for bcw_wid in bcw_administered_list:
            self.load_a_proxy(bcw_wid=bcw_wid)

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

    def execute_assignment_statement(self, asgn_stmt_dict, q_obj, protocol, reactor_inst, wallet_pubkey=None, **kwargs):
        """

        asgn_stmt_dict = {
                "asgn_stmt": "snd_wid|rcv_wid|bcw wid|amt|fee|timestamp|timelimit",
                "sig": signature, Base85 encoded string (must be encoded back to byte then decoded from base85 encoding
                "stmt_hsh": statement_hash, SHA256 hash
                "client_id": Hex ID
            }
        :param q_obj: queue.Queue object to NetworkPropagtor.run_propagator_convo_initiator
        :param asgn_stmt_dict: main assignment statement dict
        :param kwargs: if kwargs is not empty then it should include the necessary information needed to execute the
                    assignment statement. This is usually if a wallet pubkey was needed
        :return: bool, if able to execute or not
        """

        if not kwargs:
            # first verify assignment statement is using a BCW administered by local node
            assignment_statement = asgn_stmt_dict["asgn_stmt"]

            # asgn_stmt_list = [snd_wid, rcv_wid, bcw wid, amt, fee, timestamp, timelimit]
            # timelimit is seconds after timestamp in which an asgn_stmt is considered stale
            asgn_stmt_list = assignment_statement.split(sep='|')

            # query bcw_wid not in self.dict_of_managing_bcw return false and end execution
            # This is then used by ListenerMessages class to relay a 'rej' message to sender
            if not asgn_stmt_list[2] in self.dict_of_managing_bcw:
                print(f"in Proxycenter.execute_assignment_statement, BCW not in dict_of_managing_BCW\n"
                      f"dict_of_managing_bcw is: {self.dict_of_managing_bcw}\n"
                      f"BCW_WID is {asgn_stmt_list[2]}")
                return [False]  # must return a list

            # todo: assignment statement should then be propagated to other proxies of the same BCW (if they don't have it)

            # Now that it's been established that local node manages BCW, check to see if the two
            # if the rcv wallet was newly created then it is managed by the BCW being used by the sender.
            # each local node should have a db oll all wallets of the network, this is done using log messages for
            # assignment statements
            # once queried should

            # query for sender/receiver wallet id balance [available, reserved, total]
            snd_wallet_info = WalletInfo.get_wallet_balance_info(admin_inst=self.admin_inst, wallet_id=asgn_stmt_list[0])
            snd_balance = snd_wallet_info[0]
            snd_pending_tx = snd_wallet_info[1]

            rcv_wallet_info = WalletInfo.get_wallet_balance_info(admin_inst=self.admin_inst, wallet_id=asgn_stmt_list[1])
            rcv_balance = rcv_wallet_info[0]
            rcv_pending_tx = rcv_wallet_info[1]

            if len(snd_balance) == 3:
                snd_managed = [False, "blockchain"]
            elif len(snd_balance) > 3 and isinstance(snd_balance[-1], str):
                snd_managed = [True, snd_balance[-1]] if snd_balance[-1] == asgn_stmt_list[2] else [False, snd_balance[-1]]

            else:
                print(f"in ProxyCenter, Execute Assignment statement, could not determine sender wallet manager, debug\n"
                      f"snd_wallet_info {snd_wallet_info}")
                return [False]

            if len(rcv_balance) == 3 or rcv_balance[-1] is None:
                rcv_managed = [False, "blockchain"] if rcv_balance[2] > 0 else [True, asgn_stmt_list[2]]
            elif len(rcv_balance) > 3 and isinstance(rcv_balance[-1], str):
                rcv_managed = [True, snd_balance[3]] if snd_balance[3] == asgn_stmt_list[2] else [False, snd_balance[3]]

            else:
                print(f"in ProxyCenter, Execute Assignment statement, could not determine receiver wallet manager, debug\n"
                      f"rcv_wallet_info {rcv_wallet_info}")
                return [False]
        else:
            snd_managed = kwargs['snd_managed']
            snd_wallet_info = kwargs['snd_wallet_info']
            snd_pending_tx = snd_wallet_info[1]
            rcv_managed = kwargs['rcv_managed']
            snd_balance = kwargs["snd_balance"]
            rcv_balance = kwargs["rcv_balance"]
            asgn_stmt_list = kwargs['stmt_list']
            asgn_stmt_dict = kwargs['stmt_dict']

        # ***** Execute Assignment statement according to scenario ******
        # set wallet proxy to use
        wallet_proxy: WalletProxy = self.dict_of_managing_bcw[asgn_stmt_list[2]]

        if snd_managed[0] is True and rcv_managed[0] is True:
            rsp = wallet_proxy.execute_asgn_stmt_both_managed(
                asgn_stmt_dict=asgn_stmt_dict,
                stmt_list=asgn_stmt_list,
                snd_balance=snd_balance,
                wallet_pubkey=wallet_pubkey
            )

            # once returned to ListenerMessages will send a need pubkey message
            # if kwargs is not empty then pubkey should have been sent
            if rsp is None and not kwargs:
                k = dict()
                k['snd_managed'] = snd_managed
                k["snd_wallet_info"] = snd_wallet_info
                k['rcv_managed'] = rcv_managed
                k["snd_balance"] = snd_balance
                k["rcv_balance"] = rcv_balance
                k["stmt_list"] = asgn_stmt_list
                k["stmt_dict"] = asgn_stmt_dict
                return [None, k]

            # assignment statement has been executed
            elif isinstance(rsp, dict):
                rsp_str = json.dumps(rsp)
                return [True, rsp_str]

            else:
                return [False]

        elif snd_managed[0] is True and rcv_managed[0] is False:
            # senders wallet managed by proxy's BCW and receiver's managed by another BCW or directly on the blockchain
            # things to take into consideration is when a node is proxy for both BCW or for only one.
            # Also if the
            pass
        elif snd_managed[0] is False and rcv_managed[0] is False:
            #
            pass
        elif snd_managed[0] is False and rcv_managed[0] is True:
            rsp = wallet_proxy.execute_asgn_stmt_rcv_managed(
                asgn_stmt_dict=asgn_stmt_dict,
                stmt_list=asgn_stmt_list,
                snd_balance=snd_balance,
                wallet_pubkey=wallet_pubkey,
                snd_pending_tx=snd_pending_tx,
                snd_bcw_manager=snd_managed[-1]
            )

            if rsp is None and not kwargs:
                k = dict()
                k['snd_managed'] = snd_managed
                k["snd_wallet_info"] = snd_wallet_info
                k['rcv_managed'] = rcv_managed
                k["snd_balance"] = snd_balance
                k["rcv_balance"] = rcv_balance
                k["stmt_list"] = asgn_stmt_list
                k["stmt_dict"] = asgn_stmt_dict
                return [rsp, k]

            elif rsp is None and kwargs:
                return [False]

            # callable is stored, btt message is sent to NetworkPropagtor for propagation
            # rsp = ['defer', btt_dict, a_callable]
            elif isinstance(rsp, list) and rsp[0] == "defer":
                btt_or_btr_dict: dict = rsp[1]
                update_balance_callback = rsp[2]

                if 'btt' in btt_or_btr_dict:

                    # add BTT validator, this just validates local node
                    is_btt_validated = BTTValidator.BTTValidator(
                        admin_instance=self.admin_inst,
                        btt_dict=btt_or_btr_dict,
                        wallet_pubkey=wallet_proxy.bcw_proxy_pubkey,
                        q_object=q_obj,
                        asgn_validated=True
                    ).check_validity()

                    # wait and check for blockchain inclusion, then update
                    if is_btt_validated is True:

                        # asgn_stmt_list = [snd_wid, rcv_wid, bcw wid, amt, fee, timestamp, timelimit]
                        response = self.wait_and_notify_of_blockchain_inclusion(
                            update_balance_callback=update_balance_callback,
                            end_timestamp=int(asgn_stmt_list[5]) + int(asgn_stmt_list[6]),
                            snd_wid=asgn_stmt_list[0],
                            bcw_wid=asgn_stmt_list[2],
                            protocol=protocol,

                        )

                    else:
                        response = False
                # wallet managed by another BCW
                elif 'btr' in btt_or_btr_dict:

                    is_btr_validated = BTRValidator.BTRValidator(
                        proxy_center=self,
                        btr_dict=btt_or_btr_dict,
                        wallet_pubkey=wallet_proxy.bcw_proxy_pubkey,
                        q_object=q_obj,
                        asgn_validated=True
                    ).check_validity()

                    if is_btr_validated is True:



                        # todo: create a wait and notify after BCW final response
                        response = self.wait_for_bcw_proxy_nodes_final_response(
                            update_balance_callback=update_balance_callback,
                            end_timestamp=int(asgn_stmt_list[5]) + int(asgn_stmt_list[6]),
                            msg=btt_or_btr_dict,
                            bcw_wid=snd_managed[1],
                            reactor_inst=reactor_inst
                        )
                    else:
                        response = False

                else:
                    response = False

                print(f"In execute_assignment_statement, ProxyCenter.py, response is {response}")

                # if response is a dict, then btt was included in blockchain and asgn_stmt executed

                if isinstance(response, dict):
                    rsp_str = json.dumps(response)
                    return [True, rsp_str]

                # if btt not included in the blockchain on time, then a false is sent to token sender
                else:
                    return [False]

    def wait_and_notify_of_blockchain_inclusion(self, update_balance_callback, end_timestamp: int, **kwargs):

        # todo: find out why code after time.sleep(60) does not execute

        """

        :param update_balance_callback: a callback function to update balances and create a notification message
        :param end_timestamp: this is usually gotten from the assgn statement, by adding timestamp+timelimit
        :param kwargs:
        :return:
        """

        snd_wid = kwargs["snd_wid"]
        bcw_wid = kwargs["bcw_wid"]
        protocol = kwargs["protocol"]

        print(f"in Wait_and_notify_of_blockchain_inclusion, Proxycenter.py:\n"
              f"snd_wid {snd_wid}\n"
              f"bcw_wid {bcw_wid}\n"
              f"end time {end_timestamp}\n"
              f"time.time {time.time()}")
        while time.time() <= end_timestamp and self.is_program_running.is_set() is True:
            print(f"waiting for blockchain inclusion, admin {self.admin_inst.admin_id}")
            time.sleep(30)
            print(f"waiting for blockchain inclusion, admin {self.admin_inst.admin_id}, after 60 seconds")
            tmp_bal = self.get_db_manager().get_from_wallet_balances_db(
                wallet_id=snd_wid
            )
            print("***")
            print(f"in Proxcenter.py, tmp_bal {tmp_bal}")
            if tmp_bal[-1] == bcw_wid:  # the last data in balance list is the BCW wallet id, if managed by a bcw
                print(f"in Wait_and_notify, proxycenter.py, ")
                return update_balance_callback()

            # protocol.transport.write(self.wait_msg)

        return False

    def wait_for_bcw_proxy_nodes_final_response(self, update_balance_callback, end_timestamp: int, msg, bcw_wid,
                                                reactor_inst, **kwargs):

        # THIS IS A BLOCKING CODE. WILL WAIT TILL RESPONSE IS RECEIVED FROM A VALID PROXY NODE OF BCW
        response = self.proxy_communicator.send_to_bcw(
            bcw_wid=bcw_wid,
            msg=msg
        )






