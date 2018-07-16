"""
used to verify that a connected peer is running a compatible software implementing the same rules.
"""

from Orses_Cryptography_Core.Hasher import Hasher


import base64


class ConnectedNodeValidator:
    def __init__(self, peer_node_info_dict, admin_inst, wallet_pubkey=None, q_object=None):

        self.admin_inst = admin_inst
        self.peer_software_hash_list = peer_node_info_dict["1"]
        self.peer_addr = peer_node_info_dict["2"]  # "ip address"
        self.compatible_hashes = admin_inst.compatible_hash if admin_inst.compatible_hash else \
            ConnectedNodeValidator.get_hash_of_important_files(self.admin_inst)

    def check_validity(self):

        if self._compare_software_hash_list() is True:
            #  update address_list if
            self.admin_inst.fl.update_addresses(address_list=[self.peer_addr, ])
            return True

        return False

    def _compare_software_hash_list(self):
        local_software_hash_list = self.get_hash_of_important_files(self.admin_inst)
        is_same = self.peer_software_hash_list[-1] == local_software_hash_list[-1]  # combined hash is the same

        if is_same:
            return True

        # todo: get compatible hashes and check if peer combined_hash in compabitible hashes
        # todo: for now self.get_compatible_hashes() returns empty set {}

        return self.peer_software_hash_list[-1] in self.get_compatible_hashes()

    @staticmethod
    def get_compatible_hashes():
        """
        used to get the sha256 hash of certain key files,
        at this moment:
        Orses_Core/start_node.py
        Orses_Core/Orses_Validator_Core/AssignmentStatementValidator.py
        Orses_Core/Orses_Validator_Core/TokenReservationRequestValidator.py
        Orses_Core/Orses_Validator_Core/TokenReservationRevokeValidator.py
        Orses_Core/Orses_Validator_Core/TokenTransferValidator.py
        Orses_Core/Orses_Cryptography_Core/DigitalSignerValidator.py
        Orses_Core/Orses_Cryptography_Core/DigitalSigner.py
        Orses_Core/Orses_Cryptography_Core/Encryption.py
        Orses_Core/Orses_Cryptography_Core/Decryption.py
        Orses_Core/Orses_Cryptography_Core/PKIGeneration.py

        this should be run during startup of program. IT SHOULD NOT BE RUN EVERYTIME
        For two nodes to communicate, they must validate each others file hash
        :param hash_form: the type of hash to get, default is base85 str
        :return: [start_node.py, /Orses_Validator_Core/AssignmentStatementValidator.py, ....etc, combined_hash]

        """
        # todo: get compatible hashes and check if peer combined_hash in compabitible hashes
        return {}



    @staticmethod
    def get_hash_of_important_files(admin_inst):
        list_of_filepaths = admin_inst.fl.get_path_of_important_files()
        list_of_hashes = list()

        for filepath in list_of_filepaths:
            opened_file = open(filepath, "rb")
            hash_of_file = Hasher.sha_hasher(data=opened_file.read(), hash_form="hex")  # sha_hasher will accept bytes or str
            opened_file.close()
            list_of_hashes.append(hash_of_file)

        combined_hash = ""

        for a_hash in list_of_hashes:
            combined_hash+=a_hash

        combined_hash = Hasher.sha_hasher(data=combined_hash, hash_form="b85_str")
        list_of_hashes.append(combined_hash)

        return list_of_hashes





