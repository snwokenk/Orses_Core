"""
this file will allow for loading of key data for competing.
these pieces of information needed includes:

getting the last block received and requesting for blocks

It includes class with data
"""
import os, json, shutil
from Orses_Validator_Core.NewBlockValidator import NewBlockValidator


class BlockChainData:
    def __init__(self, admin_instance, create_genesis_only=False):

        path_of_main = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Blockchain_Data")
        try:
            shutil.copytree(path_of_main, admin_instance.fl.get_block_data_folder_path())
        except FileExistsError:
            print("In BlockChainData.py, __init__: Blockchain_Data folder already exists")


    def load_data(self):
        pass


    @staticmethod
    def get_current_known_block(admin_instance):
        """
        retrieves the last block known to this node.
        This info is the used by network propagator to find out if
        :return: returns the last known block, this is then used to query the network for newer blocks
        """
        file1 = os.path.join(admin_instance.fl.get_block_data_folder_path(), "last_block_number")

        try:
            with open(file1, "r") as jfile:
                block_number = json.load(jfile)
        except FileNotFoundError:
            print("File Not Found in CompetitorDataLoading.py")
            return None
        else:
            print("File Found in CompetitorDataLoading.py")
            # file2 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Blockchain_Data",
            #                      f"{block_number}")

            file2 = os.path.join(admin_instance.fl.get_block_data_folder_path(), str(block_number))
            try:
                with open(file2, "r") as inBlock:
                    block_info = json.load(inBlock)
            except FileNotFoundError as e:
                print(f"\n-----\nError in {__file__}\nTrying to oepn file: {block_number}\n"
                      f"Exception raised: {e}")
                return None
            else:
                return [block_number, block_info]

    @staticmethod
    def get_block(block_no, admin_instance):

        # file1 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Blockchain_Data",
        #                      f"{block_no}")

        file1 = os.path.join(admin_instance.fl.get_block_data_folder_path(), str(block_no))

        try:
            with open(file1, "r") as jfile:
                block = json.load(jfile)
        except FileNotFoundError:
            block = None

        return block


    @staticmethod
    def save_current_block(block_no, block, admin_instance):

        # validate_block then save preferable use reactor.
        pass

    @staticmethod
    def save_a_propagated_block(block_no, block, admin_instance):

        # verify that we don't already have block:
        if BlockChainData.get_block(block_no, admin_instance=admin_instance) is None:
            isValidated = NewBlockValidator(block_no,block, False)

            if isValidated is True:
                file1 = os.path.join(admin_instance.fl.get_block_data_folder_path(), str(block_no))

                with open(file1, "w") as jfile:
                    json.dump(block, jfile)
                return True
        else:
            return None



if __name__ == '__main__':
    genesis_block = {
        "block_header": {
            "protocol_rule_hash": "fe3f01abad",
            "merkle_root":"d88397fb3c91614409bf6358848baa305aea28bbc2cc1ba87503ca2f20cfb578",
            "nonce:": format(41042163, "x"),  # turns to hex without the 0X
            "extraNonce": 0,
            "block_hash": "000000a75ea76fbe7af548c521c8275d005229363300da297f2f022814928814",
            "block_number": 0
        },
        "tka": {
            "Wd8661c5e3c7b93f5344f4c2536470f383071dd43": 850_000_000,
            "W0df521b542a840cb5d5ed6c819e913af83b4baa4": 150_000_000,
            "W82d9d7288822e181851add314956744f308d7841": 35_000_000,
            "Waaa4adb908bd17966b757b8fe93d4f95330ff2c6": 50_000_000
        },

    }
    f = 0
    file1 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Blockchain_Data", "last_block_number")
    print(file1)
    print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(os.path.abspath(__file__))
    # with open(file1, "w") as jfile:
    #     json.dump(f, jfile)
    # print(os.path.join(os.path.dirname(os.getcwd()), "Blockchain_Data", "last_block_number"))
    # print(os.listdir(os.path.join(os.path.dirname(os.getcwd()), "Blockchain_Data")))
