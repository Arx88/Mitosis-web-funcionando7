"""
Servicio de base de datos MongoDB
Maneja todas las operaciones de persistencia
"""

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Any
import json
# from src.utils.json_encoder import mongo_json_serializer  # Not needed for basic operations


class DatabaseService:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Conectar a MongoDB"""
        try:
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/task_manager')
            self.client = MongoClient(mongo_url)
            self.db = self.client.get_default_database()
            
            # Crear índices
            self.create_indexes()
            
            print(f"✅ Connected to MongoDB: {mongo_url}")
            
        except Exception as e:
            print(f"❌ Error connecting to MongoDB: {e}")
    
    def check_connection(self) -> Dict[str, Any]:
        """Verificar conexión con MongoDB y retornar información detallada"""
        try:
            # Probar conexión
            self.client.admin.command('ping')
            
            # Obtener información de la base de datos
            db_stats = self.db.command('dbstats')
            
            return {
                'status': 'connected',
                'database': self.db.name,
                'collections': len(self.db.list_collection_names()),
                'size_mb': round(db_stats.get('dataSize', 0) / (1024 * 1024), 2),
                'healthy': True
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'healthy': False
            }
            
    def create_indexes(self):
        """Crear índices para optimizar consultas"""
        try:
            # Índices para tareas
            self.db.tasks.create_index("task_id")
            self.db.tasks.create_index("created_at")
            
            # Índices para conversaciones
            self.db.conversations.create_index("task_id")
            self.db.conversations.create_index("created_at")
            
            # Índices para archivos
            self.db.files.create_index("task_id")
            self.db.files.create_index("file_id")
            
            # Índices para shares
            self.db.shares.create_index("share_id")
            
        except Exception as e:
            print(f"⚠️  Error creating indexes: {e}")
    
    def is_connected(self) -> bool:
        """Verificar si la conexión está activa"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    # === TASKS ===
    
    def save_task(self, task_data: Dict) -> str:
        """Guardar una tarea (con upsert para prevenir duplicados)"""
        try:
            task_data['updated_at'] = datetime.now()
            
            # Si no tiene created_at, es una nueva tarea
            if 'created_at' not in task_data:
                task_data['created_at'] = datetime.now()
            
            # Usar replace_one con upsert para prevenir duplicados
            filter_query = {"task_id": task_data.get('task_id')}
            result = self.db.tasks.replace_one(
                filter_query, 
                task_data, 
                upsert=True
            )
            
            if result.upserted_id:
                return str(result.upserted_id)
            elif result.modified_count > 0:
                # Tarea actualizada, obtener el _id existente
                existing_task = self.db.tasks.find_one(filter_query)
                return str(existing_task['_id']) if existing_task else None
            else:
                return None
            
        except Exception as e:
            print(f"Error saving task: {e}")
            return None
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Obtener una tarea por ID"""
        try:
            task = self.db.tasks.find_one({"task_id": task_id})
            if task:
                task['_id'] = str(task['_id'])
            return task
            
        except Exception as e:
            print(f"Error getting task: {e}")
            return None
    
    def update_task(self, task_id: str, updates: Dict) -> bool:
        """Actualizar una tarea"""
        try:
            updates['updated_at'] = datetime.now()
            
            result = self.db.tasks.update_one(
                {"task_id": task_id},
                {"$set": updates}
            )
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error updating task: {e}")
            return False
    
    def get_all_tasks(self, limit: int = 100) -> List[Dict]:
        """Obtener todas las tareas"""
        try:
            tasks = list(self.db.tasks.find().sort("created_at", -1).limit(limit))
            for task in tasks:
                task['_id'] = str(task['_id'])
            return tasks
            
        except Exception as e:
            print(f"Error getting all tasks: {e}")
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """Eliminar una tarea y toda su información relacionada"""
        try:
            # Eliminar tarea
            self.db.tasks.delete_one({"task_id": task_id})
            
            # Eliminar conversaciones relacionadas
            self.db.conversations.delete_many({"task_id": task_id})
            
            # Eliminar archivos relacionados
            self.db.files.delete_many({"task_id": task_id})
            
            return True
            
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False
    
    # === CONVERSATIONS ===
    
    def save_conversation(self, conversation_data: Dict) -> str:
        """Guardar una conversación"""
        try:
            conversation_data['created_at'] = datetime.now()
            conversation_data['updated_at'] = datetime.now()
            
            result = self.db.conversations.insert_one(conversation_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return None
    
    def get_conversation(self, task_id: str) -> Optional[Dict]:
        """Obtener conversación por task_id"""
        try:
            conversation = self.db.conversations.find_one({"task_id": task_id})
            if conversation:
                conversation['_id'] = str(conversation['_id'])
            return conversation
            
        except Exception as e:
            print(f"Error getting conversation: {e}")
            return None
    
    def update_conversation(self, task_id: str, updates: Dict) -> bool:
        """Actualizar conversación"""
        try:
            updates['updated_at'] = datetime.now()
            
            result = self.db.conversations.update_one(
                {"task_id": task_id},
                {"$set": updates},
                upsert=True
            )
            return result.acknowledged
            
        except Exception as e:
            print(f"Error updating conversation: {e}")
            return False
    
    def add_message_to_conversation(self, task_id: str, message: Dict) -> bool:
        """Agregar mensaje a conversación"""
        try:
            message['timestamp'] = datetime.now()
            
            result = self.db.conversations.update_one(
                {"task_id": task_id},
                {
                    "$push": {"messages": message},
                    "$set": {"updated_at": datetime.now()}
                },
                upsert=True
            )
            return result.acknowledged
            
        except Exception as e:
            print(f"Error adding message to conversation: {e}")
            return False
    
    # === FILES ===
    
    def save_file(self, file_data: Dict) -> str:
        """Guardar información de archivo"""
        try:
            file_data['created_at'] = datetime.now()
            file_data['updated_at'] = datetime.now()
            
            result = self.db.files.insert_one(file_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving file: {e}")
            return None
    
    def get_file(self, file_id: str) -> Optional[Dict]:
        """Obtener archivo por ID"""
        try:
            file_doc = self.db.files.find_one({"file_id": file_id})
            if file_doc:
                file_doc['_id'] = str(file_doc['_id'])
            return file_doc
            
        except Exception as e:
            print(f"Error getting file: {e}")
            return None
    
    def get_task_files(self, task_id: str) -> List[Dict]:
        """Obtener todos los archivos de una tarea"""
        try:
            files = list(self.db.files.find({"task_id": task_id}).sort("created_at", -1))
            for file_doc in files:
                file_doc['_id'] = str(file_doc['_id'])
            return files
            
        except Exception as e:
            print(f"Error getting task files: {e}")
            return []
    
    def delete_file(self, file_id: str) -> bool:
        """Eliminar archivo"""
        try:
            result = self.db.files.delete_one({"file_id": file_id})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    # === SHARES ===
    
    def save_share(self, share_data: Dict) -> str:
        """Guardar información de compartir"""
        try:
            share_data['created_at'] = datetime.now()
            
            result = self.db.shares.insert_one(share_data)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving share: {e}")
            return None
    
    def get_share(self, share_id: str) -> Optional[Dict]:
        """Obtener información de compartir"""
        try:
            share = self.db.shares.find_one({"share_id": share_id})
            if share:
                share['_id'] = str(share['_id'])
            return share
            
        except Exception as e:
            print(f"Error getting share: {e}")
            return None
    
    # === TOOL RESULTS ===
    
    def save_tool_result(self, tool_result: Dict) -> str:
        """Guardar resultado de herramienta"""
        try:
            tool_result['created_at'] = datetime.now()
            
            result = self.db.tool_results.insert_one(tool_result)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving tool result: {e}")
            return None
    
    def get_task_tool_results(self, task_id: str) -> List[Dict]:
        """Obtener resultados de herramientas de una tarea"""
        try:
            results = list(self.db.tool_results.find({"task_id": task_id}).sort("created_at", -1))
            for result in results:
                result['_id'] = str(result['_id'])
            return results
            
        except Exception as e:
            print(f"Error getting task tool results: {e}")
            return []
    
    # === UTILITY ===
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas de la base de datos"""
        try:
            stats = {
                'tasks_count': self.db.tasks.count_documents({}),
                'conversations_count': self.db.conversations.count_documents({}),
                'files_count': self.db.files.count_documents({}),
                'shares_count': self.db.shares.count_documents({}),
                'tool_results_count': self.db.tool_results.count_documents({}),
                'connected': self.is_connected()
            }
            return stats
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, days_old: int = 30) -> Dict:
        """Limpiar datos antiguos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Eliminar tareas viejas
            tasks_deleted = self.db.tasks.delete_many({"created_at": {"$lt": cutoff_date}})
            
            # Eliminar conversaciones viejas  
            conversations_deleted = self.db.conversations.delete_many({"created_at": {"$lt": cutoff_date}})
            
            # Eliminar archivos viejos
            files_deleted = self.db.files.delete_many({"created_at": {"$lt": cutoff_date}})
            
            # Eliminar shares viejos
            shares_deleted = self.db.shares.delete_many({"created_at": {"$lt": cutoff_date}})
            
            return {
                'tasks_deleted': tasks_deleted.deleted_count,
                'conversations_deleted': conversations_deleted.deleted_count,
                'files_deleted': files_deleted.deleted_count,
                'shares_deleted': shares_deleted.deleted_count
            }
            
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
            return {'error': str(e)}