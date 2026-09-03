# -*- coding: utf-8 -*-
"""문항 제시 순서 무작위화 실험(심사 대응, R2-9).

동일 페르소나 부분표본(시드 42, 프레이밍 실험과 동일 규모)에 대해 2024 문항셋을
  F(고정 순서): 본 실험과 동일한 코드북 순서 — 같은 날 재생성한 통제군, K=3회 독립 응답
  R(무작위 순서): 페르소나마다 36문항의 제시 순서를 독립 무작위 치환 — 1회 응답
으로 생성한다. 모델·온도·top_p·thinking·시스템 지시·문항 문구·보기는 모두 동일하며,
유일한 차이는 문항의 제시 순서다. F의 복수 응답은 (i) 순서 효과를 생성 노이즈와 대조하는
자연 귀무 기준(F1 vs F2)과 (ii) 페르소나-응답 이중 재표집 계층 부트스트랩의 재료가 된다.

Gemini Batch API 전용(사전등록 파라미터 불변). 산출:
  outputs/order_exp_gemini_{F1,F2,F3,R1}.csv  — 원 응답(문항코드별 보기번호)
  outputs/order_exp_gemini_R1_orders.json     — 페르소나별 제시 순서(감사용)
"""
import os, json, time, argparse, random
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
import generate
from generate import (sample_personas, build_user_prompt, SYSTEM_TMPL, persona_description,
                      _batch_line, parse_json, conditional_skips, validate, call_with_backoff,
                      GeminiClient)
from items import ITEMS_BY_WAVE

WAVE = 2024
ITEMS = ITEMS_BY_WAVE[WAVE]
CODES = list(ITEMS.keys())


def permuted_items(seed):
    """페르소나별 고정 시드로 문항 순서를 치환한 dict(삽입 순서 = 제시 순서)."""
    rng = random.Random(seed)
    order = CODES[:]
    rng.shuffle(order)
    return {c: ITEMS[c] for c in order}, order


def run_batch_custom(personas, temperature, out_csv, user_fn, tag, poll_interval=30,
                     max_rounds=3, workdir="outputs", chunk_size=1000):
    """generate.run_batch 와 동일한 라운드·검증 규약을 따르되 페르소나별 설문 문자열을
    user_fn(idx) 로 받는다(순서 치환용). 재생성 라운드에서도 동일 순서를 유지한다."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    def write_rows(results, pending_note):
        rows = []
        for idx, p in enumerate(personas):
            r = dict(results.get(idx) or {"_error": pending_note})
            r.update({"_idx": idx, "_model": "gemini", "_wave": WAVE,
                      "성별": p.get("gender"), "연령대": p.get("age")})
            rows.append(r)
        pd.DataFrame(rows).sort_values("_idx").to_csv(out_csv, index=False, encoding="utf-8-sig")
        return rows

    results, pending = {}, list(range(len(personas)))
    for rnd in range(max_rounds):
        if not pending:
            break
        chunks = [pending[i:i + chunk_size] for i in range(0, len(pending), chunk_size)]
        print(f"[{tag} 라운드 {rnd+1}] 대상 {len(pending)}건 → {len(chunks)}개 서브배치", flush=True)
        next_pending = []
        for ci, chunk in enumerate(chunks):
            jsonl = os.path.join(workdir, f"order_{tag}_r{rnd}c{ci}.jsonl")
            with open(jsonl, "w", encoding="utf-8") as fp:
                for idx in chunk:
                    p = personas[idx]
                    system = SYSTEM_TMPL.format(persona=p.get("persona_prompt") or persona_description(p))
                    fp.write(json.dumps(_batch_line(f"i{idx}", system, user_fn(idx), temperature),
                                        ensure_ascii=False) + "\n")
            up = call_with_backoff(lambda: client.files.upload(
                file=jsonl, config=types.UploadFileConfig(mime_type="jsonl")))
            job = call_with_backoff(lambda: client.batches.create(
                model=GeminiClient.MODEL, src=up.name, config={"display_name": f"order_{tag}_r{rnd}c{ci}"}))
            print(f"    배치 {job.name} 대기…", flush=True)
            while True:
                job = call_with_backoff(lambda: client.batches.get(name=job.name))
                st = str(job.state)
                if any(x in st for x in ["SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED"]):
                    break
                time.sleep(poll_interval)
            if "SUCCEEDED" not in st:
                raise RuntimeError(f"배치 실패: {st} / {getattr(job, 'error', None)}")
            data = call_with_backoff(lambda: client.files.download(file=job.dest.file_name)).decode("utf-8")
            ok = 0
            for line in data.strip().splitlines():
                o = json.loads(line)
                idx = int(o["key"][1:])
                resp = o.get("response")
                try:
                    txt = resp["candidates"][0]["content"]["parts"][0]["text"]
                    ans = parse_json(txt)
                except Exception:
                    next_pending.append(idx); continue
                skip = conditional_skips(ITEMS, ans)
                ans = {k: v for k, v in ans.items() if k not in skip}
                if validate(ans, ITEMS, skip):
                    next_pending.append(idx)
                else:
                    results[idx] = {k: int(v) for k, v in ans.items() if k in ITEMS}; ok += 1
            write_rows(results, "pending_or_failed")
            print(f"    성공 {ok} / 재생성 {len(chunk)-ok} (누적 성공 {len(results)})", flush=True)
        pending = next_pending
    for idx in pending:
        results.setdefault(idx, {"_error": "format_violation_after_batch_retries"})
    rows = write_rows(results, "format_violation_after_batch_retries")
    n_err = sum(1 for r in rows if r.get("_error"))
    print(f"완료: {out_csv} (총 {len(rows)}, 오류 {n_err})", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=1200)
    ap.add_argument("--arms", default="F1,F2,F3,R1")
    ap.add_argument("--poll", type=int, default=30)
    a = ap.parse_args()
    personas = sample_personas("analysis_ready.csv", "nemotron_personas_korea.csv", WAVE, seed=42, limit=a.limit)
    print(f"[표집] 페르소나 {len(personas)}명 (시드 42, 프레이밍 실험과 동일 부분표본)", flush=True)
    fixed_survey = build_user_prompt(ITEMS, set())
    orders = {}
    for idx in range(len(personas)):
        _, order = permuted_items(1000 + idx)
        orders[idx] = order
    json.dump({"seed_rule": "random.Random(1000+idx)", "fixed_order": CODES,
               "orders": {str(k): v for k, v in orders.items()}},
              open("outputs/order_exp_gemini_R1_orders.json", "w", encoding="utf-8"), ensure_ascii=False)
    for arm in a.arms.split(","):
        out = f"outputs/order_exp_gemini_{arm}.csv"
        if os.path.exists(out):
            prev = pd.read_csv(out, encoding="utf-8-sig")
            if "_error" not in prev.columns or prev["_error"].isna().mean() > 0.9:
                print(f"[{arm}] 기존 산출물 존재, 건너뜀: {out}", flush=True); continue
        if arm.startswith("F"):
            user_fn = lambda idx: fixed_survey
        else:
            user_fn = lambda idx: build_user_prompt(permuted_items(1000 + idx)[0], set())
        print(f"[{arm}] 시작 ({'고정' if arm.startswith('F') else '무작위'} 순서, temp=1.0)", flush=True)
        run_batch_custom(personas, 1.0, out, user_fn, arm, poll_interval=a.poll)
