# Project file format (.vd)

A project file (`.vd`) is a plain text file that defines the systems involved in a design and their roles.

## Example

```
drawings;name;ip;role;mainrole        
all;VBRBACKUPSERVER01;192.168.207.100;VBRBACKUPSERVER;1        
all;VBRBACKUPSERVER01;;VBRCONSOLE;0        
all;VBRREPOWIN01;192.168.204.100;VBRPOWERNFS;1        
all;VBRREPOWIN01;;VBRBACKUPREPOSITORYWINDOWS;0        
all;VBRREPOWIN01;;VBRBACKUPREPOSITORY;0        
all;VBRREPOWIN01;;VBRMOUNTSERVER;0
```

## Field reference

| **Field** | **Description** |
| :-: | :-: |
| `drawings` | Drawing name(s) the system belongs to. Multiple names separated by commas. |
| `name` | System name. |
| `ip` | IP address. Defined only for the primary role; ignored for secondary roles. |
| `role` | Role the system plays. Relationships are resolved via the database. |
| `mainrole` | `1` = primary role, `0` = secondary role. |

## Notes

- Lines starting with `#` are comments, and are ignored by the parser.

- A system can appear multiple times, once per role.

- Drawing names must be unique and must not be substrings of each other, as the parser uses simple text matching.

## Example breakdown

`VBRBACKUPSERVER01` has two roles: primary `VBRBACKUPSERVER` and secondary `VBRCONSOLE`.

`VBRREPOWIN01` has one primary role (`VBRPOWERNFS`) and three secondary roles (`VBRBACKUPREPOSITORYWINDOWS`, `VBRBACKUPREPOSITORY`, `VBRMOUNTSERVER`).

All systems in this example belong to a drawing named `all`.

