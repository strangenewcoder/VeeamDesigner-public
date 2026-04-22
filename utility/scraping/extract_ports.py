"""
Parse HTML saved from Veeam Web Site.
Getting the info about TCP/IP ports usage of Veeam Products.
This works for VB385 tables.
"""

import re
import sys
from bs4 import BeautifulSoup


def fix_mojibake(text):
    """
    Fix some unintended character encoding.
    """

    replacements = {
        "â€”": "-",  # em dash
        "â€“": "-",  # en dash
        "\u2014": "-",  # em dash (unicode) ← aggiunto
        "\u2013": "-",  # en dash (unicode) ← aggiunto
        "â€˜": "‘",  # left single quotation mark
        "â€™": "’",  # right single quotation mark
        "â€œ": "“",  # left double quotation mark
        "â€": "”",  # right double quotation mark
        "â€¦": "…",  # ellipsis
        "â€¢": "•",  # bullet
        "â€": "†",  # dagger (sometimes misinterpreted quote)
        "â„¢": "™",  # trademark
        "Â©": "©",  # copyright
        "Â®": "®",  # registered
        "Â": "",  # stray encoding artifact (often before currency/quotes)
        "\u00a0": " ",  # non-breaking space
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    return text


def normalize_table_rows(rows):
    """
    Fix some anomaly about tables extracted from HTML page.
    """

    normalized_rows = []
    last_from = ""
    last_to = ""
    last_protocol = ""
    last_desc = ""

    for row in rows:
        # Skip rows that are clearly not data
        if len(row) == 0:
            continue

        # Skip header row if it contains known labels
        header_keywords = {"from", "to", "protocol", "port", "notes"}
        row_lower = [cell.strip().lower() for cell in row]
        if any(h in header_keywords for h in row_lower):
            continue

        # Reconstruct based on length
        if len(row) == 5:
            last_from = row[0].strip()
            last_to = row[1].strip()
            last_protocol = row[2].strip()
            last_desc = row[4].strip()
            normalized_rows.append(row)
        elif len(row) == 4:
            last_to = row[0].strip()
            last_protocol = row[1].strip()
            last_desc = row[3].strip()
            normalized_rows.append([last_from] + row)
        elif len(row) == 3:
            last_protocol = row[0].strip()
            last_desc = row[2].strip()
            normalized_rows.append([last_from, last_to] + row)
        elif len(row) == 2:
            desc = row[1].strip()
            if len(desc) > 10:
                normalized_rows.append([last_from, last_to, last_protocol] + row)
            else:
                normalized_rows.append([last_from, last_to] + row + [last_desc])

    return normalized_rows


def extract_port_tables(html_path):
    """
    Parse HTML file to extract tables with the info desired.
    """

    with open(html_path) as f:
        soup = BeautifulSoup(f, "html.parser")

    results = []

    # Find all tables
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            row = [cell.get_text(separator=" ", strip=True) for cell in cells]
            if row:
                rows.append(row)
        results.append(rows)

    return results


def main():
    """
    Main function.
    """

    if len(sys.argv) != 3:
        print("Usage: python extract_ports input.html productcode")
        sys.exit(1)

    input_html = sys.argv[1]
    product_code = sys.argv[2]

    # Extract tables
    tables = extract_port_tables(input_html)

    # Final flat output list
    final_rows = []

    # Normalize tables
    for table in tables:
        normalized = normalize_table_rows(table)
        for row in normalized:
            final_rows.append([product_code] + row)

    # Print CSV-style output
    print("product;sourceService;targetService;protocol;port;description")
    for row in final_rows:
        # Clean NBSP and and other encoded info from the last column (description)
        cleaned_row = [fix_mojibake(col) for col in row]

        # Remove space before final dot (if any) in description
        if cleaned_row[-1]:
            cleaned_row[-1] = re.sub(r"\s+\.$", ".", cleaned_row[-1])

            # Remove starting and ending double quotes if present
            if cleaned_row[-1].startswith('"') and cleaned_row[-1].endswith('"'):
                cleaned_row[-1] = cleaned_row[-1][1:-1]

        print(";".join(cleaned_row))


if __name__ == "__main__":
    main()
