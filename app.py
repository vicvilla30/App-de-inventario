from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import pandas as pd
import io

app = Flask(__name__)

# ---------- BASE DE DATOS ----------
def init_db():
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
            nombre TEXT,
            descripcion TEXT,
            categoria TEXT,
            cantidad INTEGER,
            precio_unitario REAL,
            ubicacion TEXT,
            proveedor TEXT
        )
    """)
    conn.commit()
    conn.close()

# ---------- FUNCIONES ----------
def get_products(busqueda=""):
    conn = sqlite3.connect("inventario.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if busqueda:
        cursor.execute("SELECT * FROM productos WHERE nombre LIKE ?", ('%' + busqueda + '%',))
    else:
        cursor.execute("SELECT * FROM productos")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_product(id):
    conn = sqlite3.connect("inventario.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (id,))
    product = cursor.fetchone()
    conn.close()
    return product

def add_product(data):
    with sqlite3.connect("inventario.db", timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO productos 
            (codigo, nombre, descripcion, categoria, cantidad, precio_unitario, ubicacion, proveedor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()

def update_product(id, data):
    with sqlite3.connect("inventario.db", timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE productos SET
            codigo=?, nombre=?, descripcion=?, categoria=?, cantidad=?, precio_unitario=?, ubicacion=?, proveedor=?
            WHERE id=?
        """, data + (id,))
        conn.commit()

def delete_product(id):
    with sqlite3.connect("inventario.db", timeout=10) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM productos WHERE id=?", (id,))
        conn.commit()

# ---------- RUTAS ----------
@app.route("/", methods=["GET", "POST"])
def index():
    busqueda = ""
    categoria_seleccionada = "Todas"

    if request.method == "POST":
        busqueda = request.form.get("busqueda", "").strip()
        categoria_seleccionada = request.form.get("categoria", "Todas")

    conn = sqlite3.connect("inventario.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM productos WHERE 1=1"
    params = []

    if busqueda:
        query += " AND nombre LIKE ?"
        params.append('%' + busqueda + '%')

    if categoria_seleccionada != "Todas":
        query += " AND categoria = ?"
        params.append(categoria_seleccionada)

    cursor.execute(query, params)
    productos = cursor.fetchall()
    conn.close()

    # Obtener lista de categorías únicas para el select
    categorias = [row["categoria"] for row in get_products()]
    categorias = sorted(list(set(categorias)))

    valor_total = sum(p["cantidad"] * p["precio_unitario"] for p in productos)
    return render_template("index.html", 
                           productos=productos, 
                           valor_total=valor_total,
                           busqueda=busqueda,
                           categorias=categorias,
                           categoria_seleccionada=categoria_seleccionada)

@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "POST":
        data = (
            request.form["codigo"],
            request.form["nombre"],
            request.form["descripcion"],
            request.form["categoria"],
            int(request.form["cantidad"]),
            float(request.form["precio"]),
            request.form["ubicacion"],
            request.form["proveedor"]
        )
        add_product(data)
        return redirect(url_for("index"))
    return render_template("agregar.html")

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    product = get_product(id)
    if not product:
        return "Producto no encontrado", 404
    if request.method == "POST":
        data = (
            request.form["codigo"],
            request.form["nombre"],
            request.form["descripcion"],
            request.form["categoria"],
            int(request.form["cantidad"]),
            float(request.form["precio"]),
            request.form["ubicacion"],
            request.form["proveedor"]
        )
        update_product(id, data)
        return redirect(url_for("index"))
    return render_template("editar.html", product=product)

@app.route("/eliminar/<int:id>", methods=["GET", "POST"])
def eliminar(id):
    product = get_product(id)
    if not product:
        return "Producto no encontrado", 404
    if request.method == "POST":
        delete_product(id)
        return redirect(url_for("index"))
    return render_template("eliminar.html", product=product)

# ---------- EXPORTACIÓN ----------
@app.route("/exportar/csv")
def exportar_csv():
    conn = sqlite3.connect("inventario.db")
    df = pd.read_sql_query("SELECT * FROM productos", conn)
    conn.close()
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, sep=';')
    buffer.seek(0)
    return send_file(
        io.BytesIO(buffer.getvalue().encode('utf-8')),
        mimetype="text/csv",
        as_attachment=True,
        download_name="inventario.csv"
    )

@app.route("/exportar/excel")
def exportar_excel():
    conn = sqlite3.connect("inventario.db")
    df = pd.read_sql_query("SELECT * FROM productos", conn)
    conn.close()
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="inventario.xlsx"
    )

# ---------- INICIAR APP ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)


# ---------- INICIAR APP ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

