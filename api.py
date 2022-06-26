from asyncio import create_task
import logging
from time import sleep
from flask import Flask, jsonify, request
from flask_json_schema import JsonSchema, JsonValidationError
import json


sleep (90)
log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.auth import PlainTextAuthProvider

from cassandra.query import dict_factory

pacientes_counter = 0
recetas_counter = 0

app = Flask(__name__)

def cassandra_conn():
    auth_provider = PlainTextAuthProvider('cassandra','cassandra')
    cluster = Cluster(['cassandra'], auth_provider=auth_provider)
    session = cluster.connect()
    return session, cluster

def CreateTables(session):
    KEYSPACE = "pacientes"
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

    KEYSPACE = "recetas"
    log.info("creating keyspace...")
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS %s
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '3' }
        """ % KEYSPACE)

    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)

    log.info("creating table...")
    session.execute("""
        CREATE TABLE IF NOT EXISTS recetas (
            id int,
            id_paciente int,
            comentario text,
            farmaco text,
            doctor text,
            PRIMARY KEY (id)
        )
        """)

def InsertPaciente(session, data):
    KEYSPACE = "pacientes"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    prepared = session.prepare("""
        INSERT INTO paciente ("id", "nombre", "apellido", "rut", "email", "fecha_nacimiento")
        VALUES (?, ?, ?, ?, ?, ?)
        """)

    session.execute(prepared, (pacientes_counter, '%s' %data['nombre'],'%s'%data['apellido'],'%s' %data['rut'],'%s' %data['email'],'%s'%data['fecha_nacimiento']))
    pacientes_counter = pacientes_counter + 1

def InsertReceta(session, data):
    KEYSPACE = "recetas"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    paciente_id = SelectPaciente(session,data['rut'])
    if paciente_id == None:
        InsertPaciente(session,data)
        paciente_id= pacientes_counter-1
    else:
        prepared = session.prepare("""
            INSERT INTO recetas ("id", "id_paciente", "comentario", "farmaco", "doctor")
            VALUES (?, ?, ?, ?, ?, ?)
            """)

        session.execute(prepared, (recetas_counter, '%s' %paciente_id, '%s','%s'%data['comentario'],'%s' %data['farmaco'],'%s' %data['doctor']))
        recetas_counter = recetas_counter + 1

def SelectPaciente(session, rut):
    KEYSPACE = "pacientes"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    future = session.execute_async("SELECT id FROM paciente WHERE rut=%s" %rut)
    log.info("id\tnombre\tapellido\trut\temail\tfecha_nacimiento")
    log.info("---\t----\t----\t----\t----\t----")

    try:
        rows = future.result()
    except Exception:
        log.exception("Error reading rows:")
        return
    
    #for row in rows:
    #   log.info(''.join(str(row)))
    return rows

def Delete(session,data):
    KEYSPACE = "recetas"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    
    session.execute("DELETE FROM recetas WHERE id='%s';"%data['id'])

def UpdateReceta(session,data):
    KEYSPACE = "recetas"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    session.execute("""UPDATE recetas 
    SET comentario="%s",
    farmaco="%s",
    doctor="%s"
    WHERE id="%s";
    """ %data['comentario'] %data['farmaco'] %data['doctor'] %data['id'])

def main():
    session, cluster = cassandra_conn()
    CreateTables(session)

@app.route('/')
def hello_world():
    session, cluster = cassandra_conn()
    CreateTables(session)
    return 'Hello, World!'

@app.route('/create', methods=['POST'])
def get_body():
    session, cluster = cassandra_conn()
    data = request.get_json()
    log.info(data)
    new = { "id": f"{data['id']}",
            "id_paciente": f"{data['id_paciente']}",
            "nombre": f"{data['nombre']}",
            "apellido": f"{data['apellido']}",
            "rut": f"{data['rut']}",
            "email": f"{data['email']}",
            "fecha_nacimiento": f"{data['fecha_nacimiento']}",
            "comentario": f"{data['comentario']}",
            "farmaco": f"{data['farmaco']}",
            "doctor": f"{data['doctor']}"
           }
    
    InsertReceta(session,new)

    return (new)

@app.route('/get', methods=['GET'])
def get_body():
    session, cluster = cassandra_conn()
    session.row_factory = dict_factory
    pacientes = session.execute("SELECT * FROM paciente")
    
    pacientes_response = []
    for pac in list(pacientes):
        aux = dict(pac)
        aux["id"] = str(pac["id"])
        pacientes_response.append(aux)
    
    recetas = session.execute("SELECT * FROM recetas")

    recetas_response = []
    for rec in list(recetas):
        aux = dict(rec)
        aux["id"] = str(rec["id"])
        recetas_response.append(aux)

    return jsonify({"Pacientes: ": pacientes_response, "Recetas": recetas_response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)