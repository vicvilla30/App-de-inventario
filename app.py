from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import pandas as pd

app = Flask(__name__)

# -------------------
# Funciones de DB
# -------------------

def get_data():
    conn = sqlite3.connect("inventario.db")
    df = pd.read_sql_query("SELECT * FROM productos", conn)
    conn.close()
    return df

def add_product(data):
    conn = sqlite3.connect("inventario.db", timeout=10)  # espera si está bloqueada
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO productos 
        (codigo, nombre, descripcion, categoria, cantidad, precio_unitario, ubicacion, proveedor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()  # 🔹 Muy importante

def get_product(id):
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos WHERE id = ?", (id,))
    product = cursor.fetchone()  # Tupla o None
    conn.close()
    return product

def update_product(id, data):
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE productos
        SET codigo=?, nombre=?, descripcion=?, categoria=?, cantidad=?, precio_unitario=?, ubicacion=?, proveedor=?
        WHERE id=?
    """, (*data, id))
    conn.commit()
    conn.close()

def delete_product(id):
    conn = sqlite3.connect("inventario.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id=?", (id,))
    conn.commit()
    conn.close()

# -------------------
# Rutas Flask
# -------------------

@app.route("/", methods=["GET", "POST"])
def index():
    df = get_data()
    categorias = df["categoria"].dropna().unique().tolist()
    categoria_seleccionada = request.form.get("categoria", "Todas")
    busqueda = request.form.get("busqueda", "").strip().lower()

    if categoria_seleccionada != "Todas":
        df = df[df["categoria"] == categoria_seleccionada]
    if busqueda:
        df = df[
            df["nombre"].str.lower().str.contains(busqueda, na=False) |
            df["codigo"].str.lower().str.contains(busqueda, na=False)
        ]

    df["valor_total"] = df["cantidad"] * df["precio_unitario"]
    valor_total = df["valor_total"].sum()
    productos = df.to_dict(orient="records")

    return render_template(
        "index.html",
        productos=productos,
        categorias=categorias,
        categoria_seleccionada=categoria_seleccionada,
        busqueda=busqueda,
        valor_total=valor_total
    )

@app.route("/agregar", methods=["GET", "POST"])
def agregar():
    if request.method == "POST":
        try:
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
            print("DEBUG agregando:", data)
            add_product(data)
            return redirect(url_for("index"))
        except Exception as e:
            return f"Error al agregar producto: {e}"
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

if __name__ == "__main__":
    app.run(debug=True)
