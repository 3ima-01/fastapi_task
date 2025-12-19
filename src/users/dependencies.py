from fastapi import status

from exceptions import BadRequestDataException


def validate_positive_user_id(user_id: int) -> int:
    if user_id <= 0:
        raise BadRequestDataException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request"
        )
    return user_id
