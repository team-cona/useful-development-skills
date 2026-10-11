"""Fetch every toss.tech article page and convert the rendered body to markdown.
usage: python3 -I scrape.py <scratch_dir>
"""
import glob, json, os, re, sys, time, urllib.request
from html.parser import HTMLParser

S = sys.argv[1]
OUT = os.path.join(S, "md")
HTML = os.path.join(S, "html")
os.makedirs(OUT, exist_ok=True)
os.makedirs(HTML, exist_ok=True)

posts = []
for f in sorted(glob.glob(os.path.join(S, "api", "list_*.json"))):
    posts += json.load(open(f))["success"]["results"]


def fetch(key):
    p = os.path.join(HTML, f"{key}.html")
    if os.path.exists(p) and os.path.getsize(p) > 10000:
        return open(p, encoding="utf-8").read()
    req = urllib.request.Request(f"https://toss.tech/article/{key}", headers={"User-Agent": "Mozilla/5.0"})
    h = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    open(p, "w", encoding="utf-8").write(h)
    time.sleep(0.4)
    return h


class Conv(HTMLParser):
    BLOCK = {"p", "h1", "h2", "h3", "h4", "li", "blockquote", "figcaption", "pre", "tr"}

    def __init__(self, bold_classes, code_classes):
        super().__init__(convert_charrefs=True)
        self.bold, self.codec = bold_classes, code_classes
        self.out, self.buf = [], []
        self.stack = []  # (tag, markers)
        self.in_article = False
        self.depth_article = 0
        self.list_stack = []
        self.skip = 0
        self.pre = 0
        self.aside = 0
        self.quote = 0

    def flush(self, prefix=""):
        t = "".join(self.buf)
        if not self.pre:
            t = re.sub(r"[ \t]+", " ", t).strip()
        if t:
            self.out.append(prefix + t)
        self.buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article":
            self.in_article = True
        if not self.in_article:
            return
        if tag in ("style", "script", "button", "svg", "template"):
            self.skip += 1
            return
        if self.skip:
            return
        cls = set((a.get("class") or "").split())
        role = a.get("role")
        if tag == "div" and role in ("table", "row", "cell", "columnheader", "rowheader"):
            if role == "table":
                self.flush(); self.out.append("[표 시작]")
            elif role == "row":
                self.flush()
            else:
                self.buf.append(" | ")
            tag = "div:" + role
        mark = ""
        if tag in ("strong", "b") or (tag == "span" and cls & self.bold):
            mark = "**"
        elif tag == "code" and not self.pre or (tag == "span" and cls & self.codec):
            mark = "`"
        if tag in ("ul", "ol"):
            self.list_stack.append(tag)
        if tag == "pre":
            self.flush(); self.pre += 1; self.out.append("```")
        if tag == "aside":
            self.flush(); self.aside += 1; self.out.append("[콜아웃 박스 시작]")
        if tag == "blockquote":
            self.flush(); self.quote += 1
        if tag in self.BLOCK and tag not in ("pre",):
            self.flush()
        if tag == "img":
            self.flush()
            self.out.append(f"[이미지: alt='{a.get('alt','')}' src={(a.get('src') or '')[:300] if not (a.get('src') or '').startswith('data:') else 'data-uri'}]")
        if tag == "video":
            self.out.append("[동영상]")
        if tag == "hr":
            self.out.append("---")
        if tag == "br":
            self.buf.append("\n" if self.pre else " ")
        if tag in ("td", "th"):
            self.buf.append(" | ")
        if mark:
            self.buf.append(mark)
        self.stack.append((tag, mark))

    def handle_endtag(self, tag):
        if not self.in_article:
            return
        if tag == "div":
            for t_, _ in reversed(self.stack):
                if t_.startswith("div"):
                    tag = t_
                    break
        if tag in ("style", "script", "button", "svg", "template"):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        # pop to matching tag
        while self.stack:
            t, m = self.stack.pop()
            if m:
                self.buf.append(m)
            if t == tag:
                break
        lvl = len(self.list_stack)
        pfx = "> " * self.quote
        if tag == "h1": self.flush(pfx + "# ")
        elif tag == "h2": self.flush(pfx + "## ")
        elif tag == "h3": self.flush(pfx + "### ")
        elif tag == "h4": self.flush(pfx + "#### ")
        elif tag == "li":
            mk = "1." if self.list_stack and self.list_stack[-1] == "ol" else "-"
            self.flush(pfx + "  " * (lvl - 1) + mk + " ")
        elif tag == "figcaption": self.flush("[캡션] ")
        elif tag == "pre":
            self.flush(); self.out.append("```"); self.pre -= 1
        elif tag in ("p", "tr"): self.flush(pfx + ("| " if tag == "tr" else ""))
        if tag in ("ul", "ol") and self.list_stack:
            self.list_stack.pop()
        if tag == "blockquote":
            self.flush("> " * self.quote); self.quote -= 1
        if tag == "aside":
            self.flush(); self.aside -= 1; self.out.append("[콜아웃 박스 끝]")
        if tag == "div:row": self.flush("|")
        if tag == "div:table":
            self.flush(); self.out.append("[표 끝]")
        if tag == "article":
            self.flush(); self.in_article = False

    def handle_data(self, d):
        if self.in_article and not self.skip:
            self.buf.append(d)


def convert(h):
    styles = dict(re.findall(r"\.(css-[a-z0-9]+)\{([^}]*)\}", h))
    bold = {c for c, s in styles.items() if re.search(r"font-weight:(bold|[6-9]00)", s)}
    code = {c for c, s in styles.items() if "monospace" in s or "font-family:SFMono" in s}
    c = Conv(bold, code)
    c.feed(h)
    c.flush()
    return "\n".join(c.out)


index = []
for i, p in enumerate(posts):
    key = p["key"]
    try:
        h = fetch(key)
        md = convert(h)
    except Exception as e:
        print("fail", key, e, flush=True)
        continue
    cats = "/".join(c["name"] for c in p.get("categories") or [])
    head = f"---\nkey: {key}\ntitle: {p['title']}\nsubtitle: {p.get('subtitle')}\ncategory: {cats}\nseries: {p.get('series') and p['series'].get('title') if isinstance(p.get('series'), dict) else p.get('series')}\npublished: {p.get('publishedTime')}\neditor: {(p.get('editor') or {}).get('name')}\nviews: {p.get('viewCount')}\n---\n"
    open(os.path.join(OUT, f"{key}.md"), "w", encoding="utf-8").write(head + md)
    index.append({"key": key, "title": p["title"], "subtitle": p.get("subtitle"), "cat": cats,
                  "published": p.get("publishedTime"), "views": p.get("viewCount"), "chars": len(md)})
    if i % 25 == 0:
        print(i, key, len(md), flush=True)
json.dump(index, open(os.path.join(S, "index.json"), "w"), ensure_ascii=False, indent=1)
print("done", len(index))
