import os, json, pathlib

class FileAction:

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
