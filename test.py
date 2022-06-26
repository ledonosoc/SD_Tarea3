from flask import Flask, jsonify, request, render_template, redirect, url_for, flash, session, abort
from flask_json_schema import JsonSchema, JsonValidationError
import json

import os
import sys
import uuid
import logging

from cassandra.cluster import Cluster
from cassandra.query import dict_factory

from operator import itemgetter

from model.receta import RecetaSchema
from model.paciente import PacienteSchema

from time import sleep

sleep(90)

log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

def CreateTables():
    #KEYSPACE = os.environ["CASSANDRA_KEYSPACE"]
    #cluster = Cluster([os.environ["CASSANDRA_IP_ADDRESS"]], port=9042)
    #session = cluster.connect()
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
            id UUID,
            nombre text,
            apellido text,
            rut text,
            email text,
            fecha_nacimiento text,
            PRIMARY KEY ((nombre, apellido), id)
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
            id UUID,
            paciente_id UUID,
            fecha_nacimiento text,
            comentario text,
            farmacos text,
            doctor text,
            PRIMARY KEY ((id))
        )
        """)

def cassandra_conn():
    #cluster = Cluster(contact_points=[ os.environ["CASSANDRA_IP_ADDRESS"] ], port=9042)
    cluster = Cluster(contact_points=['cassandra'], auth_provider=auth_provider)
    #session = cluster.connect(keyspace)
    session = cluster.connect()
    #return session
    return cluster, session

app = Flask(__name__)
schema = JsonSchema(app)
with app.app_context():
    try:
        CreateTables()
    except Exception as e:
        print(e)
        sys.exit(1)

@app.route('/' , methods=['POST'])
def get():
    try:
        session = cassandra_conn('Pacientes')
        session.row_factory = dict_factory
        users = session.execute("SELECT * FROM paciente")
        
        users_response = []
        for user in list(users):
            aux = dict(user)
            aux["id"] = str(user["id"])
            users_response.append(aux)

        session = cassandra_conn('Recetas')
        session.row_factory = dict_factory
        recetas = session.execute("SELECT * FROM receta")

        recetas_response = []
        for receta in list(recetas):
            aux = dict(receta)
            aux["paciente_id"] = str(receta["paciente_id"])
            recetas_response.append(aux)

        return jsonify({"pacientes": users_response, "recetas": recetas_response})

    except Exception as e:
        print(e)
        sys.exit(1)



@app.rout('/create', methods=["POST"])
def create():
    try:
        #KEYSPACE = "Pacientes"
        session = cassandra_conn('Pacientes')
        data = request.get_json()
        receta = RecetaSchema().load(data, partial=('id', 'id_paciente'), unknown='EXCLUDE')
        paciente = PacienteSchema().load(data, partial=('id'), unknown='EXCLUDE')

        data = {**receta, **paciente}
        nombre, apellido, rut, email, fecha_nacimiento, comentario, farmacos, doctor = itemgetter(
            'nombre',
            'apellido',
            'rut',
            'email',
            'fecha_nacimiento',
            'comentario',
            'farmacos',
            'doctor'
            )(data)
        session.row_factory = dict_factory
        users = session.execute("SELECT * FROM paciente WHERE nombre = %s AND apellido = %s", [nombre, apellido])

        response = []
        for user in list(users):
            aux = dict(user)
            aux["id"] = str(user["id"])
            response.append(aux)

        if len(response) == 0:
            newUserId = uuid.uuid4()
            session.row_factory = dict_factory
            insertresponse = session.excute("""
            INSERT INTO paciente (id, nombre, apellido, rut, email, fecha_nacimiento)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            [newUserId, nombre, apellido, rut, email, fecha_nacimiento], trace=True)

        else:
            newUserId = response[0]["id"]
        
        session.cassandra_conn('Recetas')
        newRecetaId = uuid.uuid4()
        session.excute("""
        INSERT INTO paciente (id, nombre, apellido, rut, email, fecha_nacimiento)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        [newUserId, nombre, apellido, rut, email, fecha_nacimiento])

        return jsonify({"status: ": "ok"})

    except Exception as e:
        return jsonify({"status: ": "error", "message": str(e)})

@app.route('/edit', methods=["POST"])
def edit():
    try:
        data = request.get_json()
        receta = RecetaSchema().load(data, partial=('id_paciente'), unknown='EXCLUDE')

        id, comment, farmacos, doc = itemgetter(
            'id',
            'comentario',
            'farmacos',
            'doctor'
            )(receta)
        session = cassandra_conn('Recetas')
        session.execute("""UPDATE recetas SET comentario = %s, farmacos = %s, doctor = %s WHERE id = %s IF EXISTS""",
         [comment, farmacos, doc, id])

        return jsonify({"status: ": "ok"})
    
    except Exception as e:
        return jsonify({"status: ": "error", "message": str(e)})

@app.route('/delete', methods=["POST"])
def delete():
    try:
        data = request.get_json()
        receta = RecetaSchema().load(data, partial=('comentario', 'doctor', 'farmacos', 'id_paciente'), unknown='EXCLUDE')

        id = itemgetter('id')(receta)
        session = cassandra_conn('Recetas')
        session.execute("""DELETE FROM recetas WHERE id = %s IF EXISTS""", [id])

        return jsonify({"status: ": "ok"})

    except Exception as e:
        return jsonify({"status: ": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)