#!/usr/bin/env python3
"""结构与难度阶梯校验：python3 check_homework.py homework.json

只检查"可客观判定"的东西；题目内容是否正确由 verify_items.py 与读回门禁负责。
退出码 0 = 无 ERROR（可能有 WARN）；1 = 有 ERROR，必须修。
"""
import re
import statistics
import sys
from collections import Counter

sys.path.insert(0, __import__("os").path.dirname(__file__))
from hw_common import (PROFILE_DIMS, STEP_KEY, as_list, demand, is_mc, items_of,  # noqa: E402
                       layer_name, load)

ERR, WARN = [], []


def err(m):
    ERR.append(m)


def warn(m):
    WARN.append(m)


REQUIRED_META = ["subject", "grade", "topic", "lesson_goal", "time_budget_min"]
REQUIRED_ITEM = ["id", "layer", "type", "stem", "answer", "solution", "objective", "profile", "p_est", "source", "time_min"]
JARGON = ["分层", "脚手架", "支架", "难度画像", "设计意图", "错因", "干扰项", "考查点", "认知要求",
          "A层", "B层", "C层", "学困生", "后进生", "优等生"]
ANSWER_LEAK = re.compile(r"(【答案】|【解析】|答案[:：]|正确答案[是为:：]|正确选项[是为:：])")


def check_meta(hw):
    m = hw.get("meta", {})
    for k in REQUIRED_META:
        if not m.get(k):
            err(f"meta.{k} 缺失")
    if not as_list(m.get("curriculum_refs")):
        err("meta.curriculum_refs 为空：至少写一条对应的课标内容要求/学业要求（用自己的话概括，不编条文号）")
    if not as_list(m.get("prerequisites")):
        warn("meta.prerequisites 为空：基础层的支架应指向具名的前置知识")


def check_layers(hw):
    layers = hw.get("layers", [])
    ids = [L.get("id") for L in layers]
    if len(layers) < 2:
        err("layers 少于 2 层，不是分层作业")
    if len(set(ids)) != len(ids):
        err(f"layers id 重复: {ids}")
    for L in layers:
        if not L.get("who"):
            warn(f"层 {L.get('id')} 未写 who（谁做：全体必做/多数选做/学有余力选做）")
        if not items_of(hw, L.get("id")):
            err(f"层 {L.get('id')} 没有题目")
    return ids


def check_items(hw, layer_ids):
    items = hw.get("items", [])
    seen = set()
    for it in items:
        iid = it.get("id", "?")
        if iid in seen:
            err(f"题号重复 {iid}")
        seen.add(iid)
        for k in REQUIRED_ITEM:
            if it.get(k) in (None, "", [], {}):
                err(f"{iid}: 缺字段 {k}")
        if it.get("layer") not in layer_ids:
            err(f"{iid}: layer={it.get('layer')} 不在 layers 中")
        p = it.get("profile") or {}
        for k in list(PROFILE_DIMS) + [STEP_KEY]:
            if not isinstance(p.get(k), (int, float)):
                err(f"{iid}: profile.{k} 缺失或非数字")
        sol = as_list(it.get("solution"))
        s = p.get(STEP_KEY)
        if isinstance(s, (int, float)) and sol and abs(len(sol) - s) > 2:
            warn(f"{iid}: 标注推理步数 s={s}，但解析写了 {len(sol)} 步——标注与解析应一致")
        # student-facing text hygiene
        student_text = it.get("stem", "") + " ".join(as_list(it.get("options"))) + str(it.get("scaffold") or "")
        if ANSWER_LEAK.search(student_text):
            err(f"{iid}: 学生可见文字里出现答案/解析标记")
        for j in JARGON:
            if j in student_text:
                warn(f"{iid}: 学生可见文字含教学术语「{j}」")
        for ref in re.findall(r"\{\{\s*([A-Za-z0-9_-]+)\s*\}\}", student_text + str(it.get("figure") or "")):
            if ref not in {x.get("id") for x in hw.get("items", [])}:
                err(f"{iid}: 引用了不存在的题目 {{{{{ref}}}}}")
        if re.search(r"第[一二三四]关第|[ABC]层第|第\s*\d+\s*题", student_text):
            warn(f"{iid}: 题干里直接写了'第几题/第几关第几题'——引用别的题请写 {{{{题目id}}}}，由渲染自动编号")
        sit = it.get("situation")
        if isinstance(sit, dict) and sit.get("used"):
            for k in ("role", "realism"):
                if not sit.get(k):
                    err(f"{iid}: 用了情境但 situation.{k} 为空（情境闸门必须写明情境承担什么、数据为何合理）")
        if it.get("layer") != (layer_ids[0] if layer_ids else None) and not it.get("upgrade"):
            err(f"{iid}: 非基础层题目必须写 upgrade（相对哪道题、在哪个维度上升级）")
        if not it.get("check"):
            err(f"{iid}: 缺 check（验证方式与结果）")
        if is_mc(it):
            check_mc(it)


