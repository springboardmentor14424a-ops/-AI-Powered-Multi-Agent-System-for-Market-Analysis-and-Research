
from security import hash_password, verify_password

# Original password (test only)
password = "Test@12345"

# Generate password hash
hashed_password = hash_password(password)

print("Original password:", password)
print("Hashed password:", hashed_password)

# Verify correct password
print("Correct password:", verify_password(password, hashed_password))

# Verify incorrect password
print("Wrong password:", verify_password("Wrong@123", hashed_password))
