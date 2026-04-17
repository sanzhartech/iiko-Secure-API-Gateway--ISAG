import os
import json
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_keys():
    # Paths
    keys_dir = Path(__file__).parent.parent / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    
    private_key_path = keys_dir / "private.pem"
    public_key_path = keys_dir / "public.pem"
    public_json_path = keys_dir / "public_keys.json"

    print(f"Generating RSA keys in {keys_dir}...")

    # Generate Private Key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Serialize Private Key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Serialize Public Key
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Write PEM files
    private_key_path.write_bytes(private_pem)
    public_key_path.write_bytes(public_pem)
    
    # Write JSON store (for multi-key support validation)
    public_keys_data = {
        "default": public_pem.decode("utf-8")
    }
    public_json_path.write_text(json.dumps(public_keys_data, indent=2), encoding="utf-8")

    print(f"Success!")
    print(f"  - Private key: {private_key_path}")
    print(f"  - Public key: {public_key_path}")
    print(f"  - Public JSON store: {public_json_path}")

if __name__ == "__main__":
    generate_keys()
