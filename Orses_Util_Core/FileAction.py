from Orses_Util_Core import Filenames_VariableNames

import os, json, pathlib, platform, hashlib


class FileAction:
    def __init__(self, admin=None):
        self.admin = admin
        self.username = admin.admin_name if admin is not None else None
        self.start_up_filename = "startup_file"
        self.network_wallets_data_filename = "Wallets_Data"
        self.__folders_created = False
        self.__project_path = FileAction.get_main_folder()
        self.__sandbox_folder_path = os.path.join(self.__project_path, Filenames_VariableNames.sandbox_folder)
        self.__live_folder_path = os.path.join(self.__project_path, Filenames_VariableNames.data_folder)
        self.__username_folder_path = None

        self.create_admin_folder(is_sandbox=admin.is_sandbox)


    """
    use section for creation of folders and returning of paths
    """

    def check_if_admin_folder_exist(self, is_sandbox=False):
        if self.admin.is_sandbox:
            return os.path.isdir(self.__sandbox_folder_path)
        else:
            return os.path.isdir(self.__live_folder_path)

    def create_admin_folder(self, is_sandbox=False):
        if self.__folders_created is True:
            return True
        elif not isinstance(self.username, str):
            return None

        def create_f(f_path):
            try:
                os.makedirs(f_path)
            except FileExistsError:
                return True
            except Exception as e:
                print(e)
                return False
            else:
                return True


        # make sure data folder or sandbox folder is created
        if is_sandbox is True:
            is_created = create_f(self.__sandbox_folder_path)
            self.__username_folder_path = os.path.join(self.__sandbox_folder_path, self.username)
        else:
            is_created = create_f(self.__live_folder_path)
            self.__username_folder_path = os.path.join(self.__live_folder_path, self.username)


        is_created1 = create_f(self.__username_folder_path)
        self.__folders_created = True if (is_created and is_created1) else False

        return self.__folders_created

    def load_startup_file(self):

        start_file = self.open_file_from_json(filename=self.start_up_filename, in_folder=self.__username_folder_path)

        return start_file

    def save_startup_file(self, **kwargs):
        """

        :param kwargs: dictionary should contain  is_competitor and always_compete which are boolean,
            can contain other things
        :return:
        """

        if kwargs:

            self.save_json_into_file(
                filename=self.start_up_filename,
                python_json_serializable_object=kwargs,
                in_folder=self.__username_folder_path
            )

            return True

    def get_address_file_path(self):
        return os.path.join(self.get_username_folder_path(), Filenames_VariableNames.default_addr_list_sandbox) if (
            self.admin.is_sandbox) else \
            os.path.join(self.get_username_folder_path(), Filenames_VariableNames.default_addr_list)

    def get_username_folder_path(self):
        if isinstance(self.__username_folder_path, str) and self.__folders_created:
            return self.__username_folder_path

    def get_live_data_folder_path(self):
        if isinstance(self.__live_folder_path, str) and self.__folders_created:
            return self.__live_folder_path

    def get_sandbox_data_folder_path(self):
        if isinstance(self.__sandbox_folder_path, str) and self.__folders_created:
            return self.__sandbox_folder_path

    def get_keys_folder_path(self):
        rsp = os.path.join(self.get_username_folder_path(), Filenames_VariableNames.key_folder)
        return rsp

    def get_proxy_center_folder_path(self):
        '''
        folder where all proxy data is stored
        is a folder of folders with each folder in it representing a wallet proxy OR Leveldb folder
        :return:
        '''
        folder_path = os.path.join(self.__username_folder_path, Filenames_VariableNames.proxy_center_folder)

        try:
            os.mkdir(folder_path)
        except OSError:
            pass

        return folder_path

    def get_wallet_proxy_folder_path(self, proxy_name: str):
        """
        gets folder of a wallet proxy
        :param proxy_name: name of Wallet proxy
        :return:
        """
        folder_path = os.path.join(self.get_proxy_center_folder_path(), proxy_name)
        try:
            os.mkdir(folder_path)
        except OSError:
            pass

        return folder_path

    def get_wallets_folder_path(self):
        """
        folder where admin's wallets are stored
        :return:
        """

        folder_path = os.path.join(self.__username_folder_path, Filenames_VariableNames.wallets_folder)

        try:
            os.mkdir(folder_path)
        except OSError:
            pass

        return folder_path

    def get_clients_wallet_folder_path(self):
        return os.path.join(self.__username_folder_path, Filenames_VariableNames.clients_wallets_data)

    def get_admin_data_folder_path(self):
        return os.path.join(self.__username_folder_path, Filenames_VariableNames.admin_data)

    def get_mempool_data_folder_path(self):
        return os.path.join(self.__username_folder_path, Filenames_VariableNames.mempool_data)

    def get_block_data_folder_path(self):
        return os.path.join(self.__username_folder_path, Filenames_VariableNames.block_folder)

    def update_addresses(self, address_list, ):
        """
        updates address list file and Admin.known_addresses with new address
        :param address_list:
        :return:
        """
        addr_filename = self.get_address_file_path()
        addr_data = self.open_file_from_json(filename=addr_filename)

        for ip_address in address_list:
            print("in File action ip address updates", ip_address, address_list)
            if ip_address not in addr_data:
                addr_data.update({ip_address: 55602})
                try:
                    self.admin.known_addresses.update({ip_address[0]: 55602})
                except AttributeError:
                    pass

                self.save_json_into_file(
                    filename=addr_filename,
                    python_json_serializable_object=addr_data
                )

    def get_addresses(self):
        addr_filename = self.get_address_file_path()

        return self.open_file_from_json(filename=addr_filename)

    def get_blacklisted_admin(self):
        # TODO: get or created blacklisted file

        return {}


    """
    section for static functions for saving/loading text, bytes and json files
    also for creating folders for export/import
    """
    @staticmethod
    def create_folder(folder_name):
        path1 = os.path.join(pathlib.Path.home(), "Desktop", "CryptoHub_External_Files", folder_name)
        try:
            os.makedirs(path1)
        except FileExistsError:
            pass


    @staticmethod
    def delete_file(filename, in_folder=None):

        try:
            filename = os.path.abspath(os.path.join(in_folder, filename))
            os.remove(filename)
        except FileNotFoundError:
            pass
        finally:
            return True
    @staticmethod
    def open_file_into_byte(filename, in_folder=None):
        if in_folder:
            try:
                os.mkdir(in_folder)
            except OSError:
                pass
            finally:
                filename = os.path.abspath(os.path.join(in_folder, filename))

        try:
            with open(filename, 'rb') as bitefile:
                data_byte_array = bitefile.read()
        except FileNotFoundError:
            return b''
        else:
            return data_byte_array

    @staticmethod
    def save_byte_into_file(filename, byte_to_write, in_folder=None):
        if in_folder:
            try:
                os.mkdir(in_folder)
            except OSError:
                pass
            finally:
                filename = os.path.abspath(os.path.join(in_folder, filename))
        with open(filename, 'wb') as bitefile:
            bitefile.write(byte_to_write)

    @staticmethod
    def save_json_into_file(filename, python_json_serializable_object, in_folder=None):
        if in_folder:
            try:
                os.mkdir(in_folder)
            except OSError:
                pass
            finally:
                filename = os.path.abspath(os.path.join(in_folder, filename))
        with open(filename, "w") as infile:
            json.dump(python_json_serializable_object, infile)

        return True

    @staticmethod
    def open_file_from_json(filename, in_folder=None):
        if in_folder:
            try:
                os.mkdir(in_folder)
            except OSError:
                pass
            finally:
                filename = os.path.abspath(os.path.join(in_folder, filename))

        try:
            with open(filename, 'r') as outfile:
                d = json.load(outfile)
        except FileNotFoundError:
            return []
        else:

            return d

    @staticmethod
    def open_file(filename, in_folder=None):
        if in_folder:
            try:
                os.mkdir(in_folder)
            except OSError:
                pass
            finally:
                filename = os.path.abspath(os.path.join(in_folder, filename))
        with open(filename, 'r') as outfile:
            d = outfile.read()

        return d

    @staticmethod
    def save_file(filename, data, in_folder=None):
        if in_folder:
            try:
                os.mkdir(in_folder)
            except OSError:
                pass
            finally:
                filename = os.path.abspath(os.path.join(in_folder, filename))
        with open(filename, "w") as infile:
            infile.write(data)

        return True

    @staticmethod
    def copy_file(src, st):
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @classmethod
    def splitTheFiles(cls, file_name, numberOfPart=3):

        """
        when function called, it splits  file stored in arrayofByte into the numberOfPart times

        example:

            1 with open("cloud.txt", "rb") as biteFile:
            2 dataByteArray = bytearray(biteFile.read())

            3 splitTheFiles(arrayOfByte=dataByteArray, numberOfPart=3)

        In above example, file "cloud.txt" is opened, in binary or byte mode and assigned to variable dataByteArray.
        file then called in line 3 which tells function to take file and divided it by 3 (numberOfPart=3)

        :param arrayOfByte: byte file to be split, usually got by opening file in "rb" mode
        :param numberOfPart: number of parts to split arrayOfByte. default=3
        :return: list of bytearrays of original file
        """
        arrayOfByte = FileAction.open_file_into_byte(filename=file_name)
        sizeOfFile = len(arrayOfByte)
        sizeOfEachPart = sizeOfFile // numberOfPart
        remainderOfParts = sizeOfFile % numberOfPart
        print(sizeOfFile, sizeOfEachPart, remainderOfParts)
        startNumber = 0

        listOfParts = list()
        for i in range(0, sizeOfEachPart * (numberOfPart), sizeOfEachPart):
            # loop till i is equals to last whole part ie. 121/10 = 12,24,36,48,60,72,84,96,108(end here), 120
            if i == 0:
                continue
            listOfParts.append(arrayOfByte[startNumber:i])
            startNumber += sizeOfEachPart

        listOfParts.append(arrayOfByte[startNumber:sizeOfFile])  # this will gather data from 108 - 121

        return listOfParts

    @staticmethod
    def get_main_folder():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def get_path_of_important_files():
        """
        returns a list of paths for important files for hashing
        Files to get:
        start_node.py
        note for windows rather than "/" use "\"
        Orses_Validator_Core/AssignmentStatementValidator.py
        Orses_Validator_Core/TokenReservationRequestValidator.py
        Orses_Validator_Core/TokenReservationRevokeValidator.py
        Orses_Validator_Core/TokenTransferValidator.py

        Orses_Cryptography_Core/DigitalSignerValidator.py
        Orses_Cryptography_Core/DigitalSigner.py
        Orses_Cryptography_Core/Encryption.py
        Orses_Cryptography_Core/Decryption.py
        Orses_Cryptography_Core/PKIGeneration.py
        :return: list of paths of importan files. This list is used to
        """
        main_folder = FileAction.get_main_folder()
        sys_dep_slash = "\\" if platform.system() == "Windows" else "/"
        list_filenames = [
            "start_node.py",
            f"Orses_Validator_Core{sys_dep_slash}AssignmentStatementValidator.py",
            f"Orses_Validator_Core{sys_dep_slash}TokenTransferValidator.py",
            f"Orses_Validator_Core{sys_dep_slash}TokenReservationRequestValidator.py",
            f"Orses_Validator_Core{sys_dep_slash}TokenReservationRevokeValidator.py",
            f"Orses_Cryptography_Core{sys_dep_slash}DigitalSignerValidator.py",
            f"Orses_Cryptography_Core{sys_dep_slash}DigitalSigner.py",
            f"Orses_Cryptography_Core{sys_dep_slash}Encryption.py",
            f"Orses_Cryptography_Core{sys_dep_slash}Decryption.py",
            f"Orses_Cryptography_Core{sys_dep_slash}PKIGeneration.py"

        ]
        list_of_filepaths = []

        for name in list_filenames:
            list_of_filepaths.append(os.path.join(main_folder, name))

        return list_of_filepaths

if __name__ == '__main__':
    print(os.getcwd())
    main_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    k = FileAction.get_path_of_important_files()
    print(len(k))
