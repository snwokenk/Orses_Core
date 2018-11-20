"""
used by proxies to communicate directly with other proxies.

"""
import multiprocessing, json

from Orses_Network_Messages_Core.NetworkQuery import NetworkQuery
from Orses_Network_Messages_Core.QueryClass import QueryClass
from Orses_Validator_Core import BTRValidator


class BCWMessageExecutor:
    """
    will have a library of methods used to execute messages(ie Balance Transfer Request) for a BCW
    """

    def execute_message(self, msg):
        pass

    # this should be called in receive_from_bcw
    def execute_btr_msg(self, admin_inst, protocol, msg):
        """
        used to execute a btr message
        :param msg:
        :return:
        """
        # todo: add q_obj allowing to broadcast notification message
        if 'btr' in msg:
            net_propagator = admin_inst.get_net_propagator()
            q_obj_to_propagator_initiator = net_propagator.q_object_validator
            Validator = BTRValidator.BTRValidator(
                admin_instance=admin_inst,
                send_network_notif=True,  # will send notification message to network if valid
                btr_dict=msg,
                q_object=q_obj_to_propagator_initiator

            )

            is_valid = Validator.check_validity()

            # local node does not have BCW proxy pubkey
            if is_valid is None:
                query_msg = QueryClass.request_bcw_proxy_pubkey(
                    bcw_wid=msg['btr']['snd_bcw'],
                    admin_id_of_proxy=msg['admin_id']
                )

                # BLOCKING CODE, execute_btr_msg() SHOULD BE RUNNING IN NON REACTOR THREAD
                proxy_pubkey = NetworkQuery.send_a_query(
                    query_msg=query_msg,
                    admin_inst=admin_inst,
                    protocol=protocol,


                )

                if proxy_pubkey:
                    Validator = BTRValidator.BTRValidator(
                        admin_instance=admin_inst,
                        btr_dict=msg,
                        send_network_notif=True,
                        wallet_pubkey=proxy_pubkey,  # named 'wallet_pubkey' for compatibility but takes proxy_pubkey
                        q_object=q_obj_to_propagator_initiator
                    )

                    is_valid = Validator.check_validity()

                    if is_valid is True:
                        # return notification message,
                        pass

                    else:
                        return False



                pass
        else:
            print(f"in BCWMessageExecutor, ProxyNetworkCommunuicator.py")


        # divide into useful parts


