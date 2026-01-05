from src.exceptions import BadRequestDataException


def validate_positive_id(user_id: int) -> int:
    if user_id <= 0:
        raise BadRequestDataException(detail="Unprocessable data in request")
    return user_id
