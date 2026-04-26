"""
check_styles.py — Check that every role in ports_definitions has a
                  corresponding style file in the STYLES directory,
                  and report any extra files with no matching role.

Usage:
    python check_styles.py -p <project_name>

The database file is expected at <project_name>.db.
The STYLES environment variable must point to the styles directory.
"""

import argparse
import os
import sqlite3
import sys


def get_cli_arguments():
    """Parse and return CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Check style files against roles defined in the database."
    )
    parser.add_argument(
        "-p",
        "--project",
        required=True,
        help="Project name — database file is <project>.db",
    )
    return parser.parse_args()


def opendb(file_name):
    """Validate and connect to an existing SQLite database.

    Raises:
        FileNotFoundError: if the file does not exist.
        RuntimeError: if the file is not a valid SQLite database.
    """
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Database file not found: '{file_name}'")

    with open(file_name, "rb") as f:
        header = f.read(16)
    if not header.startswith(b"SQLite format 3"):
        raise RuntimeError(f"File is not a valid SQLite database: '{file_name}'")

    conn = sqlite3.connect(file_name)
    print(f"[INFO] Connected to: {file_name}")
    return conn


def get_roles(conn):
    """Return all distinct non-empty roles from ports_definitions.

    Collects both from_role and to_role columns.

    Returns:
        Sorted list of unique role strings.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT from_role FROM ports_definitions WHERE from_role != ''
        UNION
        SELECT DISTINCT to_role   FROM ports_definitions WHERE to_role   != ''
    """)
    rows = cursor.fetchall()
    cursor.close()
    return sorted(role for (role,) in rows)


def get_style_files(styles_dir):
    """Return the set of base names (without .txt) from the styles directory.

    Args:
        styles_dir: path to the directory containing .txt style files.

    Returns:
        Set of role names derived from .txt filenames.

    Raises:
        FileNotFoundError: if the directory does not exist.
    """
    if not os.path.isdir(styles_dir):
        raise FileNotFoundError(f"STYLES directory not found: '{styles_dir}'")

    return {
        os.path.splitext(f)[0] for f in os.listdir(styles_dir) if f.endswith(".txt")
    }


def main():
    """Main function."""
    args = get_cli_arguments()

    db_file = f"{args.project}.db"

    styles_dir = os.environ.get("STYLES")
    if not styles_dir:
        print("[ERROR] STYLES environment variable is not set.")
        sys.exit(1)

    try:
        conn = opendb(db_file)
        db_roles = get_roles(conn)
        conn.close()

        style_names = get_style_files(styles_dir)

        db_role_set = set(db_roles)

        missing = sorted(db_role_set - style_names)  # roles in DB but no .txt file
        extra = sorted(style_names - db_role_set)  # .txt files with no DB role

        print(f"\n[INFO] Roles in DB       : {len(db_role_set)}")
        print(f"[INFO] Style files found : {len(style_names)}")

        if not missing and not extra:
            print("\n[OK] All roles have a matching style file. No extra files found.")
            return

        if missing:
            print(f"\n[MISSING] {len(missing)} role(s) have no style file:")
            for role in missing:
                print(f"  - {role}  →  expected: {styles_dir}/{role}.txt")

        if extra:
            print(f"\n[EXTRA] {len(extra)} style file(s) have no matching role:")
            for name in extra:
                print(f"  - {name}.txt")

    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except sqlite3.OperationalError as e:
        print(f"[ERROR] Database error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
