from enum import StrEnum


class TransactionStatusEnum(StrEnum):
    PROCESSED = "PROCESSED"
    ROLL_BACKED = "ROLLBACKED"
