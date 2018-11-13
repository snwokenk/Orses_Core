"""
used by proxies to communicate directly with other proxies.

"""

from Orses_Network_Messages_Core.NetworkQuery import NetworkQuery
from Orses_Network_Messages_Core.QueryClass import QueryClass

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

    def get_db_manager(self):
        return self.admin_inst.get_db_manager()

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

        list_of_bcw_proxies = self.get_proxies_of_bcw(bcw_wid=bcw_wid)
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
            query_msg = QueryClass.get_network_addresses_by_admin_id(
                admin_inst=self.admin_inst,
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




    def get_reactor(self):
        return self.admin_inst.net_propagator.reactor_instance

    def conn_to_proxy(self):
        pass

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
        dict_of_connecated_proxies: dict = self.get_currently_connected_proxies(bcw_wid=bcw_wid)

        try:
            proxy_id_protocol = dict_of_connecated_proxies.popitem()
        except KeyError:
            return False

        # todo: finish up this function

