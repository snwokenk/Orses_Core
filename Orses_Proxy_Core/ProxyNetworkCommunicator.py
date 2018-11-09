"""
used by proxies to communicate directly with other proxies.

"""


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

        list_of_bcw_wid_proxies, curr_conn_proxy_dict = self.get_currently_connected_proxies(bcw_wid=bcw_wid)

        if curr_conn_proxy_dict:  # not empty
            return curr_conn_proxy_dict
        else:  # no proxy of BCW_wid is currently connected

            # todo: complete
            propagator = self.admin_inst.get_net_propagator()
            net_manager = propagator.network_manager


            return net_manager.

    def get_reactor(self):
        return self.admin_inst.net_propagator.reactor_instance

    def conn_to_proxy(self):
        pass

    def send_to_bcw(self, bcw_wid, msg):
        """
        This
        :param bcw_wid:
        :param msg:
        :return:
        """

