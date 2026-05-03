# VeeamDesigner
Create Veeam Design Diagram &amp; Firewall configurations (POC)

## Documentation

See [walkthrough.md](walkthrough.md) for the full guide.

## Third-party components

This project relies on the following third-party tools and libraries.

### Python libraries

| Library | Purpose | Install |
| :-- | :-- | :-- |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing | `pip install beautifulsoup4` |
| [N2G](https://github.com/dmulyalin/N2G) | Draw.io diagram generation | `pip install n2g` |
| [Flask](https://flask.palletsprojects.com/) | Web server for Ports Explorer | `pip install flask` |

### Frontend libraries

| Library | Version | Purpose |
| :-- | :-- | :-- |
| [HTMX](https://htmx.org) | 1.9.12 | Dynamic partial page updates in Ports Explorer (loaded via CDN) |
| [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) | — | Monospace font used in Ports Explorer UI (loaded via Google Fonts) |
| [Syne](https://fonts.google.com/specimen/Syne) | — | Sans-serif font used in Ports Explorer UI (loaded via Google Fonts) |

### Tools

| Tool | Purpose |
| :-- | :-- |
| [DB Browser for SQLite](https://sqlitebrowser.org) | Inspect and manage SQLite databases |
| [Draw.io](https://app.diagrams.net) | Open and arrange generated `.drawio` diagrams |

### Reference projects

| Project | Purpose |
| :-- | :-- |
| [MagicPorts](https://magicports.veeambp.com/) | Inspiration for this project |
| [Ports App Backend](https://github.com/shapedthought/ports_server) | Source of the original `allports_updated.db` database schema |