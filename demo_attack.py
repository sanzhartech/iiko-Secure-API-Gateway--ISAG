import time
import requests
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

BASE_URL = "http://localhost:8000" # Assuming backend port or proxy
# Note: For this script to work fully, you'd normally need a valid token. 
# We'll simulate attempts that the gateway will reject to trigger Audit Logs.

print(f"{Fore.CYAN}{Style.BRIGHT}=== ISAG Demo Attack Script ===")
print("Sending requests to demonstrate real-time dashboard reactions...\n")

def send_request(endpoint, token=None, expected_status=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=2)
        color = Fore.GREEN if response.status_code < 400 else Fore.RED
        print(f"[{color}{response.status_code}{Style.RESET_ALL}] GET {endpoint}")
    except Exception as e:
        print(f"[{Fore.RED}ERROR{Style.RESET_ALL}] Connection failed: {e}")

print(f"{Fore.CYAN}[Phase 1] Normal Traffic Pulse...{Style.RESET_ALL}")
for i in range(5):
    send_request("/health")
    time.sleep(0.5)

print(f"\n{Fore.RED}[Phase 2] Aggressive Burst (Trigger Rate Limit)...{Style.RESET_ALL}")
# The auth endpoint is rate limited to 10/minute usually.
for i in range(15):
    send_request("/api/v1/auth/token")
    time.sleep(0.1)

print(f"\n{Fore.MAGENTA}[Phase 3] Unauthorized Forgery Attempt...{Style.RESET_ALL}")
fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
for i in range(3):
    send_request("/api/v1/proxy/catalog", token=fake_token)
    time.sleep(0.5)

print(f"\n{Fore.CYAN}{Style.BRIGHT}=== Attack Simulation Complete ===")
print("Check the ISAG Admin Dashboard 'Live Threat Feed' to see the results!")
