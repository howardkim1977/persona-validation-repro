# -*- coding: utf-8 -*-
"""MANIFEST.sha256 재생성(패키지 루트에서 실행). MANIFEST 자신과 .git, __pycache__, .DS_Store 는 제외한다(아카이브에 포함되지 않는 파일)."""
import hashlib, os
ROOT=os.path.dirname(os.path.abspath(__file__)); SKIP={"MANIFEST.sha256",".DS_Store"}
def sha256(p):
    m=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1<<20),b""): m.update(c)
    return m.hexdigest()
entries=[]
for dp,dns,fns in os.walk(ROOT):
    dns[:]=[d for d in dns if d not in (".git","__pycache__")]
    for fn in sorted(fns):
        if fn in SKIP or fn.endswith(".pyc"): continue
        p=os.path.join(dp,fn); entries.append((os.path.relpath(p,ROOT),sha256(p)))
with open(os.path.join(ROOT,"MANIFEST.sha256"),"w",encoding="utf-8") as w:
    for rel,h in sorted(entries): w.write(f"{h}  {rel}\n")
print(f"MANIFEST.sha256: {len(entries)} files")
