## Introduction

This project was inspired by the [MagicPorts website](https://magicports.veeambp.com/), which provides a visual representation of the TCP/IP ports used by Veeam products.

After seeing it, I thought it would be useful to have a tool that generates:

1. **Draw.io schematics** of a Veeam infrastructure, including TCP/IP port information.
2. **Firewall Rule Lookalike** of a Veeam infrastructure, including TCP/IP port information.

To get started, I explored the [Ports App Backend Project](https://github.com/shapedthought/ports_server) on GitHub.

Inside, I found a SQLite database (`allports_updated.db`) that appears to contain the same information available on the official Veeam documentation website.

However, I noticed some strange characters in the data, a common issue I've encountered before when scraping HTML sources.

For this reason, I decided to rebuild the database from scratch (while keeping the same schema), allowing me to compare results and double-check data accuracy.

## Scraping

To recreate the database:

1. Save the official Veeam ports documentation page in HTML format.

2. Run the Python script `extract_ports.py` to parse the HTML and convert the data into CSV:

   ```
   python extract_ports.py PortsVBR.html VBR > VBR.csv
   ```
   This parses the HTML, adds the `VBR` product code, and saves the output to `VBR.csv`.
   
3. Merge all CSV in a single file named `all_ports.csv`, leaving the first row, that contain the fields name, only at the begining of the file.

4. Import the CSV into a new SQLite database (`scraped_db.db`), in a table named `all_ports`: This preserve the same schema as the original MagicPorts database. To work with SQLite databases, I use [DB Browser for SQLite](https://sqlitebrowser.org), which makes creating a table from a CSV very straightforward.

## Initiatilizing the database

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

The idea was to introduce the concept of **system roles**, making the database more normalized and easier to query.

### Port normalization

The `original_port` field contains port information in various formats found in the Veeam documentation. The `ports` field is populated with a normalized version of this data, handling cases such as:

- If no digits found — descriptive string, return as-is.
- Replace 'or' with comma.
- Replace N+ patterns with 'N to N+1000' ranges.
- Normalize dash ranges: N-N → N to N.
- Parentheses: discard if starts with 'for'; keep if purely digits;
   extract first number if digits present; discard otherwise.
- Normalize whitespace.
- Normalize commas (ensure single space after comma).
- Split by comma or space into tokens.
- Merge tokens around 'to' into ranges; discard non-numeric tokens.
- Join with ', ' and strip trailing comma/whitespace.

### Role mappings

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

All this processing, and the creation of required tables for the rest of the project, are handled by `init_db.py`. Run it passing the project name:

```
python init_db.py -p scraped_db
```

This will recreate the tables in `scraped_db.db` and populate `ports_definitions` from `all_ports`.

## Ports Explorer

To explore the ports definitions, i've created PortsExplorer.
This is a Flask/HTMX projects, that you launch with

```
python portsexplorer.py -p scraped_db
```

This create an instance of a webserver 

```
* Serving Flask app 'portsexplorer'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
```

Running an app, that read ports definition from the scraped_db.db database.

Connecting using a browser to the URL displayed, you can click on source and target roles, to display the port relationship from and to the selected roles, and clicking on one relationship you can see the desctiption of the relationship.

## Project file format

A project file (`.vd`) is a plain text file that defines the systems involved in a design and their roles.

### Example

```
# drawings;name;ip;role;mainrole
all;VBRBACKUPSERVER01;192.168.207.100;VBRBACKUPSERVER;1
all;VBRBACKUPSERVER01;;VBRCONSOLE;0
all;VBRREPOWIN01;192.168.204.100;VBRPOWERNFS;1
all;VBRREPOWIN01;;VBRBACKUPREPOSITORYWINDOWS;0
all;VBRREPOWIN01;;VBRBACKUPREPOSITORY;0
all;VBRREPOWIN01;;VBRMOUNTSERVER;0
```

### Field reference

| **Field** | **Description** |
| :-- | :-- |
| `drawings` | Drawing name(s) the system belongs to. Multiple names separated by commas. |
| `name` | System name. |
| `ip` | IP address. Defined only for the primary role; ignored for secondary roles. |
| `role` | Role the system plays. Relationships are resolved via the database. |
| `mainrole` | `1` = primary role, `0` = secondary role. |

### Notes

- Lines starting with `#` are comments and are ignored by the parser.
- A system can appear multiple times, once per role.
- Drawing names must be unique and must not be substrings of each other, as the parser uses simple text matching.

### Example breakdown

`VBRBACKUPSERVER01` has two roles: primary `VBRBACKUPSERVER` and secondary `VBRCONSOLE`.

`VBRREPOWIN01` has one primary role (`VBRPOWERNFS`) and three secondary roles (`VBRBACKUPREPOSITORYWINDOWS`, `VBRBACKUPREPOSITORY`, `VBRMOUNTSERVER`).

All systems in this example belong to a drawing named `all`.
