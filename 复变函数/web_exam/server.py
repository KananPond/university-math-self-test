# -*- coding: utf-8 -*-
"""
文件名：server.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 本地判分服务：按随机种子从复变函数题库抽题下发，并提供实时得分、
   交卷判分、记录保存与闪电训练接口。
2. 只监听本机回环地址；答案、解析与复核规则不下发给前端。
3. 复数图解由前端 canvas 渲染，服务端只下发图形数据。
4. 用法： python server.py [端口]，默认端口 8767。
"""

import json
import os
import random
import sys
import time
import hashlib
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

WEB_EXAM_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(WEB_EXAM_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from grader import (  # noqa: E402
    load_paper,
    public_paper,
    grade_paper,
    normalize_answers,
)
from checker import score_objective, check_single  # noqa: E402
from bank import BANK, bank_summary  # noqa: E402
from bank import drill_gen  # noqa: E402

BASE_DIR = WEB_EXAM_DIR
STATIC_DIR = os.path.join(BASE_DIR, "static")
RECORD_DIR = os.path.join(BASE_DIR, "records")
WRONGBOOK_PATH = os.path.join(RECORD_DIR, "drill_wrongbook.json")

DEFAULT_PORT = 8767
MAX_BODY_BYTES = 1024 * 1024
MAX_SEED = 10 ** 9
MAX_DRILL_COUNT = 60

TYPE_NAMES = {"choice": "选择题", "judge": "判断题",
              "fill": "填空题", "calc": "计算题"}

# 闪电训练可用的知识点（与题库 kp 受控词表一致）
DRILL_KPS = ["复数的表示", "模与辐角", "四则运算", "共轭与倒数",
             "幂与根", "棣莫弗公式"]


def json_response(handler, payload, status=200):
    """输出 JSON 响应。"""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def clean_text(value, limit=40000):
    """把前端提交的文本规范化为字符串。"""
    if not isinstance(value, str):
        return ""

    return value[:limit]


def parse_seed(raw):
    """解析随机种子，非法时返回 None。"""
    try:
        seed = int(raw)
    except (TypeError, ValueError):
        return None
    if seed < 0 or seed > MAX_SEED:
        return None

    return seed


def public_drill_item(item, wrong_id=None):
    """剥离训练条目的答案与解析。"""
    payload = {
        "id": item["id"],
        "kind": item.get("kind") or "number",
        "kp": item.get("kp"),
        "stem": item.get("stem"),
        "answer_type": item.get("answer_type") or "number",
    }
    if wrong_id:
        payload["wrongId"] = wrong_id
    if item.get("figure"):
        payload["figure"] = item["figure"]
    blanks = item.get("blanks")
    if blanks:
        payload["blanks"] = [
            {"label": blank.get("label", "第 %d 空" % (index + 1)),
             "answer_type": blank.get("answer_type") or "number"}
            for index, blank in enumerate(blanks)
        ]

    return payload


# --------------------------------------------------------------------------
# 闪电训练错题本：服务端持久化，答案不下发
# --------------------------------------------------------------------------

def wrong_item_id(item):
    """错题的稳定标识：同一道题在不同随机种子下仍是同一条。"""
    basis = "%s|%s|%s" % (item.get("kp"), item.get("stem"),
                          json.dumps(item.get("answer"), ensure_ascii=False,
                                     sort_keys=True))

    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]


