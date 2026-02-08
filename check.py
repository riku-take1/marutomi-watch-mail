import os
import re
import hashlib
import requests
from bs4 import BeautifulSoup

URL = "https://marutomi-fudousan.com/information.html"
STATE_FILE = "state.txt"

def extract_latest_block(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # ページ全体テキスト（HTML構造が変わっても壊れにくい）
    text = soup.get_text("\n", strip=True)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    joined = "\n".join(lines)

    # 日付らしき箇所を見つけて、その周辺を「最新更新」候補として抜き出す
    m = re.search(r"(20\d{2}年\s*\d{1,2}月\s*\d{1,2}日|20\d{2}[/-]\d{1,2}[/-]\d{1,2})", joined)
    if m:
        start = max(0, joined.rfind("\n", 0, m.start()))
        snippet = joined[start : m.start() + 1000]
    else:
        snippet = "\n".join(lines[:40])  # フォールバック

    # 余計な空白差分を潰して安定化（誤検知防止）
    snippet = re.sub(r"\s+", " ", snippet).strip()
    return snippet

def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def load_state() -> str:
    if not os.path.exists(STATE_FILE):
        return ""
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()

def save_state(sig: str) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(sig)

def main() -> None:
    r = requests.get(URL, timeout=30)
    r.raise_for_status()

    latest = extract_latest_block(r.text)
    sig = sha256(latest)
    prev = load_state()

    changed = (sig != prev)

    # GitHub Actions に結果を渡す
    out_path = os.environ.get("GITHUB_OUTPUT")
    if out_path:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")
            f.write(f"snippet={latest[:300]}\n")

    if changed:
        save_state(sig)

if __name__ == "__main__":
    main()
