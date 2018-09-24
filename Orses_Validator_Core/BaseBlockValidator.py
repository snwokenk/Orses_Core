import os

from Orses_Competitor_Core.CompetitorDataLoading import BlockChainData

class BaseBlockValidator:
    def __init__(self,  block, admin_inst, is_newly_created=False, q_object=None):
        self.admin_inst = admin_inst
        self.isNewlyCreated = is_newly_created
        self.block = block
        self.block_header = block["bh"]
        self.blockNo = int(self.block_header["block_no"])

        self.prev_blockNo = self.blockNo - 1
        self.prev_block = BlockChainData.get_block(block_no=self.prev_blockNo, admin_instance=admin_inst)
        # os.path.join(self.admin_inst.fl.get_block_data_folder_path(), str(self.prev_blockNo))
        self.q_object = q_object

    def validate(self):

        return True  # for now just return true
