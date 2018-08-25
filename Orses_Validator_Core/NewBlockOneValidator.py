from Orses_Validator_Core.NewBlockValidator import NewBlockValidator


class NewBlockOneValidator(NewBlockValidator):

    """
    Block ones validator is simple, ownership of tokens sent are validated looking at the token association transaction
    of Genesis Block. Messages Sent
    """
    def __init__(self, block_no, block, admin_inst, is_newly_created=True, q_object=None):
        super().__init__(
            block_no=block_no,
            block=block,
            admin_inst=admin_inst,
            is_newly_created=is_newly_created,
            q_object=q_object

        )


    def verify_merkle_root_parts(self):
        pass
