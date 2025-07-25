#!/usr/bin/env python3
"""
PROJECT ELDERZAN SecurityLayer - AES-256 Encryption Engine
プロジェクトエルダーザン セキュリティレイヤー - AES-256暗号化エンジン

高性能・高セキュリティAES-256暗号化システム
80%コストカット実現のための最適化暗号化
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import hashlib
import json
import logging
import secrets
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

# 暗号化ライブラリ
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class EncryptionMode(Enum):
    """暗号化モード"""

    AES_256_GCM = "AES-256-GCM"
    AES_256_CBC = "AES-256-CBC"
    FERNET = "Fernet"
    RSA_OAEP = "RSA-OAEP"

class KeyType(Enum):
    """鍵タイプ"""

    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    DERIVED = "derived"

@dataclass
class EncryptionKey:
    """暗号化鍵"""

    key_id: str
    key_type: KeyType
    algorithm: str
    key_data: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def is_expired(self) -> bool:
        """鍵有効期限チェック"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False

@dataclass
class EncryptionResult:
    """暗号化結果"""

    ciphertext: bytes
    key_id: str
    algorithm: str
    nonce: Optional[bytes] = None
    tag: Optional[bytes] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        """__post_init__特殊メソッド"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

class AES256EncryptionEngine:
    """
    AES-256暗号化エンジン

    機能:
    - AES-256-GCM認証付き暗号化
    - 鍵管理・鍵回転
    - 高性能暗号化処理
    - 非同期処理対応
    - キャッシュ最適化
    """

    def __init__(
        self, key_rotation_hours: int = 24, max_workers: int = 4, cache_size: int = 1000
    ):
        """
        暗号化エンジン初期化

        Args:
            key_rotation_hours: 鍵回転間隔（時間）
            max_workers: 並列処理ワーカー数
            cache_size: キャッシュサイズ
        """
        self.key_rotation_hours = key_rotation_hours
        self.max_workers = max_workers
        self.cache_size = cache_size

        # 鍵管理
        self.keys: Dict[str, EncryptionKey] = {}
        self.master_key: Optional[bytes] = None
        self.key_lock = threading.RLock()

        # 並列処理
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # キャッシュ
        self.encryption_cache: Dict[str, EncryptionResult] = {}
        self.cache_lock = threading.RLock()

        # 統計情報
        self.stats = {
            "encryptions": 0,
            "decryptions": 0,
            "key_generations": 0,
            "key_rotations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
        }

        # 初期化
        self._initialize_master_key()

        logger.info("AES256EncryptionEngine initialized successfully")

    def _initialize_master_key(self):
        """マスターキー初期化"""
        try:
            # マスターキー生成（実際の実装では安全な保存が必要）
            self.master_key = secrets.token_bytes(32)  # 256-bit key

            # デフォルト鍵生成
            default_key = self._generate_key("default", KeyType.SYMMETRIC)
            self.keys["default"] = default_key

            logger.info("Master key initialized successfully")

        except Exception as e:
            logger.error(f"Master key initialization failed: {e}")
            raise EncryptionError(f"Master key initialization failed: {e}")

    def _generate_key(
        self, key_id: str, key_type: KeyType, algorithm: str = "AES-256-GCM"
    ) -> EncryptionKey:
        """
        暗号化鍵生成

        Args:
            key_id: 鍵ID
            key_type: 鍵タイプ
            algorithm: 暗号化アルゴリズム

        Returns:
            EncryptionKey: 生成された鍵
        """
        try:
            if key_type == KeyType.SYMMETRIC:
                # 対称鍵生成
                key_data = secrets.token_bytes(32)  # 256-bit
            elif key_type == KeyType.ASYMMETRIC:
                # 非対称鍵生成
                private_key = rsa.generate_private_key(
                    public_exponent=65537, key_size=2048, backend=default_backend()
                )
                key_data = private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            elif key_type == KeyType.DERIVED:
                # 派生鍵生成
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=secrets.token_bytes(16),
                    iterations=100000,
                    backend=default_backend(),
                )
                key_data = kdf.derive(self.master_key)
            else:
                raise ValueError(f"Unsupported key type: {key_type}")

            # 鍵オブジェクト作成
            key = EncryptionKey(
                key_id=key_id,
                key_type=key_type,
                algorithm=algorithm,
                key_data=key_data,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=self.key_rotation_hours),
            )

            self.stats["key_generations"] += 1
            logger.info(f"Key generated: {key_id} ({key_type.value})")

            return key

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Key generation failed: {e}")
            raise EncryptionError(f"Key generation failed: {e}")

    async def encrypt_data(
        self,
        data: Union[str, bytes, Dict[str, Any]],
        key_id: str = "default",
        mode: EncryptionMode = EncryptionMode.AES_256_GCM,
        context: Optional[Dict[str, Any]] = None,
    ) -> EncryptionResult:
        """
        データ暗号化

        Args:
            data: 暗号化対象データ
            key_id: 使用する鍵ID
            mode: 暗号化モード
            context: 暗号化コンテキスト

        Returns:
            EncryptionResult: 暗号化結果
        """
        try:
            # データ正規化
            if isinstance(data, str):
                data_bytes = data.encode("utf-8")
            elif isinstance(data, dict):
                data_bytes = json.dumps(data).encode("utf-8")
            else:
                data_bytes = data

            # キャッシュチェック
            cache_key = self._generate_cache_key(data_bytes, key_id, mode)
            if cache_key in self.encryption_cache:
                self.stats["cache_hits"] += 1
                return self.encryption_cache[cache_key]

            self.stats["cache_misses"] += 1

            # 鍵取得
            key = await self._get_encryption_key(key_id)

            # 暗号化実行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, self._encrypt_with_key, data_bytes, key, mode, context
            )

            # キャッシュ保存
            with self.cache_lock:
                if len(self.encryption_cache) < self.cache_size:
                    self.encryption_cache[cache_key] = result

            self.stats["encryptions"] += 1

            return result

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Data encryption failed: {e}")
            raise EncryptionError(f"Data encryption failed: {e}")

    async def decrypt_data(
        self,
        encrypted_result: EncryptionResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        データ復号化

        Args:
            encrypted_result: 暗号化結果
            context: 復号化コンテキスト

        Returns:
            bytes: 復号化されたデータ
        """
        try:
            # 鍵取得
            key = await self._get_encryption_key(encrypted_result.key_id)

            # 復号化実行
            loop = asyncio.get_event_loop()
            plaintext = await loop.run_in_executor(
                self.executor, self._decrypt_with_key, encrypted_result, key, context
            )

            self.stats["decryptions"] += 1

            return plaintext

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Data decryption failed: {e}")
            raise DecryptionError(f"Data decryption failed: {e}")

    def _encrypt_with_key(
        self,
        data: bytes,
        key: EncryptionKey,
        mode: EncryptionMode,
        context: Optional[Dict[str, Any]] = None,
    ) -> EncryptionResult:
        """鍵を使用した暗号化"""
        try:
            if mode == EncryptionMode.AES_256_GCM:
                # AES-256-GCM暗号化
                nonce = secrets.token_bytes(12)  # 96-bit nonce
                cipher = Cipher(
                    algorithms.AES(key.key_data),
                    modes.GCM(nonce),
                    backend=default_backend(),
                )
                encryptor = cipher.encryptor()

                # 追加認証データ（AAD）
                if context:
                    aad = json.dumps(context, sort_keys=True).encode("utf-8")
                    encryptor.authenticate_additional_data(aad)

                ciphertext = encryptor.update(data) + encryptor.finalize()

                return EncryptionResult(
                    ciphertext=ciphertext,
                    key_id=key.key_id,
                    algorithm=mode.value,
                    nonce=nonce,
                    tag=encryptor.tag,
                    metadata=context,
                )

            elif mode == EncryptionMode.FERNET:
                # Fernet暗号化
                fernet = Fernet(key.key_data)
                ciphertext = fernet.encrypt(data)

                return EncryptionResult(
                    ciphertext=ciphertext,
                    key_id=key.key_id,
                    algorithm=mode.value,
                    metadata=context,
                )

            else:
                raise ValueError(f"Unsupported encryption mode: {mode}")

        except Exception as e:
            logger.error(f"Encryption with key failed: {e}")
            raise EncryptionError(f"Encryption with key failed: {e}")

    def _decrypt_with_key(
        self,
        encrypted_result: EncryptionResult,
        key: EncryptionKey,
        context: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """鍵を使用した復号化"""
        try:
            if encrypted_result.algorithm == EncryptionMode.AES_256_GCM.value:
                # AES-256-GCM復号化
                cipher = Cipher(
                    algorithms.AES(key.key_data),
                    modes.GCM(encrypted_result.nonce, encrypted_result.tag),
                    backend=default_backend(),
                )
                decryptor = cipher.decryptor()

                # 追加認証データ（AAD）
                if encrypted_result.metadata:
                    aad = json.dumps(encrypted_result.metadata, sort_keys=True).encode(
                        "utf-8"
                    )
                    decryptor.authenticate_additional_data(aad)

                plaintext = (
                    decryptor.update(encrypted_result.ciphertext) + decryptor.finalize()
                )

                return plaintext

            elif encrypted_result.algorithm == EncryptionMode.FERNET.value:
                # Fernet復号化
                fernet = Fernet(key.key_data)
                plaintext = fernet.decrypt(encrypted_result.ciphertext)

                return plaintext

            else:
                raise ValueError(
                    f"Unsupported decryption algorithm: {encrypted_result.algorithm}"
                )

        except Exception as e:
            logger.error(f"Decryption with key failed: {e}")
            raise DecryptionError(f"Decryption with key failed: {e}")

    async def _get_encryption_key(self, key_id: str) -> EncryptionKey:
        """暗号化鍵取得"""
        try:
            with self.key_lock:
                key = self.keys.get(key_id)

                if not key:
                    # 鍵が存在しない場合は生成
                    key = self._generate_key(key_id, KeyType.SYMMETRIC)
                    self.keys[key_id] = key

                # 鍵有効期限チェック
                if key.is_expired():
                    # 鍵回転実行
                    await self._rotate_key(key_id)
                    key = self.keys[key_id]

                return key

        except Exception as e:
            logger.error(f"Key retrieval failed: {e}")
            raise EncryptionError(f"Key retrieval failed: {e}")

    async def _rotate_key(self, key_id: str):
        """鍵回転"""
        try:
            with self.key_lock:
                old_key = self.keys.get(key_id)
                if old_key:
                    # 新しい鍵生成
                    new_key = self._generate_key(
                        key_id, old_key.key_type, old_key.algorithm
                    )
                    self.keys[key_id] = new_key

                    # 古い鍵をバックアップ（実際の実装では安全な保存が必要）
                    backup_key_id = (
                        f"{key_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                    self.keys[backup_key_id] = old_key

                    self.stats["key_rotations"] += 1
                    logger.info(f"Key rotated: {key_id}")

        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise EncryptionError(f"Key rotation failed: {e}")

    def _generate_cache_key(
        self, data: bytes, key_id: str, mode: EncryptionMode
    ) -> str:
        """キャッシュキー生成"""
        hasher = hashlib.sha256()
        hasher.update(data)
        hasher.update(key_id.encode("utf-8"))
        hasher.update(mode.value.encode("utf-8"))
        return hasher.hexdigest()

    async def create_key(
        self,
        key_id: str,
        key_type: KeyType = KeyType.SYMMETRIC,
        algorithm: str = "AES-256-GCM",
    ) -> EncryptionKey:
        """新しい鍵作成"""
        try:
            with self.key_lock:
                if key_id in self.keys:
                    raise ValueError(f"Key already exists: {key_id}")

                key = self._generate_key(key_id, key_type, algorithm)
                self.keys[key_id] = key

                logger.info(f"Key created: {key_id}")
                return key

        except Exception as e:
            logger.error(f"Key creation failed: {e}")
            raise EncryptionError(f"Key creation failed: {e}")

    async def delete_key(self, key_id: str):
        """鍵削除"""
        try:
            with self.key_lock:
                if key_id in self.keys:
                    del self.keys[key_id]
                    logger.info(f"Key deleted: {key_id}")
                else:
                    logger.warning(f"Key not found: {key_id}")

        except Exception as e:
            logger.error(f"Key deletion failed: {e}")
            raise EncryptionError(f"Key deletion failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            "encryption_stats": self.stats.copy(),
            "active_keys": len(self.keys),
            "cache_size": len(self.encryption_cache),
            "timestamp": datetime.now().isoformat(),
        }

    async def shutdown(self):
        """暗号化エンジンシャットダウン"""
        logger.info("AES256EncryptionEngine shutting down...")

        # エグゼキューターシャットダウン
        self.executor.shutdown(wait=True)

        # キャッシュクリア
        with self.cache_lock:
            self.encryption_cache.clear()

        # 鍵削除（実際の実装では安全な削除が必要）
        with self.key_lock:
            self.keys.clear()

        logger.info("AES256EncryptionEngine shut down successfully")

# 例外クラス
class EncryptionError(Exception):
    """暗号化エラー"""

    pass

class DecryptionError(Exception):
    """復号化エラー"""

    pass
