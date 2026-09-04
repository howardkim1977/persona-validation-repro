# -*- coding: utf-8 -*-
"""MANIFEST.sha256 재생성 및 검증(패키지 루트에서 실행).
  python3 rebuild_manifest.py          MANIFEST.sha256 를 다시 쓴다(기본 동작).
  python3 rebuild_manifest.py --check  다시 쓰지 않고 검증만 한다: 해시 불일치, 누락, 미등재 파일을 나열하고
                                       하나라도 있으면 종료 코드 1 을 반환한다.
MANIFEST 자신과 .DS_Store, 디렉터리 .git, __pycache__, 그리고 quickstart.py 가 그림을 렌더링하는 paper/ 는
제외한다(아카이브에 포함되지 않는 파일). 그 밖의 인자는 거부한다."""
import hashlib, os, sys
ROOT=os.path.dirname(os.path.abspath(__file__)); SKIP={"MANIFEST.sha256",".DS_Store","analysis_ready.csv"}  # 비공개 정제본은 패키지에 포함하지 않는다
SKIP_DIRS={".git","__pycache__","paper","private"}
MANIFEST=os.path.join(ROOT,"MANIFEST.sha256")
def sha256(p):
    m=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1<<20),b""): m.update(c)
    return m.hexdigest()
def collect():
    entries=[]
    for dp,dns,fns in os.walk(ROOT):
        dns[:]=[d for d in dns if d not in SKIP_DIRS]
        for fn in sorted(fns):
            if fn in SKIP or fn.endswith(".pyc"): continue
            if os.path.islink(os.path.join(dp,fn)): continue   # 작업용 심볼릭 링크 제외
            p=os.path.join(dp,fn); entries.append((os.path.relpath(p,ROOT),sha256(p)))
    return sorted(entries)
def rewrite():
    entries=collect()
    with open(MANIFEST,"w",encoding="utf-8") as w:
        for rel,h in entries: w.write(f"{h}  {rel}\n")
    print(f"MANIFEST.sha256: {len(entries)} files")
def check():
    listed={}
    for line in open(MANIFEST,encoding="utf-8"):
        h,rel=line.rstrip("\n").split("  ",1); listed[rel]=h
    actual=dict(collect())
    missing=sorted(r for r in listed if r not in actual)
    mismatch=sorted(r for r in listed if r in actual and actual[r]!=listed[r])
    unlisted=sorted(r for r in actual if r not in listed)
    for lab,lst in [("hash mismatch",mismatch),("missing",missing),("not in manifest",unlisted)]:
        for r in lst: print(f"  {lab}: {r}")
    ok=len(listed)-len(missing)-len(mismatch)
    print(f"MANIFEST.sha256 --check: {len(listed)} listed, {ok} verified, {len(mismatch)} mismatched, {len(missing)} missing, {len(unlisted)} unlisted")
    return 1 if (missing or mismatch or unlisted) else 0
if __name__=="__main__":
    args=sys.argv[1:]
    if args==[]: rewrite()
    elif args==["--check"]: sys.exit(check())
    else: print(f"usage: python3 {os.path.basename(__file__)} [--check]",file=sys.stderr); sys.exit(2)
