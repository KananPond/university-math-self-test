# -*- coding: utf-8 -*-
"""
文件名：api_test.py
作者：ZCode（GLM）
日期：2026-11-08
版本：1.0
文件说明：
1. 端到端接口测试：抽题 → 实时得分 → 交卷判分 → 记录保存 → 闪电训练全流程。
2. 需要本地判分服务在跑（默认 http://127.0.0.1:8767）。
3. 用法： cd 考试服务 && python web_exam/tests/api_test.py [端口]
"""

import json
import os
import sys
import urllib.error
import urllib.request

WEB_EXAM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(WEB_EXAM_DIR)
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from bank import BANK, draw_paper  # noqa: E402

PORT = 8767
if len(sys.argv) > 1:
    PORT = int(sys.argv[1])
BASE = "http://127.0.0.1:%d" % PORT

failures = []
checks = 0


def check(name, condition, detail=""):
    """记录一条检查结果。"""
    global checks
    checks += 1
    if condition:
        print("  [通过] %s" % name)
    else:
        message = "  [失败] %s" % name
        if detail:
            message += " —— %s" % detail
        print(message)
        failures.append("%s %s" % (name, detail))


def get(path):
    """发起 GET 请求并返回解析后的 JSON。"""
    with urllib.request.urlopen(BASE + path, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def post(path, payload):
    """发起 POST 请求并返回解析后的 JSON。"""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        BASE + path, data=body,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def correct_answers(paper):
    """按服务端题库复原一份「全部答对」的作答。"""
    answers = {"choice": {}, "judge": {}, "fill": {}, "calc": {}}
    for section in paper["sections"]:
        for question in section["questions"]:
            if section["type"] == "choice":
                answers["choice"][question["id"]] = question["answer"]
            elif section["type"] == "judge":
                answers["judge"][question["id"]] = question["answer"]
            elif section["mode"] == "blanks":
                values = {}
                for index, blank in enumerate(question.get("blanks") or []):
                    answer = blank.get("answer")
                    if isinstance(answer, list):
                        answer = answer[0]
                    values[str(index)] = answer
                answers["calc"][question["id"]] = {"blanks": values}
            else:
                answer = question["answer"]
                if isinstance(answer, list):
                    answer = answer[0]
                answers["fill"][question["id"]] = answer

    return answers


def main():
    seed = 20261108

    print("【测试 1】服务状态")
    health = get("/api/health")
    check("健康检查返回 ok", health.get("ok") is True)
    check("题库总量为 76 题", health.get("bankTotal") == 76,
          "bankTotal=%r" % health.get("bankTotal"))

    print("【测试 2】抽题与答案隔离")
    paper_data = get("/api/paper?seed=%d" % seed)
    public = paper_data["paper"]
    check("返回种子与请求一致", paper_data["seed"] == seed)
    check("试卷为 100 分", public["total_score"] == 100)
    total_questions = sum(len(section["questions"])
                          for section in public["sections"])
    check("每卷题量为 32 题", total_questions == 32,
          "实际 %d 题" % total_questions)

    body = json.dumps(public, ensure_ascii=False)
    leaked = []
    for section in public["sections"]:
        for question in section["questions"]:
            if "answer" in question:
                leaked.append(question["id"])
            for blank in question.get("blanks") or []:
                if "answer" in blank:
                    leaked.append(question["id"])
            if "explain" in question:
                leaked.append(question["id"])
    check("前端拿不到答案与解析", not leaked, "泄漏：%s" % leaked[:5])
    check("序列化结果里没有 explain 字段", '"explain"' not in body)

    repeat = get("/api/paper?seed=%d" % seed)
    check("同种子试卷完全一致",
          json.dumps(repeat["paper"], sort_keys=True)
          == json.dumps(public, sort_keys=True))

    other = get("/api/paper?seed=%d" % (seed + 1))
    check("不同种子试卷不同",
          json.dumps(other["paper"]["sections"], sort_keys=True)
          != json.dumps(public["sections"], sort_keys=True))

    print("【测试 4】实时得分与交卷判分")
    server_paper = draw_paper(seed, BANK)
    answers = correct_answers(server_paper)

    live = post("/api/score", {"seed": seed, "answers": answers})
    check("全部答对时实时得分满分", live["score"] == 100,
          "得分 %r" % live["score"])
    check("实时得分统计了全部题目", live["total"] == 32)

    empty = post("/api/score", {"seed": seed, "answers": {}})
    check("未作答时得分为 0", empty["score"] == 0)
    check("未作答时已答数为 0", empty["answered"] == 0)

    graded = post("/api/grade", {"seed": seed, "answers": answers})
    check("交卷判分满分", graded["score"] == 100, "得分 %r" % graded["score"])
    check("逐题结果数量与题量一致", len(graded["results"]) == 32)
    check("每题都带解析",
          all(item.get("explain") for item in graded["results"]))

    print("【测试 5】错误作答的判分")
    wrong = {"choice": {}, "judge": {}, "fill": {}, "calc": {}}
    for section in server_paper["sections"]:
        for question in section["questions"]:
            if section["type"] == "choice":
                wrong["choice"][question["id"]] = (question["answer"] + 1) % 4
            elif section["type"] == "judge":
                wrong["judge"][question["id"]] = not question["answer"]
    zero = post("/api/grade", {"seed": seed, "answers": wrong})
    check("客观题全错时客观题得 0 分",
          all(item["score"] == 0 for item in zero["results"]
              if item["type"] in ("choice", "judge")),
          "存在客观题得分非 0")

    print("【测试 6】等价写法与比例给分")
    equivalent = {"choice": {}, "judge": {}, "fill": {}, "calc": {}}
    for section in server_paper["sections"]:
        for question in section["questions"]:
            if section["type"] == "choice":
                equivalent["choice"][question["id"]] = question["answer"]
            elif section["type"] == "judge":
                equivalent["judge"][question["id"]] = question["answer"]
            elif section["mode"] == "blanks":
                values = {}
                for index, blank in enumerate(question.get("blanks") or []):
                    answer = blank.get("answer")
                    if isinstance(answer, list):
                        answer = answer[0]
                    values[str(index)] = answer.replace("/", " / ")
                equivalent["calc"][question["id"]] = {"blanks": values}
            else:
                answer = question["answer"]
                if isinstance(answer, list):
                    answer = answer[0]
                equivalent["fill"][question["id"]] = answer.replace("/", " / ")
    eq_result = post("/api/grade", {"seed": seed, "answers": equivalent})
    check("去掉空格后仍判满分", eq_result["score"] == 100,
          "得分 %r" % eq_result["score"])

    print("【测试 7】记录保存")
    saved = post("/api/save", {
        "paperId": str(seed),
        "paperTitle": "复变函数考试模拟卷（测试）",
        "savedAt": "2026-11-08 12:00:00",
        "elapsedText": "12:00",
        "seed": seed,
        "score": 100,
        "totalScore": 100,
        "details": graded["results"][:5],
    })
    check("记录保存成功", saved.get("ok") is True and saved.get("file"))

    print("【测试 8】闪电训练")
    drill = get("/api/drill?seed=555&count=12")
    check("训练题数量正确", len(drill["items"]) == 12,
          "实际 %d" % len(drill["items"]))
    check("训练题不含答案",
          all("answer" not in item for item in drill["items"]))
    check("训练题不含解析",
          all("explain" not in item for item in drill["items"]))

    item = drill["items"][0]
    server_item = None
    from bank import drill_gen
    server_item = drill_gen.item_by_id(555, item["id"])
    check("训练题可按种子复原", server_item is not None)

    if server_item:
        if server_item.get("kind") == "blanks":
            good = {}
            for index, blank in enumerate(server_item["blanks"]):
                answer = blank.get("answer")
                if isinstance(answer, list):
                    answer = answer[0]
                good[str(index)] = answer
            payload = {"id": item["id"], "seed": 555, "response": good}
        else:
            payload = {"id": item["id"], "seed": 555,
                       "response": server_item["answer"]}
        right = post("/api/drill/check", payload)
        check("训练题答对时判定正确", right.get("correct") is True)
        check("训练题判定返回解析", bool(right.get("explain")))

        if server_item.get("kind") == "blanks":
            bad = {"0": "乱写"}
            payload = {"id": item["id"], "seed": 555, "response": bad}
        else:
            payload = {"id": item["id"], "seed": 555, "response": "乱写"}
        wrong_result = post("/api/drill/check", payload)
        check("训练题答错时判定为错", wrong_result.get("correct") is False)

    print("【测试 9】错题本")
    registered = post("/api/drill/wrong", {"id": item["id"], "seed": 555})
    check("错题登记成功", registered.get("ok") is True and registered.get("wrongId"))
    book = get("/api/drill/wrongbook")
    check("错题本含刚登记的题",
          any(entry.get("wrongId") == registered.get("wrongId")
              for entry in book.get("items", [])))
    check("错题本不下发答案",
          all("answer" not in entry for entry in book.get("items", [])))
    removed = post("/api/drill/mastered", {"wrongId": registered.get("wrongId")})
    check("错题可以从错题本移除", removed.get("removed") is True)

    print("")
    if failures:
        print("测试未通过，共 %d 项失败（执行 %d 项检查）："
              % (len(failures), checks))
        for item in failures:
            print("  - %s" % item)

        return 1

    print("全部通过（执行 %d 项检查）。" % checks)

    return 0


if __name__ == "__main__":
    sys.exit(main())
