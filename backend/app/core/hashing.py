from passlib.context import CryptContext

# Use bcrypt via passlib.
# Ensures transparent handling of constant-time comparisons natively blocking timing-oracles.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain string against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Returns bcrypt hash of the plain string."""
    return pwd_context.hash(password)

def dummy_verify() -> None:
    """Takes about the same time as verify_password, preventing timing oracles."""
    pwd_context.dummy_verify()
