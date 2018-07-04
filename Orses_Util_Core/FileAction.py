from Orses_Util_Core import Filenames_VariableNames

import os, json, pathlib


class FileAction:
    def __init__(self, username=None, is_sandbox=False):
        self.username = username
        self.__folders_created = False
        self.__project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.__sandbox_folder_path = os.path.join(self.__project_path, Filenames_VariableNames.sandbox_folder)
        self.__live_folder_path = os.path.join(self.__project_path, Filenames_VariableNames.data_folder)
        self.__username_folder_path = None

        if not self.check_if_admin_folder_exist(is_sandbox):
            self.create_admin_folder(is_sandbox=is_sandbox)


    """
    use section for creation of folders and returning of paths
    """

    def check_if_admin_folder_exist(self, is_sandbox=False):
        if is_sandbox:
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
        return os.path.join(self.__username_folder_path, Filenames_VariableNames.key_folder)

    def get_wallets_folder_path(self):
        """
        folder where admin's wallets are stored
        :return:
        """
        return os.path.join(self.__username_folder_path, Filenames_VariableNames.wallets_folder)

    def get_clients_wallet_folder_path(self):
        return os.path.join(self.__username_folder_path, Filenames_VariableNames.clients_wallets_data)

    def get_admin_data_folder_path(self):
        return os.path.join(self.__username_folder_path, Filenames_VariableNames.admin_data)

    def get_mempool_data_folder_path(self):
        return os.path.join(self.__username_folder_path, Filenames_VariableNames.mempool_data)

    def get_block_data_folder_path(self):
        return os.path.join(self.__username_folder_path, Filenames_VariableNames.block_folder)

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

if __name__ == '__main__':
    print(os.getcwd())
    print(os.path.abspath(__file__))