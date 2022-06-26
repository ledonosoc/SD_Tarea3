#!/usr/bin/env python

# Copyright DataStax, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from asyncio import create_task
import logging
from time import sleep

sleep(90)

log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy

pacientes_counter = 0
recetas_counter = 0

def cassandra_conn():
   auth_provider = PlainTextAuthProvider(username='cassandra',password='cassandra')
   cluster = Cluster(['cassandra'], load_balancing_policy=DCAwareRoundRobinPolicy() ,auth_provider=auth_provider)

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
    prepared = session.prepare("""
        INSERT INTO paciente ("id", "nombre", "apellido", "rut", "email", "fecha_nacimiento")
        VALUES (?, ?, ?, ?, ?, ?)
        """)

    session.execute(prepared, (pacientes_counter, '%s' %data['nombre'],'%s'%data['apellido'],'%s' %data['rut'],'%s' %data['email'],'%s'%data['fecha_nacimiento']))
    pacientes_counter = pacientes_counter + 1

def InsertReceta(session, data):
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

def Delete(session):
    session.execute("DROP KEYSPACE " + KEYSPACE)

def SelectPaciente(session, rut):
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

def main():
    session, cluster = cassandra_conn()
    CreateTables(session)
    KEYSPACE = "pacientes"
    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)
    InsertPaciente(session)

if __name__ == "__main__":
    main()