import jwt

from app.core.config import settings
from app.core.security import create_access_token


# Generate a token for a sample user
token = create_access_token(subject="1")

print("\nGenerated JWT Token:")
print(token)

# Decode and verify the token
decoded_token = jwt.decode(
    token,
    settings.JWT_SECRET_KEY,
    algorithms=[settings.JWT_ALGORITHM]
)

print("\nDecoded Token Payload:")
print(decoded_token)

print("\nUser ID:", decoded_token["sub"])
print("Token expiration:", decoded_token["exp"])

print("\nJWT test successful!")