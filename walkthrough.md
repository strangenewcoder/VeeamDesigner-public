## Introduction

This project was inspired by the [MagicPorts website](https://magicports.veeambp.com/), which provides a representation of the TCP/IP ports used by Veeam products.

From this, I set out to build a tool that can generate:

1. **Draw.io schematics** of a Veeam infrastructure, including TCP/IP port information.
2. **Firewall rule representations** of a Veeam infrastructure, including TCP/IP port information.

## How it works

**VeeamDesigner** operates in two phases:

- A **one-time setup phase** that builds and normalizes a local database of Veeam port information from the official documentation.  
- A **per-project generation phase** that produces Draw.io diagrams and firewall rule outputs from a user-defined infrastructure description.  

To support this, a set of utility scripts was created and is provided under the `utility/` directory.

## Data source and initial exploration

I initially explored the [Ports App Backend Project](https://github.com/shapedthought/ports_server), which includes a SQLite database (`allports_updated.db`) that appears to mirror information from the official Veeam documentation.

During analysis, I noticed some inconsistencies and encoding artifacts (e.g., strange characters), which are common when extracting structured data from HTML sources.

To ensure consistency and correctness, I decided to rebuild the database from the original documentation while preserving the same schema.

## Reproducibility

Most of the tools required to run and explore this project are already included in the repository.
As a result, **rebuilding steps (database extraction, preprocessing, and intermediate generation) are optional** and provided mainly for transparency and reproducibility.

The full pipeline is documented so it can be reproduced end-to-end if needed.

In a few cases, some original inputs or intermediate files may not be fully redistributable due to external source or licensing constraints. Where this occurs, equivalent generation steps are provided instead.


## Environment creation

Get the repository from GitHub and save it in a new folder.
Open a new command prompt and go to the **VeeamDesigner** root directory.

Create a Python virtual environment (optional but recommended):

```
python -m venv venv
call venv\scripts\activate.bat
```

Install the required modules:

```
pip install beautifulsoup4 flask n2g
```

Copy and customize, if needed, the sample files before first use:

```
copy env.sample env.cmd
copy utility\init_db\role_mappings_sample.py utility\init_db\role_mappings.py
```

### Sample env.cmd

```batch
set PROJECTDIR=c:\projects\veeamdesigner
call %PROJECTDIR%\venv\scripts\activate.bat
set PATH=%PATH%;C:\Program Files\Python314\scripts;
set PYTHONPATH=%PROJECTDIR%\modules
set STYLES=%PROJECTDIR%\styles
```

Before running any command in a new shell, run the environment setup script from the root directory of **VeeamDesigner**.

```
call env.cmd
```

`env.cmd` activates the virtual environment and sets the required environment variables.

## Scraping

To recreate the database:

1. Navigate to the extract ports info utility directory:

   ```
   cd %PROJECTDIR%\utility\extract_ports
   ```

2. Save the official Veeam ports documentation page in HTML format in this folder.

3. Run the Python script `extract_ports.py` to parse the HTML and convert the data into CSV:

   ```
   python extract_ports.py -i PortsAVH7_7.html -p AVH > AVH.csv
   python extract_ports.py -i PortsVB365_8.html -p VB365 > VB365.csv
   python extract_ports.py -i PortsVBEM.html -p VBEM > VBEM.csv
   python extract_ports.py -i PortsVBR.html -p VBR > VBR.csv
   ```

   These parses the HTML, adds the product code, and saves the output to corresponding CSV files.

4. Merge all CSV in a single file named `all_ports.csv`, keeping a header row only at the beginning of the file.

   To do this, I used a text editor — creating a dedicated merge tool seemed overkill.

5. Import the CSV into a new SQLite database (`veeamdesigner.db`), in a table named `all_ports`. This preserves the same schema as the original MagicPorts database.

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

- `from_role` — normalized role code for the source service.
- `to_role` — normalized role code for the target service.
- `ports` — port information in a standardized format.

Now we have to populate these fields:

### Role mappings

The concept is very simple: Every system in a Veeam infrastructure implements one or more roles, so the idea is to "map" one or more sourceservice (or targetservice) to a from_role (or to_role).

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

The current mappings cover some common Veeam components, but the database contains many more service descriptions that are not yet mapped. It is expected and encouraged to explore the unmapped entries and extend `role_mappings.py` accordingly — the more complete the mappings, the more accurate the generated diagrams and firewall rules will be.

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

All this processing, and the creation of required tables for the rest of the project, are handled by `init_db.py`. 

Navigate to the database initialization directory:

```
cd %PROJECTDIR%\utility\init_db
```

Run it, passing the database filename:

```
python init_db.py -f veeamdesigner.db
```

NB: The `veeamdesigner.db` was provided copying the file from `extract_ports` directory.

This will recreate the tables needed in `veeamdesigner.db` and populate `ports_definitions` from `all_ports`.

## Ports Explorer

To explore the ports definitions, I created PortsExplorer, a Flask/HTMX project.

Navigate to the `portsexplorer` directory:

```
cd %PROJECTDIR%\portsexplorer
```

NB: The `veeamdesigner.db` was provided copying the file from `init_db` directory.

Launch it with:

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
─────────── Prepare the reference database (once) ──────────────

              [Veeam docs HTML]
                     │
                     ▼
              extract_ports.py
                     │
                     ▼
               all_ports.csv
                     │
                     ▼
            DB Browser for SQLite
                     │
                     ▼
              veeamdesigner.db
                     │
                     ▼
                init_db.py
       (recreates tables in same db)
                     │
                     ▼
              veeamdesigner.db
  (+ ports_definitions, systems, mappings)

```

```
─────────── Define style files (once) ──────────────

              create style files 


```

```
────────────── Project setup ───────────────────

              veeamdesigner.db
                     │
                     │ (rename/copy)
                     │
                     ▼
                <project>.db ────────────────┐
                                             │
                <project>.vd ────────────────┤
            (system definitions)             │
                                             ▼
                                      veeamdesigner.py
                                             │  
                                ┌────────────┴────────────┐
                                │           (or)          │
                               -o                        -f
                                │                         │
                                ▼                         ▼
                          <drawing>.py              firewall rules
                                │                      (stdout)
                                ▼
                        <drawing>.drawio
                              │    ▲
                  (positions  │    │ preserved)
                              ▼    │
                         Draw.io editor
```

Now, having the db file with the port relationship between the system roles, is only the beginning.

The first thing I need to define is the list of systems in the project involved in a design.

### Project file format

A project file (`.vd`) is a plain text file that defines the systems involved in a design and their roles.

#### Example

```
# drawings;name;ip;role;mainrole
site_a;VBRBACKUPSERVER01;192.168.207.100;VBRBACKUPSERVER;1
site_a;VBRBACKUPSERVER01;;VBRCONSOLE;0
site_a;VBRREPOWIN01;192.168.204.100;VBRPOWERNFS;1
site_a;VBRREPOWIN01;;VBRBACKUPREPOSITORYWINDOWS;0
site_a;VBRREPOWIN01;;VBRBACKUPREPOSITORY;0
site_a;VBRREPOWIN01;;VBRMOUNTSERVER;0
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

All systems in this example belong to a drawing named `site_a`.

---

#### Step 1 — Prepare the reference database

The reference database (`veeamdesigner.db`) contains the Veeam port and role relationship data and is built once, then reused across all projects.

If you already have a valid `veeamdesigner.db`, skip ahead to Step 2.

To rebuild it from scratch, follow the **Scraping** and **Initializing the database** sections above.

---

#### Step 2 — Define style files

Each primary role needs a corresponding style file in the `styles/` folder. The filename must match the role identifier exactly (e.g. `VBRBACKUPSERVER.txt`). In fact the only need for a primary role is to choose the style for a system.

A style file contains a single line: the Draw.io style string for that component type. Example:

```
outlineConnect=0;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;shape=mxgraph.veeam.2d.server;fillColor=#2E73B8;gradientColor=none;
```

The style files distributed are boilerplate, but you can get a style string by placing a shape in Draw.io, right-clicking it, and selecting **Edit Style**.
If you want to create more appropriate styles, create a `cust_styles` folders and modify `env.cmd` to point to this folder.

If a style file is missing for a role, the generated script will not assign a style for that system.

I've also created a utility to verify that all roles have a matching style file:

Run the style checker, passing the database filename:

```
cd %PROJECTDIR%\check_styles
check_styles.py -f <DBFILENAME>
```

---

#### Step 3 — Create a new project

Each project lives in its own subdirectory under `projects/`. This keeps all project files together and makes it easy to manage multiple independent projects side by side.

> **Note:** A `sample/` directory is provided at the root of the repository. It contains a pre-built reference project (`.db`, `.vd`, and `.drawio` files) that you can use to explore and test VeeamDesigner without touching your own work. Do not use `sample/` as your working project folder — treat it as scratch.

Open a new command prompt, and go to the veeamdesigner root directory.

Create the project folder (named **myproject** in this example) and copy the reference database into it:

```
mkdir samples\myproject
copy utility\init_db\veeamdesigner.db samples\myproject\myproject.db
```

Create the project file `samples\myproject\myproject.vd`. This is a plain text file that lists all the systems involved in the project and their roles. See the **Project file format** section for the full specification.

The overall folder layout looks like this:

```
veeamdesigner/                         ← PROJECTDIR
├── veeamdesigner.py
├── env.cmd                            ← environment setup script
├── venv/                              ← Python virtual environment
├── modules/                           ← PYTHONPATH
│   └── eprint.py
├── styles/                            ← STYLES, shared across all projects
│   ├── VBRBACKUPSERVER.txt
│   ├── VBRBACKUPREPOSITORY.txt
│   └── ...
├── sample/                            ← read-only reference project (provided)
│   ├── sample.db
│   ├── sample.vd
│   ├── site_a.drawio
│   └── ...
└── projects/                          ← your working projects go here
    └── anotherproject/
        ├── anotherproject.db
        ├── anotherproject.vd
        └── ...
```

---

#### Step 4 — Generate a drawing script

Run `veeamdesigner.py` from inside the project folder, passing the project name and a drawing name:

```
cd %PROJECTDIR%\samples\myproject
python %PROJECTDIR%\veeamdesigner.py -p myproject -w site_a
```

This produces a Python script `site_a.py` in the current folder. The script, when executed, generates the Draw.io diagram `site_a.drawio`.

What happens internally:

1. The systems matching the drawing name `site_a` are loaded from `myproject.vd` into the `systems` table.
2. If `site_a.drawio` already exists, node positions are read from it.
3. For each system, an `add_node` call is written to the script, using the existing position if available, or an auto-calculated position if not.
4. For each role relationship found in `ports_definitions`, an `add_link` call is written with the relevant ports as labels.

---

#### Step 5 — Run the drawing script

```
python site_a.py
```

This executes the generated script and writes `site_a.drawio` in the same folder. Open it in Draw.io (desktop or web).

On the first run, nodes are placed automatically: the first node starts at `x=300, y=300`, and each subsequent node is offset by 100 in both axes. The layout will be a diagonal staircase — this is intentional. You will rearrange it manually.

---

#### Step 6 — Arrange the diagram in Draw.io

Open `site_a.drawio` in Draw.io and move the nodes to where you want them. Save the file.

The next time you run Step 4, `veeamdesigner.py` will read the updated positions from `site_a.drawio` and use them in the regenerated script. Your layout is preserved across iterations.

This means the typical iteration cycle is:

```
edit myproject.vd
      │
      ▼
python %PROJECTDIR%\veeamdesigner.py -p myproject -w site_a
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

#### Step 7 — Multiple drawings per project

A project can have multiple drawings, each showing a different subset of systems or a different view of the infrastructure. The `drawings` field in the `.vd` file controls which systems appear in each drawing.

Example: a system that belongs to both `site_a` and `site_b`:

```
#always start with a comment line
#if line begin with # is a comment
#drawings;name;ip;role;mainrole
site_a,site_b;VBRBACKUPSERVER01;192.168.207.100;VBRBACKUPSERVER;1
site_a;VBRBACKUPSERVER01;;VBRCONSOLE;0
site_a;VBRREPOWIN01;192.168.204.100;VBRPOWERNFS;1
site_a;VBRREPOWIN01;;VBRBACKUPREPOSITORYWINDOWS;0
site_a;VBRREPOWIN01;;VBRBACKUPREPOSITORY;0
site_a;VBRREPOWIN01;;VBRMOUNTSERVER;0
site_b;VBRREPOLINUX01;192.168.207.101;VBRBACKUPREPOSITORYLINUX;1
```

Generate each drawing independently, from inside the project folder:

```
cd %PROJECTDIR%\samples\myproject
python %PROJECTDIR%\veeamdesigner.py -p myproject -w site_a
python %PROJECTDIR%\veeamdesigner.py -p myproject -w site_b

python site_a.py
python site_b.py
```

Each drawing has its own `.py` script and its own `.drawio` file. Positions saved in `site_a.drawio` do not affect `site_b.drawio`.

> **Note:** drawing names must not be substrings of each other. For example, do not use both `site` and `site_a` — `site` would also match `site_a` during filtering.

#### Step 8 - Look at drawings

A not obvious thing, that you can see only looking at a system positioning over it, is that a tooltip appear, with the IP Address and the roles of the system.
