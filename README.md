# 🎯 動詞 & 名詞 智慧抽籤器 (支援 Vercel 雲端部署版)

專門為抽選動詞與名詞設計的智慧抽籤工具，支援**兩種抽法**（混抽、"動詞" 的 "名詞" 句型）、**從 Google 文件雲端匯入**，並已完整設定好 **Vercel 一鍵雲端部署**！

---

## ☁️ 如何部署至 Vercel

本專案已配置好 Vercel Serverless 與靜態前端架構，可直接上傳部署：

### 方法一：透過 GitHub + Vercel 網頁控制台（最推薦）
1. 將本專案資料夾推送到您的 **GitHub** 儲存庫。
2. 開啟 [Vercel 官網 (vercel.com)](https://vercel.com/)，點擊 **「Add New...」->「Project」**。
3. 匯入剛才建立的 GitHub 專案。
4. **專案設定**（Framework Preset 維持 `Other`，根目錄維持預設），直接點擊 **「Deploy」**！
5. 部署完成後，即可獲得一個專屬的網址（如 `https://your-project.vercel.app`），手機與電腦隨時隨地都能使用！

### 方法二：透過 Vercel CLI 命令列部署
如果您有安裝 Node.js，在專案目錄下開啟終端機執行：
```bash
npx vercel
```
按照終端機提示登入並確認預設設定，即可在 1 分鐘內完成部署！

---

## ✨ 功能特色

### 1. 三種抽籤模式
* **🎲 模式一：混在一起抽**
  * 將詞庫中的「動詞」與「名詞」全部放在同一個池子中隨機抽取。
  * 可自由勾選是否顯示詞性標籤（如：`奔跑（動詞）`、`貓咪（名詞）`）。
* **🔀 模式二：隨機組裝句子**
  * 每次各抽取一個動詞與一個名詞，結合成完整的想像語句。
  * 支援多種預設格式：帶雙引號 `"{verb}" 的 "{noun}"`、緊湊句型、自訂句型等。
* **📄 模式三：抽取完整句子 (`"動詞"的"名詞"`)**
  * 從**獨立的完整句子 Google 文件**讀取並隨機抽取完整句子，自動規範為 `"動詞"的"名詞"` 格式。

### 2. 多元詞庫匯入與管理
* **🌐 Google 文件雲端匯入**：
  * 只需將 Google 文件設為「知道連結的任何人皆可查看」，貼上網址即可一鍵同步。
  * 由 Vercel 伺服器端無縫代理抓取，免除跨網域（CORS）阻擋問題。
* **📂 本機 TXT 檔案匯入**：支援直接選擇電腦中的文字檔上傳。
* **✏️ 線上即時編輯**：可直接在網頁上編輯動詞與名詞，儲存後自動保存在瀏覽器（LocalStorage），重整頁面不遺失。

### 3. 高效體驗與歷史紀錄
* **極速抽籤**：前端毫秒級即時反應，配備卡片彈出動畫與和弦音效。
* **重複機制**：支援放回抽籤，或「不重複抽取」（抽完自動循環重設池子）。
* **歷史記錄**：自動記錄過去抽籤歷程，支援一鍵複製全部結果。

---

## 💻 本地離線執行方式（免聯網/免部署）

如果您想在自己的電腦上直接執行，本專案依舊支援：

### 方式一：直接雙擊捷徑啟動（Windows）
* 雙擊 [`啟動抽籤程式-網頁版.bat`](file:///d:/411318/auto%20Q/啟動抽籤程式-網頁版.bat)：本地自動開啟瀏覽器。
* 雙擊 [`啟動抽籤程式-視窗版.bat`](file:///d:/411318/auto%20Q/啟動抽籤程式-視窗版.bat)：開啟桌面原生視窗。

### 方式二：命令列啟動
```bash
# 啟動網頁版
python app.py

# 或啟動桌面視窗版
python gui.py
```

---

## 🌐 Google 文件匯入設定指引

### 1. 文件的內容格式範例（可參考 [詞庫範本.txt](file:///d:/411318/auto%20Q/詞庫範本.txt)）
```text
[動詞]
奔跑
跳躍
飛翔
思考、創造、歌唱

[名詞]
貓咪
夢想
星星
微風、雨滴、影子
```
*(系統亦相容逗號、頓號、項目清單與雙欄表格格式)*

### 2. 開啟共用權限
1. 在 Google 文件右上角點選**「共用」**。
2. 將「一般存取權」改為**「知道連結的任何人」**（檢視者）。
3. 複製連結並貼入抽籤系統的匯入框中，點選**「立即匯入」**！

> 🔗 **專案預設綁定之 Google 文件**：  
> * **動詞 & 名詞詞庫文件**：[https://docs.google.com/document/d/166VTPgMpxjcHDP52zTFJGpnnewSKVIQAelxabE0jsH0/edit?tab=t.0](https://docs.google.com/document/d/166VTPgMpxjcHDP52zTFJGpnnewSKVIQAelxabE0jsH0/edit?tab=t.0)  
> * **完整句子獨立文件（模式三）**：[https://docs.google.com/document/d/1LTPxdxBeY0UKi9x169Lu687p_mOPIpMm3xW4qq6PNbM/edit?usp=sharing](https://docs.google.com/document/d/1LTPxdxBeY0UKi9x169Lu687p_mOPIpMm3xW4qq6PNbM/edit?usp=sharing)  
> 於任一文件內新增或修改內容後，在系統點選對應的「立即匯入」或同步按鈕即可即時更新！

---

## 📁 Vercel 專案架構說明

```text
├── api/
│   ├── index.py              <-- Vercel Serverless 後端函數 (處理 Google Docs 匯入與 API)
│   └── importer.py           <-- 詞庫解析與 Google Docs 爬取核心
├── public/
│   └── index.html            <-- 前端單頁應用程式 (部署在 Vercel 靜態邊緣節點)
├── index.html                <-- 根目錄鏡像頁面 (相容各種部署環境)
├── vercel.json               <-- Vercel 路由與重定向設定
├── requirements.txt          <-- Python 環境定義
├── app.py                    <-- 本地測試伺服器
├── gui.py                    <-- 桌面視窗版
├── 詞庫範本.txt              <-- Google 文件範本文本
└── 啟動抽籤程式-網頁版.bat    <-- 本機快捷啟動腳本
```
