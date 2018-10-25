import plyvel, os, json


class OrsesLevelDBManager:

    """
    load required databases and then before running event loop load wallet balances from genesis block

    """

    def __init__(self, admin_inst):
        self.admin_inst = admin_inst
        self.databases = dict()
        self.prefix_db = dict()

    def create_load_wallet_balances_from_genesis_block(self, overwrite=False):
        """

        :param overwrite: create a new wallet_balances database even if one exists
        :return:
        """

        print("In OrsesLevelDBManager: Creating wallet balance db from genesis block, if not exist")

        blockchain_path = self.admin_inst.fl.get_block_data_folder_path()

        # check if already created
        if self.load_db(name="wallet_balances", create_if_missing=False) and overwrite is False:
            return True

        # load block 0 ie genesis block
        block0 = self.admin_inst.fl.open_file_from_json(filename="0", in_folder=blockchain_path)
        block0_TATs = block0["tats"] if block0 else {}
        block0_BCWs = block0["bcws"] if block0 else {}

        db = self.load_db(name="wallet_balances", create_if_missing=True)
        if block0_TATs:
            with db.write_batch(transaction=True) as b:
                for tat_hash in block0_TATs:
                    # similar [('W3c8135240da9d25d3905aa7aca64c98ca6b1fede', 850000000)]
                    tmp = list(block0_TATs[tat_hash].items())
                    wid = tmp[0][0]
                    print(f"in OrsesLevelDB, Tat: {tmp}")
                    reserved_bal = block0_BCWs[wid] * 1e10 if wid in block0_BCWs else 0
                    avail_bal = (tmp[0][1]*1e10) - reserved_bal
                    b.put(
                        wid.encode(),
                        json.dumps([avail_bal, reserved_bal, avail_bal+reserved_bal]).encode()  # [avail bal, rsv_balance, total bal]
                    )

            return True

        else:
            print(f"in OrsesLevelDBMangement: Block 0 not found admin: {self.admin_inst.admin_name}")
            print(f"file paths {blockchain_path}")

            return False

    def load_required_databases(self):

        # create (if not exist) and load "wallet_balances"
        # self.create_load_wallet_balances_from_genesis_block()
        req_db_list = [
            "wallet_pubkeys",
            "confirmed_msgs_hashes",
            "unconfirmed_msgs_hashes",
            "unconfirmed_msgs_wid",
            "BCWs",  # database of all active BCW wallets
            "BCW_Proxies"  # db storing proxy information of each BCW (in Network)

        ]

        for i in req_db_list:
            self.load_db(name=i, create_if_missing=True)

    def get_from_bcw_db(self, wallet_id, recursive_count=0):
        """
        returns
        :param wallet_id:
        :param recursive_count: number of recursion
        :return:
        """

        # todo: finish up
        try:
            # bcw info list tx_hash of req, time of creation, time of expiration, block number rsv was added,
            # list of proxies, rsv dict]
            wallet_activity = self.databases["BCWs"].get(key=wallet_id.encode())

        except KeyError:
            # load up db
            if recursive_count < 1:
                recursive_count += 1
                self.load_db(name="BCWs", create_if_missing=False)
                return self.get_from_bcw_db(wallet_id=wallet_id, recursive_count=recursive_count)
            else:
                print(f"in get_from_bcw_db, unconfirmed_msgs_wid could not be loaded")
                return []

        except plyvel.Error:
            print(f"Error in OrsesLevelDBManager, BCWs DB does not exist")
            return []

        else:
            if wallet_activity:
                wallet_activity = json.loads(wallet_activity.decode())

                return wallet_activity
            else:
                return []

    def insert_into_bcw_db(self, wallet_id: str, tx_hash: str, rsv_req_dict: dict, signature: str, value=None,
                           recursive_count=0, block_number=None):
        """
        BCW database stores records of each blockchain connected wallet,
        this include the Token Reservation Request sent.

        2 other databases are kept. One stores the BCW's proxy nodes and pubkey key identifying each one.
        The other  stores BCWs that have sent a reservation revoke request.

        In addition, a proxy node db, stores each proxy nodes, BCW wallets that they are proxies for,
        proof of authorizaiton by each BCW and wallet pubkey it uses to sign network messages for each BCW

        structure of a BCW levelDB database is:

        key = wallet_id
        value = [tx_hash of rsv_req, rsv_req_dict, signature, amount_reserved, timestamp]

        value is json encoded and stored as a byte string(required by levelDB)

        :param wallet_id:
        :param tx_hash:
        :param rsv_req_dict:
        :param signature
        :param recursive_count:
        :return:
        """

        # wallet balance = [[avail bal, reserved bal, payable balance, receivable bal, total balance],
        #                       [reservation time, expiration time, tx_hash of token_reservation],
        #                       [proxy id, proxy id, proxy id, etc]

        # first get wallet balance

        if rsv_req_dict:
            pass
        elif value:
            pass

        try:

            if rsv_req_dict and isinstance(block_number, int):  # newly reserved so

                # get the proxies from reservation dict
                proxy_list = rsv_req_dict["rsv_req"]["v_node_proxies"]

                # bcw info list tx_hash of req, time of creation, time of expiration, block number rsv was added,
                # set of proxies, rsv dict]
                bcw_info_list = [tx_hash,rsv_req_dict["rsv_req"]["time"], rsv_req_dict["rsv_req"]["exp"],
                                 block_number, proxy_list, rsv_req_dict]
                value = json.dumps(bcw_info_list)



                # create individual proxy db with concatenated bcw_wid and admin id of proxy
                for adminid in proxy_list:
                    proxy_id = f"{wallet_id}{adminid}"

                    # an empty dict is put in place, this is replaced when the actual node responds with a unique
                    # pubkey for use with BCW, if it doesn't then, it could mean admin node has refused to become a
                    # proxy for BCW
                    self.databases["BCW_Proxies"].put(key=proxy_id.encode(), value=b'{}')


                    # check if admin in admin list is current node
                    if adminid == self.admin_inst.admin_id:
                        self.admin_inst.proxy_center.initiate_new_proxy(
                            bcw_wid=wallet_id
                        )


            elif value:
                value = json.dumps(value)
            else:
                print(f"rsv_req_dict is None AND Value is None OR Block Number is needed")
                return False

        except Exception as e:
            print(f"in in insert_into_bcw_db, OrseslevelDBManagement.py: error occured: {e}")
            return False

        try:
            self.databases["BCWs"].put(key=wallet_id.encode(), value=value.encode())

            # todo: insert proxies of BCW into BCW_Proxies db

        except KeyError:

            if recursive_count < 1:
                print(f"")
                recursive_count += 1
                self.load_db(name="BCWs")
                return self.insert_into_bcw_db(
                    wallet_id=wallet_id,
                    tx_hash=tx_hash,
                    rsv_req_dict=rsv_req_dict,
                    signature=signature,
                    recursive_count=recursive_count
                )
            else:
                print(f"in in insert_into_bcw_db, OrseslevelDBManagement.py: not able to load 'BCWs' db")
                return False

        return True

    def get_proxy_pubkey(self, proxy_id: str):
        """

        :param proxy_id: a concatenation of admin_id+walletid
        :return: pubkey dict
        """

        pubkey: bytes = self.databases["BCW_Proxies"].get(key=proxy_id.encode())

        if pubkey:
            pubkey = json.loads(pubkey.decode())
            return pubkey
        else:
            return {}

    def get_from_unconfirmed_db_wid(self, wallet_id: str, recursive_count=0, pop_value=False, pop_from_value=None):
        """

        :param wallet_id:
        :param only_value:
        :param pop_value: if wallet_id entry should be deleted and returned
        :param pop_from_value: if str(should be a hash), hash should be popped from value(value without hash inserted
        :return: dictionary with key as tx_hash and value as list:
            [tx_type, "sender" or "receiver, main_tx, sig,fee,  amt_tokens(sender=neg., receiver=pos. ]
        """

        try:
            # {tx_hash: [tx_type, "sender" or "receiver, main_tx, sig,fee,  amt_tokens(sender=neg., receiver=pos.]}
            wallet_activity = self.databases["unconfirmed_msgs_wid"].get(key=wallet_id.encode())
        except KeyError:
            # load up db
            if recursive_count < 1:
                recursive_count += 1
                self.load_db(name="unconfirmed_msgs_wid", create_if_missing=False)
                return self.get_from_unconfirmed_db_wid(wallet_id=wallet_id, recursive_count=recursive_count)
            else:
                print(f"in get_from_unconfirmed_db_wid, unconfirmed_msgs_wid could not be loaded")
                return {}

        except plyvel.Error:
            print(f"Error in OrsesLevelDBManager, get_from_uncofirmed_db_wid DB does not exist")
            return {}
        else:
            print(f"in get_from_uncofirmed_db_wid, wallet activity: {wallet_activity} admin {self.admin_inst.admin_name}")
            if wallet_activity:
                wallet_activity = json.loads(wallet_activity.decode())
                if pop_value:
                    self.databases["unconfirmed_msgs_wid"].delete(key=wallet_id.encode())
                elif pop_from_value:

                    print(f"debug: in OrsesLevelDB: in pop from value: value to pop {pop_from_value} admin {self.admin_inst.admin_name}")
                    activity = wallet_activity.pop(pop_from_value, [])
                    print(f"debug: in OrsesLevelDB: in pop from value, {wallet_activity} admin {self.admin_inst.admin_name}")

                    # if activity is empty wallet id will be deleted from db
                    self.insert_into_unconfirmed_db_wid(
                        wallet_id=wallet_id,
                        value=wallet_activity,
                        tx_hash='',
                        tx_type='',
                        amt=0,
                        fee=0,
                        main_tx={},
                        signature=''
                    )
                    return activity


            else:
                wallet_activity = {}

            return wallet_activity

    def insert_into_unconfirmed_db_wid(self, tx_type: str, wallet_id: str, tx_hash: str, signature: str,
                                       main_tx: dict, amt: int, fee: int, recursive_count=0, sender=True, value=None):
        """
        Insert into db using wallet id as key
        :param tx_type: This is can ttx, rvk_req, rsv_req or misc_msgs
        :param wallet_id:
        :param tx_hash: hash
        :param signature: signature of transaction
        :param main_tx: dict containting the main details of a msg
        :param amt: amount involved tx is for, if it is a ttx or rvk_req or rsv_req then it should be > 0
        :param fee: amount to be paid to administrators/blockcreators. should always be (fee > 0)
        :param value: previous value if any
        :return:
        """

        # todo: clarify reservation revoke, make sure reservation revoke waits the appropriate amount of blocks
        # todo: before it is valid

        # get previous activities if any and add to it
        # dict at index 0 of activity, tells the net of avail and reserved.
        # when

        # strip main_tx of transaction hash to reduce redundant storage and bandwidth use
        # print(main_tx)
        # main_tx.pop("tx_hash")
        # main_tx.pop("sig")

        if value is None:
            prev_activity = self.get_from_unconfirmed_db_wid(wallet_id=wallet_id)


            # set amount
            if sender is True:  # then receiver
                snd_or_rcv ="sender"
                amt = -amt if tx_type != "rvk_req" else 0
                fee = -fee

            else:
                snd_or_rcv = "receiver"
                fee = 0

            if prev_activity:

                # prev_activity dict
                prev_activity[tx_hash] = [tx_type, snd_or_rcv, main_tx, signature, fee, amt]
                # number to subtract is fees and amount
                # prev_activity.append(
                #     [tx_type, snd_or_rcv, main_tx, signature, tx_hash, fee, amt]
                # )
                value = json.dumps(prev_activity)
            else:

                # number to add is amt, fees are taken by block creator
                value = json.dumps(
                    {
                       tx_hash: [tx_type, snd_or_rcv, main_tx, signature, fee, amt],
                    }
                )
        else:
            if value and not isinstance(value, str):
                value = json.dumps(value)
            elif not value:
                self.databases["unconfirmed_msgs_wid"].delete(wallet_id.encode())
                return None

        try:
            with self.databases["unconfirmed_msgs_wid"].write_batch(transaction=True) as wb:
                wb.put(key=wallet_id.encode(), value=value.encode())

        except KeyError:
            # print(f"in OrsesLevelDBManagement: keyerror occured, Loading db called 'wallet_balances'")
            self.load_db(name="unconfirmed_msgs_wid")

            if recursive_count < 1:
                recursive_count += 1
                return self.insert_into_unconfirmed_db_wid(
                    wallet_id=wallet_id,
                    tx_hash=tx_hash,
                    signature=signature,
                    main_tx=main_tx,
                    tx_type=tx_type,
                    amt=amt,
                    fee=fee,
                    sender=sender
                )
            else:
                print(f"in insert_into_unconfirmed_db_wid, unconfirmed_msgs_wid could not be created")
                return False
        else:
            return True

    def get_from_unconfirmed_db(self, tx_hash: str, recursive_count=0, pop_value=False, json_decoded=True):
        """
        gets transaction related to tx_hash
        :param tx_hash: hash of transaction, also the key for leveldb database
        :param recursive_count: number of times function called recursively. limited to only 1 time before returing
        :param pop_value: if this is true, tx_hash entry is deleted and then returned
        :param json_decoded: if this is false then a json encoded string  of python list is returned
        :return: list if json_decoded is True alse string representation of list if false
        """

        try:
            # b'[main_tx, signature, rcv_wid, sending_wid]' decode and json load python object
            # if hash represents a 'btt' then  b'[main_tx, signature, rcv_wid, sending_wid, 'mc']'
            activity_of_hash = self.databases["unconfirmed_msgs_hashes"].get(key=tx_hash.encode())

        except KeyError:

            if recursive_count < 1:
                recursive_count += 1
                self.load_db(name="unconfirmed_msgs_hashes", create_if_missing=False)
                return self.get_from_unconfirmed_db(tx_hash=tx_hash, recursive_count=recursive_count)
            else:
                print(f"in get_from_unconfirmed_db, OrsesLevelDBManagement.py,  unconfirmed_msgs_hashes not created")
        except plyvel.Error:
            print(f"Error in OrsesLevelDBManager, unconfirmed DB does not exist")
            return {}

        else:
            if activity_of_hash:
                if pop_value:
                    self.databases["unconfirmed_msgs_hashes"].delete(key=tx_hash.encode())
                activity_of_hash = json.loads(activity_of_hash.decode()) if json_decoded else activity_of_hash.decode()
            else:
                activity_of_hash = [] if json_decoded else ''

            return activity_of_hash

    def insert_into_unconfirmed_db(self, tx_type: str, sending_wid: str, tx_hash: str, signature: str,
                                   main_tx: dict, amt: int, fee: int, rcv_wid=None, recursive_count=0, **kwargs):
        """
        This inserts hash of message
        :param sending_wid: the senders wallet id, if tx_type is btt then bcw_wid
        :param tx_hash: transaction hash, if it is a btt then hash is hash of asgn_stmt
        :param signature:
        :param main_tx:
        :param amt: amount being sent, if it is a non token related msg (ie misc_msg) then amount == 0, amount is also 0
                    if it is "btt", this message just notifies the network of wallet management change
        :param fee: fee being sent for inclusion: This is always here, some form of fee must be paid for storing
                    messages/txs on the blockchain.
        :param rcv_wid: if tx_type is ttx or transfer transaction then rcv_wid should not be none,
                    if it is btt then should be the snd_wid of asgn statement (NOT THE rcv_wid in the asgn statement

        :param recursive_count: number of recursion
        :return:
        """

        value = [main_tx, signature, rcv_wid, sending_wid]

        if tx_type in {'btt'}:
            # rcv_wid is BCW_wid, sending wid is sender of asgn_stmt and amt == 0
            value.append("mc")  # management change

        value = json.dumps(value)

        try:
            self.databases["unconfirmed_msgs_hashes"].put(key=tx_hash.encode(), value=value.encode())
        except KeyError:
            print(f"in insert_into_unconfirmed_db() unconfirmed_msgs_hashes db not created")
            # print(f"in OrsesLevelDBManagement: keyerror occured, Loading db called 'wallet_balances'")
            self.load_db(name="unconfirmed_msgs_hashes", create_if_missing=True)

            if recursive_count < 1:
                recursive_count += 1
                return self.insert_into_unconfirmed_db(
                    sending_wid=sending_wid,
                    tx_hash=tx_hash,
                    signature=signature,
                    main_tx=main_tx,
                    tx_type=tx_type,
                    rcv_wid=rcv_wid,
                    amt=amt,
                    fee=fee,
                    recursive_count=recursive_count
                )
            else:
                print(f"error in insert_into_unconfirmed_db(): unconfirmed_msgs_hashes db can not be created")
                return False
        else:
            is_inserted = self.insert_into_unconfirmed_db_wid(
                wallet_id=sending_wid,
                tx_hash=tx_hash,
                signature=signature,
                main_tx=main_tx,
                tx_type=tx_type,
                amt=amt,
                fee=fee,
                sender=True
            )

        if is_inserted:
            if rcv_wid is not None:
                rcv_inserted = self.insert_into_unconfirmed_db_wid(
                    wallet_id=rcv_wid,
                    tx_hash=tx_hash,
                    signature=signature,
                    main_tx=main_tx,
                    tx_type=tx_type,
                    amt=amt,
                    fee=fee,
                    sender=False
                )
                if rcv_inserted:
                    return True
            else:
                return True

        return False

    def insert_into_confirmed_db(self, tx_hash, tx_list, recursive_count=0):
        try:
            self.databases["confirmed_msgs_hashes"].put(key=tx_hash.encode(), value=tx_list.encode())
        except KeyError:
            if recursive_count < 1:
                recursive_count += 1
                self.load_db(name="confirmed_msgs_hashes", create_if_missing=True)
                return self.insert_into_confirmed_db(tx_hash=tx_hash, tx_list=tx_list, recursive_count=recursive_count)
            else:
                print(f"could not created confirmed_msgs_hashes in OrsesLevelDBManagement.py")
                return False
        else:
            return True

    def get_a_prefixed_db(self, db_name: str, prefix: str, create_if_not_exist=True):
        """
        this returns a prefixed_db class.
        a prefixed db class allows you to put a key/value pair with the prefixed value
        ie if your key was wallet id b"wf443434034" and value was b'[500, 0]'. The prefixed db class
        with a prefix of b'0-' would insert your key as b"0-wf443434034" when calling put.

        if you decide to get the wallet id, a prefixed db class would only check for
        the wallet id with a prefix of b"0-"

        :param db_name: the name of the leveldb database to create a prefixed db class from
        :param prefix: the prefix to use
        :param create_if_not_exist: create a prefix db if it does not exist (does not create a new leveldb
        if it does not exist)
        :return: the prefixed db class or
                if leveldb has not been loaded or prefixed db does not exist and create_if_not_exist == False
        """

        try:
            if prefix in self.prefix_db:
                tmp = self.prefix_db[prefix]
            elif create_if_not_exist:
                tmp = self.databases[db_name].prefixed_db(prefix.encode())
                self.prefix_db[prefix] = tmp
            else:
                print(f"in OrsesLevelDBManager: prefixed db: {prefix} does not exist and create_if_not_exist is False")
                return None
        except KeyError:
            print(f"Error, Troubleshoot, database {db_name} not loaded")
            return None

        else:
            return tmp

    def load_db(self, name: str, create_if_missing=True, in_folder=None):
        """
        some databases are crated in data_client_wallet folder of user folder
        others are created in data_mempool
        :param name: the name of the database
        :param create_if_missing: create a database if not exist
        :param in_folder: folder to store leveDB
        :return:
        """
        #todo: create folder names

        # create filename/path
        if name in {"wallet_balances",
                    "wallet_pubkeys",
                    "temp_wallet_balances"}:
            filename = os.path.join(self.admin_inst.fl.get_clients_wallet_folder_path(), name)
        elif name in {"BCWs", "BCW_Proxies", 'local_'}:
            filename = os.path.join(self.admin_inst.fl.get_proxy_center_folder_path(), name)
        elif isinstance(in_folder, str):
            filename = os.path.join(in_folder, name)
        else:
            filename = os.path.join(self.admin_inst.fl.get_mempool_data_folder_path(), name)

        # load or create database
        try:
            db = plyvel.DB(filename, create_if_missing=create_if_missing)
        except plyvel.Error as e:
            print(f"in load_db, error occured: {e}")
            return None
        else:
            self.databases[name] = db

            return db

    def insert_into_wallet_balances_prefixed_db(self, wallet_id: str, wallet_data: list, prefix: str):
        """
        a leveldb database stores the wallet balances of all wallets managed by the blockchain
        :param wallet_id: wallet id to update
        :param wallet_data: json_encoded wallet data of balances:
                            [int, int, int] = [free token balance, reserved_token_balance, total token]
        :return: bool, true if successul
        """
        wallet_data = json.dumps(wallet_data)
        db_prefix = self.get_a_prefixed_db(db_name="temp_wallet_balances", prefix=prefix)
        if not db_prefix:
            return False
        else:
            db_prefix.put(key=wallet_id.encode(), value=wallet_data.encode())
            return True

    def get_from_temp_wallet_balances_prefixed_db(self, wallet_id: str, prefix: str, only_value=True):
        """
        use to retrieve wallet balance data
        :param wallet_id:
        :return: if only_value is True then [free token balance, reserved_token_balance, total token] else
                [wallet id, [free token balance, reserved_token_balance, total token]]
        """

        db_prefix = self.get_a_prefixed_db(db_name="temp_wallet_balances", prefix=prefix, create_if_not_exist=False)
        if not db_prefix:
            return False
        else:
            wallet_balance = db_prefix.get(key=wallet_id.encode())
            if wallet_balance:
                wallet_balance = [wallet_balance.decode(), json.loads(wallet_balance[1].decode())]
            else:
                wallet_balance = [None, None, None]  # prefixed_balance should return None if no entry

            if wallet_balance and only_value:
                wallet_balance = wallet_balance[1]

            return wallet_balance

    def update_wallet_balance_db(self, wallet_id: str, wallet_data: list):
        """
        use this when you're sure database exist.
        :param wallet_id:
        :param wallet_data:
        :return:
        """

        try:
            wallet_data = json.dumps(wallet_data)
            self.databases["wallet_balances"].put(key=wallet_id.encode(), value=wallet_data.encode())

        except KeyError:
            return False

        except plyvel.Error:
            return False

        return True

    def insert_into_wallet_balances_db(self, wallet_id: str, wallet_data: list):
        """
        a leveldb database stores the wallet balances of all wallets managed by the blockchain
        :param wallet_id: wallet id to update
        :param wallet_data: json_encoded wallet data of balances:
                            [int, int, int] = [free token balance, reserved_token_balance, total token]
                            Or [int, int, int, string] = [free token balance, reserved_token_balance, total token, managing bcw]
                            Or [int, int, int, int, int] = [free token balance, reserved_token_balance, payable balance, receivable balance,  total token]

        :return: bool, true if successul
        """
        # amounts are stored as ints of ntakiris ie 1 orses token = 10,000,000,000 (10 billion) ntakiris
        # amounts are sent over the network as floats with with max decimal places of 10
        # this means the minimum amount of orses token is  0.0000000001 or 01e-10 == 1 ntakiri
        wallet_data = json.dumps(wallet_data)
        try:
            self.databases["wallet_balances"].put(key=wallet_id.encode(), value=wallet_data.encode())
        except KeyError:
            # print(f"in OrsesLevelDBManagement: keyerror occured, Loading db called 'wallet_balances'")
            self.load_db(name="wallet_balances")
            return self.insert_into_wallet_balances_db(wallet_id=wallet_id, wallet_data=wallet_data)
        else:
            return True

    def get_from_wallet_balances_db(self, wallet_id: str, recursive_count=0):
        """
        use to retrieve wallet balance data
        :param wallet_id:
        :param recursive_count
        :return: if only_value is True then [free token balance, reserved_token_balance, total token] else
                [wallet id, [free token balance, reserved_token_balance, total token]]
        """

        try:
            # wallet balance = b'[free token amount, reserved token amount, total balance]
            # if bcw then = b'[avail bal, reserved bal, payable bal, receivable bal, total bal]'
            wallet_balance = self.databases["wallet_balances"].get(key=wallet_id.encode())

            print(f"self.databases {self.databases}")

        except KeyError as e:
            print(f"error in get_from_wallet_balances_db(), error msg: {e}")
            # load up db
            self.load_db(name="wallet_balances", create_if_missing=False)
            if recursive_count < 1:
                recursive_count += 1
                return self.get_from_wallet_balances_db(wallet_id=wallet_id, recursive_count=recursive_count)
            else:
                print(f"error in get_from_wallet_balances_db(), recursive limit")
                return [0,0,0]
        except plyvel.Error:
            print(f"Error in OrsesLevelDBManager, wallet_balances DB does not exist")
            return [0,0,0]
        else:
            if wallet_balance:
                wallet_balance = json.loads(wallet_balance.decode())
            else:
                wallet_balance = [0,0,0]  # available, reserved, total


            return wallet_balance


if __name__ == '__main__':
    try:
        db = plyvel.DB("/home/snwokenk/IdeaProjects/Orses_Core/sandbox/sn/data_client_wallet/wallet_balances", create_if_missing=True)
        db2 = plyvel.DB("/home/snwokenk/IdeaProjects/Orses_Core/sandbox/sn/data_mempool/confirmed_msgs_hashes", create_if_missing=False)
    except plyvel.Error as e:
        print(e)
    else:

        for i in db:
            print(i)

        print("====")
        #
        # for i in db2:
        #     print(i)






