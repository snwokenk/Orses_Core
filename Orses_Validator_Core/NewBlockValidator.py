"""

module used to validate new blocks,
validation requires:
block is gotten from WinnerValidator, which validates the winning hash and receives the
winning block(and the other runner ups)

"""

# todo: create validation logic


class NewBlockValidator:
    def __init__(self, block_no, block, is_newly_created=False):
        self.isNewlyCreated = is_newly_created
        self.blockNo = block_no
        self.block = block

    def validate(self):

        return True  # for now just return true

