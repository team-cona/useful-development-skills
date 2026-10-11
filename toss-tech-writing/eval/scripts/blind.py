"""Build blind 'spot the imitation' rounds: each round = 1 generated excerpt + 3 real Toss excerpts.
usage: python3 -I blind.py <out_dir> <seed> <generated.md> <real1.md> <real2.md> ... (>=3 real)
Writes rounds.md (for judge) and key.json (answers).
"""
import json, os, random, re, sys

def excerpts(path, n_want, rng):
    t = open(path, encoding="utf-8").read()
    if t.startswith("---\n"):
        t = t.split("---\n", 2)[2]
    t = re.sub(r"\s*\[확인 필요[^\]]*\]", "", t)
    lines = []
    for l in t.splitlines():
        l = l.strip()
        if not l or "[!NOTE]" in l or "[!TIP]" in l:
            continue
        l = re.sub(r"^>\s*", "", l)
        lines.append(l)
    lines = lines[2:]  # skip title/byline or first lines
    blocks, cur, inc = [], [], False
    for l in lines:
        if l.startswith("```"):
            inc = not inc; cur = []; continue
        if not inc and (l.startswith(("[이미지", "![", "[캡션", "*", "[콜아웃", "[동영상")) or l == "---"):
            continue
        bad = inc or l.startswith(("#", "[", "!", "|", "<")) or "지원하기" in l or "궁금하다면" in l
        if bad:
            if sum(len(x) for x in cur) >= 300: blocks.append(cur)
            cur = []; continue
        cur.append(l)
        if sum(len(x) for x in cur) >= 500:
            blocks.append(cur); cur = []
    if sum(len(x) for x in cur) >= 300: blocks.append(cur)
    # drop very first block (intro self-intro gives author away) when possible
    if len(blocks) > n_want + 1: blocks = blocks[1:]
    rng.shuffle(blocks)
    out = []
    for b in blocks[:n_want]:
        txt = "\n\n".join(b)
        txt = re.sub(r"\*\*", "", txt)  # remove bold markup differences
        out.append(txt)
    return out

out_dir, seed, gen, reals = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]
rng = random.Random(seed)
gen_ex = excerpts(gen, 3, rng)
real_pool = []
for r in reals:
    real_pool += [(os.path.basename(r), e) for e in excerpts(r, 3, rng)]
rng.shuffle(real_pool)
rounds, key = [], []
for i, g in enumerate(gen_ex):
    items = [("GEN", g)] + [real_pool[(i * 3 + j) % len(real_pool)] for j in range(3)]
    rng.shuffle(items)
    labels = "ABCD"
    key.append({"round": i + 1, "answer": labels[[x[0] for x in items].index("GEN")], "sources": [x[0] for x in items]})
    body = "\n\n".join(f"### {labels[k]}\n\n{txt}" for k, (_, txt) in enumerate(items))
    rounds.append(f"## 라운드 {i+1}\n\n{body}")
os.makedirs(out_dir, exist_ok=True)
open(os.path.join(out_dir, "rounds.md"), "w").write("\n\n---\n\n".join(rounds))
json.dump(key, open(os.path.join(out_dir, "key.json"), "w"), ensure_ascii=False, indent=1)
print(f"{len(rounds)} rounds ->", out_dir)