def check_mc(it):
    iid = it["id"]
    opts = as_list(it.get("options"))
    if len(opts) < 3:
        err(f"{iid}: 选择题选项少于 3 个")
    bodies = [re.sub(r"^\s*[A-HＡ-Ｈ][\.．、:：\s]\s*", "", o).strip() for o in opts]
    if len(set(bodies)) != len(bodies):
        err(f"{iid}: 选项内容重复")
    ans = str(it.get("answer", "")).strip().upper()
    letters = re.findall(r"[A-H]", ans)
    if not letters:
        err(f"{iid}: 选择题答案应为选项字母，现为「{it.get('answer')}」")
        return
    dis = it.get("distractors") or {}
    letters_all = [chr(65 + i) for i in range(len(opts))]
    for L in letters_all:
        if L not in letters and not dis.get(L):
            err(f"{iid}: 干扰项 {L} 没写对应错因（distractors.{L}）")
    lens = [len(b) for b in bodies]
    if lens and len(letters) == 1:
        ki = ord(letters[0]) - 65
        if 0 <= ki < len(lens) and lens[ki] == max(lens) and max(lens) >= 1.6 * statistics.median(lens) and max(lens) > 8:
            warn(f"{iid}: 正确选项明显最长，可能凭长度猜中")


def check_figures(hw):
    try:
        import figure as F
    except Exception as e:  # noqa
        warn(f"无法加载 figure.py：{e}")
        return
    subj = str((hw.get("meta") or {}).get("subject", ""))
    for it in hw.get("items", []):
        iid = it.get("id")
        spec = it.get("figure_spec")
        if spec:
            try:
                F.render(spec)
            except Exception as e:  # noqa
                err(f"{iid}: figure_spec 画不出来：{e}")
        mentions = "如图" in str(it.get("stem", "")) or "图中" in str(it.get("stem", ""))
        if mentions and not spec and not it.get("figure"):
            err(f"{iid}: 题干说'如图'，但没有 figure_spec 也没有 figure")
        elif it.get("figure") and not spec and "数学" in subj:
            warn(f"{iid}: 数学题只有文字描述的图，请写 figure_spec 让脚本画出来（见 references/figures.md）")


def check_passages(hw):
    ids = {P.get("id") for P in as_list(hw.get("passages"))}
    for P in as_list(hw.get("passages")):
        if not P.get("text"):
            err(f"材料 {P.get('id')} 没有 text")
        if not P.get("source_note"):
            err(f"材料 {P.get('id')} 没有 source_note（原创/改写/出处——古诗文、史料须准确）")
    used = set()
    for it in hw.get("items", []):
        for pid in as_list(it.get("passage")):
            used.add(pid)
            if pid not in ids:
                err(f"{it.get('id')}: 引用的材料 {pid} 不存在")
    for pid in ids - used:
        warn(f"材料 {pid} 没有任何题目引用")


