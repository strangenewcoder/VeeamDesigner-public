"""
Create Veeam Design Diagram & Firewall configurations (POC)
"""

import argparse
import os
import sqlite3
import sys
import eprint


def get_cli_arguments():
    """
    Parse the command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate Veeam network diagrams and firewall rules"
    )
    parser.add_argument(
        "-p",
        "--project",
        required=True,
        help="project name (used as DB and .vd filename)",
    )
    parser.add_argument(
        "-w", "--drawing", required=True, help="drawing name to process"
    )
    parser.add_argument(
        "-d",
        "--drawio",
        default=False,
        action="store_true",
        help="enable Draw.io output",
    )
    parser.add_argument(
        "-f",
        "--firewall",
        default=False,
        action="store_true",
        help="enable firewall rules output",
    )
    return parser


def opendb(file_name):
    """connect to SQLite DB."""
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Database file not found: '{file_name}'")

    # quick check: SQLite files start with "SQLite format 3"
    with open(file_name, "rb") as f:
        header = f.read(16)
    if not header.startswith(b"SQLite format 3"):
        raise RuntimeError(f"File is not a valid SQLite database: '{file_name}'")

    db_conn = sqlite3.connect(file_name)
    eprint.eprint(f"[INFO] Connected to: {file_name}")
    return db_conn


def loadsystems(file_name, drawing_name, conn):
    """Load systems from .vd file into the systems table."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM systems;")

    rows_loaded = 0
    with open(file_name, "r") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(";")
            if len(parts) != 5:
                eprint.eprint(
                    f"[WARN] Line {line_num} skipped (expected 5 fields, got {len(parts)}): {line}"
                )
                continue

            drawings, name, ip, role, mainrole = parts
            if drawing_name in drawings:
                cursor.execute(
                    """
                    INSERT INTO systems (drawings, name, ip, role, mainrole)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (drawings, name, ip if ip else None, role, int(mainrole)),
                )
                rows_loaded += 1

    conn.commit()
    eprint.eprint(f"[INFO] Loaded {rows_loaded} rows for drawing '{drawing_name}'.")


def main():
    """Main function."""
    args = get_cli_arguments().parse_args()

    project_name = args.project
    drawing_name = args.drawing
    drawio_output = args.drawio
    firewall_output = args.firewall

    eprint.set_debug(False)

    eprint.eprint(f"[INFO] Project         : {project_name}")
    eprint.eprint(f"[INFO] Drawing         : {drawing_name}")
    eprint.eprint(f"[INFO] Drawio_output   : {drawio_output}")
    eprint.eprint(f"[INFO] Firewall_output : {firewall_output}")

    db_file_name = project_name + ".db"
    systems_file_name = project_name + ".vd"
    drawing_file_name = drawing_name + ".drawio"

    try:
        db_conn = opendb(db_file_name)
        loadsystems(systems_file_name, drawing_name, db_conn)
        # TODO: generate Draw.io  → drawing_file_name
        # TODO: generate firewall → if firewall_output

    except FileNotFoundError as err:
        eprint.eprint(f"[ERROR] {err}")
        sys.exit(1)
    except RuntimeError as err:
        eprint.eprint(f"[ERROR] {err}")
        sys.exit(1)
    except sqlite3.OperationalError as e:
        eprint.eprint(f"[ERROR] Database error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
