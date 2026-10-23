"""Shared helpers for the layered-homework scripts (no third-party deps)."""
import json
import sys
from pathlib import Path

LAYER_DEFAULT_NAMES = {"A": "基础巩固", "B": "能力提升", "C": "拓展挑战"}

# difficulty profile dimensions: key -> (中文名, 取值说明)
PROFILE_DIMS = {
    "k": ("知识/方法数", "0=单一 1=两个 2=三个及以上"),
    "c": ("条件呈现", "0=直接给出 1=需转化(文字/图表→关系) 2=隐含(需自己发现或构造)"),
    "r": ("情境/表征", "0=标准题型/熟悉模型 1=熟悉情境需建模 2=陌生或综合情境"),
    "o": ("开放度", "0=唯一答案 1=需说理/多法 2=开放构造/探究"),
    "g": ("认知要求", "0=识记理解 1=应用 2=分析推理 3=评价创造"),
}
STEP_KEY = "s"  # 关键推理步数 (int)

MC_TYPES = {"选择题", "单选题", "单项选择", "多选题", "不定项选择"}


def load(path):
    p = Path(path)
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"[JSON 解析失败] {p}: 第{e.lineno}行第{e.colno}列 {e.msg}")


def demand(profile):
    """Scalar 'design demand' index from an item's profile. Only used to compare layers."""
    if not isinstance(profile, dict):
        return None
    tot = 0.0
    for k in PROFILE_DIMS:
        v = profile.get(k, 0)
        tot += float(v) if isinstance(v, (int, float)) else 0
    s = profile.get(STEP_KEY, 1)
    s = float(s) if isinstance(s, (int, float)) else 1
    tot += min(s, 8) / 2.0
    return round(tot, 2)


def layer_name(hw, lid):
    for L in hw.get("layers", []):
        if L.get("id") == lid:
            return L.get("name") or LAYER_DEFAULT_NAMES.get(lid, lid)
    return LAYER_DEFAULT_NAMES.get(lid, lid)


def items_of(hw, lid):
    return [it for it in hw.get("items", []) if it.get("layer") == lid]


def is_mc(item):
    return item.get("type") in MC_TYPES or bool(item.get("options"))


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]
