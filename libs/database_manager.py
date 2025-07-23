import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class ConnectionConfig:
    """ConnectionConfigクラス"""
    database_path: str
    max_connections: int = 10
    timeout: float = 30.0
    check_same_thread: bool = False
    isolation_level: Optional[str] = None
    detect_types: int = 0


class DatabaseError(Exception):
    """DatabaseErrorクラス"""
    pass


class ConnectionPoolError(DatabaseError):
    """ConnectionPoolErrorクラス"""
    pass


class TransactionError(DatabaseError):
    """TransactionErrorクラス"""
    pass


class ConnectionPool:
    """ConnectionPoolクラス"""
    def __init__(self, config: ConnectionConfig):
        """初期化メソッド"""

        self.config = config
        self._pool = Queue(maxsize=config.max_connections)
        self._lock = threading.Lock()
        self._created_connections = 0
        self._logger = logging.getLogger(__name__)

        self._initialize_pool()

    def _initialize_pool(self):
        """initialize_pool（内部メソッド）"""
        for _ in range(min(3, self.config.max_connections)):
            conn = self._create_connection()
            self._pool.put(conn)

    def _create_connection(self) -> sqlite3.Connection:
        """create_connection作成（内部メソッド）"""
        try:
            conn = sqlite3.connect(
                self.config.database_path,
                timeout=self.config.timeout,
                check_same_thread=self.config.check_same_thread,
                isolation_level=self.config.isolation_level,
                detect_types=self.config.detect_types,
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            self._created_connections += 1
            self._logger.debug(
                f"Created new database connection ({self._created_connections})"
            )
            return conn
        except sqlite3.Error as e:
            raise ConnectionPoolError(f"Failed to create database connection: {e}")

    def get_connection(self, timeout: Optional[float] = None) -> sqlite3.Connection:
        """connection取得メソッド"""
        timeout = timeout or self.config.timeout

        try:
            return self._pool.get(timeout=timeout)
        except Empty:
            with self._lock:
                if self._created_connections < self.config.max_connections:
                    return self._create_connection()
                else:
                    raise ConnectionPoolError("Connection pool exhausted")

    def return_connection(self, conn: sqlite3.Connection):
        """return_connectionメソッド"""
        if conn:
            try:
                conn.rollback()
                self._pool.put_nowait(conn)
            except Exception as e:
                self._logger.warning(f"Failed to return connection to pool: {e}")
                self._close_connection(conn)

    def _close_connection(self, conn: sqlite3.Connection):
        """close_connection（内部メソッド）"""
        try:
            conn.close()
            with self._lock:
                self._created_connections -= 1
        except Exception as e:
            self._logger.warning(f"Error closing connection: {e}")

    def close_all(self):
        """close_allメソッド"""
        connections = []
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                connections.append(conn)
            except Empty:
                break

        for conn in connections:
            self._close_connection(conn)


class Transaction:
    """Transactionクラス"""
    def __init__(self, connection: sqlite3.Connection, pool: ConnectionPool):
        """初期化メソッド"""
        self.connection = connection
        self.pool = pool
        self._active = False
        self._logger = logging.getLogger(__name__)

    def __enter__(self):
        """__enter__特殊メソッド"""
        try:
            self.connection.execute("BEGIN")
            self._active = True
            self._logger.debug("Transaction started")
            return self
        except sqlite3.Error as e:
            self.pool.return_connection(self.connection)
            raise TransactionError(f"Failed to start transaction: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """__exit__特殊メソッド"""
        try:
            if exc_type is None:
                self.connection.commit()
                self._logger.debug("Transaction committed")
            else:
                self.connection.rollback()
                self._logger.debug("Transaction rolled back")
        except sqlite3.Error as e:
            self._logger.error(f"Error in transaction cleanup: {e}")
        finally:
            self._active = False
            self.pool.return_connection(self.connection)

        return False

    def execute(self, query:
        """execute実行メソッド"""
    str, parameters: Optional[Tuple] = None) -> sqlite3.Cursor:
        if not self._active:
            raise TransactionError("Transaction is not active")

        try:
            return self.connection.execute(query, parameters or ())
        except sqlite3.Error as e:
            raise DatabaseError(f"Query execution failed: {e}")

    def executemany(self, query:
        """executemany実行メソッド"""
    str, parameters: List[Tuple]) -> sqlite3.Cursor:
        if not self._active:
            raise TransactionError("Transaction is not active")

        try:
            return self.connection.executemany(query, parameters)
        except sqlite3.Error as e:
            raise DatabaseError(f"Batch query execution failed: {e}")


class DatabaseManager:
    """DatabaseManager - 管理システムクラス"""
    def __init__(self, config:
        """初期化メソッド"""
    ConnectionConfig):
        self.config = config
        self._pool = ConnectionPool(config)
        self._logger = logging.getLogger(__name__)

        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """ensure_database_exists（内部メソッド）"""
        db_path = Path(self.config.database_path)
        if not db_path.parent.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self):
        """connection取得メソッド"""
        conn = None
        try:
            conn = self._pool.get_connection()
            yield conn
        finally:
            if conn:
                self._pool.return_connection(conn)

    def transaction(self) -> Transaction:
        """transactionメソッド"""
        conn = self._pool.get_connection()
        return Transaction(conn, self._pool)

    def execute(self, query:
        """execute実行メソッド"""
    str, parameters: Optional[Tuple] = None) -> sqlite3.Cursor:
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(query, parameters or ())
                conn.commit()
                return cursor
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Query execution failed: {e}")

    def executemany(self, query:
        """executemany実行メソッド"""
    str, parameters: List[Tuple]) -> sqlite3.Cursor:
        with self.get_connection() as conn:
            try:
                cursor = conn.executemany(query, parameters)
                conn.commit()
                return cursor
            except sqlite3.Error as e:
                conn.rollback()
                raise DatabaseError(f"Batch query execution failed: {e}")

    def select_one(
        self, query: str, parameters: Optional[Tuple] = None
    ) -> Optional[sqlite3.Row]:
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(query, parameters or ())
                return cursor.fetchone()
            except sqlite3.Error as e:
                raise DatabaseError(f"Select query failed: {e}")

    def select_all(
        self, query: str, parameters: Optional[Tuple] = None
    ) -> List[sqlite3.Row]:
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(query, parameters or ())
                return cursor.fetchall()
            except sqlite3.Error as e:
                raise DatabaseError(f"Select query failed: {e}")

    def select_many(
        self, query: str, parameters: Optional[Tuple] = None, size: int = 100
    ) -> List[sqlite3.Row]:
        with self.get_connection() as conn:
            try:
                cursor = conn.execute(query, parameters or ())
                return cursor.fetchmany(size)
            except sqlite3.Error as e:
                raise DatabaseError(f"Select query failed: {e}")

    def insert(self, table:
        """insertメソッド"""
    str, data: Dict[str, Any]) -> int:
        columns = list(data.keys())
        placeholders = ", ".join(["?" for _ in columns])
        values = list(data.values())

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        cursor = self.execute(query, tuple(values))
        return cursor.lastrowid

    def insert_many(self, table:
        """insert_manyメソッド"""
    str, data: List[Dict[str, Any]]) -> int:
        if not data:
            return 0

        columns = list(data[0].keys())
        placeholders = ", ".join(["?" for _ in columns])
        values = [tuple(row[col] for col in columns) for row in data]

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        cursor = self.executemany(query, values)
        return cursor.rowcount

    def update(
        self,
        table: str,
        data: Dict[str, Any],
        where_clause: str,
        where_params: Optional[Tuple] = None,
    ) -> int:
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        params = list(data.values())
        if where_params:
            params.extend(where_params)

        cursor = self.execute(query, tuple(params))
        return cursor.rowcount

    def delete(
        self, table: str, where_clause: str, where_params: Optional[Tuple] = None
    ) -> int:
        query = f"DELETE FROM {table} WHERE {where_clause}"
        cursor = self.execute(query, where_params)
        return cursor.rowcount

    def create_table(
        self,
        table_name: str,
        columns: Dict[str, str],
        constraints: Optional[List[str]] = None,
    ):
        column_defs = [f"{name} {definition}" for name, definition in columns.items()]

        if constraints:
            column_defs.extend(constraints)

        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
        self.execute(query)

    def drop_table(self, table_name:
        """drop_tableメソッド"""
    str):
        query = f"DROP TABLE IF EXISTS {table_name}"
        self.execute(query)

    def table_exists(self, table_name:
        """table_existsメソッド"""
    str) -> bool:
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.select_one(query, (table_name,))
        return result is not None

    def get_table_info(self, table_name:
        """table_info取得メソッド"""
    str) -> List[sqlite3.Row]:
        query = f"PRAGMA table_info({table_name})"
        return self.select_all(query)

    def vacuum(self):
        """vacuumメソッド"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")

    def analyze(self):
        """analyze分析メソッド"""
        with self.get_connection() as conn:
            conn.execute("ANALYZE")

    def get_connection_count(self) -> int:
        """connection_count取得メソッド"""
        return self._pool._created_connections

    def close(self):
        """closeメソッド"""
        self._pool.close_all()
        self._logger.info("Database manager closed")

    def __enter__(self):
        """__enter__特殊メソッド"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """__exit__特殊メソッド"""
        self.close()


def create_database_manager(database_path:
    """database_manager作成メソッド"""
str, **kwargs) -> DatabaseManager:
    config = ConnectionConfig(database_path=database_path, **kwargs)
    return DatabaseManager(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    config = ConnectionConfig(database_path="test.db", max_connections=5, timeout=10.0)

    with DatabaseManager(config) as db:
        db.create_table(
            "users",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "name": "TEXT NOT NULL",
                "email": "TEXT UNIQUE NOT NULL",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            },
        )

        user_id = db.insert("users", {"name": "John Doe", "email": "john@example.com"})
        print(f"Inserted user with ID: {user_id}")

        user = db.select_one("SELECT * FROM users WHERE id = ?", (user_id,))
        print(f"User: {dict(user)}")

        with db.transaction() as tx:
            tx.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                ("Jane Doe", "jane@example.com"),
            )
            tx.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                ("Bob Smith", "bob@example.com"),
            )

        users = db.select_all("SELECT * FROM users")
        print(f"All users: {[dict(user) for user in users]}")
