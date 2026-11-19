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

        # 預設資訊與詞庫清單 (相容 Vercel rewrite /api/index.py 等各種路徑)
        if "health" in path:
            self._send_json({"status": "healthy"})
        else:
            data = {
                "status": "online",
                "default_gdoc_url": getattr(importer, "DEFAULT_GDOC_URL", "https://docs.google.com/document/d/166VTPgMpxjcHDP52zTFJGpnnewSKVIQAelxabE0jsH0/edit?tab=t.0"),
                "default_verbs": importer.DEFAULT_VERBS,
                "default_nouns": importer.DEFAULT_NOUNS,
                "default_sentences": getattr(importer, "DEFAULT_SENTENCES", []),
                "total_default_words": len(importer.DEFAULT_VERBS) + len(importer.DEFAULT_NOUNS),
                "total_default_sentences": len(getattr(importer, "DEFAULT_SENTENCES", [])),
                "message": "動詞與名詞智慧抽籤器 API 運作中"
            }
            self._send_json(data)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            req_data = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            req_data = {}

        # 詞庫解析 (直接傳送純文字內容)
        if "text" in req_data or "parse-text" in path:
            text = req_data.get("text", "")
            verbs, nouns, sentences = importer.parse_word_bank(text)
            self._send_json({
                "success": True,
                "verbs": verbs,
                "nouns": nouns,
                "sentences": sentences,
                "verbs_count": len(verbs),
                "nouns_count": len(nouns),
                "sentences_count": len(sentences)
            })
            return

        # Google Docs 雲端匯入端點
        # 相容 /api/index.py (Vercel rewrite)、/api/import-google-doc、/api/import、/api 等
        if "url" in req_data or "import" in path or path in ("/api/index.py", "/api/index", "/api", ""):
            url = req_data.get("url", "").strip() or getattr(importer, "DEFAULT_GDOC_URL", "")
            if not url:
                self._send_json({"error": "請提供有效的 Google 文件網址或 ID！"}, status=400)
                return

            try:
                content = importer.fetch_google_doc_text(url)
                verbs, nouns, sentences = importer.parse_word_bank(content)

                if not verbs and not nouns and not sentences:
                    self._send_json({
                        "error": "從文件中未解析出任何動詞、名詞或句子！\n請確認文件是否有標註 [動詞]、[名詞] 或 [句子] 區塊。"
                    }, status=400)
                    return

                self._send_json({
                    "success": True,
                    "verbs": verbs,
                    "nouns": nouns,
                    "sentences": sentences,
                    "verbs_count": len(verbs),
                    "nouns_count": len(nouns),
                    "sentences_count": len(sentences)
                })
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return

        self._send_json({"error": f"未知的 POST 端點: {path}"}, status=404)
