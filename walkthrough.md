## Introduction

This project was inspired by the [MagicPorts website](https://magicports.veeambp.com/), which provides a representation of the TCP/IP ports used by Veeam products.

After seeing it, I thought it would be useful to have a tool that generates:

1. **Draw.io schematics** of a Veeam infrastructure, including TCP/IP port information.
2. **Firewall Rule Lookalike** of a Veeam infrastructure, including TCP/IP port information.

To get started, I explored the [Ports App Backend Project](https://github.com/shapedthought/ports_server) on GitHub.

Inside, I found a SQLite database (`allports_updated.db`) that appears to contain the same information available on the official Veeam documentation website.

However, I noticed some strange characters in the data, a common issue I've encountered before when scraping HTML sources.

For this reason, I decided to rebuild the database from scratch (while keeping the same schema), allowing me to compare results and double-check data accuracy.

To do this, I created a couple of utility scripts.

## Scraping

To recreate the database:

1. Save the official Veeam ports documentation page in HTML format.

2. Run the Python script `extract_ports.py` to parse the HTML and convert the data into CSV:

   ```
   python extract_ports.py -i PortsVBR.html -p VBR > VBR.csv
   ```
   
   This parses the HTML, adds the `VBR` product code, and saves the output to `VBR.csv`.
   
3. Merge all CSV in a single file named `all_ports.csv`, keeping a header row only at the beginning of the file.

   To do this, I used a text editor — creating a dedicated merge tool seemed overkill.

4. Import the CSV into a new SQLite database (`veeamdesigner.db`), in a table named `all_ports`: This preserves the same schema as the original MagicPorts database.
   
   To work with SQLite databases, I use [DB Browser for SQLite](https://sqlitebrowser.org), which makes creating a table from a CSV very straightforward.

## Initializing the database

While studying the database, I realized that the structure was not very query-friendly.
In particular, the `sourceservice` and `targetservice` columns were more descriptive than relational keys.
To improve this, I created a new table:

```sql
CREATE TABLE ports_definitions (
    id            INTEGER PRIMARY KEY,
    product       TEXT,
    sourceservice TEXT,
    targetservice TEXT,
    protocol      TEXT,
    original_port TEXT,
    description   TEXT,
    from_role     TEXT,
    to_role       TEXT,
    ports         TEXT
);
```

This new table contains the original information, plus three additional columns:

- `from_role` — normalized role code for the source service
- `to_role` — normalized role code for the target service
- `ports` — port information in a standardized format

Now we have to populate these fields:

### Role mappings

The concept is very simple: Every system in a Veeam infrastructure implements one or more roles, so the idea to "map" one or more sourceservice (or targetservice) to a from_role (or to_role).

The mappings from service names to role codes are defined in `role_mappings.py`:

```python
ROLE_MAPPINGS = {
    "Backup server": "VBRBACKUPSERVER",
    "%plug-in%": "VBRBACKUPSERVER",
    "Veeam backup & replication console": "VBRCONSOLE",
    "Backup repository": "VBRBACKUPREPOSITORY",
    "Backup repository or gateway server": "VBRBACKUPREPOSITORY",
    ...
}
```

For example:

- A service containing `"Backup server"` will be mapped to `"VBRBACKUPSERVER"`.
- A service containing `"%plug-in%"` will also be mapped to `"VBRBACKUPSERVER"` (the `%` acts as a wildcard, matching any substring).

The current mappings cover the most common Veeam components, but the database contains many more service descriptions that are not yet mapped. It is expected and encouraged to explore the unmapped entries and extend `role_mappings.py` accordingly — the more complete the mappings, the more accurate the generated diagrams and firewall rules will be.

To find unmapped entries, you can run this query in DB Browser for SQLite:

```sql
SELECT DISTINCT sourceservice FROM ports_definitions WHERE from_role = ''
UNION
SELECT DISTINCT targetservice FROM ports_definitions WHERE to_role = '';
```

### Port normalization

The `original_port` field contains port information in various formats found in the Veeam documentation. The `ports` field is populated with a normalized version of this data, handling cases such as:

- If no digits found — descriptive string, return as-is.
- Replace 'or' with comma.
- Replace N+ patterns with 'N to N+1000' ranges.
- Normalize dash ranges: N-N → N to N.
- Parentheses: discard if starts with 'for'; keep if purely digits; extract first number if digits present; discard otherwise.
- Normalize whitespace.
- Normalize commas: remove spaces before comma, ensure one space after.
- Split by comma or space into tokens.
- Merge tokens around 'to' into ranges; discard non-numeric tokens.
- Join with ', ' and strip trailing comma/whitespace.

All this processing, and the creation of required tables for the rest of the project, are handled by `init_db.py`. Run it passing the project name:

```
python init_db.py -f <DBFILENAME> 
```

This will recreate the tables needed in `<DBFILENAME>` and populate `ports_definitions` from `all_ports`.

## Ports Explorer

To explore the ports definitions, I created PortsExplorer, a Flask/HTMX project. Launch it with:

```
python portsexplorer.py -f veeamdesigner.db
```

This starts a local web server:

```
* Serving Flask app 'portsexplorer'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
```

Connecting to the URL displayed in a browser, you can click on source and target roles to display the port relationships from and to the selected role. Clicking on a relationship shows the description of that connection.

## Workflow

This section describes the end-to-end workflow for using VeeamDesigner, from setting up a new project to iteratively refining a diagram.

### Overview

```
[Veeam docs HTML]
      │
      ▼
extract_ports.py ──► all_ports.csv ──► veeamdesigner.db (all_ports table)
                                              │
                                        init_db.py
                                              │
                                              ▼
                                    ports_definitions table
                                    (role relationships + ports)
                                              │
                          ┌───────────────────┘
                          ▼
                  <project>.db  ◄── veeamdesigner.db
                          │
                  <project>.vd  ──► loadsystems()
                          │
                          ▼
                  VeeamDesigner.py
                  ├── drawio output ──► <drawing>.py ──► <drawing>.drawio
                  └── firewall output ──► firewall rules (stdout)
```

Now, having the db file with the port relationship between the system roles, is only the beginning.

The first thing I need to define is the list of systems in the project involved in a design.

### Project file format

A project file (`.vd`) is a plain text file that defines the systems involved in a design and their roles.

#### Example

```
# drawings;name;ip;role;mainrole
all;VBRBACKUPSERVER01;192.168.207.100;VBRBACKUPSERVER;1
all;VBRBACKUPSERVER01;;VBRCONSOLE;0
all;VBRREPOWIN01;192.168.204.100;VBRPOWERNFS;1
all;VBRREPOWIN01;;VBRBACKUPREPOSITORYWINDOWS;0
all;VBRREPOWIN01;;VBRBACKUPREPOSITORY;0
all;VBRREPOWIN01;;VBRMOUNTSERVER;0
```

#### Field reference

| **Field** | **Description** |
| :-- | :-- |
| `drawings` | Drawing name(s) the system belongs to. Multiple names separated by commas. |
| `name` | System name. |
| `ip` | IP address. Defined only for the primary role; ignored for secondary roles. |
| `role` | Role the system plays. Relationships are resolved via the database. |
| `mainrole` | `1` = primary role, `0` = secondary role. |

#### Notes

- Lines starting with `#` are comments and are ignored by the parser.
- A system can appear multiple times, once per role.
- Drawing names must be unique and must not be substrings of each other, as the parser uses simple text matching.

#### Example breakdown

`VBRBACKUPSERVER01` has two roles: primary `VBRBACKUPSERVER` and secondary `VBRCONSOLE`.

`VBRREPOWIN01` has one primary role (`VBRPOWERNFS`) and three secondary roles (`VBRBACKUPREPOSITORYWINDOWS`, `VBRBACKUPREPOSITORY`, `VBRMOUNTSERVER`).

All systems in this example belong to a drawing named `all`.

---

### Step 1 — Prepare the reference database

The reference database (`veeamdesigner.db`) contains the Veeam port and role relationship data and is built once, then reused across all projects.

If you already have a valid `veeamdesigner.db`, skip ahead to Step 2.

To rebuild it from scratch, follow the **Scraping** and **Initializing the database** sections above.

---

### Step 2 — Create a new project

Each project lives in its own subdirectory under `projects/`. This keeps all project files together and makes it easy to manage multiple independent projects side by side.

Create the project folder and copy the reference database into it:

```
mkdir projects\myproject
copy veeamdesigner.db  projects\myproject\myproject.db
```

Then create the project file `projects\myproject\myproject.vd`. This is a plain text file that lists all the systems involved in the project and their roles. See the **Project file format** section for the full specification.

An create a phython virtual environment (optional but useful)

```
python -m venv venv
call venv\scripts\activate.bat
pip install beautifulsoup4 flask n2g
```

The overall folder layout looks like this:

```
veeamdesigner/                         ← PROJECTDIR
├── VeeamDesigner.py
├── env.cmd                            ← environment setup script
├── venv/                              ← Python virtual environment
├── modules/                           ← PYTHONPATH
│   └── eprint.py
├── styles/                            ← STYLES, shared across all projects
│   ├── VBRBACKUPSERVER.txt
│   ├── VBRBACKUPREPOSITORY.txt
│   └── ...
├── veeamdesigner.db                      ← reference database (do not edit)
└── projects/
    ├── myproject/
    │   ├── myproject.db               ← copy of veeamdesigner.db
    │   ├── myproject.vd               ← system definitions
    │   ├── site_a.py                  ← generated drawing script
    │   ├── site_a.drawio              ← generated diagram (edit positions here)
    │   └── site_b.drawio
    └── anotherproject/
        ├── anotherproject.db
        ├── anotherproject.vd
        └── ...
```

NB: Copy and customize if needed the sample files before first use:

```
copy env_sample.cmd env.cmd
copy modules\role_mappings_sample.py modules\role_mappings.py
```
	
Before running any command in a new shell, source the environment setup script from the root directory of the project:

```
call env.cmd
```

`env.cmd` activates the virtual environment and sets the required environment variables:

```batch
set PROJECTDIR=f:\projects\veeamdesigner
call %PROJECTDIR%\venv\scripts\activate.bat
set PATH=%PATH%C:\Program Files\Python314\scripts;
set PYTHONPATH=%PROJECTDIR%\modules
set STYLES=%PROJECTDIR%\styles
```

---

### Step 3 — Define style files

Each primary role needs a corresponding style file in the `styles/` folder. The filename must match the role identifier exactly (e.g. `VBRBACKUPSERVER.txt`).
In fact the only need for a primary role is to choose the style for a system.

A style file contains a single line: the Draw.io style string for that component type. Example:

```
outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.veeam.2d.server;fillColor=#2E73B8;gradientColor=none;
```

The styles are distributed as bolierplate, but you can get a style string by placing a shape in Draw.io, right-clicking it, and selecting **Edit Style**.

If a style file is missing for a role, the generated script will not assign a style for a system.

I've also created a utility to  verify that all roles have a matching style file

```
check_styles.py -f <DBFILENAME>
```

---

### Step 4 — Generate a drawing script

Run `VeeamDesigner.py` from inside the project folder, passing the project name and a drawing name:

```
cd projects\myproject
python %PROJECTDIR%\VeeamDesigner.py -p myproject -w site_a
```

This produces a Python script `site_a.py` in the current folder. The script, when executed, generates the Draw.io diagram `site_a.drawio`.

What happens internally:

1. The systems matching the drawing name `site_a` are loaded from `myproject.vd` into the `systems` table.
2. If `site_a.drawio` already exists, node positions are read from it.
3. For each system, an `add_node` call is written to the script, using the existing position if available, or an auto-calculated position if not.
4. For each role relationship found in `ports_definitions`, an `add_link` call is written with the relevant ports as labels.

---

### Step 5 — Run the drawing script

```
cd projects\myproject
python site_a.py
```

This executes the generated script and writes `site_a.drawio` in the same folder. Open it in Draw.io (desktop or web).

On the first run, nodes are placed automatically: the first node starts at `x=300, y=300`, and each subsequent node is offset by 100 in both axes. The layout will be a diagonal staircase — this is intentional. You will rearrange it manually.

---

### Step 6 — Arrange the diagram in Draw.io

Open `site_a.drawio` in Draw.io and move the nodes to where you want them. Save the file.

The next time you run Step 4, `VeeamDesigner.py` will read the updated positions from `site_a.drawio` and use them in the regenerated script. Your layout is preserved across iterations.

This means the typical iteration cycle is:

```
edit myproject.vd
      │
      ▼
python %PROJECTDIR%\VeeamDesigner.py -p myproject -w site_a
      │
      ▼
python site_a.py
      │
      ▼
open / arrange in Draw.io  ──► save site_a.drawio
      │
      └──► repeat
```

---

### Step 7 — Multiple drawings per project

A project can have multiple drawings, each showing a different subset of systems or a different view of the infrastructure. The `drawings` field in the `.vd` file controls which systems appear in each drawing.

Example: a system that belongs to both `site_a` and `site_b`:

```
site_a,site_b;VBRBACKUPSERVER01;192.168.207.100;VBRBACKUPSERVER;1
site_a;VBRREPOWIN01;192.168.204.100;VBRPOWERNFS;1
site_b;VBRREPOLINUX01;192.168.205.100;VBRBACKUPREPOSITORYLINUX;1
```

Generate each drawing independently, from inside the project folder:

```
cd projects\myproject
python %PROJECTDIR%\VeeamDesigner.py -p myproject -w site_a
python %PROJECTDIR%\VeeamDesigner.py -p myproject -w site_b
```

Each drawing has its own `.py` script and its own `.drawio` file. Positions saved in `site_a.drawio` do not affect `site_b.drawio`.

> **Note:** drawing names must not be substrings of each other. For example, do not use both `site` and `site_a` — `site` would also match `site_a` during filtering.

