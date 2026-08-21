
import argparse
import os
import shutil
import smtplib
import sys
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytest
from config import common_config_file as config
from utils import file_folder


def parse_cli_args():
    """Parse command line arguments or fall back to config settings."""
    parser = argparse.ArgumentParser(description="Test Suite Runner")
    parser.add_argument(
        "-t",
        "--tags",
        nargs="+",
        help="pytest markers to run (e.g. -t smoke regression)",
    )
    parser.add_argument(
        "-b",
        "--browser",
        default=config.browser_type,
        help="Browser type (chromium, firefox, webkit)",
    )
    parser.add_argument(
        "-e",
        "--env",
        default=config.environment,
        help="Target environment (dev, staging, production)",
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode"
    )
    return parser.parse_args()


def build_pytest_args(cli_args):
    """Construct pytest execution arguments dynamically."""
    tags = cli_args.tags or config.execution_type
    marker_expr = " or ".join(tags)

    args = [
        "tests", # Target tests folder explicitly
        "-v",
        f"--target-browser={cli_args.browser}",
        f"--target-env={cli_args.env}",
        # f"-m={marker_expr}",
    ]

    # Pass -m and marker expression as separate arguments
    if tags:
        marker_expr = " or ".join(tags)
        args.extend(["-m", marker_expr])

    if cli_args.headless or config.headless_mode:
        args.append("--headless")

    # Target test directory defined in config/ini or explicitly default to "tests"
    args.append("tests")

    return args


def send_report_email(zip_path=None):
    """Trigger email delivery post-execution with optional attachment."""
    if not config.recipients:
        print("No recipients configured. Skipping email delivery.")
        return

    print(
        f"Sending execution report from {config.sender_email} to {config.recipients}..."
    )

    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg["From"] = config.sender_email
    msg["To"] = ", ".join(config.recipients)
    msg["Subject"] = config.subject

    body = f"""
    <h2>Test Execution Completed</h2>
    <p><b>Environment:</b> {config.environment}</p>
    <p><b>Browser:</b> {config.browser_type}</p>
    <p>Please find the attached execution report.</p>
    """
    msg.attach(MIMEText(body, "html"))

    # Attach the ZIP file if available
    if zip_path and os.path.exists(zip_path):
        with open(zip_path, "rb") as attachment:
            part = MIMEBase("application", "zip")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        filename = os.path.basename(zip_path)
        part.add_header(
            "Content-Disposition", f"attachment; filename={filename}"
        )
        msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(config.sender_email, config.sender_password)
        server.sendmail(config.sender_email, config.recipients, msg.as_string())
        server.quit()
        print("Report email sent successfully.")
    except Exception as e:
        print(f"Failed to send email report: {e}")


def cleanup_and_prep_directories():
    """Safely delete previous test artifacts and re-create directory structures."""
    for folder_name in ["reports", "cookies"]:
        target_dir = os.path.join(os.getcwd(), folder_name)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

    file_folder.create_file_and_folder()

def create_reports_zip(reports_dir="reports", output_zip="execution_report"):
    """Compress the reports directory into a ZIP file."""
    if not os.path.exists(reports_dir) or not os.listdir(reports_dir):
        print(
            f"Directory '{reports_dir}' is missing or empty. Skipping ZIP creation."
        )
        return None

    try:
        # Archives 'reports' directory into 'execution_report.zip'
        zip_path = shutil.make_archive(
            base_name=output_zip, format="zip", root_dir=reports_dir
        )
        print(f"Created reports archive: {zip_path}")
        return zip_path
    except Exception as e:
        print(f"Failed to create ZIP archive: {e}")
        return None


def main():
    cli_args = parse_cli_args()

    # Clean previous run data once per execution
    cleanup_and_prep_directories()

    # Build flags and run pytest suite
    pytest_args = build_pytest_args(cli_args)
    exit_code = pytest.main(pytest_args)


    # Post-execution reporting logic
    # Exit code 5 means no tests were collected
    if exit_code == 5:
        print("No tests collected. Skipping email report generation.")
    # Trigger post-execution reporting
    elif config.email_report:
        # Create ZIP archive from the reports folder and send email
        zip_file = create_reports_zip(
            reports_dir="reports", output_zip="execution_report"
        )
        send_report_email(zip_file)


if __name__ == "__main__":
    main()