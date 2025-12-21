from fastapi import HTTPException, status


class UserAlreadyExistsException(HTTPException):
    def __init__(self, email: str) -> None:
        detail = f"User with email=`{email}` already exists"
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UserNotExistsException(HTTPException):
    def __init__(self, user_id: int) -> None:
        detail = f"User with id=`{user_id}` does not exist"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UserAlreadyBlockedException(HTTPException):
    def __init__(self, user_id: int) -> None:
        detail = f"User with id=`{user_id}` is already blocked"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UserAlreadyActiveException(HTTPException):
    def __init__(self, user_id: int) -> None:
        detail = f"User with id=`{user_id}` is already active"
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UserIsBlockedException(HTTPException):
    def __init__(self, user_id: int) -> None:
        detail = f"User with id=`{user_id}` is blocked"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
