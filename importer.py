"""
Google 文件匯入與詞庫解析模組
支援從 Google Docs 公開連結或文字內容解析動詞與名詞詞庫。
"""

import re
import urllib.request
import urllib.error
import ssl

DEFAULT_VERBS = [
    "奔跑", "跳躍", "飛翔", "思考", "凝視", "探索", "歌唱", "燃燒",
    "綻放", "流浪", "傾聽", "繪製", "追逐", "擁抱", "等待", "發明",
    "漂浮", "穿梭", "喚醒", "守護", "編織", "閃爍", "跨越", "紀錄"
]

DEFAULT_NOUNS = [
    "貓咪", "夢想", "星星", "微風", "海浪", "時光", "宇宙", "火焰",
    "森林", "影子", "雨滴", "記憶", "旅人", "秘密", "指南針", "島嶼",
    "咖啡", "夕陽", "花瓣", "地圖", "音符", "羽毛", "微笑", "燈塔"
]

def extract_doc_id(url_or_id: str) -> str:
    """從 Google Docs 網址或字串中提取 Document ID"""
    text = url_or_id.strip()
    # 支援標準 Google Doc 網址格式:
    # https://docs.google.com/document/d/1xxxxxx-xxxx/edit...
    match = re.search(r'docs\.google\.com/document/d/([a-zA-Z0-9_-]+)', text)
    if match:
        return match.group(1)
    
    # 支援發布到網路格式:
    # https://docs.google.com/document/d/e/2PACX-xxxx/pub
    match_pub = re.search(r'docs\.google\.com/document/d/e/([a-zA-Z0-9_-]+)', text)
    if match_pub:
        return match_pub.group(1)
    
    # 如果使用者直接輸入 ID (英數字、底線、減號)
    if re.match(r'^[a-zA-Z0-9_-]{20,}$', text):
        return text
    
    return text

