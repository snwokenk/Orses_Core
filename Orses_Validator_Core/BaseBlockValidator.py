import os


class BaseBlockValidator:
    def __init__(self, block_no, block, admin_inst, is_newly_created=False, q_object=None):
        self.admin_inst = admin_inst
        self.isNewlyCreated = is_newly_created
        self.blockNo = block_no
        self.block = block
        self.prev_blockNo = block_no - 1
        self.prev_block = os.path.join(self.admin_inst.fl.get_block_data_folder_path(), self.prev_blockNo)
        self.q_object = q_object

    def validate(self):

        return True  # for now just return true