def check_mc_positions(hw):
    keys = []
    for it in hw.get("items", []):
        if is_mc(it) and it.get("type") not in {"多选题", "不定项选择"}:
            m = re.findall(r"[A-H]", str(it.get("answer", "")).upper())
            if len(m) == 1:
                keys.append(m[0])
    if len(keys) >= 4:
        c = Counter(keys)
        top, n = c.most_common(1)[0]
        if n / len(keys) > 0.5:
            warn(f"单选题答案过于集中：{dict(c)}（{top} 占 {n}/{len(keys)}）")
    run = 1
    for a, b in zip(keys, keys[1:]):
        run = run + 1 if a == b else 1
        if run >= 3:
            warn(f"连续 {run} 道单选题答案都是 {b}")
            break


def check_ladder(hw, layer_ids):
    """难度阶梯：层中位数严格递增；后层每题高于前层中位数；最高层至少一道 g>=2。"""
    meds = []
    for lid in layer_ids:
        ds = [demand(it.get("profile")) for it in items_of(hw, lid)]
        ds = [d for d in ds if d is not None]
        meds.append(statistics.median(ds) if ds else None)
    report = []
    for lid, md in zip(layer_ids, meds):
        report.append(f"{lid}({layer_name(hw, lid)}) 中位 {md}")
    print("难度画像：" + " < ".join(report))
    for i in range(1, len(layer_ids)):
        a, b = meds[i - 1], meds[i]
        if a is None or b is None:
            continue
        if b - a < 1.0:
            err(f"层 {layer_ids[i]} 与 {layer_ids[i-1]} 难度中位差 {round(b-a,2)} < 1：阶梯不明显（是不是只换了数字？）")
        for it in items_of(hw, layer_ids[i]):
            d = demand(it.get("profile"))
            if d is not None and d <= a:
                err(f"{it['id']}: 难度画像 {d} 不高于上一层中位 {a}，放错层或没有真正升级")
    if layer_ids:
        top = items_of(hw, layer_ids[-1])
        if top and not any((it.get("profile") or {}).get("g", 0) >= 2 for it in top):
            err(f"最高层 {layer_ids[-1]} 没有一道认知要求 g≥2（分析推理/评价创造）的题")
        base = items_of(hw, layer_ids[0])
        if base and not any((it.get("profile") or {}).get("g", 0) >= 1 for it in base):
            warn(f"基础层 {layer_ids[0]} 全是识记题（g=0），基础层也应有理解/应用")
    # within-layer: by estimated difficulty coefficient, items should get harder (p_est non-increasing)
    for lid in layer_ids:
        ps = [(it["id"], it.get("p_est")) for it in items_of(hw, lid) if isinstance(it.get("p_est"), (int, float))]
        for (i1, p1), (i2, p2) in zip(ps, ps[1:]):
            if p2 > p1 + 0.05:
                warn(f"层 {lid} 内 {i2}（p={p2}）比前一题 {i1}（p={p1}）更容易，层内应由易到难排列")


P_RANGE = [(0.85, 0.95), (0.65, 0.80), (0.40, 0.60)]


def check_p_est(hw, layer_ids):
    meds = []
    for i, lid in enumerate(layer_ids):
        ps = [it.get("p_est") for it in items_of(hw, lid) if isinstance(it.get("p_est"), (int, float))]
        for it in items_of(hw, lid):
            p = it.get("p_est")
            if isinstance(p, (int, float)) and not 0 < p <= 1:
                err(f"{it['id']}: p_est={p} 应在 (0,1]")
        meds.append(statistics.median(ps) if ps else None)
        if ps and len(layer_ids) == 3:
            lo, hi = P_RANGE[i]
            md = meds[-1]
            if not (lo - 0.05 <= md <= hi + 0.05):
                warn(f"层 {lid} 预估难度系数中位 {md} 偏离参考区间 {lo}-{hi}")
    print("预估难度系数中位：" + " > ".join(f"{l}:{m}" for l, m in zip(layer_ids, meds)))
    for i in range(1, len(meds)):
        if meds[i] is not None and meds[i - 1] is not None and meds[i] >= meds[i - 1]:
            err(f"层 {layer_ids[i]} 预估难度系数不低于上一层（{meds[i]} ≥ {meds[i-1]}）")
    for it in hw.get("items", []):
        src = it.get("source")
        if isinstance(src, dict) and src.get("kind") not in {"选编", "改编", "创编"}:
            err(f"{it['id']}: source.kind 应为 选编/改编/创编")
        note = str((src or {}).get("note", "")) if isinstance(src, dict) else ""
        if re.search(r"(第\s*\d+\s*页|\d{4}\s*年.{0,8}(中考|高考|期中|期末).{0,6}第\s*\d+\s*题)", note) and not (src or {}).get("verified"):
            warn(f"{it['id']}: 来源写了具体页码/真题题号但未标 verified=true——凭记忆的出处不要写具体页码题号")


