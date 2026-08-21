from pathlib import Path
import os
import csv

root_dir = Path(__file__).parent.parent
REPORTS = os.path.join(root_dir, "reports")
COOKIES = os.path.join(root_dir, "cookies")
SCREENSHOTS = os.path.join(root_dir, "reports", "screenshots")
TEST_RESULT_CSV = os.path.join(root_dir, "reports", "test_results.csv")
ENV_FILE = os.path.join(root_dir, ".env")

ENV_TEMPLATE = """Here you can store multiple db configurations for different environments. ex: db1, db2 which can be used while querying DB.

# ==========================
# DATABASE CONFIGURATIONS
# ==========================

# Usage Example:
# with DBMANAGER("DB1") as db:
# with DBMANAGER("DB2") as db:

# ----- DB1 (Postgres) -----
DB1_DB_TYPE=postgres
DB1_DB_HOST=XXX.X.X.X
DB1_DB_PORT=5432
DB1_DB_USER=XXXXX_XXXX
DB1_DB_PASSWORD=XXXXXXXXXX
DB1_DB_NAME=XXXXXXXX_XXXXXXX

# ----- DB2 (MySQL) -----
DB1_DB_TYPE=mysql
DB1_DB_HOST=XXX.X.X.X
DB1_DB_PORT=3306
DB1_DB_USER=XXXXX_XXXX
DB1_DB_PASSWORD=XXXXXXXXXX
DB1_DB_NAME=XXXXXXXX_XXXXXXX

# SSH Config prefix is used in utils/ssh_connection.py to connect to remote server and execute commands on remote server.
# You can have multiple ssh configuration for different environments. 
# ex: ssh1,ssh2 which can be used while connection to remote server.
# ssh configuration
SSH_TOTP_SECRET= Key from authenticator app (e.g. Google Authenticator) for SSH connection to remote server.
SSH_TOTP_INTERVAL=30 # Time interval in seconds for generating TOTP code for SSH connection to remote server.
SSH_KEY_PATH=C:/Users/username/.ssh/id_rsa # Path to private key file for SSH connection to remote server.
SSH_KEYPATH=C:\\sers\\yourPemFile.pem # Path to private key file for SSH connection to remote server. 
SSH_PORT= 32 # SSH port number for SSH connection to remote server.
SSH_USER=XXXXXX # SSH username for SSH connection to remote server.
SSH_HOST=XXX.X.X.X # SSH host for SSH connection to remote server.
SSH_LOCAL_PORT=5432 # Local port for SSH connection to remote server.
SSH_REMOTE_DB_HOST=XXX.X.X.X # Remote database host for SSH connection to remote server.
SSH_REMOTE_DB_PORT=5432 # Remote database port for SSH conenction to remote server.
SSH_PASTE_DELAY_SECONDS=2 # Delay in seconds for pasting the TOTP code in the SSH connection to remote server.
"""


def file_exists(file_path: str):
    """Check if a file or directory exists at the given path."""
    return os.path.exists(file_path)
def create_file_and_folder():
    """
    Create necessary folders and files for test execution.
    """
    if not file_exists(REPORTS):
        os.mkdir(REPORTS)
    if not file_exists(SCREENSHOTS):
        os.mkdir(SCREENSHOTS)
    if not file_exists(COOKIES):
        os.mkdir(COOKIES)
    if not os.path.exists(TEST_RESULT_CSV):
        with open(TEST_RESULT_CSV, mode="x", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Test Name", "Status",]) 