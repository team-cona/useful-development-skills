"""Corpus-level quantitative style stats for toss.tech markdown dumps.
usage: python3 -I stats.py <md_dir> [<md_dir_or_file> ...]   (first = corpus)
"""
import glob, os, re, sys, statistics as st
from collections import Counter


def load(path):
    files = sorted(glob.glob(os.path.join(path, "*.md"))) if os.path.isdir(path) else [path]
    docs = []
    for f in files:
        t = open(f, encoding="utf-8").read()
        meta, body = {}, t
        if t.startswith("---\n"):
            _, m, body = t.split("---\n", 2)
            meta = dict(l.split(": ", 1) for l in m.strip().splitlines() if ": " in l)
        # drop title/byline lines and trailing CTA
        lines = [l for l in body.splitlines() if l.strip()]
        if lines and lines[0].startswith("# "):
            lines = lines[1:]
        if lines and re.search(r"\d{4}년 \d+월 \d+일$", lines[0]):
            lines = lines[1:]
        docs.append((os.path.basename(f), meta, lines))
    return docs


def sentences(lines):
    out = []
    inc = False
    for l in lines:
        if l == "```":
            inc = not inc
            continue
        if inc:
            continue
        if l.startswith(("[이미지", "```", "[콜아웃", "[동영상", "#", "|")):
            continue
        l = re.sub(r"^(> |- |1\. |\s)+", "", l)
        for s in re.split(r"(?<=[.?!])\s+", l):
            s = s.strip()
            if len(s) > 4:
                out.append(s)
    return out


END = {
    "요체(~요)": r"(요|죠|까요\?|나요\?|죠\?|요\?)[.!?]?$",
    "합쇼체(~습니다/니다)": r"(니다|니까\?)[.!?]?$",
    "평서체(~다)": r"(?<!니)다[.!]?$",
}


def doc_stats(lines):
    text = "\n".join(lines)
    sents = sentences(lines)
    ends = Counter()
    for s in sents:
        s2 = s.replace("**", "").rstrip(" )\"'”’*`")
        for k, rx in END.items():
            if re.search(rx, s2):
                ends[k] += 1
                break
        else:
            ends["기타(명사형/콜론 등)"] += 1
    in_code = False
    code_blocks = 0
    for l in lines:
        if l == "```":
            in_code = not in_code
            code_blocks += 0.5
    body_chars = sum(len(l) for l in lines if not l.startswith("[이미지"))
    return {
        "chars": body_chars,
        "sents": len(sents),
        "sent_len": st.mean(len(s) for s in sents) if sents else 0,
        "h2": sum(l.startswith("## ") for l in lines),
        "h3": sum(l.startswith("### ") for l in lines),
        "h4": sum(l.startswith("#### ") for l in lines),
        "img": sum(l.startswith("[이미지") for l in lines),
        "callout": sum(l == "[콜아웃 박스 시작]" for l in lines),
        "quote": sum(l.startswith("> ") for l in lines),
        "bullets": sum(bool(re.match(r"\s*(- |1\. )", l)) for l in lines),
        "code": int(code_blocks),
        "bold": len(re.findall(r"\*\*[^*]+\*\*", text)),
        "q_sents": sum(s.endswith("?") for s in sents),
        "ends": ends,
        "first": lines[0] if lines else "",
        "headings": [l for l in lines if re.match(r"#{2,4} ", l)],
        "paras_per_img": None,
        "para_len": st.mean([len(l) for l in lines if not l.startswith(("[", "#", "-", ">", "```", "1.", "|"))] or [0]),
    }


def summarize(docs, label, show_lists=False):
    S = [doc_stats(l) for _, _, l in docs if l]
    S = [s for s in S if s["sents"] >= 10]
    n = len(S)
    def med(k): return st.median(s[k] for s in S)
    ends = Counter()
    for s in S: ends.update(s["ends"])
    tot = sum(ends.values())
    print(f"=== {label}: {n} docs ===")
    for k in ["chars", "sents", "sent_len", "para_len", "h2", "h3", "img", "callout", "quote", "bullets", "code", "bold", "q_sents"]:
        print(f"  {k:10s} median={med(k):8.1f}  mean={st.mean(s[k] for s in S):8.1f}")
    per1k = lambda k: st.median(s[k] / max(s["chars"], 1) * 1000 for s in S)
    print(f"  img/1k자={per1k('img'):.2f}  heading/1k자={st.median((s['h2']+s['h3']+s['h4'])/s['chars']*1000 for s in S):.2f}  bold/1k자={per1k('bold'):.2f}  질문문장비율={st.median(s['q_sents']/s['sents'] for s in S):.3f}")
    print("  말끝:", {k: f"{v/tot:.1%}" for k, v in ends.most_common()})
    # per-doc dominant mix
    yo = [s["ends"]["요체(~요)"] / max(s["sents"], 1) for s in S]
    print(f"  문서별 요체 비율 median={st.median(yo):.2f} p25={sorted(yo)[n//4]:.2f} p75={sorted(yo)[3*n//4]:.2f}")
    return S


if __name__ == "__main__":
    corpus = load(sys.argv[1])
    S = summarize(corpus, "corpus")
    for p in sys.argv[2:]:
        summarize(load(p), p)
