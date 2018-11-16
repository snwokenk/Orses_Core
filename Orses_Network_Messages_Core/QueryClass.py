"""
Hold query class, with static methods meant to get query response
"""


class QueryClass:


    @staticmethod
    def request_msg_network_addr_by_admin_id(peer_admin_id):
        """

        :param peer_admin_id: peer admin id
        :return:
        """

        return ['1', peer_admin_id]

    @staticmethod
    def get_network_addr_by_admin_id(admin_inst, *args):
        """
        :param admin_inst: admin instance of local node
        :param args:
        :return:
        """

        peer_admin_id = args[0]
        known_addresses: dict = admin_inst.known_addresses

        peer_addr: list = known_addresses.get(peer_admin_id, [])

        if not peer_addr:

            return []

        return [peer_admin_id, peer_addr]

    @staticmethod
    def request_msg_network_addresses_by_admin_id(list_of_peer_admin_id):
        return ['2', list_of_peer_admin_id]

    @staticmethod
    def get_network_addresses_by_admin_id(admin_inst, list_of_peer_admin_id):
        """

        :param list_of_peer_admin_id: list of peer admins whose address is needed
        :param admin_inst: admin instance of local node
        :return: list either [[admin_id, [host, port], ...] or empty list
        """

        known_addresses: dict = admin_inst.known_addresses

        list_of_addresses = list()

        for admin_id in list_of_peer_admin_id:
            peer_addr: list = known_addresses.get(admin_id, None)
            if peer_addr:
                list_of_addresses.append([admin_id, peer_addr])

        if not list_of_addresses:  # if empty

            return []

        return list_of_addresses

    @staticmethod
    def request_bcw_proxy_pubkey(bcw_wid, admin_id_of_proxy):
        return ['3', [bcw_wid, admin_id_of_proxy]]

    @staticmethod
    def get_bcw_proxy_pubkey(admin_inst, bcw_wid, admin_id_of_proxy):
        """

        :param admin_inst: an admin_inst
        :param bcw_wid: wallet id of BCW represented
        :param admin_id_of_proxy: admin id of proxy representing BCW
        :return:
        """

        proxy_center = admin_inst.get_proxy_center()

        if proxy_center:
            wallet_proxy = proxy_center.get_a_proxy(bcw_wid=bcw_wid)

            # local node not a proxy of bcw_wid, check dict
            if wallet_proxy is None:
               pubkey = proxy_center.get_a_proxy_pubkey(
                   bcw_wid=bcw_wid,
                   admin_id_of_proxy=admin_id_of_proxy
               )
            else:
                pubkey = wallet_proxy.get_pubkey()
        else:
            pubkey = {}

        return pubkey




# keys represent query id which can be used to get callable for a specified query
dict_of_query_callable = dict()

# arguments are admin_id, local admin instance
dict_of_query_callable['1'] = QueryClass.get_network_addr_by_admin_id
dict_of_query_callable['2'] = QueryClass.get_network_addresses_by_admin_id
dict_of_query_callable['3'] = QueryClass.get_bcw_proxy_pubkey


if __name__ == '__main__':
    pass