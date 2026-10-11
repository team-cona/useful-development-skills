"""토스 기술 블로그(2024~2026) 글 227편의 분포와 초안을 비교한다.

usage: python3 style_check.py <draft.md> [--cat Engineering|Design|all]

초안 표기: 그림은 `![설명](경로)` 또는 `[이미지: ...]` 한 줄, 콜아웃은 `> [!NOTE]`/`[콜아웃 박스 시작]`,
소제목은 ##/###, 굵은 글씨는 **...**. 코드 블록(```)은 문장 집계에서 뺀다.
"""
import json, os, re, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = json.load(open(os.path.join(HERE, "baseline.json"), encoding="utf-8"))

END = {
    "요체": r"(요|죠|까요\?|나요\?|죠\?|요\?)[.!?]?$",
    "합쇼체": r"(니다|니까\?)[.!?]?$",
    "평서체": r"(?<!니)다[.!]?$",
}

# 토스 글에 거의 항상 나오는 표지. (이름, 정규식, 토스 글 중 등장 비율)
SIGNATURES = [
    ("'~는데요' 연결", r"는데요[.?]|인데요[.?]|었는데요|았는데요", 0.55),
    ("'~죠' 맞장구", r"죠[.?]", 0.85),
    ("'그래서/하지만/그런데'로 여는 문장", r"(^|\n|\. )(그래서|하지만|그런데)", 0.90),
    ("1인칭 '저희/저는/제가'", r"저희|저는|제가", 0.85),
    ("숫자 근거", r"\d+(\.\d+)?\s?(%|배|ms|초|분|시간|일|개|건|명|만|억|GB|MB|TB|p)", 0.90),
    ("자문자답 질문(~까요?)", r"까요\?|을까\?|일까\?", 0.70),
]


def load(path):
    t = open(path, encoding="utf-8").read()
    if t.startswith("---\n"):
        t = t.split("---\n", 2)[2]
    lines = [l.rstrip() for l in t.splitlines() if l.strip()]
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return lines


def is_fig(l):
    return l.startswith(("[이미지", "![", "[그림"))


def sentences(lines):
    out, inc = [], False
    for l in lines:
        if l.startswith("```"):
            inc = not inc
            continue
        if inc or is_fig(l) or l.startswith(("#", "|", "[콜아웃", "[표", "[캡션")):
            continue
        l = re.sub(r"^(>\s*(\[![A-Z]+\])?\s*|- |\d+\. |\s)+", "", l)
        for s in re.split(r"(?<=[.?!])\s+", l):
            s = s.strip()
            if len(s) > 4:
                out.append(s)
    return out


def metrics(lines):
    sents = sentences(lines)
    ends = {k: 0 for k in END}
    for s in sents:
        s2 = s.replace("**", "").rstrip(" )\"'”’*`")
        for k, rx in END.items():
            if re.search(rx, s2):
                ends[k] += 1
                break
    body = [l for l in lines if not is_fig(l)]
    chars = max(sum(len(l) for l in body), 1)
    k = chars / 1000
    n = max(len(sents), 1)
    paras = [l for l in lines if not l.startswith(("[", "!", "#", "-", ">", "```", "|")) and not re.match(r"\d+\. ", l)]
    text = "\n".join(lines)
    prose = [l for l in lines if not l.startswith(("[", "!", "#", "-", ">", "```", "|", "*")) and not re.match(r"\d+\. ", l) and len(l) > 20]
    nsent = lambda p: len([s for s in re.split(r"(?<=[.?!])\s+", p) if len(s) > 4])
    plen = [len(p) for p in prose] or [0]
    heads = [re.sub(r"^#+ ", "", l).replace("**", "").strip() for l in lines if re.match(r"#{2,3} ", l)]
    sq = sum(h.endswith("?") or bool(re.search(r"(요|다|죠)[.!]?$", h)) for h in heads)
    return {
        "문장·질문형 소제목 비율": sq / max(len(heads), 1),
        "한 문장 문단 비율": sum(nsent(p) == 1 for p in prose) / max(len(prose), 1),
        "문단 길이 편차(CV)": (st.pstdev(plen) / st.mean(plen)) if st.mean(plen) else 0,
        "요체 비율": ends["요체"] / n,
        "합쇼체 비율": ends["합쇼체"] / n,
        "평서체(~다) 비율": ends["평서체"] / n,
        "평균 문장 길이": st.mean([len(s) for s in sents] or [0]),
        "평균 문단 길이": st.mean([len(p) for p in paras] or [0]),
        "소제목/1k자": sum(bool(re.match(r"#{2,4} ", l)) for l in lines) / k,
        "그림/1k자": sum(is_fig(l) for l in lines) / k,
        "굵은글씨/1k자": len(re.findall(r"\*\*[^*]+\*\*", text)) / k,
        "질문문장 비율": sum(s.rstrip("*").endswith("?") for s in sents) / n,
        "목록줄 비율": sum(bool(re.match(r"\s*(- |\d+\. )", l)) for l in lines) / max(len(lines), 1),
        "본문 글자수": chars,
    }


