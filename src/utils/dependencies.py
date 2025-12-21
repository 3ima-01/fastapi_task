from fastapi import status

from exceptions import BadRequestDataException


def validate_positive_id(id: int) -> int:
    if id <= 0:
        raise BadRequestDataException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request"
        )
    return id
