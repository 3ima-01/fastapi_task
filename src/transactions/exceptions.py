from fastapi import HTTPException, status


class TransactionNotExistsException(HTTPException):
    def __init__(self, transaction_id: int) -> None:
        detail = f"Transaction with id=`{transaction_id}` does not exist"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class TransactionDoesNotBelongToUserException(HTTPException):
    def __init__(self, transaction_id: int, user_id: int) -> None:
        detail = f"Transaction with id=`{transaction_id}` does not belong to user with id=`{user_id}`"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class TransactionAlreadyRollbackedException(HTTPException):
    def __init__(self, transaction_id: int) -> None:
        detail = f"Transaction with id=`{transaction_id}` is already rollbacked"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class NotEnoughBalanceException(HTTPException):
    def __init__(self) -> None:
        detail = "Not enough balance"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
