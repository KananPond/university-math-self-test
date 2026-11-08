# -*- coding: utf-8 -*-
"""
文件名：server.py
作者：ZCode（GLM）
日期：2026-10-02
版本：1.0
文件说明：
1. 本地判分服务：按随机种子从线性代数题库抽题下发，并提供实时得分、
   交卷判分与记录保存接口。
2. 只监听本机回环地址；答案、解析与复核规则不下发给前端。
3. 矩阵题面由前端 canvas 图形化渲染，服务端只下发矩阵数据。
4. 用法： python server.py [端口]，默认端口 8766。
"""

import json
import os
import random
import sys
import time
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
from checker import score_objective  # noqa: E402
from bank import BANK, bank_summary  # noqa: E402

BASE_DIR = WEB_EXAM_DIR
STATIC_DIR = os.path.join(BASE_DIR, "static")
RECORD_DIR = os.path.join(BASE_DIR, "records")

DEFAULT_PORT = 8766
MAX_BODY_BYTES = 1024 * 1024
MAX_SEED = 10 ** 9

TYPE_NAMES = {"choice": "选择题", "judge": "判断题",
              "fill": "填空题", "calc": "计算题"}


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
    lines.append("| 题号 | 类型 | 得分 | 满分 |")
    lines.append("|------|------|------|------|")
    for item in record["details"]:
        lines.append("| %s | %s | %s | %s |"
                     % (item["no"], item["section"],
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
            lines.append("- %s（%s）：得分 %s / %s"
                         % (item["no"], item["section"],
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

    server_version = "LAExamServer/1.0"

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
            })

            return
        elif parsed.path == "/api/paper":
            self.handle_paper(parse_qs(parsed.query))

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
            "details": details[:80],
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
    print("线性代数考试模拟系统已启动： http://127.0.0.1:%d/" % port)
    print("矩阵可视化实验台： http://127.0.0.1:%d/viz.html" % port)
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
