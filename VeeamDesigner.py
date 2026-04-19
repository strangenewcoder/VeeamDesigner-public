"""
Create Veeam Design Diagram & Firewall configurations (POC)
"""

import argparse
import os
import sqlite3
import sys
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
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

    # loading the mappings
    cursor.execute("DELETE FROM mappings;")
    cursor.execute("""
        INSERT INTO mappings (from_name, from_role, to_name, to_role)
        SELECT DISTINCT
            s_from.name AS from_name,
            s_from.role AS from_role,
            s_to.name   AS to_name,
            s_to.role   AS to_role
        FROM systems s_from
        JOIN ports_definitions p ON s_from.role = p.from_role
        JOIN systems s_to        ON s_to.role   = p.to_role
        WHERE s_from.name != s_to.name
    """)

    conn.commit()
    eprint.eprint(f"[INFO] Loaded {rows_loaded} rows for drawing '{drawing_name}'.")


def read_drawio(file_name):
    """
    Read and parse a drawio file.
    Returns a dictionary keyed by object id:
    {id: (label, x, y, width, height, style)}
    """
    result = {}

    if not os.path.exists(file_name):
        return result

    tree = ET.parse(file_name)
    root = tree.getroot()

    for obj in root.findall(".//object"):
        obj_id = obj.get("id")
        if not obj_id:
            continue

        geo = obj.find(".//mxGeometry")
        if geo is None:
            continue

        tmp_width = geo.get("width")
        tmp_height = geo.get("height")
        if not tmp_width or not tmp_height:
            continue

        # strip HTML from label
        soup = BeautifulSoup(obj.get("label", ""), "html.parser")
        obj_label = soup.text

        # truncate floats to int
        coord_x = geo.get("x", "0").split(".")[0]
        coord_y = geo.get("y", "0").split(".")[0]
        width = tmp_width.split(".")[0]
        height = tmp_height.split(".")[0]

        # obj_cell = obj.find(".//mxCell")
        # style = obj_cell.get("style") if obj_cell is not None else ""

        result[obj_id] = (obj_label, coord_x, coord_y, width, height)

        eprint.debug_eprint(
            f"[DRAWIO] id={obj_id} label={obj_label} x={coord_x} y={coord_y} w={width} h={height}"
        )

    return result


def getobj(conn):
    """
    Returns a list of systems with their main role and secondary roles.
    Each row: (name, ip, main_role, other_roles)
    """
    curs = conn.cursor()
    curs.execute("""
        SELECT
            s_main.name,
            s_main.ip,
            s_main.role                      AS main_role,
            GROUP_CONCAT(s_other.role, ', ') AS other_roles
        FROM systems s_main
        LEFT JOIN systems s_other
            ON  s_other.name     = s_main.name
            AND s_other.mainrole = 0
        WHERE s_main.mainrole = 1
        GROUP BY s_main.name, s_main.ip, s_main.role
    """)
    data = curs.fetchall()
    curs.close()

    eprint.debug_epprint(data)

    return data


def output_code_begin(drawing_name):
    """
    Returns the header lines of the generated Python script.
    """
    lines = []
    lines.append("import os")
    lines.append("from N2G import drawio_diagram")
    lines.append(f"styles_dir = os.environ.get('STYLES', '.')")
    lines.append("diagram = drawio_diagram()")
    lines.append('diagram.add_diagram("Page-1")')
    lines.append("")
    
    return lines
    

def output_code_nodes(db_obj_data, drawing_content):
    """
    Returns the add_node lines of the generated Python script.
    """
    lines = []
    auto_x = 300
    auto_y = 300

    for name, ip, main_role, other_roles in db_obj_data:

        if name in drawing_content:
            _, x_pos, y_pos, width, height = drawing_content[name]
            eprint.debug_eprint(f"[DRAWIO] {name} found in drawing at x={x_pos} y={y_pos}")
        else:
            x_pos  = str(auto_x)
            y_pos  = str(auto_y)
            width  = "60"
            height = "60"
            auto_x += 100
            auto_y += 100
            eprint.debug_eprint(f"[DRAWIO] {name} not found, auto-positioned at x={x_pos} y={y_pos}")

        style_file = f"styles_dir + '/{main_role}.txt'"

        lines.append(
            f'diagram.add_node('
            f'id="{name}", '
            f'label="{name}", '
            f'style={style_file}, '
            f'x_pos="{x_pos}", '
            f'y_pos="{y_pos}", '
            f'width="{width}", '
            f'height="{height}", '
            f'data={{"ip": "{ip or ""}", "role": "{main_role}", "other_roles": "{other_roles or ""}"}})'
        )
        eprint.debug_eprint(f"[DRAWIO] node line added: {name} role={main_role}")

    lines.append("")
    
    return lines
    
    
def output_code_end(drawing_file_name):
    """
    Returns the footer lines of the generated Python script.
    """
    folder   = os.path.dirname(drawing_file_name) or "./"
    filename = os.path.basename(drawing_file_name)
    lines = []
    lines.append(f'diagram.dump_file(filename="{filename}", folder="{folder}")')
    
    return lines
    
    
def write_script(drawing_name, drawing_file_name, db_obj_data, drawing_content):
    """
    Assembles and writes the generated Python script to file.
    """
    script_file = drawing_name + ".py"

    lines  = output_code_begin(drawing_name)
    lines += output_code_nodes(db_obj_data, drawing_content)
    lines += output_code_end(drawing_file_name)

    with open(script_file, "w") as f:
        f.write("\n".join(lines))

    eprint.debug_eprint(f"[SCRIPT] written: {script_file}")
    
    print(f"[OK] Script generated: {script_file}")
    
    
def main():
    """Main function."""
    args = get_cli_arguments().parse_args()

    project_name = args.project
    drawing_name = args.drawing
    drawio_output = args.drawio
    firewall_output = args.firewall

    eprint.set_debug(True)

    eprint.eprint(f"[INFO] Project         : {project_name}")
    eprint.eprint(f"[INFO] Drawing         : {drawing_name}")
    eprint.eprint(f"[INFO] Drawio_output   : {drawio_output}")
    eprint.eprint(f"[INFO] Firewall_output : {firewall_output}")

    db_file_name = project_name + ".db"
    systems_file_name = project_name + ".vd"
    drawing_file_name = drawing_name + ".drawio"

    try:
        db_conn = opendb(db_file_name)
        # Read the systems file
        loadsystems(systems_file_name, drawing_name, db_conn)
        # Read the drawio.file
        drawing_content = read_drawio(drawing_file_name)
        # Read obj data from db
        db_obj_data = getobj(db_conn)
        # Swrite script to generate Draw.io
        write_script(drawing_name, drawing_file_name, db_obj_data, drawing_content)
        
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
