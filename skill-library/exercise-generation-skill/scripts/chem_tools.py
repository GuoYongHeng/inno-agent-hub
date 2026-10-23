"""化学验算小工具（供 check.code 使用）：from chem_tools import atoms, balance, mr, AR

- atoms("Ca(OH)2") -> Counter({'O': 2, 'H': 2, 'Ca': 1})；支持括号、结晶水"CuSO4·5H2O"、离子电荷"CO3[2-]"
- balance(["Fe2O3","CO"], ["Fe","CO2"]) -> [1, 3, 2, 3]；不能唯一配平时返回 None
- mr("CaCO3") -> 100（相对分子质量，默认用初中教材常用相对原子质量 AR；可传入题干给定的 ar 字典）
注意：balance 只检查原子守恒（和电荷守恒），**不能**说明反应真的会发生（Cu + HCl 也能"配平"），反应事实要人工核对。
"""
from sympy import Matrix, Rational, igcd, ilcm
import re
from collections import Counter
def _parse(s):
    toks = re.findall(r"[A-Z][a-z]?|\d+|\(|\)", s)
    assert "".join(toks) == s, "化学式里有无法识别的字符: " + s
    stack, i = [Counter()], 0
    while i < len(toks):
        t = toks[i]; i += 1
        if t == "(":
            stack.append(Counter()); continue
        n = 1
        if i < len(toks) and toks[i].isdigit():
            n = int(toks[i]); i += 1
        if t == ")":
            for e, v in stack.pop().items(): stack[-1][e] += v*n
        else:
            stack[-1][t] += n
    assert len(stack) == 1, "括号不配对: " + s
    return stack[0]
def atoms(f):
    # 化学式 -> 原子计数。支持括号、结晶水（·）；离子电荷写在 [ ] 里，如 'CO3[2-]'
    total = Counter()
    for part in re.sub(r"\[.*?\]", "", f).split("·"):
        m = re.match(r"(\d*)(.*)", part)
        for e, v in _parse(m.group(2)).items(): total[e] += int(m.group(1) or 1)*v
    return total
def charge(f):
    m = re.search(r"\[(\d*)([+-])\]", f)
    return 0 if not m else (1 if m.group(2) == "+" else -1)*int(m.group(1) or 1)
def balance(lhs, rhs):
    # 求最小整数系数。零空间维数不为 1 时返回 None：说明反应物或生成物写错了，不能唯一配平
    sp = lhs + rhs; sg = [1]*len(lhs) + [-1]*len(rhs)
    els = sorted({e for f in sp for e in atoms(f)})
    rows = [[atoms(f)[e]*s for f, s in zip(sp, sg)] for e in els]
    if any(charge(f) for f in sp):
        rows.append([charge(f)*s for f, s in zip(sp, sg)])
    ns = Matrix(rows).nullspace()
    if len(ns) != 1:
        return None
    v = ns[0]*ilcm(*[x.q for x in ns[0]])
    v = v/igcd(*[int(x) for x in v])
    return [int(x) for x in (v if v[0] > 0 else -v)]


# 初中/高中教材常用相对原子质量（题干另给时以题干为准）
AR = {"H": 1, "C": 12, "N": 14, "O": 16, "Na": 23, "Mg": 24, "Al": 27, "Si": 28, "P": 31, "S": 32,
      "Cl": Rational(71, 2), "K": 39, "Ca": 40, "Mn": 55, "Fe": 56, "Cu": 64, "Zn": 65, "Ag": 108,
      "Ba": 137, "I": 127, "Br": 80, "Li": 7, "F": 19, "Ne": 20, "He": 4}


def mr(formula, ar=None):
    table = ar or AR
    return sum(table[e] * n for e, n in atoms(formula).items())
