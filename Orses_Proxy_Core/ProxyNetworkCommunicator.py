"""
used by proxies to communicate directly with other proxies.

"""


class ProxyNetworkCommunicator:
    def __init__(self, proxy_center_inst):
        self.proxy_center_inst = proxy_center_inst
        self.admin_inst = proxy_center_inst.admin_inst
        self.is_program_running = proxy_center_inst.is_program_running
        self.db_manager = self.admin_inst.get_db_manager()

        # will include a dict of known proxies
        self.known_proxies = None

        # dict holding connected proxies
        self.connected_proxies = dict()

        # bcw to proxies dict mapping BCW to proxies
        self.bcw_to_proxy = dict()

    def get_proxies_of_bcw(self):
        # used to get BCW proxies, returns a list
        pass

    def conn_to_proxy(self):
        pass

    def send_to_bcw(self, bcw_wid, msg, reactor_inst):
        """
        This
        :param bcw_wid:
        :param msg:
        :return:
        """

