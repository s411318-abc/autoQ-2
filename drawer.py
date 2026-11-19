"""
詞彙抽取核心模組 (Word Drawer Engine)
支援：
1. 混在一起抽 (混合動詞與名詞隨機抽取)
2. 組合句型抽法 ("動詞" 的 "名詞")
支援放回/不放回抽取模式、歷史紀錄與統計。
"""

import random
from datetime import datetime

class WordDrawer:
    def __init__(self, verbs=None, nouns=None):
        self.verbs = list(dict.fromkeys(verbs or []))
        self.nouns = list(dict.fromkeys(nouns or []))
        
        # 不放回抽籤時使用的剩餘詞庫
        self.remaining_mixed = []
        self.remaining_verbs = []
        self.remaining_nouns = []
        
        self.history = []
        self.reset_pools()

    def set_word_bank(self, verbs: list[str], nouns: list[str]):
        """更新動詞與名詞詞庫"""
        self.verbs = list(dict.fromkeys([v.strip() for v in verbs if v.strip()]))
        self.nouns = list(dict.fromkeys([n.strip() for n in nouns if n.strip()]))
        self.reset_pools()

    def reset_pools(self):
        """重設不放回抽取的剩餘詞庫池"""
        self.remaining_verbs = list(self.verbs)
        self.remaining_nouns = list(self.nouns)
        
        # 混合池：每個元素為 tuple (word, '動詞' | '名詞')
        mixed = [(v, '動詞') for v in self.verbs] + [(n, '名詞') for n in self.nouns]
        random.shuffle(mixed)
        self.remaining_mixed = mixed

    def get_stats(self) -> dict:
        """取得當前詞庫統計"""
        return {
            "total_verbs": len(self.verbs),
            "total_nouns": len(self.nouns),
            "total_words": len(self.verbs) + len(self.nouns),
            "remaining_verbs": len(self.remaining_verbs),
            "remaining_nouns": len(self.remaining_nouns),
            "remaining_mixed": len(self.remaining_mixed),
        }

    def draw_mixed(self, count: int = 1, allow_repeat: bool = True, show_type: bool = False) -> dict:
        """
        模式一：混在一起抽
        :param count: 抽取的詞數
        :param allow_repeat: 是否允許重複抽取 (True: 放回抽取, False: 不放回抽取)
        :param show_type: 結果是否標註詞性標籤，如「奔跑 (動詞)」
        :return: 字典包含結果列表、元資料及提示訊息
        """
        all_pool = [(v, '動詞') for v in self.verbs] + [(n, '名詞') for n in self.nouns]
        if not all_pool:
            return {"error": "目前詞庫為空，請先匯入動詞或名詞！", "results": []}

        count = max(1, count)
        results = []
        message = ""

        if allow_repeat:
            # 放回抽取
            chosen = random.choices(all_pool, k=count)
            for word, ptype in chosen:
                display = f"{word}（{ptype}）" if show_type else word
                results.append({
                    "text": display,
                    "word": word,
                    "type": ptype
                })
        else:
            # 不放回抽取
            if len(self.remaining_mixed) < count:
                message = f"剩餘詞庫不足 {count} 個（剩餘 {len(self.remaining_mixed)} 個），已全部抽出並自動重設詞庫！"
                needed_from_reset = count - len(self.remaining_mixed)
                
                # 先抽完剩餘的
                chosen = list(self.remaining_mixed)
                self.reset_pools()
                
                # 若總詞彙量仍小於 count，只能全部抽出
                if len(self.remaining_mixed) <= needed_from_reset:
                    chosen += list(self.remaining_mixed)
                    self.reset_pools()
                else:
                    for _ in range(needed_from_reset):
                        chosen.append(self.remaining_mixed.pop())
            else:
                chosen = []
                for _ in range(count):
                    chosen.append(self.remaining_mixed.pop())

            for word, ptype in chosen:
                display = f"{word}（{ptype}）" if show_type else word
                results.append({
                    "text": display,
                    "word": word,
                    "type": ptype
                })

        entry = {
            "id": len(self.history) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "混在一起抽",
            "count": count,
            "results": [r["text"] for r in results],
            "raw": results,
            "message": message
        }
        self.history.append(entry)
        
        return {
            "mode": "mixed",
            "results": results,
            "formatted": [r["text"] for r in results],
            "message": message,
            "stats": self.get_stats()
        }

    def draw_sentence(self, count: int = 1, allow_repeat: bool = True, 
                      template: str = '"{verb}" 的 "{noun}"') -> dict:
        """
        模式二：抽出格式為 "動詞" 的 "名詞" 的句子
        :param count: 抽取幾組句子
        :param allow_repeat: 是否允許重複抽取
        :param template: 句型模板，預設為 '"{verb}" 的 "{noun}"'，也可支援 '{verb}的{noun}' 等
        :return: 字典包含結果列表、元資料及提示訊息
        """
        if not self.verbs or not self.nouns:
            missing = []
            if not self.verbs:
                missing.append("動詞")
            if not self.nouns:
                missing.append("名詞")
            return {
                "error": f"詞庫缺少 {' 和 '.join(missing)}，無法組成「動詞的句子」！",
                "results": []
            }

        count = max(1, count)
        results = []
        message = ""

        if allow_repeat:
            # 放回抽取
            v_choices = random.choices(self.verbs, k=count)
            n_choices = random.choices(self.nouns, k=count)
            for v, n in zip(v_choices, n_choices):
                sentence = template.format(verb=v, noun=n)
                results.append({
                    "text": sentence,
                    "verb": v,
                    "noun": n
                })
        else:
            # 不放回抽取
            v_chosen = []
            n_chosen = []
            
            # 檢查動詞剩餘量
            if len(self.remaining_verbs) < count:
                message += f"動詞剩餘不足（剩餘 {len(self.remaining_verbs)} 個，已循環重置）；"
                v_chosen.extend(self.remaining_verbs)
                needed = count - len(self.remaining_verbs)
                self.remaining_verbs = list(self.verbs)
                random.shuffle(self.remaining_verbs)
                while needed > 0:
                    take = min(needed, len(self.remaining_verbs))
                    v_chosen.extend(self.remaining_verbs[:take])
                    self.remaining_verbs = self.remaining_verbs[take:]
                    needed -= take
                    if needed > 0:
                        self.remaining_verbs = list(self.verbs)
                        random.shuffle(self.remaining_verbs)
            else:
                for _ in range(count):
                    v_chosen.append(self.remaining_verbs.pop())

            # 檢查名詞剩餘量
            if len(self.remaining_nouns) < count:
                message += f"名詞剩餘不足（剩餘 {len(self.remaining_nouns)} 個，已循環重置）；"
                n_chosen.extend(self.remaining_nouns)
                needed = count - len(self.remaining_nouns)
                self.remaining_nouns = list(self.nouns)
                random.shuffle(self.remaining_nouns)
                while needed > 0:
                    take = min(needed, len(self.remaining_nouns))
                    n_chosen.extend(self.remaining_nouns[:take])
                    self.remaining_nouns = self.remaining_nouns[take:]
                    needed -= take
                    if needed > 0:
                        self.remaining_nouns = list(self.nouns)
                        random.shuffle(self.remaining_nouns)
            else:
                for _ in range(count):
                    n_chosen.append(self.remaining_nouns.pop())

            for v, n in zip(v_chosen, n_chosen):
                sentence = template.format(verb=v, noun=n)
                results.append({
                    "text": sentence,
                    "verb": v,
                    "noun": n
                })

        entry = {
            "id": len(self.history) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "動詞的名詞句子",
            "count": count,
            "results": [r["text"] for r in results],
            "raw": results,
            "message": message
        }
        self.history.append(entry)

        return {
            "mode": "sentence",
            "results": results,
            "formatted": [r["text"] for r in results],
            "message": message,
            "stats": self.get_stats()
        }

    def clear_history(self):
        """清空抽籤歷史紀錄"""
        self.history = []