def check_time(hw, layer_ids):
    """time_budget_min = 中等学生完成前两层（必做+第二层）的总时长；最高层为选做，另计。"""
    budget = (hw.get("meta") or {}).get("time_budget_min")
    if not isinstance(budget, (int, float)) or not layer_ids:
        return
    per = {lid: sum(float(it.get("time_min") or 0) for it in items_of(hw, lid)) for lid in layer_ids}
    core = layer_ids[:2] if len(layer_ids) >= 3 else layer_ids
    t_core = sum(per[l] for l in core)
    print(f"预计用时：各层 {per}；前两层合计 {t_core} 分钟；预算 {budget} 分钟")
    if t_core > budget * 1.15:
        err(f"前两层预计 {t_core} 分钟，超过预算 {budget} 分钟（中等学生做不完）")
    if t_core < budget * 0.6:
        warn(f"前两层只需 {t_core} 分钟，明显少于预算 {budget} 分钟")
    if per[layer_ids[0]] > budget * 0.6:
        warn(f"基础层 {per[layer_ids[0]]} 分钟，占预算过多，留给提升层的时间不够")


def check_upgrade_refs(hw):
    ids = {it.get("id") for it in hw.get("items", [])}
    for it in hw.get("items", []):
        up = it.get("upgrade")
        if isinstance(up, dict):
            if up.get("from") and up["from"] not in ids:
                err(f"{it['id']}: upgrade.from={up['from']} 不存在")
            if not up.get("dims"):
                err(f"{it['id']}: upgrade.dims 为空（说明在哪些维度上升了）")
            elif not set(as_list(up.get("dims"))) <= (set(PROFILE_DIMS) | {STEP_KEY}):
                err(f"{it['id']}: upgrade.dims 必须取自 k/s/c/r/o/g")
            if not up.get("how"):
                err(f"{it['id']}: upgrade.how 为空（一句话说清新增了什么思考，不能只是换数字）")
        elif up is not None and not isinstance(up, dict):
            err(f"{it['id']}: upgrade 应为对象 {{from, dims, how}}")


def check_checks(hw):
    for it in hw.get("items", []):
        ck = it.get("check") or {}
        if not isinstance(ck, dict):
            continue
        st = ck.get("status")
        if st and st != "pass":
            err(f"{it['id']}: 验证状态为 {st}，未通过的题不能交付")
        if ck.get("method") not in {"python", "blind", "both"}:
            err(f"{it['id']}: check.method 应为 python / blind / both")


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: python3 check_homework.py homework.json")
    hw = load(sys.argv[1])
    check_meta(hw)
    layer_ids = check_layers(hw)
    check_items(hw, layer_ids)
    check_upgrade_refs(hw)
    check_passages(hw)
    check_figures(hw)
    check_mc_positions(hw)
    check_ladder(hw, layer_ids)
    check_p_est(hw, layer_ids)
    check_time(hw, layer_ids)
    check_checks(hw)
    for w in WARN:
        print("WARN ", w)
    for e in ERR:
        print("ERROR", e)
    print(f"结果：{len(ERR)} 个 ERROR，{len(WARN)} 个 WARN")
    sys.exit(1 if ERR else 0)


if __name__ == "__main__":
    main()
