"""
動詞 & 名詞 智慧抽籤器 - 桌面版視窗程式 (Tkinter Desktop GUI)
提供免開瀏覽器的原生桌面視窗操作體驗。
支援：
1. 混在一起抽
2. 隨機組裝句子
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading

import importer
import drawer

class DrawAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 動詞 & 名詞 智慧抽籤器 (桌面版)")
        self.root.geometry("680x740")
        self.root.minsize(600, 620)

        # 初始化抽籤引擎
        self.drawer_engine = drawer.WordDrawer(
            importer.DEFAULT_VERBS, 
            importer.DEFAULT_NOUNS
        )
        
        # 設定風格樣式
        self.setup_styles()
        # 建立介面元件
        self.create_widgets()
        # 更新詞庫狀態標籤
        self.update_stats_display()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        font_family = "Microsoft JhengHei"
        style.configure(".", font=(font_family, 10))
        style.configure("Header.TLabel", font=(font_family, 16, "bold"), foreground="#312e81")
        style.configure("SubHeader.TLabel", font=(font_family, 9), foreground="#64748b")
        style.configure("Stats.TLabel", font=(font_family, 10, "bold"), foreground="#4338ca")
        style.configure("Title.TLabelframe.Label", font=(font_family, 11, "bold"), foreground="#1e293b")
        style.configure("Action.TButton", font=(font_family, 12, "bold"), foreground="white", background="#4f46e5")
        style.map("Action.TButton", background=[("active", "#4338ca"), ("pressed", "#3730a3")])

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="16")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 頂部標題
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        lbl_title = ttk.Label(header_frame, text="🎯 動詞 & 名詞 智慧抽籤器", style="Header.TLabel")
        lbl_title.pack(anchor="center")
        lbl_sub = ttk.Label(header_frame, text="支援 Google 文件匯入 · 混抽 · 隨機組句", style="SubHeader.TLabel")
        lbl_sub.pack(anchor="center", pady=(2, 6))

        # 詞庫管理區塊
        bank_frame = ttk.LabelFrame(main_frame, text="📚 詞庫管理", style="Title.TLabelframe", padding="10")
        bank_frame.pack(fill=tk.X, pady=6)

        bank_top = ttk.Frame(bank_frame)
        bank_top.pack(fill=tk.X)

        self.lbl_stats = ttk.Label(bank_top, text="詞庫狀態載入中...", style="Stats.TLabel")
        self.lbl_stats.pack(side=tk.LEFT, padx=4)

        btn_gdoc = ttk.Button(bank_top, text="🌐 從 Google 文件匯入", command=self.open_google_doc_dialog)
        btn_gdoc.pack(side=tk.RIGHT, padx=4)

        btn_edit = ttk.Button(bank_top, text="✏️ 檢視/手動編輯", command=self.open_edit_dialog)
        btn_edit.pack(side=tk.RIGHT, padx=4)

        # 抽籤設定區塊
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ 抽籤模式與設定", style="Title.TLabelframe", padding="10")
        settings_frame.pack(fill=tk.X, pady=6)

        # 模式單選
        self.var_mode = tk.StringVar(value="mixed")
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.pack(fill=tk.X, pady=4)

        r1 = ttk.Radiobutton(mode_frame, text="🎲 模式一：混在一起抽 (動詞與名詞混合)", 
                             variable=self.var_mode, value="mixed", command=self.on_mode_change)
        r1.pack(anchor="w", pady=2)
        
        r2 = ttk.Radiobutton(mode_frame, text="🔀 模式二：隨機組裝句子 (\"動詞\" 的 \"名詞\")", 
                             variable=self.var_mode, value="sentence", command=self.on_mode_change)
        r2.pack(anchor="w", pady=2)

        # 細節選項
        opt_frame = ttk.Frame(settings_frame)
        opt_frame.pack(fill=tk.X, pady=6)

        ttk.Label(opt_frame, text="抽籤數量：").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        self.spin_count = ttk.Spinbox(opt_frame, from_=1, to=100, width=5)
        self.spin_count.set(3)
        self.spin_count.grid(row=0, column=1, sticky="w", padx=4, pady=4)

        self.var_no_repeat = tk.BooleanVar(value=False)
        chk_no_repeat = ttk.Checkbutton(opt_frame, text="不重複抽取 (不放回)", variable=self.var_no_repeat)
        chk_no_repeat.grid(row=0, column=2, sticky="w", padx=12, pady=4)

        # 模式一附加選項
        self.var_show_type = tk.BooleanVar(value=True)
        self.chk_show_type = ttk.Checkbutton(opt_frame, text="標註詞性 (動詞/名詞)", variable=self.var_show_type)
        self.chk_show_type.grid(row=1, column=0, columnspan=3, sticky="w", padx=4, pady=4)

        # 模式二附加選項
        self.sentence_opt_frame = ttk.Frame(settings_frame)
        ttk.Label(self.sentence_opt_frame, text="句型格式：").pack(side=tk.LEFT, padx=4)
        self.combo_template = ttk.Combobox(self.sentence_opt_frame, values=[
            '"{verb}" 的 "{noun}" (帶引號)',
            '{verb}的{noun} (緊湊無引號)',
            '{verb} 的 {noun} (空格無引號)',
            '一個{verb}的{noun}',
            '正在{verb}的{noun}'
        ], state="readonly", width=25)
        self.combo_template.current(0)
        self.combo_template.pack(side=tk.LEFT, padx=4)

        # 抽籤大按鈕
        self.btn_draw = tk.Button(main_frame, text="🎲 立即抽籤！", font=("Microsoft JhengHei", 12, "bold"),
                                  bg="#4f46e5", fg="white", activebackground="#4338ca", activeforeground="white",
                                  relief=tk.FLAT, cursor="hand2", pady=10, command=self.do_draw)
        self.btn_draw.pack(fill=tk.X, pady=8)

        # 抽取結果展示區
        res_frame = ttk.LabelFrame(main_frame, text="🎉 抽籤結果", style="Title.TLabelframe", padding="10")
        res_frame.pack(fill=tk.BOTH, expand=True, pady=6)

        # 結果文字區
        self.txt_result = tk.Text(res_frame, font=("Microsoft JhengHei", 13), wrap=tk.WORD, height=8, relief=tk.SOLID, bd=1)
        self.txt_result.pack(fill=tk.BOTH, expand=True, pady=4)
        self.txt_result.insert(tk.END, "點擊上方「🎲 立即抽籤！」開始抽取！\n")
        self.txt_result.config(state=tk.DISABLED)

        # 結果操作按鈕列
        btn_bar = ttk.Frame(res_frame)
        btn_bar.pack(fill=tk.X, pady=(4, 0))

        btn_copy = ttk.Button(btn_bar, text="📋 複製本次結果", command=self.copy_results)
        btn_copy.pack(side=tk.LEFT, padx=4)

        btn_reset_pool = ttk.Button(btn_bar, text="🔄 重設剩餘池", command=self.reset_pools)
        btn_reset_pool.pack(side=tk.LEFT, padx=4)

        btn_history = ttk.Button(btn_bar, text="📜 查看歷史紀錄", command=self.show_history)
        btn_history.pack(side=tk.RIGHT, padx=4)

        self.lbl_notice = ttk.Label(main_frame, text="", foreground="#d97706", font=("Microsoft JhengHei", 9))
        self.lbl_notice.pack(anchor="w")

    def on_mode_change(self):
        mode = self.var_mode.get()
        if mode == "mixed":
            self.sentence_opt_frame.pack_forget()
            self.chk_show_type.grid(row=1, column=0, columnspan=3, sticky="w", padx=4, pady=4)
        else:
            self.chk_show_type.grid_remove()
            self.sentence_opt_frame.pack(fill=tk.X, pady=4)

    def update_stats_display(self):
        stats = self.drawer_engine.get_stats()
        text = f"動詞: {stats['total_verbs']} | 名詞: {stats['total_nouns']} | 總計: {stats['total_words']}"
        self.lbl_stats.config(text=text)

    def do_draw(self):
        try:
            count = int(self.spin_count.get())
        except ValueError:
            count = 1

        mode = self.var_mode.get()
        allow_repeat = not self.var_no_repeat.get()

        if mode == "mixed":
            show_type = self.var_show_type.get()
            res = self.drawer_engine.draw_mixed(count=count, allow_repeat=allow_repeat, show_type=show_type)
        else:
            tpl_choice = self.combo_template.get()
            if '帶引號' in tpl_choice:
                template = '"{verb}" 的 "{noun}"'
            elif '緊湊無引號' in tpl_choice:
                template = '{verb}的{noun}'
            elif '空格無引號' in tpl_choice:
                template = '{verb} 的 {noun}'
            elif '一個' in tpl_choice:
                template = '一個{verb}的{noun}'
            elif '正在' in tpl_choice:
                template = '正在{verb}的{noun}'
            else:
                template = '"{verb}" 的 "{noun}"'

            res = self.drawer_engine.draw_sentence(count=count, allow_repeat=allow_repeat, template=template)

        if "error" in res and res["error"]:
            messagebox.showerror("錯誤", res["error"])
            return

        formatted = res.get("formatted", [])
        self.last_results = formatted

        # 顯示在文字框
        self.txt_result.config(state=tk.NORMAL)
        self.txt_result.delete("1.0", tk.END)
        for i, item in enumerate(formatted, 1):
            self.txt_result.insert(tk.END, f"{i}. {item}\n")
        self.txt_result.config(state=tk.DISABLED)

        if res.get("message"):
            self.lbl_notice.config(text="⚠️ " + res["message"])
        else:
            self.lbl_notice.config(text="")

    def copy_results(self):
        content = self.txt_result.get("1.0", tk.END).strip()
        if not content or "點擊上方" in content:
            messagebox.showwarning("提示", "目前沒有結果可複製！")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("複製成功", "已將抽籤結果複製到剪貼簿！")

    def reset_pools(self):
        self.drawer_engine.reset_pools()
        messagebox.showinfo("提示", "已重設不重複抽籤池！")

    def open_google_doc_dialog(self):
        default_url = getattr(importer, "DEFAULT_GDOC_URL", "https://docs.google.com/document/d/166VTPgMpxjcHDP52zTFJGpnnewSKVIQAelxabE0jsH0/edit?tab=t.0")
        url = simpledialog.askstring(
            "從 Google 文件匯入",
            "請貼上 Google 文件網址或 Document ID：\n\n"
            "※ 請確保 Google 文件權限已設為「知道連結的任何人都能查看」",
            initialvalue=default_url,
            parent=self.root
        )
        if not url:
            return

        def task():
            try:
                content = importer.fetch_google_doc_text(url)
                verbs, nouns = importer.parse_word_bank(content)
                if not verbs and not nouns:
                    self.root.after(0, lambda: messagebox.showerror(
                        "匯入失敗", "無法從文件中辨識出動詞或名詞！\n請確認文件是否有標籤 [動詞] 與 [名詞]。"
                    ))
                    return

                self.drawer_engine.set_word_bank(verbs, nouns)
                self.root.after(0, lambda: [
                    self.update_stats_display(),
                    messagebox.showinfo("匯入成功", f"成功載入詞庫！\n動詞：{len(verbs)} 個\n名詞：{len(nouns)} 個")
                ])
            except Exception as e:
                self.root.after(0, lambda err=str(e): messagebox.showerror("匯入錯誤", err))

        threading.Thread(target=task, daemon=True).start()

    def open_edit_dialog(self):
        # 詞庫編輯子視窗
        win = tk.Toplevel(self.root)
        win.title("✏️ 檢視與編輯詞庫")
        win.geometry("560x480")
        win.minsize(480, 380)

        top_f = ttk.Frame(win, padding=10)
        top_f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(top_f, text="動詞清單 (每行一個)：").grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Label(top_f, text="名詞清單 (每行一個)：").grid(row=0, column=1, sticky="w", pady=(0, 4))

        txt_v = tk.Text(top_f, width=24, height=15)
        txt_v.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        txt_v.insert(tk.END, "\n".join(self.drawer_engine.verbs))

        txt_n = tk.Text(top_f, width=24, height=15)
        txt_n.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        txt_n.insert(tk.END, "\n".join(self.drawer_engine.nouns))

        top_f.rowconfigure(1, weight=1)
        top_f.columnconfigure(0, weight=1)
        top_f.columnconfigure(1, weight=1)

        btn_box = ttk.Frame(win, padding=10)
        btn_box.pack(fill=tk.X)

        def save():
            v_raw = txt_v.get("1.0", tk.END)
            n_raw = txt_n.get("1.0", tk.END)

            full_text = f"[動詞]\n{v_raw}\n[名詞]\n{n_raw}"
            verbs, nouns = importer.parse_word_bank(full_text)

            if not verbs and not nouns:
                messagebox.showerror("錯誤", "動詞與名詞不能同時為空！", parent=win)
                return
            self.drawer_engine.set_word_bank(verbs, nouns)
            self.update_stats_display()
            messagebox.showinfo("成功", f"詞庫已更新！\n動詞: {len(verbs)} 個，名詞: {len(nouns)} 個", parent=win)
            win.destroy()

        def restore():
            if messagebox.askyesno("確認", "是否還原為預設示範詞庫？", parent=win):
                self.drawer_engine.set_word_bank(
                    importer.DEFAULT_VERBS, 
                    importer.DEFAULT_NOUNS
                )
                self.update_stats_display()
                txt_v.delete("1.0", tk.END)
                txt_v.insert(tk.END, "\n".join(self.drawer_engine.verbs))
                txt_n.delete("1.0", tk.END)
                txt_n.insert(tk.END, "\n".join(self.drawer_engine.nouns))

        ttk.Button(btn_box, text="🔄 還原預設詞庫", command=restore).pack(side=tk.LEFT)
        ttk.Button(btn_box, text="💾 儲存並套用", command=save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_box, text="取消", command=win.destroy).pack(side=tk.RIGHT)

    def show_history(self):
        hist_win = tk.Toplevel(self.root)
        hist_win.title("📜 抽籤歷史紀錄")
        hist_win.geometry("520x420")

        f = ttk.Frame(hist_win, padding=10)
        f.pack(fill=tk.BOTH, expand=True)

        txt = tk.Text(f, wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True)

        if not self.drawer_engine.history:
            txt.insert(tk.END, "尚無歷史紀錄。")
        else:
            for item in reversed(self.drawer_engine.history):
                txt.insert(tk.END, f"[{item['timestamp']}] {item['mode']} (抽 {item['count']} 個):\n")
                for r in item["results"]:
                    txt.insert(tk.END, f"  • {r}\n")
                txt.insert(tk.END, "\n")
        txt.config(state=tk.DISABLED)

        b_frame = ttk.Frame(hist_win, padding=6)
        b_frame.pack(fill=tk.X)
        
        def clear():
            self.drawer_engine.clear_history()
            txt.config(state=tk.NORMAL)
            txt.delete("1.0", tk.END)
            txt.insert(tk.END, "已清空歷史紀錄。")
            txt.config(state=tk.DISABLED)

        ttk.Button(b_frame, text="🗑️ 清空紀錄", command=clear).pack(side=tk.LEFT)
        ttk.Button(b_frame, text="關閉", command=hist_win.destroy).pack(side=tk.RIGHT)


def main():
    root = tk.Tk()
    app = DrawAppGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
