
from datetime import datetime, timezone
from types import SimpleNamespace

from app.schemas.user import UserResponse


# Simulate a database user object
fake_user = SimpleNamespace(
    user_id=1,
    full_name="Rajesh Reddy",
    email="rajesh@example.com",
    password_hash="SECRET_HASH_SHOULD_NOT_APPEAR",
    created_at=datetime.now(timezone.utc)
)

# Convert database-like object into API response
response = UserResponse.model_validate(fake_user)

print("API RESPONSE:")
print(response.model_dump())

print("\nJSON RESPONSE:")
print(response.model_dump_json())

# Security check
assert "password_hash" not in response.model_dump()
assert "password" not in response.model_dump()

print("\nSECURITY TEST PASSED: Password hash is not exposed.")

