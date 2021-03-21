from enum import Enum

class ShareStatus(Enum):
    NO_SHARE = 0
    SHARE_FROM_SELF_TO_OTHER = 1
    SHARE_FROM_OTHER_TO_SELF = 2
