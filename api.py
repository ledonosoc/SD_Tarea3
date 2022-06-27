from asyncio import create_task
import logging
from time import sleep
from flask import Flask, jsonify, request
from flask_json_schema import JsonSchema, JsonValidationError
import json

#sleep (90)
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
    global pacientes_counter
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
    global recetas_counter
    KEYSPACE = "recetas"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    paciente_id = SelectPaciente(session,data['rut'])
    prepared = session.prepare("""
            INSERT INTO recetas ("id", "id_paciente", "comentario", "farmaco", "doctor")
            VALUES (?, ?, ?, ?, ?)
            """)
    if paciente_id == None:
        InsertPaciente(session,data)
        paciente_id= pacientes_counter-1
        session.execute(prepared, (recetas_counter, paciente_id,'%s'%data['comentario'],'%s' %data['farmaco'],'%s' %data['doctor']))
        recetas_counter = recetas_counter + 1
    else:
        session.execute(prepared, (recetas_counter, paciente_id,'%s'%data['comentario'],'%s' %data['farmaco'],'%s' %data['doctor']))
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
    return str(rows)

def Select(session):
    KEYSPACE = "pacientes"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    future = session.execute_async("SELECT * FROM paciente")
    log.info("id\tnombre\tapellido\trut\temail\tfecha_nacimiento")
    log.info("---\t----\t----\t----\t----\t----")

    try:
        rows1 = future.result()
    except Exception:
        log.exception("Error reading rows:")
        return
    html=''
    for row in rows1:
        log.info(''.join(str(row)))    
        html += '<h4>' + ''.join(str(row))
    KEYSPACE = "recetas"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    future = session.execute_async("SELECT * FROM recetas")
    log.info("id\tid_paciente\tcomentario\tfarmaco\tdoctor")
    log.info("---\t----\t----\t----\t----")

    try:
        rows2 = future.result()
    except Exception:
        log.exception("Error reading rows:")
        return
    
    for row in rows2:
        log.info(''.join(str(row)))
        html += '<h4>' + ''.join(str(row))

    return html

def Delete(session,data):
    KEYSPACE = "recetas"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    
    session.execute("DELETE FROM recetas WHERE id=%s;"%data['id'])

def UpdateReceta(session,data):
    KEYSPACE = "recetas"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    session.execute("""UPDATE recetas 
    SET comentario="%s",
    farmaco="%s",
    doctor="%s"
    WHERE id=%s;
    """ %data['comentario'] %data['farmaco'] %data['doctor'] %data['id'])

def InsertTest(session):
    KEYSPACE = "pacientes"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    prepared = session.prepare("""INSERT INTO paciente ("id", "nombre", "apellido", "rut", "email", "fecha_nacimiento")
        VALUES (?, ?, ?, ?, ?, ?)
        """)
    for i in range(5):
        session.execute(prepared, (i,'name','lastname','123','bla@bla','1/1/1'))
    KEYSPACE = "recetas"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    prepared = session.prepare("""INSERT INTO recetas ("id", "id_paciente", "comentario", "farmaco", "doctor") VALUES (?, ?, ?, ?, ?)""")
    for i in range(5):
        session.execute(prepared, (i,i,'blabla','remedio','doc'))
    

@app.route('/')
def hello_world():
    session, cluster = cassandra_conn()
    CreateTables(session)
    return 'Tablas creadas correctamente! Bienvenido'

@app.route('/create', methods=['POST'])
def get_body():
    session, cluster = cassandra_conn()
    data = request.get_json()
    log.info(data)
    new = { "nombre": f"{data['nombre']}",
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
def getAll():
    session, cluster = cassandra_conn()
    resultado = Select(session)
    return resultado

@app.route('/delete', methods=['POST'])
def delete():
    session, cluster = cassandra_conn()
    data = request.get_json()
    log.info(data)
    new = { "id": f"{data['id']}"
           }
    
    Delete(session,new)   

    return (new)

@app.route('/edit', methods=['POST'])
def edit():
    session, cluster = cassandra_conn()
    data = request.get_json()
    log.info(data)
    new = { "id": f"{data['id']}",
            "comentario": f"{data['comentario']}",
            "farmaco": f"{data['farmaco']}",
            "doctor": f"{data['doctor']}"
           }
    
    UpdateReceta(session,new)   

    return (new)

@app.route('/test', methods=['GET'])
def test():
    session, cluster = cassandra_conn()
    InsertTest(session)
    return 'Insertado de prueba correcto'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True, threaded=True)