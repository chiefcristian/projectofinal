import sqlite3
from flask import Flask, jsonify, request
from abc import ABC, abstractmethod

# Configuración inicial
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()

    # Tabla de usuarios
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        meta_calorica INTEGER
                    )''')

    # Tabla de recetas
    cursor.execute('''CREATE TABLE IF NOT EXISTS recetas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT NOT NULL,
                        instrucciones TEXT,
                        calorias INTEGER
                    )''')

    # Tabla de ingredientes
    cursor.execute('''CREATE TABLE IF NOT EXISTS ingredientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre TEXT UNIQUE NOT NULL
                    )''')

    # Relación receta-ingrediente
    cursor.execute('''CREATE TABLE IF NOT EXISTS receta_ingrediente (
                        receta_id INTEGER,
                        ingrediente_id INTEGER,
                        cantidad INTEGER,
                        FOREIGN KEY (receta_id) REFERENCES recetas (id),
                        FOREIGN KEY (ingrediente_id) REFERENCES ingredientes (id)
                    )''')

    # Tabla de planificación semanal
    cursor.execute('''CREATE TABLE IF NOT EXISTS planificacion_semanal (
                        usuario_id INTEGER,
                        dia TEXT,
                        comida TEXT,
                        receta_id INTEGER,
                        FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                        FOREIGN KEY (receta_id) REFERENCES recetas (id)
                    )''')

    # Tabla de registro de ingesta calórica
    cursor.execute('''CREATE TABLE IF NOT EXISTS registro_calorico (
                        usuario_id INTEGER,
                        fecha TEXT,
                        calorias INTEGER,
                        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                    )''')

    conn.commit()
    conn.close()

init_db()

class Entidad(ABC):
    @abstractmethod
    def guardar(self):
        pass

    @abstractmethod
    def eliminar(self):
        pass
class Usuario(Entidad):
    def __init__(self, nombre, email, meta_calorica):
        self.nombre = nombre
        self.email = email
        self.meta_calorica = meta_calorica

    def guardar(self):
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, email, meta_calorica) VALUES (?, ?, ?)",
                       (self.nombre, self.email, self.meta_calorica))
        conn.commit()
        conn.close()

    def actualizar_meta(self, nueva_meta):
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET meta_calorica = ? WHERE email = ?", (nueva_meta, self.email))
        conn.commit()
        conn.close()

class Receta(Entidad):
    def __init__(self, nombre, instrucciones, calorias, ingredientes):
        self.nombre = nombre
        self.instrucciones = instrucciones
        self.calorias = calorias
        self.ingredientes = ingredientes  # Lista de ingredientes y cantidades

    def guardar(self):
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO recetas (nombre, instrucciones, calorias) VALUES (?, ?, ?)",
                       (self.nombre, self.instrucciones, self.calorias))
        receta_id = cursor.lastrowid

        # Guardar ingredientes
        for ingrediente, cantidad in self.ingredientes.items():
            cursor.execute("INSERT OR IGNORE INTO ingredientes (nombre) VALUES (?)", (ingrediente,))
            cursor.execute("SELECT id FROM ingredientes WHERE nombre = ?", (ingrediente,))
            ingrediente_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO receta_ingrediente (receta_id, ingrediente_id, cantidad) VALUES (?, ?, ?)",
                           (receta_id, ingrediente_id, cantidad))

        conn.commit()
        conn.close()
class PlanificacionSemanal(Entidad):
    def __init__(self, usuario_id, dia, comida, receta_id):
        self.usuario_id = usuario_id
        self.dia = dia
        self.comida = comida
        self.receta_id = receta_id

    def guardar(self):
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO planificacion_semanal (usuario_id, dia, comida, receta_id)
                          VALUES (?, ?, ?, ?)''', (self.usuario_id, self.dia, self.comida, self.receta_id))
        conn.commit()
        conn.close()
class RegistroCalorico(Entidad):
    def __init__(self, usuario_id, fecha, calorias):
        self.usuario_id = usuario_id
        self.fecha = fecha
        self.calorias = calorias

    def guardar(self):
        conn = sqlite3.connect("app.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO registro_calorico (usuario_id, fecha, calorias) VALUES (?, ?, ?)",
                       (self.usuario_id, self.fecha, self.calorias))
        conn.commit()
        conn.close()
@app.route("/usuarios", methods=["POST"])
def crear_usuario():
    data = request.json
    usuario = Usuario(data["nombre"], data["email"], data["meta_calorica"])
    usuario.guardar()
    return jsonify({"mensaje": "Usuario creado exitosamente"}), 201


@app.route("/recomendar_recetas", methods=["POST"])
def recomendar_recetas():
    data = request.json
    ingredientes_usuario = set(data["ingredientes"])

    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute('''SELECT r.id, r.nombre, r.instrucciones FROM recetas r
                      JOIN receta_ingrediente ri ON r.id = ri.receta_id
                      JOIN ingredientes i ON ri.ingrediente_id = i.id
                      WHERE i.nombre IN ({seq})'''.format(seq=','.join(['?'] * len(ingredientes_usuario))),
                   tuple(ingredientes_usuario))

    recetas = cursor.fetchall()
    conn.close()
    return jsonify({"recetas": recetas}), 200

@app.route("/lista_compras/<int:usuario_id>", methods=["GET"])
def generar_lista_compras(usuario_id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute('''SELECT i.nombre, SUM(ri.cantidad) as cantidad_total
                      FROM planificacion_semanal ps
                      JOIN receta_ingrediente ri ON ps.receta_id = ri.receta_id
                      JOIN ingredientes i ON ri.ingrediente_id = i.id
                      WHERE ps.usuario_id = ?
                      GROUP BY i.nombre''', (usuario_id,))

    lista_compras = cursor.fetchall()
    conn.close()
    return jsonify({"lista_compras": lista_compras}), 200

if __name__ == "__main__":
    app.run(debug=True)
