import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
import logging
import os

QUESTION_CACHE_DIR = "E:/math-ai/math-ai-backend/question_cache"

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', 'root')
        self.database = os.getenv('DB_NAME', 'cs')
        self.connection = None
        self.connect()  # 调用 connect 方法建立连接
        self._init_tables()  # 初始化表结构

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                return True
        except Error as e:
            print(f"Error while connecting to MySQL: {e}")
            return False
    
    def _init_tables(self):
        """初始化数据库表结构"""
        try:
            cursor = self.connection.cursor()
            
            # 创建 users 表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建 api_keys 表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                api_key VARCHAR(64) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
            # 修改后的 user_documents 表结构
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_documents (
                id INT PRIMARY KEY AUTO_INCREMENT,
                user_id INT NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size BIGINT NOT NULL,  -- 新增字段
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            ''')
            
              # 创建questions表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id VARCHAR(36) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                conversation_id VARCHAR(36),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_conversation_id (conversation_id),
                INDEX idx_user_id (user_id)
            )
            ''')
            
            # 创建reference_files表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reference_files (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                question_id VARCHAR(36) NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT,
                description TEXT,
                similarity FLOAT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
            ''')
            self.connection.commit()
        except Error as e:
            print(f"初始化表失败: {e}")

    def close(self):
        if self.connection.is_connected():
            self.connection.close()

    def user_exists(self, username):
        cursor = self.connection.cursor()
        query = "SELECT id FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        cursor.close()
        return result is not None

    def create_user(self, username, password_hash, email):
        cursor = self.connection.cursor()
        query = "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, password_hash, email))
        self.connection.commit()
        user_id = cursor.lastrowid
        cursor.close()
        return user_id

    def verify_user(self, username, password_hash):
        cursor = self.connection.cursor()
        query = "SELECT id, password_hash FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        cursor.close()
        if result and result[1] == password_hash:
            return result[0]
        return None

    def generate_api_key(self, user_id):
        import secrets
        api_key = secrets.token_hex(32)

        cursor = self.connection.cursor()
        query = "INSERT INTO api_keys (user_id, api_key) VALUES (%s, %s)"
        cursor.execute(query, (user_id, api_key))
        self.connection.commit()
        cursor.close()

        return api_key

    def get_api_key(self, user_id):
        cursor = self.connection.cursor()
        query = "SELECT api_key FROM api_keys WHERE user_id = %s ORDER BY created_at DESC LIMIT 1"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result[0]
        return None

    def validate_api_key(self, api_key):
        cursor = self.connection.cursor(dictionary=True)
        query = """
        SELECT ak.user_id, ak.api_key, ak.last_used 
        FROM api_keys ak
        JOIN users u ON ak.user_id = u.id
        WHERE ak.api_key = %s
        """
        cursor.execute(query, (api_key,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            # 更新最后使用时间
            cursor = self.connection.cursor()
            update_query = "UPDATE api_keys SET last_used = %s WHERE api_key = %s"
            cursor.execute(update_query, (datetime.now(), api_key))
            self.connection.commit()
            cursor.close()

            return result['user_id']
        return None

    # 会话相关方法
    def create_conversation(self, user_id, title=None):
        cursor = self.connection.cursor()
        query = "INSERT INTO conversations (user_id, title) VALUES (%s, %s)"
        cursor.execute(query, (user_id, title))
        self.connection.commit()
        conversation_id = cursor.lastrowid
        cursor.close()
        return conversation_id

    def get_conversations(self, user_id):
        cursor = self.connection.cursor(dictionary=True)
        query = "SELECT id, title, created_at FROM conversations WHERE user_id = %s ORDER BY created_at DESC"
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        return results

    # 消息相关方法
    def add_message(self, conversation_id, role, content):
        cursor = self.connection.cursor()
        query = "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)"
        cursor.execute(query, (conversation_id, role, content))
        self.connection.commit()
        message_id = cursor.lastrowid
        cursor.close()
        return message_id

    def get_messages(self, conversation_id):
        cursor = self.connection.cursor(dictionary=True)
        query = """
        SELECT role, content, timestamp 
        FROM messages 
        WHERE conversation_id = %s 
        ORDER BY timestamp ASC  # 改为正序排列
        """
        cursor.execute(query, (conversation_id,))
        results = cursor.fetchall()
        cursor.close()
        return results
    
    def get_all_api_keys(self, user_id):
        """获取用户所有API密钥"""
        cursor = self.connection.cursor()
        # 添加 user_id 到查询结果中
        query = "SELECT user_id, api_key, created_at, last_used FROM api_keys WHERE user_id = %s ORDER BY created_at DESC"
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        # 返回的字典中包含 "user_id" 键
        return [{"user_id": row[0], "api_key": row[1], "created_at": row[2], "last_used": row[3]} for row in results]
    
    def delete_api_key(self, user_id, api_key):
        try:
            cursor = self.connection.cursor()
            query = "DELETE FROM api_keys WHERE api_key = %s AND user_id = %s"
            cursor.execute(query, (api_key, user_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self.connection.rollback()
            logging.error(f"删除API密钥失败: {str(e)}")
            return False

    # 添加问题相关方法
    def save_question(self, question_id, user_id, content, conversation_id=None):
        """保存问题到数据库"""
        try:
            cursor = self.connection.cursor()
            query = """
            INSERT INTO questions (id, user_id, content, conversation_id, created_at) 
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (question_id, user_id, content, conversation_id, datetime.now()))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"保存问题失败: {e}")
            return False
    
    def get_question(self, question_id):
        """获取问题内容"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM questions WHERE id = %s"
            cursor.execute(query, (question_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            print(f"获取问题失败: {e}")
            return None
    
    # 添加参考资料相关方法
    def save_reference_files(self, question_id, reference_files):
        """保存参考资料到数据库"""
        try:
            cursor = self.connection.cursor()
            
            # 先删除该问题已有的参考资料
            delete_query = "DELETE FROM reference_files WHERE question_id = %s"
            cursor.execute(delete_query, (question_id,))
            
            # 插入新的参考资料
            insert_query = """
            INSERT INTO reference_files 
            (question_id, file_name, file_path, file_type, description, similarity, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            for ref in reference_files:
                cursor.execute(insert_query, (
                    question_id,
                    ref.get("file_name", ""),
                    ref.get("file_path", ""),
                    ref.get("file_type", ""),
                    ref.get("description", ""),
                    ref.get("similarity", 0.0),
                    ref.get("source", "local")
                ))
            
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"保存参考资料失败: {e}")
            self.connection.rollback()
            return False
    
    def get_reference_files(self, question_id):
        """获取问题的参考资料"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT file_name, file_path, file_type, description, similarity, source
            FROM reference_files
            WHERE question_id = %s
            ORDER BY similarity DESC
            """
            cursor.execute(query, (question_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"获取参考资料失败: {e}")
            return []
    # 在Database类中添加以下方法

    def save_user_document(self, user_id, file_name, file_path, file_type, file_size):
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM user_documents WHERE user_id = %s AND file_name = %s", 
                        (user_id, file_name))
            if cursor.fetchone():
                return False

            query = """
            INSERT INTO user_documents 
            (user_id, file_name, file_path, file_type, file_size)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, file_name, file_path, file_type, file_size))
            self.connection.commit()
            return True
        except Error as e:
            print(f"保存用户文档失败: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def get_user_documents(self, user_id):
        """获取用户文档列表"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT id, file_name, file_path, file_type, created_at 
            FROM user_documents 
            WHERE user_id = %s 
            ORDER BY created_at DESC
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"获取用户文档失败: {e}")
            return []
        finally:
            cursor.close()
            
    def delete_user_document(self, doc_id, user_id):
        """删除用户文档"""
        try:
            cursor = self.connection.cursor()
            query = "DELETE FROM user_documents WHERE id = %s AND user_id = %s"
            cursor.execute(query, (doc_id, user_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"删除用户文档失败: {e}")
            return False