def main():
    draft = sys.argv[1]
    cat = sys.argv[sys.argv.index("--cat") + 1] if "--cat" in sys.argv else "all"
    ref = BASE[cat]
    lines = load(draft)
    me = metrics(lines)
    text = "\n".join(l for l in lines if not is_fig(l))
    print(f"# style_check: {os.path.basename(draft)}  (기준: 토스 글 {ref['n']}편, 분야={cat})")
    print(f"{'지표':16s} {'초안':>8s}   {'토스 p10 ~ p90 (중앙값)':>28s}  판정")
    ok_n = 0
    for k, v in me.items():
        b = ref["metrics"][k]
        ok = b["p10"] <= v <= b["p90"]
        ok_n += ok
        print(f"{k:16s} {v:8.2f}   {b['p10']:8.2f} ~ {b['p90']:8.2f} ({b['p50']:7.2f})  {'OK' if ok else '벗어남'}")
    print(f"\n분포 안 지표: {ok_n}/{len(me)}")

    print("\n# 토스 글에서 드문 표현 (초안 1만 자당 / 토스 글 상위 5%)")
    bad = 0
    for name, b in ref["phrases"].items():
        n = len(re.findall(b["rx"], text))
        rate = n / max(len(text), 1) * 10000
        flag = n >= 2 and rate > b["p95"]
        bad += flag
        if n:
            print(f"  {name:26s} {n}회 ({rate:5.2f})  기준 {b['p95']:5.2f}{'  <-- 과다' if flag else ''}")
    print(f"  과다 표현: {bad}개")

    print("\n# 과한 흉내 (토스 글 상위 10%보다 많으면 티가 남)")
    over_bad = 0
    for name, b in ref["over"].items():
        n = len(re.findall(b["rx"], text))
        rate = n / max(len(text), 1) * 1000
        if name in ("굵은 글씨", "단위 붙은 숫자"):
            flag = rate > b["rate_p90"] and n >= 3
            basis = f"1천 자당 {rate:4.1f} / 상한 {b['rate_p90']:.1f}"
        else:
            flag = n > max(b["cnt_p90"], 0) and n >= 1
            basis = f"상한 {b['cnt_p90']:.0f}회 (중앙값 {b['cnt_p50']:.0f})"
        over_bad += flag
        if n or flag:
            print(f"  {name:36s} {n:3d}회  {basis}{'  <-- 과다' if flag else ''}")
    numrx = r"\d+(\.\d+)?\s?(%|배|ms|초|분|개|건|명|만|억|KB|MB|GB|%p)"
    dense = [l for l in lines if not l.startswith(("|", "[", "!", "#")) and len(re.findall(numrx, l)) > 2]
    flag = len(dense) > ref["dense_para_p90"]
    over_bad += flag
    print(f"  {'숫자가 3개 넘게 몰린 문단':36s} {len(dense):3d}개  상한 {ref['dense_para_p90']}개{'  <-- 과다' if flag else ''}")
    for l in dense[:3]:
        print(f"      · {l[:70]}…")
    print(f"  과한 흉내: {over_bad}개")

    print("\n# 토스다운 표지 (있으면 좋지만 억지로 채우지 않는다)")
    miss = 0
    for name, rx, share in SIGNATURES:
        n = len(re.findall(rx, text))
        miss += n == 0
        print(f"  {name:28s} {n:3d}회  (토스 글 {share:.0%}에 등장)")
    score = (ok_n / len(me) * 50 + (1 - min(bad, 3) / 3) * 15
             + (1 - min(over_bad, 4) / 4) * 25 + (1 - min(miss, 3) / 3) * 10)
    print(f"\n정량 점수: {score:.0f}/100  (분포 50 + 드문 표현 15 + 과한 흉내 25 + 표지 10)")
    print("참고: 실제 토스 글은 중앙값 79~81점, 상위 25%가 88점이다. '과다'·'벗어남' 표시만 고치고 범위 안 지표는 건드리지 않는다.")
    if score >= 92:
        print("주의: 실제 토스 글 대부분보다 높은 점수다. 지표를 맞추려고 문장을 다듬었다면 그 수정을 되돌려도 된다.")


if __name__ == "__main__":
    main()