class ProxyNetworkCommunicator:
    def __init__(self, proxy_center_inst):
        self.proxy_center_inst = proxy_center_inst
        self.admin_inst = proxy_center_inst.admin_inst
        self.is_program_running = proxy_center_inst.is_program_running
        # self.db_manager = self.admin_inst.get_db_manager()

        # will include a dict of known proxies
        self.known_proxies = dict()

        # dict holding connected proxies
        self.connected_proxies = dict()

        # bcw to proxies dict mapping BCW to proxies
        self.bcw_to_proxy = dict()

        self.proxy_to_convo = dict() #{bcw_wid: {proxy_id: }}

    def get_db_manager(self):
        return self.admin_inst.get_db_manager()

    def get_reactor(self):

        return self.admin_inst.get_net_propagator().network_manager.reactor_inst

    def get_proxies_of_bcw(self, bcw_wid):
        # used to get BCW proxies, returns a list
        db_manager = self.get_db_manager()

        # index 4 of bcw_info_list is list of proxies
        bcw_info_list = db_manager.get_from_bcw_db(
            wallet_id=bcw_wid
        )

        if bcw_info_list:

            # index 4 of bcw_info_list is the proxy list
            return bcw_info_list[4]
        else:
            return []

    def get_conn_protocols_from_propagator(self):

        propagator = self.admin_inst.get_net_propagator()

        # {admin_id: protocol id}
        return propagator.connected_protocols_admin_id

    def get_currently_connected_proxies(self, bcw_wid):
        """
        used to get proxies of BCW that local node is already
        connected to
        :return:
        """

        list_of_bcw_proxies = self.bcw_to_proxy.get(bcw_wid, None)

        if list_of_bcw_proxies is None:
            list_of_bcw_proxies = self.get_proxies_of_bcw(bcw_wid=bcw_wid)
            self.bcw_to_proxy[bcw_wid] = list_of_bcw_proxies


        conn_protocols_dict = self.get_conn_protocols_from_propagator()
        dict_of_connected_proxies = {p_id: conn_protocols_dict[p_id] for p_id in list_of_bcw_proxies if p_id in conn_protocols_dict}
        return [list_of_bcw_proxies, dict_of_connected_proxies]

    def get_connected_proxies(self, bcw_wid):
        """
        gets connected proxies of bcw. If none, queries other nodes for addresses and then connects to bcw proxy
        :param bcw_wid:
        :return: dictionary of proxy with protocol {admin id: protocol}
        """

        list_of_bcw_wid_proxies, curr_conn_proxy_dict = self.get_currently_connected_proxies(bcw_wid=bcw_wid)

        if curr_conn_proxy_dict:  # not empty
            return curr_conn_proxy_dict
        else:  # no proxy of BCW_wid is currently connected

            # create message
            query_msg = QueryClass.request_msg_network_addresses_by_admin_id(
                list_of_peer_admin_id=list_of_bcw_wid_proxies
            )
            # get addresses of bcw proxies
            # [[admin_id, [host, port], ...] or []
            # BLOCKING CODE
            bcw_proxies_addresses = NetworkQuery.send_sequential_query(
                admin_inst=self.admin_inst,
                query_msg=query_msg,
                list_of_protocols=list(self.get_conn_protocols_from_propagator().items())

            )
            if bcw_proxies_addresses:
                bcw_proxy_id = bcw_proxies_addresses[0][0]
                bcw_proxies_addresses = dict(bcw_proxies_addresses)
                self.admin_inst.fl.update_addresses(
                    address_dict=bcw_proxies_addresses
                )
                net_manager = self.admin_inst.get_net_propagator().network_manager

                list_of_connected_validated_proxies = net_manager.connect_to_admins(
                    list_of_admins=list(bcw_proxies_addresses.keys()),
                    wait_till_validated=True
                )

                # if list of connected proxies is not empty, call function to get list of connected bcw
                if list_of_connected_validated_proxies:
                    return self.get_currently_connected_proxies(bcw_wid=bcw_wid)[1]

            return {}

    def send_to_bcw(self, bcw_wid, msg):
        """

        FUNCTION IS A BLOCKING FUNCTION:
        This can be run in another thread, possible use defertothread and then add callback function or if already
        running on a non reactor thread and willing to block, then wait
        :param bcw_wid:
        :param msg:
        :return:
        """
        # get connected proxies
        # this is a potentially blocking code (do not run in reactor thread (use callInThread)
        dict_of_connected_proxies: dict = self.get_currently_connected_proxies(bcw_wid=bcw_wid)

        try:
            proxy_id_protocol = dict_of_connected_proxies.popitem()
        except KeyError:
            return False

        q_obj = multiprocessing.Queue()

        pms = ProxyMessageSender(
            msg=msg,
            bcw_wid=bcw_wid,
            proxy_communicator_inst=self,
            protocol=proxy_id_protocol,
            q_obj=q_obj
        )
        pms.speak()

    def receive_from_bcw(self, msg):
        pass


class ProxyMessageSender:

    convo_id = 0
    instances_of_class = dict()  # {convo_id: instance of Proxy_message}

    def __init__(self, msg, bcw_wid, proxy_communicator_inst, protocol, q_obj=None):
        self.q_obj = q_obj
        self.proxy_communicator_inst = proxy_communicator_inst
        self.protocol = protocol
        self.bcw_wid = bcw_wid
        self.msg = msg
        self.reactor = proxy_communicator_inst.get_reactor()
        self.first_msg_sent = False
        self.convo_ended = False
        self.convo_id = self.__get_convo_id()
        self.prop_type = 'p'
        self.type_of_msg = 'snd'

    def __get_convo_id(self):

        while True:
            convo_id = ProxyMessageSender.convo_id
            if convo_id not in ProxyMessageSender.instances_of_class:
                ProxyMessageSender.instances_of_class[convo_id] = self
                break
            else:
                an_instance: ProxyMessageSender = ProxyMessageSender.instances_of_class[convo_id]

                if an_instance.convo_ended is True:
                    ProxyMessageSender.instances_of_class[convo_id] = self
                    break
                else:
                    ProxyMessageSender.convo_id += 1
                    continue

        return convo_id

    def speak(self):

        reactor = self.reactor

        reactor.callFromThread(
            self.protocol.transport.write,
            json.dumps([self.prop_type, self.convo_id, self.type_of_msg, self.msg]).encode()

        )

    def listen(self, response):

        self.convo_ended = True
        self.q_obj.put(response)

    @classmethod
    def get_instance_of_class(cls, convo_id):
        return cls.instances_of_class.get(convo_id, None)


class ProxyMessageResponder:
    def __init__(self, msg, protocol, proxy_communicator_inst, q_obj=None):
        self.protocol = protocol
        self.msg = msg
        self.q_obj = q_obj
        self.proxy_communicator_inst = proxy_communicator_inst
        self.protocol = protocol
        self.reactor = proxy_communicator_inst.get_reactor()
        self.convo_id = msg[1]

    def listen(self, msg):
        pass

