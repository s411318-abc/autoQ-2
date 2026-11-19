"""
Vercel Serverless Function 進入點 (Entry Point)
處理 API 路由請求，包含 Google 文件下載與詞庫解析，並提供 CORS 支援。
"""

import sys
import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

# 確保能引用同目錄及上一層模組
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

try:
    import importer
except ImportError:
    from api import importer

class handler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')

        # 預設資訊與詞庫清單
        if path in ("", "/api", "/api/words", "/api/index"):
            data = {
                "status": "online",
                "default_verbs": importer.DEFAULT_VERBS,
                "default_nouns": importer.DEFAULT_NOUNS,
                "total_default_words": len(importer.DEFAULT_VERBS) + len(importer.DEFAULT_NOUNS),
                "message": "動詞與名詞智慧抽籤器 API 運作中"
            }
            self._send_json(data)
        elif path == "/api/health":
            self._send_json({"status": "healthy"})
        else:
            self._send_json({"error": f"找不到端點: {path}"}, status=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            req_data = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            req_data = {}

        # Google Docs 雲端匯入端點
        if path in ("/api/import-google-doc", "/api/import", "/api"):
            url = req_data.get("url", "").strip()
            if not url:
                self._send_json({"error": "請提供有效的 Google 文件網址或 ID！"}, status=400)
                return

            try:
                content = importer.fetch_google_doc_text(url)
                verbs, nouns = importer.parse_word_bank(content)

                if not verbs and not nouns:
                    self._send_json({
                        "error": "從文件中未解析出任何動詞或名詞！\n請確認文件是否有標註 [動詞] 與 [名詞] 區塊。"
                    }, status=400)
                    return

                self._send_json({
                    "success": True,
                    "verbs": verbs,
                    "nouns": nouns,
                    "verbs_count": len(verbs),
                    "nouns_count": len(nouns)
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)

        # 詞庫解析 (直接傳送純文字內容進行解析)
        elif path == "/api/parse-text":
            text = req_data.get("text", "")
            verbs, nouns = importer.parse_word_bank(text)
            self._send_json({
                "success": True,
                "verbs": verbs,
                "nouns": nouns,
                "verbs_count": len(verbs),
                "nouns_count": len(nouns)
            })

        else:
            self._send_json({"error": f"未知的 POST 端點: {path}"}, status=404)
