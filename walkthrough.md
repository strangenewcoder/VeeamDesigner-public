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

3. Import the CSV into a new SQLite database (`allports_veeamdesigner.db`), preserving the same schema as the original MagicPorts database. To work with SQLite databases, I use [DB Browser for SQLite](https://sqlitebrowser.org), which makes creating a table from a CSV very straightforward.

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
