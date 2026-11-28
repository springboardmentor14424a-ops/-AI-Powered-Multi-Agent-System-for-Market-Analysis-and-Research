from pydantic import ValidationError
from app.schemas.user import UserRegister


# Test 1: Valid registration data
try:
    user = UserRegister(
        full_name="Rajesh Reddy",
        email="rajesh@example.com",
        password="StrongPass123"
    )

    print("VALID DATA:")
    print(user)

except ValidationError as error:
    print(error)


# Test 2: Invalid registration data
try:
    UserRegister(
        full_name="R",
        email="invalid-email",
        password="123"
    )

except ValidationError as error:
    print("\nINVALID DATA REJECTED:")
    print(error)