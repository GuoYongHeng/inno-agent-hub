#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""活人感体检 —— 中文文案的包装语扫描器。

用法:
    python3 check_copy.py draft.md
    cat draft.md | python3 check_copy.py -
    python3 check_copy.py --list          # 查看全部检测规则

输出的是提示，不是判决。命中项逐条回答"这里真实存在什么"，
最终仍以三条判据（去名 / 证伪 / 念出声）人工裁定。
"""

import re
import sys

# ---------------------------------------------------------------- 检测规则
# (代号, 中文名, 说明, 追问, [正则])
RULES = [
    (
        "PREACH", "说教与共情越界",
        "在评价对方的处境，而不是描述它。品牌挪用当事人的自嘲即消费苦难。",
        "这句话是在描述对方的处境，还是在评价对方的处境？",
        [
            r"那是因为你[还太]?",
            r"你还年轻",
            r"你不懂",
            r"等你[长大成熟]",
            r"真正[懂的]{1,3}人[都才]",
            r"懂的人自然懂",
            r"我[懂知道]{1,2}你[的很]",
            r"别再.{0,8}了",
            r"其实你[需要想要]{2}",
            r"生活的毒打",
            r"成年人的世界",
            r"你值得拥有",
            r"你配得上",
            r"等一个.{0,6}的人",
            r"社畜|打工人的宿命|牛马",
        ],
    ),
    (
        "FAKE_INTIMACY", "故作亲昵",
        "用称呼和语气词冒充关系。关系是攒出来的，不是称呼出来的。",
        "把称呼和语气词删掉，这句话的信息量变了吗？没变就是在充数。",
        [
            r"宝子|宝宝们|宝儿",
            r"家人们|谁懂啊",
            r"集美|铁子|盆友",
            r"亲爱的.{0,6}朋友们",
            r"小可爱|小仙女",
            r"绝绝子|冲鸭|yyds|awsl|吼不吼",
            r"[哦呢啦哒]～|～+",
            r"一下下|么么[哒哒]",
        ],
    ),
    (
        "ABSTRACT", "抽象套话",
        "被提纯过的词，滤掉了场景、温度和生活痕迹，只剩正确但空洞的结论。",
        "这个词背后，具体发生了什么动作？谁做的？做了几次？在哪做的？",
        [
            r"匠心|工匠精神",
            r"赋能|助力|打造|深耕|布局",
            r"闭环|生态|抓手|颗粒度|心智|链路(?!异常)",
            r"一站式|全方位|全流程|多维度|沉浸式",
            r"致力于|竭诚|用心服务|贴心服务|无微不至",
            r"极致(?:体验|享受|品质)|卓越|一流|领先|高端大气",
            r"优质|严选|精心[挑选打造]|品质保证|品质之选",
            r"加强管理|提高.{0,4}意识|落实.{0,4}责任|高度重视",
            r"全面提升|持续优化|保驾护航|赋予新的",
            r"以[客用]户为中心|用户至上",
            r"新篇章|新征程|新高度|里程碑",
        ],
    ),
    (
        "BUREAU", "公文腔",
        "主语是发布方，动作是免责。把主语换成读者，句子自然就活了。",
        "如果当面说这件事，第一句话会怎么开口？",
        [
            r"请广大|敬请知悉|望周知|特此[通公]告|特此通知",
            r"现将.{0,10}[通知如下事项]",
            r"如有不便.{0,6}谅解|敬请谅解",
            r"按照.{0,6}相关规定|根据.{0,6}(?:上级|相关)(?:要求|规定|精神)",
            r"务必[提高确保严格]|切实[加强做好保障]|严格[遵守执行落实]",
            r"积极响应|大力推进|统筹推进",
            r"共同[守护营造维护]",
            r"兹[定有]|谨此|莅临|共襄",
        ],
    ),
    (
        "AI_TONE", "AI 腔",
        "用结构冒充内容：对仗、递进、总分让句子读起来完整，信息量却是零。",
        "删掉这个连接结构，剩下的信息还在吗？不在就说明整句是空的。",
        [
            r"不仅仅?是.{0,16}更是",
            r"在.{0,12}的(?:今天|时代|当下|背景下)",
            r"随着.{0,12}的(?:发展|到来|普及|深入)",
            r"让我们一起|一起来看看吧",
            r"值得(?:注意|一提)的是",
            r"综上所述|总而言之|总的来说",
            r"无论是.{0,16}还是.{0,16}都",
            r"不可否认|毋庸置疑|众所周知",
            r"首先.{0,80}其次.{0,80}最后",
            r"开启.{0,8}新[篇章时代]",
            r"从.{0,10}到.{0,10}，(?:是|见证)",
            r"这不[仅只].{0,12}，(?:更|而是)",
        ],
    ),
    (
        "EMPTY_PROMISE", "空承诺",
        "无法被验证的承诺等于没有承诺，还消耗一次信任。",
        "换成一个数字、一个时间点、一个人名或岗位，说不说得出口？",
        [
            r"更好的[服务体验]|更优的[服务体验]",
            r"尽最大努力|尽[快早]处理|尽[快早]为您",
            r"第一时间",
            r"相关人员|有关部门|专人跟进(?!，)",
            r"视情况(?:而定)?|酌情",
            r"耐心等待|敬请期待",
            r"我们(?:将|会)持续|不断改进",
        ],
    ),
]

# 具体信号 A：数字、单位、时间、中文数量词
NUMERIC = re.compile(
    r"\d+\s*[:：]\d+"
    r"|\d+\s*(?:点|分钟|分|秒|小时|天|周|月|年|号|米|公里|厘米|平米|平方米|克|斤|吨|元|块|次|遍|层|楼|人|家|台|部|条|张|件|只|个|%|％)"
    r"|[二两三四五六七八九十百千万][一二三四五六七八九十百千万]*\s*(?:个|只|件|条|张|台|部|次|遍|层|楼|米|元|块|分|秒|天|号|点|年|月|日|斤|克|吨|杯|份|步|趟|家|人|班)"
    r"|一\s*(?:楼|层|米|元|块|分钟|秒|天|号|点|年|月|日|斤|克|吨|杯|趟|遍)"
    r"|\d+"
)

# 具体信号 B：可被拍下来的名词（场所 / 物件 / 交通 / 身体 / 时间锚）
# 这个词表永远不可能全，只用来把"完全没有实物"的文案筛出来；
# 判断名词是否具体，最终仍靠人做去名测试。
CONCRETE_NOUN = re.compile(
    r"车间|饭堂|食堂|后厨|仓库|库房|货架|工位|前台|门口|门卫|走廊|楼道|电梯|台阶|扶手|"
    r"一楼|二楼|三楼|楼下|楼上|院子|操场|停车场|会议室|办公室|人事处|窗口|柜台|收银|试衣间|"
    r"空调|电视|冰箱|风扇|插座|充电|饮水机|微波炉|打印机|摄像头|门禁|钥匙|工牌|雨伞|椅子|桌子|"
    r"泥头车|货车|叉车|电动车|摩托|自行车|地铁|公交|高铁|快递|包裹|中转仓|头盔|口罩|安全帽|"
    r"公路|马路|路口|红绿灯|人行道|工地|车位|"
    r"发票|收据|单据|台账|报表|简历|邮箱|电话|短信|微信群|二维码|小票|"
    r"孩子|小孩|老人|同事|师傅|店员|保安|阿姨|司机|工人|老板|"
    r"下雨|暴雨|台风|降温|停电|停水|断网"
)

def concrete_hits(text):
    return len(NUMERIC.findall(text)) + len(CONCRETE_NOUN.findall(text))


SECOND = re.compile(r"你|您|咱|自己|各位")
FIRST = re.compile(r"我们|我司|本公司|本店|本平台|本厂|本司|敝司")
BANG = re.compile(r"[!！]")
SENT_SPLIT = re.compile(r"[。！？!?；;\n]+")


def load(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def scan(text):
    lines = text.splitlines()
    found = []  # (code, name, why, ask, lineno, line, matched)
    for code, name, why, ask, pats in RULES:
        for pat in pats:
            rx = re.compile(pat)
            for i, line in enumerate(lines, 1):
                for m in rx.finditer(line):
                    found.append((code, name, why, ask, i, line.strip(), m.group(0)))
    return found


def metrics(text):
    body = re.sub(r"\s", "", text)
    n = len(body) or 1
    concrete = concrete_hits(text)
    second = len(SECOND.findall(text))
    first = len(FIRST.findall(text))
    bang = len(BANG.findall(text))
    sents = [s.strip() for s in SENT_SPLIT.split(text) if s.strip()]
    lens = [len(re.sub(r"\s", "", s)) for s in sents] or [0]
    return {
        "chars": n,
        "concrete": concrete,
        "concrete_density": concrete * 100.0 / n,
        "second": second,
        "first": first,
        "bang_density": bang * 100.0 / n,
        "avg_sent": sum(lens) / float(len(lens)),
        "long_sents": [s for s, L in zip(sents, lens) if L > 45],
    }


def bar(ok):
    return "OK  " if ok else "!!  "


def report(text):
    found = scan(text)
    m = metrics(text)

    print("=" * 68)
    print("活人感体检")
    print("=" * 68)

    # ---- 命中
    by_code = {}
    for f in found:
        by_code.setdefault(f[0], []).append(f)

    if not found:
        print("\n[命中] 词表层面没抓到东西。")
    else:
        print("\n[命中] 共 %d 处\n" % len(found))
        for code, name, why, ask, _pats in RULES:
            items = by_code.get(code)
            if not items:
                continue
            print("-" * 68)
            print("%s  %s（%d 处）" % (code, name, len(items)))
            print("  为什么是问题：%s" % why)
            print("  改写时先回答：%s" % ask)
            seen = set()
            for _c, _n, _w, _a, ln, line, word in items:
                key = (ln, word)
                if key in seen:
                    continue
                seen.add(key)
                snippet = line if len(line) <= 46 else line[:46] + "…"
                print("    L%-4d 「%s」  ← %s" % (ln, word, snippet))
            print()

    # ---- 指标
    print("-" * 68)
    print("[指标]\n")
    ok_concrete = m["concrete_density"] >= 1.5
    print("%s具体度      每百字 %.1f 个可拍摄信号（数字/单位/时间/实物名词）  参考线 >= 1.5"
          % (bar(ok_concrete), m["concrete_density"]))
    if not ok_concrete:
        print("      现场信息不足。回到 Step 1 第 2 问：这里真实存在什么？")
    if m["chars"] < 60:
        print("      正文不足 60 字，密度值噪声大，以命中项和三条判据为准。")
    print("      名词词表不可能全，只筛掉完全没有实物的文案；具体与否仍靠人做去名测试。")

    ok_aud = m["second"] >= m["first"] and m["second"] > 0
    print('%s对象感      你/您/自己/各位 %d 次 vs 我们/本公司 %d 次  目标 前者 >= 后者且不为 0'
          % (bar(ok_aud), m["second"], m["first"]))
    if m["second"] == 0 and m["chars"] > 40:
        print("      通篇没有指向读者的词，是在广播不是在说话。先选定一个具体的人再写。")
    elif not ok_aud:
        print("      主语偏向发布方，多半在自我表达。把每句的主语翻过来试试。")

    ok_bang = m["bang_density"] <= 1.0
    print("%s感叹号      每百字 %.1f 个  目标 <= 1.0" % (bar(ok_bang), m["bang_density"]))
    if not ok_bang:
        print("      语气强度替代不了信息强度。删掉感叹号，看句子还剩什么。")

    ok_len = m["avg_sent"] <= 30
    print("%s句长        平均 %.0f 字  目标 <= 30（一句只说一件事）"
          % (bar(ok_len), m["avg_sent"]))
    for s in m["long_sents"][:3]:
        print("      过长：%s…" % s[:40])

    # ---- 结论
    critical = len(by_code.get("PREACH", [])) + len(by_code.get("FAKE_INTIMACY", []))
    metric_fail = sum(
        1 for x in (ok_concrete, ok_aud, ok_bang, ok_len) if not x
    )
    print()
    print("=" * 68)
    if critical:
        verdict = "重写。命中说教/假亲昵红线 %d 处——这类问题改词没用，动机不对。" % critical
    elif len(found) >= 5 or not ok_concrete:
        verdict = "需要大改。先补现场信息，再逐条处理命中词。"
    elif found:
        verdict = "需要改。问题局部，按命中项逐句替换即可。"
    elif metric_fail:
        verdict = ("没命中禁词，但指标不过——大概率是通篇观点陈述："
                   "句子都正确，就是没有现场和对方。先走一遍去名测试。")
    else:
        verdict = "机器这边没抓到问题。"
    print("[结论] %s" % verdict)
    print("""
这是提示不是判决。最终过三条判据：
  1 去名测试   删掉品牌/主体名，还剩多少信息？
  2 证伪测试   这句话能被验证或推翻吗？
  3 念出声测试 能对着一个具体的人念出来而不尴尬吗？
以及一句真诚自检：这句话是真的为对方好，还是只想让对方觉得我很真诚？""")
    return 0 if (not critical and not found and not metric_fail) else 1


def list_rules():
    for code, name, why, ask, pats in RULES:
        print("\n%s  %s" % (code, name))
        print("  %s" % why)
        print("  追问：%s" % ask)
        for p in pats:
            print("    - %s" % p)
    print("\n具体信号 · 数字/单位：\n    %s" % NUMERIC.pattern)
    print("\n具体信号 · 实物名词：\n    %s" % CONCRETE_NOUN.pattern)


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[1] == "--list":
        list_rules()
        return 0
    try:
        text = load(argv[1])
    except OSError as e:
        print("读不了文件：%s" % e, file=sys.stderr)
        return 2
    if not text.strip():
        print("空文本。", file=sys.stderr)
        return 2
    return report(text)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
