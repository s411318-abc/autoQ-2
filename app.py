"""
動詞 & 名詞 智慧抽籤器 - 本機伺服器 (Local Runner & Vercel Preview)
可在本機直接執行，亦與 Vercel 雲端部署架構完全一致相容。
"""

import sys
import os
import json
import socket
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading

import importer

# 根目錄與檔案路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_FILE = os.path.join(BASE_DIR, "public", "index.html")
if not os.path.exists(INDEX_FILE):
    INDEX_FILE = os.path.join(BASE_DIR, "index.html")

class LocalRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # 簡化日誌輸出
        pass

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

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
        path = parsed.path

        if path in ("/", "/index.html"):
            if os.path.exists(INDEX_FILE):
                with open(INDEX_FILE, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()

        elif path in ("/api", "/api/words", "/api/index"):
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
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip('/')

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            req_data = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            req_data = {}

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

def find_free_port(start_port=8080, max_port=8180):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def start_server():
    port = find_free_port(8080)
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, LocalRequestHandler)
    url = f"http://127.0.0.1:{port}"
    print("=" * 60)
    print("🎯 動詞 & 名詞 智慧抽籤器 (本機與 Vercel 相容版) 已啟動！")
    print(f"👉 請開啟瀏覽器訪問：{url}")
    print("👉 按下鍵盤 Ctrl + C 可停止伺服器")
    print("=" * 60)
    
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已正常停止。")
        httpd.server_close()

if __name__ == "__main__":
    start_server()
