from flask import Flask, request, jsonify, redirect
from urllib.parse import urlencode
from .oauth_provider import OAuth2Provider
from .models import OAuthClient

app = Flask(__name__)
oauth_provider = OAuth2Provider()

@app.route('/oauth/authorize', methods=['GET'])
def authorize():
    """認可エンドポイント"""
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    response_type = request.args.get('response_type')
    scope = request.args.get('scope', '')
    state = request.args.get('state', '')

    # クライアント検証
    client = oauth_provider.clients.get(client_id)
    if not client:
        return jsonify({"error": "invalid_client"}), 400

    if redirect_uri not in client.redirect_uris:
        return jsonify({"error": "invalid_redirect_uri"}), 400

    # ユーザー認証（簡略化）
    user_id = "authenticated_user"

    # 認可コード生成
    code = oauth_provider.generate_authorization_code(
        client_id, user_id, redirect_uri, scope
    )

    # リダイレクト
    params = {"code": code}
    if state:
        params["state"] = state

    redirect_url = f"{redirect_uri}?{urlencode(params)}"
    return redirect(redirect_url)

@app.route('/oauth/token', methods=['POST'])
def token():
    """トークンエンドポイント"""
    grant_type = request.form.get('grant_type')

    if grant_type == 'authorization_code':
        code = request.form.get('code')
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')

        token = oauth_provider.exchange_code_for_token(
            code, client_id, client_secret
        )

        if not token:
            return jsonify({"error": "invalid_grant"}), 400

        return jsonify({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "token_type": token.token_type,
            "expires_in": token.expires_in,
            "scope": token.scope
        })

    return jsonify({"error": "unsupported_grant_type"}), 400

@app.route('/api/user', methods=['GET'])
def get_user():
    """保護されたリソース"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"error": "invalid_token"}), 401

    token = auth_header[7:]
    if not oauth_provider.validate_token(token):
        return jsonify({"error": "invalid_token"}), 401

    return jsonify({
        "id": "user123",
        "name": "Test User",
        "email": "user@example.com"
    })
