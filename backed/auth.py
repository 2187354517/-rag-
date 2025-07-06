from database import Database
import hashlib
import secrets
from datetime import datetime  # 确保导入 datetime

class Auth:
    def __init__(self):
        self.db = Database()
        if not self.db.connection:
            print("数据库连接失败，请检查配置。")
            raise ConnectionError("数据库连接失败，请检查配置。")

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password, email):
        """返回格式 (status, data)"""
        if self.db.user_exists(username):
            return False, "用户名已存在"

        password_hash = self.hash_password(password)
        user_id = self.db.create_user(username, password_hash, email)
        if user_id:
            api_key = self.db.generate_api_key(user_id)
            return True, {"user_id": user_id, "api_key": api_key}
        return False, "注册失败"

    def login_user(self, username, password):
        """返回格式 (status, data)"""
        password_hash = self.hash_password(password)
        user_id = self.db.verify_user(username, password_hash)
        if user_id:
            api_key = self.db.get_api_key(user_id)
            return True, {"user_id": user_id, "api_key": api_key}
        return False, "用户名或密码错误"

    def generate_api_key(self, user_id):
        api_key = secrets.token_hex(32)
        cursor = self.db.connection.cursor()
        query = "INSERT INTO api_keys (user_id, api_key) VALUES (%s, %s)"
        cursor.execute(query, (user_id, api_key))
        self.db.connection.commit()
        cursor.close()
        return api_key

    def get_api_key(self, user_id):
        cursor = self.db.connection.cursor()
        query = "SELECT api_key FROM api_keys WHERE user_id = %s ORDER BY created_at DESC LIMIT 1"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return result[0]
        return None

    def validate_api_key(self, api_key):
        cursor = self.db.connection.cursor(dictionary=True)
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
            cursor = self.db.connection.cursor()
            update_query = "UPDATE api_keys SET last_used = %s WHERE api_key = %s"
            cursor.execute(update_query, (datetime.now(), api_key))
            self.db.connection.commit()
            cursor.close()

            return result['user_id']
        return None


