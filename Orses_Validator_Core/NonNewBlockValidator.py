"""

used to validate blocks that are not new.

it does not automatically propagate valid blocks
"""

from Orses_Validator_Core.BaseBlockValidator import BaseBlockValidator
# todo: create validation logic


class NonNewBlockValidator(BaseBlockValidator):

    def __init__(self, block, admin_inst,is_newly_created=False, q_object=None):
        super().__init__(
            block=block,
            admin_inst=admin_inst,
            is_newly_created=is_newly_created,
            q_object=q_object
        )

    def validate(self):
        return True  # for now return true
