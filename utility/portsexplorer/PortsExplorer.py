"""
PortsExplorer — Flask/HTMX tool for exploring the ports_definitions table.
"""

import argparse
import os
import sqlite3

from flask import Flask, render_template, request, g

app = Flask(__name__)

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def get_db():
    """Open the db."""

    if "db" not in g:
        g.db = sqlite3.connect(app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    """Close the db."""

    if e:
        print(f"Teardown due to error: {e}")
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """/ app route."""

    db = get_db()
    roles = db.execute(
        "SELECT DISTINCT from_role FROM ports_definitions WHERE from_role != '' ORDER BY from_role"
    ).fetchall()
    return render_template("index.html", roles=[r["from_role"] for r in roles])


@app.route("/to_roles")
def to_roles():
    """/to_roles route."""

    from_role = request.args.get("from_role", "")
    db = get_db()
    rows = db.execute(
        """
        SELECT DISTINCT to_role FROM ports_definitions
        WHERE from_role = ? AND to_role != ''
        ORDER BY to_role
        """,
        (from_role,),
    ).fetchall()
    return render_template(
        "partials/to_roles.html",
        to_roles=[r["to_role"] for r in rows],
        from_role=from_role,
    )


@app.route("/ports")
def ports():
    """/ports route."""

    from_role = request.args.get("from_role", "")
    to_role = request.args.get("to_role", "")
    db = get_db()

    # Direct: from_role → to_role
    direct = db.execute(
        """
        SELECT DISTINCT ports FROM ports_definitions
        WHERE from_role = ? AND to_role = ? AND ports != ''
        ORDER BY ports
        """,
        (from_role, to_role),
    ).fetchall()

    # Reverse: to_role → from_role
    reverse = db.execute(
        """
        SELECT DISTINCT ports FROM ports_definitions
        WHERE from_role = ? AND to_role = ? AND ports != ''
        ORDER BY ports
        """,
        (to_role, from_role),
    ).fetchall()

    port_entries = []
    for r in direct:
        port_entries.append({"ports": r["ports"], "direction": "direct"})
    for r in reverse:
        port_entries.append({"ports": r["ports"], "direction": "reverse"})

    return render_template(
        "partials/ports.html",
        port_entries=port_entries,
        from_role=from_role,
        to_role=to_role,
    )


@app.route("/descriptions")
def descriptions():
    """/descriptions route."""

    from_role = request.args.get("from_role", "")
    to_role = request.args.get("to_role", "")
    selected_ports = request.args.get("ports", "")
    direction = request.args.get("direction", "direct")
    db = get_db()

    if direction == "direct":
        q_from, q_to = from_role, to_role
    else:
        q_from, q_to = to_role, from_role

    rows = db.execute(
        """
        SELECT product, sourceservice, targetservice, protocol,
               original_port, description, from_role, to_role, ports
        FROM ports_definitions
        WHERE from_role = ? AND to_role = ? AND ports = ?
        ORDER BY product, sourceservice
        """,
        (q_from, q_to, selected_ports),
    ).fetchall()

    return render_template(
        "partials/descriptions.html",
        rows=rows,
        from_role=from_role,
        to_role=to_role,
        ports=selected_ports,
        direction=direction,
    )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main():
    """
    Main function.
    """

    parser = argparse.ArgumentParser(description="Ports explorer web UI")
    parser.add_argument(
        "-p",
        "--project",
        required=True,
        help="Project name — database file is <project>.db",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000, type=int)
    args = parser.parse_args()

    app.config["DB_PATH"] = f"{args.project}.db"
    if not os.path.exists(app.config["DB_PATH"]):
        print(f"[ERROR] Database not found: {app.config["DB_PATH"]}")
        raise SystemExit(1)

    app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
