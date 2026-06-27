"""Quick test of cray adapter prompt building."""
import sys, os
sys.path.insert(0, ".")
import tempfile, pathlib, subprocess, re

ws = pathlib.Path(tempfile.mkdtemp())
(ws / "main.py").write_text("def reverse_words(s): pass\n", encoding="utf-8")

prompt = "Read main.py then implement reverse_words(s) to reverse word order. Write code. Run test."
safe = prompt.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ")

cmd = f'cray --input "{safe}" -d "{ws}" -m deepseek-v4-flash --max-turns 6 -p default -v'

proc = subprocess.run(
    cmd, capture_output=True,
    shell=True, cwd=str(ws), timeout=180,
    encoding="utf-8", errors="replace",
)
output = (proc.stdout or "") + "\n" + (proc.stderr or "")

tools = re.findall(r'allowing "(\w+)"', output, re.IGNORECASE)
print(f"Tools: {tools}")

content = (ws / "main.py").read_text(encoding="utf-8")
modified = "def reverse_words(s): pass" not in content
print(f"Modified: {modified}")
print(f"Code:\n{content[:300]}")
