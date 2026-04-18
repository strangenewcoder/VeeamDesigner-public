"""
Create Veeam Design Diagram & Firewall configurations (POC)
"""

import argparse


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


def main():
    """Main function."""
    args = get_cli_arguments().parse_args()

    project_name = args.project
    drawing_name = args.drawing
    drawio_output = args.drawio
    firewall_output = args.firewall

    print(f"[INFO] Project         : {project_name}")
    print(f"[INFO] Drawing         : {drawing_name}")
    print(f"[INFO] Drawio_output   : {drawio_output}")
    print(f"[INFO] Firewall_output : {firewall_output}")

    db_file_name = project_name + ".db"
    systems_file_name = project_name + ".vd"
    drawing_file_name = drawing_name + ".drawio"


if __name__ == "__main__":
    main()
