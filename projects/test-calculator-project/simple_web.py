#!/usr/bin/env python3
"""
Test Project - 簡単なWebインターフェース
"""

from flask import Flask, render_template_string, request, jsonify
import sys
import os

# 計算機モジュールをインポート
sys.path.append(os.path.dirname(__file__))
from calculator import add, multiply, Calculator

app = Flask(__name__)

# HTMLテンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧮 Test Project - 計算機デモ</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(31,38,135,0.3);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .calc-section {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select, button {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        input, select {
            background: rgba(255,255,255,0.9);
            color: #333;
        }
        button {
            background: #4CAF50;
            color: white;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
        }
        button:hover {
            background: #45a049;
        }
        .result {
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 18px;
            font-weight: bold;
            text-align: center;
        }
        .history {
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .history h3 {
            margin-top: 0;
        }
        .history-item {
            background: rgba(255,255,255,0.1);
            padding: 8px;
            margin: 5px 0;
            border-radius: 5px;
            font-family: monospace;
        }
        .flex-group {
            display: flex;
            gap: 10px;
        }
        .flex-group > div {
            flex: 1;
        }
        .project-info {
            text-align: center;
            margin-top: 30px;
            font-size: 14px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧮 Test Project Calculator</h1>
        
        <div class="calc-section">
            <h2>🔢 基本計算</h2>
            <form id="calcForm">
                <div class="flex-group">
                    <div class="form-group">
                        <label for="num1">数値 A:</label>
                        <input type="number" id="num1" name="num1" step="any" required>
                    </div>
                    <div class="form-group">
                        <label for="operation">操作:</label>
                        <select id="operation" name="operation">
                            <option value="add">足し算 (+)</option>
                            <option value="multiply">掛け算 (×)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="num2">数値 B:</label>
                        <input type="number" id="num2" name="num2" step="any" required>
                    </div>
                </div>
                <button type="submit">計算実行</button>
            </form>
            
            <div id="result" class="result" style="display: none;"></div>
        </div>
        
        <div class="history">
            <h3>📊 計算履歴</h3>
            <div id="history-list">
                <p style="text-align: center; opacity: 0.7;">まだ計算履歴がありません</p>
            </div>
        </div>
        
        <div class="project-info">
            <p>🏛️ <strong>エルダーズギルド</strong> - Test Project</p>
            <p>📍 パス: /home/aicompany/ai_co/test_project/</p>
            <p>🔧 技術: Python + Flask + Calculator Module</p>
            <p>🎯 用途: TDD学習・テスト実装の実習</p>
        </div>
    </div>

    <script>
        const calcForm = document.getElementById('calcForm');
        const resultDiv = document.getElementById('result');
        const historyList = document.getElementById('history-list');

        calcForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(calcForm);
            const data = {
                num1: parseFloat(formData.get('num1')),
                num2: parseFloat(formData.get('num2')),
                operation: formData.get('operation')
            };
            
            try {
                const response = await fetch('/calculate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    resultDiv.innerHTML = `
                        <div>
                            <strong>結果: ${result.result}</strong><br>
                            <small>${result.operation_display}</small>
                        </div>
                    `;
                    resultDiv.style.display = 'block';
                    updateHistory();
                } else {
                    resultDiv.innerHTML = `
                        <div style="color: #ff6b6b;">
                            <strong>エラー: ${result.error}</strong>
                        </div>
                    `;
                    resultDiv.style.display = 'block';
                }
            } catch (error) {
                resultDiv.innerHTML = `
                    <div style="color: #ff6b6b;">
                        <strong>エラー: ${error.message}</strong>
                    </div>
                `;
                resultDiv.style.display = 'block';
            }
        });
        
        async function updateHistory() {
            try {
                const response = await fetch('/history');
                const data = await response.json();
                
                if (data.history && data.history.length > 0) {
                    historyList.innerHTML = data.history
                        .slice(-10)  // 最新10件
                        .reverse()   // 新しい順
                        .map(item => `<div class="history-item">${item}</div>`)
                        .join('');
                } else {
                    historyList.innerHTML = '<p style="text-align: center; opacity: 0.7;">まだ計算履歴がありません</p>';
                }
            } catch (error) {
                console.error('履歴取得エラー:', error);
            }
        }
        
        // ページ読み込み時に履歴を取得
        updateHistory();
    </script>
</body>
</html>
"""

# グローバル計算機インスタンス
calc = Calculator()

@app.route('/')
def index():
    """メインページ"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/calculate', methods=['POST'])
def calculate():
    """計算API"""
    try:
        data = request.json
        num1 = float(data['num1'])
        num2 = float(data['num2'])
        operation = data['operation']
        
        result = calc.calculate(operation, num1, num2)
        
        operation_symbols = {
            'add': '+',
            'multiply': '×'
        }
        
        return jsonify({
            'success': True,
            'result': result,
            'operation_display': f"{num1} {operation_symbols.get(operation, '?')} {num2} = {result}"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/history')
def get_history():
    """計算履歴API"""
    return jsonify({
        'history': calc.history
    })

@app.route('/health')
def health():
    """ヘルスチェック"""
    return jsonify({
        'status': 'healthy',
        'project': 'Test Project Calculator',
        'path': '/home/aicompany/ai_co/test_project/',
        'functions': ['add', 'multiply', 'Calculator class']
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9002, debug=True)