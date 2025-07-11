#!/usr/bin/env python3
"""
Mock API Server for Upload Image Service Frontend Testing
"""
import json
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import uuid

class MockAPIHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)

        # Health check
        if parsed_path.path == '/health':
            self.send_json_response({"status": "ok"})
            return

        # Get sessions list
        if parsed_path.path == '/api/v1/submission/admin/sessions':
            sessions = [
                {
                    "id": "session_001",
                    "submitter_name": "田中太郎",
                    "submitter_email": "tanaka@example.com",
                    "submission_type": "individual",
                    "status": "not_uploaded",
                    "description": "個人契約者用書類の提出",
                    "created_at": "2025-07-11T10:00:00Z",
                    "uploaded_files": []
                },
                {
                    "id": "session_002",
                    "submitter_name": "佐藤商事株式会社",
                    "submitter_email": "sato@example.com",
                    "submission_type": "corporate",
                    "status": "needs_reupload",
                    "description": "法人契約者用書類の提出",
                    "created_at": "2025-07-11T09:30:00Z",
                    "uploaded_files": [
                        {
                            "filename": "登記簿謄本.pdf",
                            "size": 1024000,
                            "uploaded_at": "2025-07-11T10:15:00Z"
                        }
                    ]
                },
                {
                    "id": "session_003",
                    "submitter_name": "山田花子",
                    "submitter_email": "yamada@example.com",
                    "submission_type": "individual",
                    "status": "approved",
                    "description": "個人契約者用書類の提出",
                    "created_at": "2025-07-11T08:00:00Z",
                    "uploaded_files": [
                        {
                            "filename": "身分証明書.jpg",
                            "size": 512000,
                            "uploaded_at": "2025-07-11T08:30:00Z"
                        },
                        {
                            "filename": "住民票.pdf",
                            "size": 256000,
                            "uploaded_at": "2025-07-11T08:35:00Z"
                        }
                    ]
                }
            ]
            self.send_json_response({"sessions": sessions})
            return

        # Get specific session
        if parsed_path.path.startswith('/api/v1/submission/sessions/'):
            session_id = parsed_path.path.split('/')[-1]
            session = {
                "id": session_id,
                "submitter_name": "テスト提出者",
                "submitter_email": "test@example.com",
                "submission_type": "individual",
                "status": "not_uploaded",
                "description": "テスト用セッション",
                "created_at": "2025-07-11T12:00:00Z",
                "uploaded_files": []
            }
            self.send_json_response(session)
            return

        # Google Drive settings
        if parsed_path.path == '/api/v1/admin/google-drive/settings':
            settings = {
                "google_drive_enabled": False,
                "google_drive_parent_folder_id": "",
                "google_drive_folder_name_format": "[{session_id}]_{submitter_name}",
                "google_drive_auto_create_folders": True,
                "google_drive_share_with_submitter": True,
                "credentials_uploaded": False
            }
            self.send_json_response(settings)
            return

        # Google Drive connection test
        if parsed_path.path == '/api/v1/admin/google-drive/test-connection':
            status = {
                "connected": False,
                "error": "認証ファイルが設定されていません"
            }
            self.send_json_response(status)
            return

        # Default 404
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)

        # Create session
        if parsed_path.path == '/api/v1/submission/sessions':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            session_id = f"session_{str(uuid.uuid4())[:8]}"
            response = {
                "session_id": session_id,
                "message": "セッションが作成されました",
                "url": f"/submission/{session_id}"
            }
            self.send_json_response(response)
            return

        # Upload files
        if parsed_path.path.startswith('/api/v1/submission/sessions/') and parsed_path.path.endswith('/upload'):
            # For file uploads, we just mock the response since parsing multipart is complex
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    # Read the body to prevent connection issues
                    post_data = self.rfile.read(content_length)

                response = {
                    "message": "ファイルのアップロードが完了しました",
                    "uploaded_files": [
                        {
                            "filename": "test_document.pdf",
                            "size": 1024000,
                            "uploaded_at": "2025-07-11T12:00:00Z"
                        }
                    ]
                }
                self.send_json_response(response)
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {"error": f"Upload failed: {str(e)}"}
                self.wfile.write(json.dumps(error_response).encode('utf-8'))
                return

        # Google Drive test connection
        if parsed_path.path == '/api/v1/admin/google-drive/test-connection':
            response = {
                "connected": True,
                "message": "接続テストが成功しました",
                "folder_name": "テストフォルダ"
            }
            self.send_json_response(response)
            return

        # Default 404
        self.send_response(404)
        self.end_headers()

    def do_PUT(self):
        """Handle PUT requests"""
        parsed_path = urlparse(self.path)

        # Update session status
        if '/status' in parsed_path.path:
            response = {
                "message": "ステータスが更新されました"
            }
            self.send_json_response(response)
            return

        # Update Google Drive settings
        if parsed_path.path == '/api/v1/admin/google-drive/settings':
            response = {
                "message": "設定が保存されました"
            }
            self.send_json_response(response)
            return

        # Default 404
        self.send_response(404)
        self.end_headers()

    def send_json_response(self, data):
        """Send JSON response with CORS headers"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        """Log requests"""
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def run_server(port=8001):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MockAPIHandler)
    print(f"🚀 Mock API Server running on http://localhost:{port}")
    print("📋 Available endpoints:")
    print("  GET  /health")
    print("  GET  /api/v1/submission/admin/sessions")
    print("  POST /api/v1/submission/sessions")
    print("  GET  /api/v1/submission/sessions/{id}")
    print("  POST /api/v1/submission/sessions/{id}/upload")
    print("  PUT  /api/v1/submission/sessions/{id}/status")
    print("  GET  /api/v1/admin/google-drive/settings")
    print("  PUT  /api/v1/admin/google-drive/settings")
    print("  GET  /api/v1/admin/google-drive/test-connection")
    print("  POST /api/v1/admin/google-drive/test-connection")
    print("")
    print("Press Ctrl+C to stop the server")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.shutdown()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    run_server(port)