def fetch_google_doc_text(doc_url_or_id: str) -> str:
    """
    從 Google 文件下載純文字內容。
    要求：該 Google 文件的共用權限必須設為「知道連結的任何人都能查看」。
    """
    doc_id = extract_doc_id(doc_url_or_id)
    
    # 若是發布到網路的 URL
    if "docs.google.com/document/d/e/" in doc_url_or_id:
        export_url = doc_url_or_id
        if not export_url.endswith('/pub'):
            export_url = export_url.rstrip('/') + '/pub'
    else:
        export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

    req = urllib.request.Request(
        export_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=12) as response:
            final_url = response.geturl()
            # 檢查是否被重導向至 Google 登入頁面
            if "accounts.google.com" in final_url or "ServiceLogin" in final_url:
                raise PermissionError(
                    "無法讀取文件：該 Google 文件未開啟公開存取！\n"
                    "請在 Google 文件右上角點選『共用』按鈕，將『一般存取權』改為『知道連結的任何人都可以查看』。"
                )
            
            raw_bytes = response.read()
            
            # 嘗試 UTF-8 (含 BOM 處理)
            try:
                content = raw_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                content = raw_bytes.decode('utf-8', errors='replace')
                
            # 檢查內容是否是 HTML 登入/錯誤頁面
            if "<html" in content.lower() and ("sign in" in content.lower() or "accounts.google.com" in content):
                raise PermissionError(
                    "無法讀取文件：該 Google 文件需要登入權限！\n"
                    "請在 Google 文件右上角點選『共用』，設定為『知道連結的任何人都可以查看』。"
                )
                
            return content

    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise PermissionError(
                "權限不足：該 Google 文件未公開！請至 Google 文件設定共用權限為『知道連結的任何人』。"
            )
        elif e.code == 404:
            raise FileNotFoundError(f"找不到該 Google 文件 (HTTP 404)，請檢查文件 ID 或網址是否正確。")
        else:
            raise RuntimeError(f"下載失敗 (HTTP 狀態碼: {e.code})：{e.reason}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"網路連線失敗：{e.reason}，請確認網路連線是否正常。")


def clean_word(word: str) -> str:
    """清理單詞中的標點、序號與空白"""
    # 去除序號如 1. 1、 (1) - * •
    w = re.sub(r'^(?:[\d]+[\.、\)]|[\-\*•\(\)（）])\s*', '', word.strip())
    # 去除引號、括號等
    w = w.strip(' \t\n\r"\'“”‘’[]【】()（）{}')
    return w

def parse_word_bank(content: str) -> tuple[list[str], list[str]]:
    """
    智慧解析文字內容為 (動詞列表, 名詞列表)
    支援多種格式：
    1. 區塊標題式：
       [動詞]
       奔跑
       跳躍
       [名詞]
       貓咪
       夢想
    2. 標籤冒號式：
       動詞：跑, 跳, 飛
       名詞：貓, 狗, 鳥
    3. 雙欄/表格式：
       動詞    名詞
       奔跑    貓咪
       飛翔    夢想
    """
    verbs = []
    nouns = []
    current_section = None
    
    lines = content.splitlines()
    
    # 檢查是否為雙欄表頭格式 (例如 第一行包含 動詞 和 名詞)
    is_table_mode = False
    v_col_idx = -1
    n_col_idx = -1
    
    for idx, line in enumerate(lines[:10]):
        cleaned = line.strip()
        if not cleaned:
            continue
        cols = [c.strip() for c in re.split(r'[\t,|｜]+', cleaned) if c.strip()]
        has_v = any('動詞' in c or 'verb' in c.lower() for c in cols)
        has_n = any('名詞' in c or 'noun' in c.lower() for c in cols)
        if has_v and has_n:
            is_table_mode = True
            for i, c in enumerate(cols):
                if '動詞' in c or 'verb' in c.lower():
                    v_col_idx = i
                elif '名詞' in c or 'noun' in c.lower():
                    n_col_idx = i
            # 表頭之後的行以雙欄方式讀取
            lines = lines[idx+1:]
            break
            
    if is_table_mode and v_col_idx != -1 and n_col_idx != -1:
        for line in lines:
            if not line.strip():
                continue
            cols = [clean_word(c) for c in re.split(r'[\t,|｜]+', line.strip())]
            if len(cols) > v_col_idx:
                v = clean_word(cols[v_col_idx])
                if v and not ('動詞' in v or 'verb' in v.lower()):
                    verbs.append(v)
            if len(cols) > n_col_idx:
                n = clean_word(cols[n_col_idx])
                if n and not ('名詞' in n or 'noun' in n.lower()):
                    nouns.append(n)
        return list(dict.fromkeys(verbs)), list(dict.fromkeys(nouns))

    # 傳統區塊 / 標籤行解析
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # 匹配動詞區塊標題
        v_header_match = re.match(
            r'^(?:#+\s*)?(?:\[|【)?(?:\s*動詞\s*|Verbs?)(?:\]|】)?(?:\s*[:：])?(.*)$',
            line_clean,
            re.IGNORECASE
        )
        # 匹配名詞區塊標題
        n_header_match = re.match(
            r'^(?:#+\s*)?(?:\[|【)?(?:\s*名詞\s*|Nouns?)(?:\]|】)?(?:\s*[:：])?(.*)$',
            line_clean,
            re.IGNORECASE
        )
        
        if v_header_match:
            current_section = 'verb'
            rest = v_header_match.group(1).strip()
            if rest:
                items = re.split(r'[,，、;；\s\t/]+', rest)
                for item in items:
                    c = clean_word(item)
                    if c:
                        verbs.append(c)
            continue
            
        if n_header_match:
            current_section = 'noun'
            rest = n_header_match.group(1).strip()
            if rest:
                items = re.split(r'[,，、;；\s\t/]+', rest)
                for item in items:
                    c = clean_word(item)
                    if c:
                        nouns.append(c)
            continue
            
        # 當前在某個區塊內
        if current_section:
            items = re.split(r'[,，、;；\t]+', line_clean)
            for item in items:
                sub_items = item.split()
                for sub in sub_items:
                    c = clean_word(sub)
                    if c:
                        if current_section == 'verb':
                            verbs.append(c)
                        elif current_section == 'noun':
                            nouns.append(c)
                            
    # 去重且保留原有順序
    verbs = list(dict.fromkeys(verbs))
    nouns = list(dict.fromkeys(nouns))
    
    return verbs, nouns
