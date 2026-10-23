#!/usr/bin/env python3
"""计算类题目的独立验算：python3 verify_items.py homework.json [--write]

对每道 check.method 为 "python" 或 "both" 的题：
  - 在独立子进程里运行 check.code（已 `from sympy import *`，并可用 math / fractions / itertools）。
    代码必须**只用题干给出的条件**重新算一遍，把最终结果赋给变量 `ans`。
  - 把 `ans` 与 check.expect 比较。expect 是一个 Python/sympy 表达式字符串，
    例如 "Rational(7,4)"、"[2, 3]"、"{x: 4}"、"Interval.Lopen(-3, Rational(7,4))"、"'B'"。
  - 数值/符号用 simplify(a-b)==0 判等；列表/元组逐项；集合/字典按元素；字符串去空白比较。
--write 会把 check.status(pass/fail) 与 check.detail 写回 json。
blind 类题目不在这里判定（见 references/verification.md 的读回门禁）。
缺 sympy 时会报错退出：先问用户是否安装，或改用 blind。
"""
import json
import subprocess
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hw_common import load  # noqa: E402

RUNNER = r'''
import sys, json, math, fractions, itertools
from sympy import *
from sympy import Interval, FiniteSet, Rational, sqrt, pi
def _eq(a, b):
    if isinstance(a, str) or isinstance(b, str):
        return str(a).replace(" ", "") == str(b).replace(" ", "")
    if isinstance(a, dict) and isinstance(b, dict):
        return set(map(str, a)) == set(map(str, b)) and all(_eq(a[k], b[[kk for kk in b if str(kk) == str(k)][0]]) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, (set, frozenset)) and isinstance(b, (set, frozenset)):
        return len(a) == len(b) and all(any(_eq(x, y) for y in b) for x in a)
    try:
        sa, sb = sympify(a), sympify(b)
        if isinstance(sa, Set) or isinstance(sb, Set):
            return sa == sb
        d = simplify(sa - sb)
        if d == 0:
            return True
        try:
            return abs(float(N(d))) < 1e-9
        except Exception:
            return False
    except Exception:
        return a == b
NS = {k: v for k, v in globals().items() if not k.startswith("__")}
NS["__name__"] = "__check__"
_pre = set(NS)
exec(compile(sys.stdin.read(), "<check>", "exec"), NS)
if "ans" not in NS:
    print(json.dumps({"ok": False, "detail": "代码没有给出变量 ans"})); sys.exit()
expect = eval(sys.argv[1], NS)
ok = _eq(NS["ans"], expect)
print(json.dumps({"ok": bool(ok), "detail": f"ans={NS['ans']!r} expect={expect!r}"}, ensure_ascii=False))
'''


def run_one(code, expect, timeout=30):
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(Path(__file__).parent) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    try:
        r = subprocess.run([sys.executable, "-c", RUNNER, expect], input=textwrap.dedent(code),
                           capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return False, "超时"
    out = r.stdout.strip().splitlines()
    if r.returncode != 0 or not out:
        tail = (r.stderr or "").strip().splitlines()[-3:]
        return False, "运行出错: " + " | ".join(tail)
    try:
        res = json.loads(out[-1])
    except json.JSONDecodeError:
        return False, "输出无法解析: " + out[-1][:200]
    return res["ok"], res["detail"]


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: python3 verify_items.py homework.json [--write]")
    try:
        import sympy  # noqa: F401
    except ImportError:
        sys.exit("缺少 sympy：先询问用户是否安装（python3 -m pip install sympy），或把计算题改为 blind 验证")
    path = Path(sys.argv[1])
    hw = load(path)
    n_fail = n_run = 0
    for it in hw.get("items", []):
        ck = it.get("check") or {}
        if ck.get("method") not in {"python", "both"}:
            continue
        n_run += 1
        if not ck.get("code") or not ck.get("expect"):
            ok, detail = False, "缺 check.code 或 check.expect"
        else:
            ok, detail = run_one(ck["code"], str(ck["expect"]))
        print(("PASS " if ok else "FAIL ") + f"{it.get('id')}: {detail}")
        if not ok:
            n_fail += 1
        if "--write" in sys.argv:
            ck["py_status"] = "pass" if ok else "fail"
            ck["py_detail"] = detail
            if ck.get("method") == "python":
                ck["status"] = ck["py_status"]
            elif ck.get("method") == "both" and not ok:
                ck["status"] = "fail"
            it["check"] = ck
    if "--write" in sys.argv:
        path.write_text(json.dumps(hw, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"验算 {n_run} 题，失败 {n_fail} 题")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
