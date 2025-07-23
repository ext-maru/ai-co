#!/usr/bin/env python3
"""
GitHub API Base Class

GitHub API実装の基底クラス
"""

import logging
import requests
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class GitHubAPIBase:
    """GitHub API実装の基底クラス"""
    
    def __init__(self, token: str, repo_owner: str, repo_name: str):
        """
        初期化
        
        Args:
            token: GitHub Personal Access Token
            repo_owner: リポジトリオーナー
            repo_name: リポジトリ名
        """
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        self.logger = logger
        
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        GitHub APIリクエストを実行
        
        Args:
            method: HTTPメソッド
            endpoint: APIエンドポイント
            data: リクエストデータ
            
        Returns:
            レスポンスデータ
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
                
            if response.status_code in [200, 201, 204]:
                return {"success": True, "data": response.json() if response.content else {}}
            else:
                error_msg = f"GitHub API error: {response.status_code}"
                if response.content:
                    try:
                        error_data = response.json()
                        error_msg = f"{error_msg} - {error_data.get('message', 'Unknown error')}"
                    except:
                        pass
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    def _make_api_request(
        self,
        endpoint: str,
        method: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        GitHub APIリクエスト（create_pull_request.py互換インターフェース）
        
        Args:
            endpoint: APIエンドポイント
            method: HTTPメソッド
            json_data: JSONリクエストデータ
            params: クエリパラメータ
            
        Returns:
            レスポンスデータ
        """
        data = json_data if method.upper() in ['POST', 'PUT', 'PATCH'] else params
        return self._make_request(method, endpoint, data)