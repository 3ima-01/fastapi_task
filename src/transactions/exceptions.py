from fastapi import HTTPException, status


class TransactionNotExistsException(HTTPException):
    def __init__(self, transaction_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with id=`{transaction_id}` does not exist",
        )


class TransactionDoesNotBelongToUserException(HTTPException):
    def __init__(self, transaction_id: int, user_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with id=`{transaction_id}` does not belong to user with id=`{user_id}`",
        )


class TransactionAlreadyRollbackedException(HTTPException):
    def __init__(self, transaction_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction with id=`{transaction_id}` is already rollbacked",
        )


class NotEnoughBalanceException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough balance",
        )
