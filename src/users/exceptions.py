from fastapi import HTTPException, status


class UserAlreadyExistsException(HTTPException):
    def __init__(self, email: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email=`{email}` already exists",
        )


class UserNotExistsException(HTTPException):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id=`{user_id}` does not exist",
        )


class UserAlreadyBlockedException(HTTPException):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with id=`{user_id}` is already blocked",
        )


class UserAlreadyActiveException(HTTPException):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with id=`{user_id}` is already active",
        )


class UserIsBlockedException(HTTPException):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id=`{user_id}` is blocked",
        )


class UserBalanceDoesNotExists(HTTPException):
    def __init__(self, user_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Balance for user id=`{user_id}` does not exists",
        )
