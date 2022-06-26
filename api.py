from asyncio import create_task
import logging
from time import sleep
from flask import Flask, jsonify, request
from flask_json_schema import JsonSchema, JsonValidationError
import json


sleep (240)
log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging. StreamHandler
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.auth import PlainTextAuthProvider

from cassandra.query import dict_factory

app = Flask(__name__)

def cassandra_conn():
    auth_provider = PlainTextAuthProvider('cassandra','cassandra')
    cluster = Cluster(['cassandra'], auth_provider=auth_provider)
    session = cluster.connect()
    return session, cluster

def CreateTables():
    KEYSPACE = "Pacientes"
    log.info("creating keyspace...")
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS %s
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
        """ % KEYSPACE)

    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)

    log.info("creating table...")
    session.execute("""
        CREATE TABLE IF NOT EXISTS paciente (
            id int,
            nombre text,
            apellido text,
            rut text,
            email text,
            fecha_nacimiento text,
            PRIMARY KEY (id)
        )
        """)

    KEYSPACE = "Recetas"
    log.info("creating keyspace...")
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS %s
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '3' }
        """ % KEYSPACE)
    
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)

    log.info("creating table...")
    session.execute("""
        CREATE TABLE IF NOT EXISTS receta (
            id int,
            paciente_id int,
            fecha_nacimiento text,
            comentario text,
            farmacos text,
            doctor text,
            PRIMARY KEY (id)
        )
        """)

def Insert(session):
    query = SimpleStatement("""
        INSERT INTO paciente ("id", "nombre", "apellido", "rut", "email", "fecha_nacimiento")
        VALUES (%(id)s, %(nombre)s, %(apellido)s, %(rut)s, %(email)s, , %(fecha)s)
        """, consistency_level=ConsistencyLevel.ONE)

    prepared = session.prepare("""
        INSERT INTO paciente ("id", "nombre", "apellido", "rut", "email", "fecha_nacimiento")
        VALUES (?, ?, ?, ?, ?, ?)
        """)

    for i in range(10):
        log.info("inserting row %d" % i)
        session.execute(query, dict(id="%d" % i, nombre='a', apellido='b', rut="", email="" ,fecha=""))
        session.execute(prepared, ("%d" % i, 'b', 'b','b','b','b'))

def Eliminar(session):
    session.execute("DROP KEYSPACE " + KEYSPACE)

def main():
    session, cluster = cassandra_conn()
    CreateTables(session)
    KEYSPACE = "pacientes"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    Insert(session)

    future = session.execute_async("SELECT * FROM paciente")
    log.info("id\tnombre\tapellido\trut\temail\tfecha_nacimiento")
    log.info("---\t----\t----\t----\t----\t----")

    try:
        rows = future.result()
    except Exception:
        log.exception("Error reading rows:")
        return

    for row in rows:
        log.info('\t'.join(row))

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/create', methods=['POST'])
def get_body():
    data = request.get_json()
    log.info(data)
    new = {"nombre": f"{data['nombre']}",
           "apellido": f"{data['apellido']}",
            "rut": f"{data['rut']}",
            "email": f"{data['email']}",
            "fecha_nacimiento": f"{data['fecha_nacimiento']}",
            "comentario": f"{data['comentario']}",
            "farmacos": f"{data['farmacos']}",
            "doctor": f"{data['doctor']}"
           }
    
    print(new)

    return (new)



if __name__ == '__main__':
    main()
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)