def load_wrongbook():
    """读取错题本。"""
    if not os.path.isfile(WRONGBOOK_PATH):
        return []
    try:
        with open(WRONGBOOK_PATH, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []

    return data


def save_wrongbook(items):
    """保存错题本。"""
    os.makedirs(RECORD_DIR, exist_ok=True)
    with open(WRONGBOOK_PATH, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(items, handle, ensure_ascii=False, indent=2)


def add_wrong_item(item):
    """把一道做错的训练题登记到错题本，返回错题 id。"""
    entry_id = wrong_item_id(item)
    items = load_wrongbook()
    for entry in items:
        if entry.get("id") == entry_id:
            entry["misses"] = int(entry.get("misses", 1)) + 1
            entry["lastMissedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_wrongbook(items)

            return entry_id

    items.append({
        "id": entry_id,
        "item": item,
        "misses": 1,
        "lastMissedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_wrongbook(items)

    return entry_id


def remove_wrong_item(entry_id):
    """从错题本移除一条（答对且连续答对后调用）。"""
    items = load_wrongbook()
    kept = [entry for entry in items if entry.get("id") != entry_id]
    if len(kept) != len(items):
        save_wrongbook(kept)

        return True

    return False


def build_record_markdown(record):
    """把一次交卷结果整理成可粘贴到日志的 Markdown 文本。"""
    lines = []
    lines.append("# %s" % record["paperTitle"])
    lines.append("")
    lines.append("- 交卷时间：%s" % record["savedAt"])
    lines.append("- 抽题种子：%s" % record["seed"])
    lines.append("- 得分：%s / %s" % (record["score"], record["totalScore"]))
    lines.append("- 用时：%s" % record["elapsedText"])
    lines.append("")
    lines.append("## 各题得分")
    lines.append("")
    lines.append("| 题号 | 大题 | 知识点 | 得分 | 满分 |")
    lines.append("|------|------|--------|------|------|")
    for item in record["details"]:
        lines.append("| %s | %s | %s | %s | %s |"
                     % (item["no"], item["section"], item.get("kp") or "-",
                        item["score"], item["full"]))
    lines.append("")

    wrong = [item for item in record["details"]
             if float(item["score"]) < float(item["full"])]
    lines.append("## 错题清单（%d 题）" % len(wrong))
    lines.append("")
    if not wrong:
        lines.append("本次模拟无错题。")
    else:
        for item in wrong:
            lines.append("- %s（%s · %s）：得分 %s / %s"
                         % (item["no"], item["section"],
                            item.get("kp") or "-",
                            item["score"], item["full"]))
    lines.append("")

    return "\n".join(lines)


def save_record(record):
    """把交卷记录写入 records 目录，返回生成的两个文件名。"""
    os.makedirs(RECORD_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base_name = "%s_%s" % (stamp, record.get("paperId", "paper"))
    json_name = base_name + ".json"
    md_name = base_name + ".md"

    with open(os.path.join(RECORD_DIR, json_name), "w",
              encoding="utf-8", newline="\n") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)

    with open(os.path.join(RECORD_DIR, md_name), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(build_record_markdown(record))

    return json_name, md_name


class ExamRequestHandler(SimpleHTTPRequestHandler):
    """静态文件与判分接口共用的请求处理器。"""

    server_version = "CVExamServer/1.0"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(),
                                        fmt % args))

    def end_headers(self):
        # 考试页面与静态资源一律禁止缓存，保证改版后刷新即生效
        if not self.path.startswith("/api"):
            self.send_header("Cache-Control",
                             "no-cache, no-store, must-revalidate")
        super().end_headers()

    def read_json_body(self):
        """读取并解析请求体，返回字典或 None。"""
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if length <= 0 or length > MAX_BODY_BYTES:
            return None
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

        return data if isinstance(data, dict) else None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.path = "/index.html"
        elif parsed.path == "/api/health":
            summary = bank_summary(BANK)
            json_response(self, {
                "ok": True,
                "time": time.time(),
                "bank": summary,
                "bankTotal": sum(summary.values()),
                "drillKps": DRILL_KPS,
            })

            return
        elif parsed.path == "/api/paper":
            self.handle_paper(parse_qs(parsed.query))

            return
        elif parsed.path == "/api/drill":
            self.handle_drill(parse_qs(parsed.query))

            return
        elif parsed.path == "/api/drill/wrongbook":
            self.handle_wrongbook_list()

            return

        super().do_GET()

    def do_POST(self):
        data = self.read_json_body()
        if data is None:
            json_response(self,
                          {"ok": False, "error": "请求体不是合法的 JSON。"},
                          400)

            return

        if self.path == "/api/score":
            self.handle_score(data)
        elif self.path == "/api/grade":
            self.handle_grade(data)
        elif self.path == "/api/save":
            self.handle_save(data)
        elif self.path == "/api/drill/check":
            self.handle_drill_check(data)
        elif self.path == "/api/drill/wrong":
            self.handle_drill_wrong(data)
        elif self.path == "/api/drill/mastered":
            self.handle_drill_mastered(data)
        else:
            json_response(self, {"ok": False, "error": "未知接口。"}, 404)

    def handle_paper(self, query):
        """按种子抽题并下发（不含答案与解析）。"""
        seed = None
        if "seed" in query:
            seed = parse_seed(query["seed"][0])
        if seed is None:
            seed = random.randrange(1, MAX_SEED)

        paper = load_paper(seed)
        json_response(self, {
            "ok": True,
            "seed": seed,
            "paper": public_paper(paper),
            "bank": bank_summary(BANK),
        })

    def handle_drill(self, query):
        """下发一组闪电训练题（不含答案与解析）。"""
        seed = None
        if "seed" in query:
            seed = parse_seed(query["seed"][0])
        if seed is None:
            seed = random.randrange(1, MAX_SEED)

        count = 10
        if "count" in query:
            try:
                count = int(query["count"][0])
            except (TypeError, ValueError):
                count = 10
        count = max(1, min(MAX_DRILL_COUNT, count))

        kps = None
        if "kp" in query:
            raw = query["kp"][0]
            wanted = [part.strip() for part in raw.split(",") if part.strip()]
            allowed = [kp for kp in wanted if kp in DRILL_KPS]
            if allowed:
                kps = allowed

        items = drill_gen.generate_items(seed, count, kps)
        json_response(self, {
            "ok": True,
            "seed": seed,
            "kps": kps or DRILL_KPS,
            "items": [public_drill_item(item) for item in items],
        })

    def handle_drill_check(self, data):
        """闪电训练单题判定：服务端按种子复原题目后精确判分。"""
        item = None
        wrong_id = clean_text(data.get("wrongId"), 64)

        if wrong_id:
            for entry in load_wrongbook():
                if entry.get("id") == wrong_id:
                    item = entry.get("item")
                    break
        else:
            item_id = clean_text(data.get("id"), 120)
            if not item_id:
                json_response(self,
                              {"ok": False, "error": "缺少题目 id。"}, 400)

                return

            seed = parse_seed(data.get("seed"))
            if seed is None:
                try:
                    seed = int(item_id.split("_")[1])
                except (IndexError, ValueError):
                    json_response(self,
                                  {"ok": False, "error": "缺少抽题种子。"}, 400)

                    return

            item = drill_gen.item_by_id(seed, item_id)

        if item is None:
            json_response(self, {"ok": False, "error": "找不到该训练题。"}, 404)

            return

        response = data.get("response")
        outcome = check_single(item, response)
        outcome["ok"] = True
        outcome["id"] = item.get("id")
        outcome["kp"] = item.get("kp")
        if wrong_id:
            outcome["wrongId"] = wrong_id
        json_response(self, outcome)

    def handle_wrongbook_list(self):
        """返回错题本（不含答案）。"""
        entries = load_wrongbook()
        items = []
        for entry in entries:
            item = entry.get("item") or {}
            payload = public_drill_item(item, entry.get("id"))
            payload["misses"] = entry.get("misses", 1)
            payload["lastMissedAt"] = entry.get("lastMissedAt", "")
            items.append(payload)
        json_response(self, {"ok": True, "items": items})

    def handle_drill_wrong(self, data):
        """把做错的训练题登记进错题本。"""
        item_id = clean_text(data.get("id"), 120)
        if not item_id:
            json_response(self, {"ok": False, "error": "缺少题目 id。"}, 400)

            return

        seed = parse_seed(data.get("seed"))
        if seed is None:
            try:
                seed = int(item_id.split("_")[1])
            except (IndexError, ValueError):
                json_response(self,
                              {"ok": False, "error": "缺少抽题种子。"}, 400)

                return

        item = drill_gen.item_by_id(seed, item_id)
        if item is None:
            json_response(self, {"ok": False, "error": "找不到该训练题。"}, 404)

            return

        wrong_id = add_wrong_item(item)
        json_response(self, {"ok": True, "wrongId": wrong_id})

    def handle_drill_mastered(self, data):
        """错题连续答对后从错题本移除。"""
        wrong_id = clean_text(data.get("wrongId"), 64)
        if not wrong_id:
            json_response(self, {"ok": False, "error": "缺少错题 id。"}, 400)

            return

        removed = remove_wrong_item(wrong_id)
        json_response(self, {"ok": True, "removed": removed})

    def handle_score(self, data):
        """实时统计当前得分，只返回总分与作答进度，不下发答案。"""
        seed = parse_seed(data.get("seed"))
        if seed is None:
            json_response(self, {"ok": False, "error": "缺少抽题种子。"}, 400)

            return

        answers = normalize_answers(data.get("answers"))
        paper = load_paper(seed)
        result = score_objective(paper, answers)
        result["ok"] = True
        json_response(self, result)

    def handle_grade(self, data):
        """回收全部作答并判分，返回逐题结果与参考答案。"""
        seed = parse_seed(data.get("seed"))
        if seed is None:
            json_response(self, {"ok": False, "error": "缺少抽题种子。"}, 400)

            return

        answers = normalize_answers(data.get("answers"))
        paper = load_paper(seed)
        result = grade_paper(paper, answers)
        result["ok"] = True
        result["title"] = paper["title"]
        json_response(self, result)

    def handle_save(self, data):
        """保存交卷记录，供复盘与写入日志。"""
        details = data.get("details")
        if not isinstance(details, list):
            details = []

        record = {
            "paperId": clean_text(data.get("paperId"), 64),
            "paperTitle": clean_text(data.get("paperTitle"), 200),
            "savedAt": clean_text(data.get("savedAt"), 40),
            "elapsedText": clean_text(data.get("elapsedText"), 40),
            "seed": parse_seed(data.get("seed")),
            "score": data.get("score", 0),
            "totalScore": data.get("totalScore", 100),
            "details": details[:120],
        }
        json_name, md_name = save_record(record)
        json_response(self, {"ok": True, "file": json_name,
                             "markdown": md_name})


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, AttributeError):
            pass

    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("端口参数不是整数，使用默认端口 %d。" % DEFAULT_PORT)

    if not os.path.isdir(STATIC_DIR):
        print("未找到 static 目录：%s" % STATIC_DIR)
        return 1

    summary = bank_summary(BANK)
    print("题库规模：%s" % "、".join("%s %d" % (TYPE_NAMES[key], count)
                                     for key, count in summary.items()))
    server = ThreadingHTTPServer(("127.0.0.1", port), ExamRequestHandler)
    print("复变函数考试模拟系统已启动： http://127.0.0.1:%d/" % port)
    print("闪电训练： http://127.0.0.1:%d/drill.html" % port)
    print("复平面实验台： http://127.0.0.1:%d/plane.html" % port)
    print("按 Ctrl + C 停止服务。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止。")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
