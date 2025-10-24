import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from pymongo.cursor import Cursor
import redis
from neo4j import GraphDatabase

import bcrypt
# Configuración de conexiones desde variables de entorno (Docker-friendly)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def check_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def set_access_token(dni: str, minutes: int = 60) -> None:
    if redis_client:
        redis_client.setex(f"acceso:{dni}", timedelta(minutes=minutes), "1")

def check_access_token(dni: str) -> bool:
    if redis_client:
        return bool(redis_client.get(f"acceso:{dni}"))
    return False
REDIS_DB = int(os.getenv("REDIS_DB", 0))
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# TTL configurations
ACCESO_TTL = 3600  # 1 hora
RECORDATORIO_TTL = 600  # 10 minutos

def get_mongo_client(uri: str = None) -> MongoClient:
    return MongoClient(uri or MONGO_URI)

# MongoDB: Conexión y colecciones
mongo_client = get_mongo_client()
db = mongo_client["vidasana"]
pacientes: Collection = db["pacientes"]
turnos: Collection = db["turnos"]
habitos: Collection = db["habitos"]

# Función para limpiar DNIs duplicados antes de crear el índice
def _limpiar_duplicados():
    pipeline = [
        {"$group": {
            "_id": "$dni",
            "doc_id": {"$last": "$_id"},
            "count": {"$sum": 1}
        }},
        {"$match": {
            "count": {"$gt": 1}
        }}
    ]
    
    duplicados = list(pacientes.aggregate(pipeline))
    for dup in duplicados:
        # Mantener solo el documento más reciente para cada DNI
        pacientes.delete_many({
            "dni": dup["_id"],
            "_id": {"$ne": dup["doc_id"]}
        })

# Crear índices de forma segura
def _setup_indices():
    try:
        # Primero limpiar duplicados
        _limpiar_duplicados()
        
        # Verificar si ya existe el índice
        indices_actuales = pacientes.list_indexes()
        tiene_indice_dni = any(
            idx.get("key", {}).get("dni") == 1 
            for idx in indices_actuales
        )
        
        if not tiene_indice_dni:
            pacientes.create_index("dni", unique=True)
            
        # Otros índices (no únicos)
        turnos.create_index([("fecha", DESCENDING)])
        habitos.create_index([("dni", 1), ("fecha", -1)])
        
    except Exception as e:
        print(f"Advertencia al configurar índices: {str(e)}")

# Ejecutar setup de índices
_setup_indices()

# Redis: Control de acceso y recordatorios
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

# Neo4j: Red social médico-paciente (opcional)
driver = None
try:
    # Conectar con las credenciales proporcionadas
    driver = GraphDatabase.driver(NEO4J_URI, auth=("neo4j", "test12345"))
    # Verificar conexión
    with driver.session() as session:
        session.run("RETURN 1")
    print("Conexión exitosa a Neo4j")
            
    if driver is None:
        print("No se pudo conectar a Neo4j - la funcionalidad de red social estará deshabilitada")
        
except Exception as e:
    print(f"Error al configurar Neo4j: {str(e)}")
    driver = None

# Helpers de MongoDB
def insert_one(collection: Collection, document: Dict) -> str:
    result = collection.insert_one(document)
    return str(result.inserted_id)

def update_one(collection: Collection, query: Dict, update: Dict) -> bool:
    result = collection.update_one(query, update)
    return result.modified_count > 0

def find_one(collection: Collection, query: Dict) -> Optional[Dict]:
    return collection.find_one(query)

def find(collection: Collection, query: Dict) -> Cursor:
    return collection.find(query)

# Helpers de Redis
def set_access_token(dni: str) -> bool:
    try:
        redis_client.setex(f"acceso:{dni}", ACCESO_TTL, "activo")
        return True
    except redis.RedisError:
        return False

def set_reminder(dni: str, fecha: str, mensaje: str) -> bool:
    try:
        redis_client.setex(f"recordatorio:{dni}:{fecha}", RECORDATORIO_TTL, mensaje)
        return True
    except redis.RedisError:
        return False

def check_access(dni: str) -> bool:
    try:
        return bool(redis_client.get(f"acceso:{dni}"))
    except redis.RedisError:
        return False

def get_access_ttl(dni: str) -> Optional[int]:
    try:
        ttl = redis_client.ttl(f"acceso:{dni}")
        # Redis devuelve -2 si la llave no existe, -1 si existe sin TTL
        if ttl is None or ttl < 0:
            return None
        return int(ttl)
    except redis.RedisError:
        return None

def get_reminder(dni: str, fecha: str) -> Optional[str]:
    try:
        value = redis_client.get(f"recordatorio:{dni}:{fecha}")
        return value.decode('utf-8') if value else None
    except redis.RedisError:
        return None

# Simulación de envío de emails
def simular_email(to_email: str, subject: str, body: str) -> None:
    print(f"\n Simulación de Email:")
    print(f"Para: {to_email}")
    print(f"Asunto: {subject}")
    print(f"Mensaje: {body}\n")
