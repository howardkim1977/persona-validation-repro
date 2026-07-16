# -*- coding: utf-8 -*-
"""합성 페르소나 응답 생성 파이프라인.

설계: 한국형 합성 페르소나 패널의 디지털·AI 서비스 이용 예측 타당성 검증(2차 자료).
정답지 = 한국미디어패널조사. 합성 페르소나(NVIDIA Nemotron-Personas-Korea)가
동일 문항에 동일 보기로 응답 → 실측 분포와 비교.

주 모델 Gemini 3.5 Flash(gemini-3.5-flash, thinking=low), 비교 모델 EXAONE.
temperature 1.0(주)/0.7(강건성), top_p 1.0. 형식 위반 시 최대 3회 재생성.

※ 본 스크립트는 사용자 환경에서 실행한다(외부 API 접근 필요).
   API 키는 환경변수로 주입하며 코드에 저장하지 않는다.
"""
import os, json, time, argparse, random, threading
from collections import defaultdict

# .env 자동 로드(선택). 키는 환경변수로만 주입하며 코드·커밋에 남기지 않는다.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv 미설치 시 셸 환경변수(export)로 주입

import pandas as pd
from items import ITEMS_BY_WAVE, CONDITIONAL, allowed_codes
from map_persona import map_persona, map_persona_dataframe, SEX_MAP, age_to_code, AGE as PERSONA_AGE

# 세그먼트 라벨(페르소나 조건화 문구)
AGE = {1:"10세 미만",2:"10대",3:"20대",4:"30대",5:"40대",6:"50대",7:"60대",8:"70대 이상"}
SCHOOL = {1:"미취학",2:"초졸 이하",3:"중졸 이하",4:"고졸 이하",5:"대졸 이하",6:"대학원 이상"}
INCOME = {1:"소득 없음",2:"월 50만원 미만",3:"월 50~100만원",4:"월 100~200만원",
          5:"월 200~300만원",6:"월 300~400만원",7:"월 400~500만원",8:"월 500만원 이상"}
AREA = {1:"서울",2:"부산",3:"대구",4:"인천",5:"광주",6:"대전",7:"울산",8:"경기",9:"강원",
        10:"충북",11:"충남",12:"전북",13:"전남",14:"경북",15:"경남",16:"제주",17:"세종"}


# ── 프롬프트 구성 ────────────────────────────────────────────────
def persona_description(p):
    """페르소나 속성 dict → 1인칭 인물 설명."""
    parts = []
    if p.get("gender"): parts.append(f"성별 {p['gender']}")
    if p.get("age"):    parts.append(f"연령 {AGE.get(p['age'], p['age'])}")
    if p.get("school"): parts.append(f"학력 {SCHOOL.get(p['school'], p['school'])}")
    if p.get("income"): parts.append(f"개인 월평균 소득 {INCOME.get(p['income'], p['income'])}")
    if p.get("area"):   parts.append(f"거주지 {AREA.get(p['area'], p['area'])}")
    if p.get("job"):    parts.append(f"직업 {p['job']}")
    if p.get("persona_text"): parts.append(p["persona_text"])  # NVIDIA 페르소나 서술(선택)
    return ", ".join(str(x) for x in parts)


SYSTEM_TMPL = (
    "당신은 다음 특성을 가진 한국의 한 개인입니다: {persona}.\n"
    "이 인물의 입장에서 일관되게, 실제 사람처럼 솔직하게 설문에 응답하십시오.\n"
    "각 문항은 제시된 보기 번호 중 하나로만 답합니다."
)

def build_user_prompt(items, conditional_skip):
    """문항 dict → 보기 포함 설문 + 출력 형식 지시."""
    lines = ["다음 문항에 답해 주십시오. 각 문항마다 보기 번호(숫자) 하나만 고릅니다.\n"]
    for code, (text, opts) in items.items():
        if code in conditional_skip:
            continue
        opt_str = " / ".join(f"{k}={v}" for k, v in opts.items())
        lines.append(f"[{code}] {text}\n  보기: {opt_str}")
    lines.append(
        "\n반드시 아래 JSON 형식으로만 출력하십시오. 설명·여는말 없이 JSON 객체 하나만 출력합니다.\n"
        '{"문항코드": 보기번호, ...}\n'
        "예: {\"p__d31002\": 1, \"p__d31001\": 3}"
    )
    return "\n".join(lines)


# ── 레이트리밋 처리 ──────────────────────────────────────────────
class RateLimitError(Exception):
    """429/RESOURCE_EXHAUSTED 등 레이트리밋. 형식 위반과 구분(재생성 카운트 미소모)."""


def _parse_retry_delay(msg, default):
    """오류 메시지의 retryDelay('14s'/'retry in 14.3s')에서 대기 초 추출."""
    import re
    m = re.search(r"retry(?:Delay)?['\"]?[:\s]+['\"]?(\d+(?:\.\d+)?)\s*s", msg)
    if m:
        return float(m.group(1))
    m = re.search(r"retry in (\d+(?:\.\d+)?)\s*s", msg)
    return float(m.group(1)) if m else default


def call_with_backoff(fn, max_tries=6, base=5.0, cap=60.0):
    """레이트리밋(429) 시 지수 백오프 재시도. 서버가 준 retryDelay 를 우선 존중.
    비레이트리밋 예외는 즉시 전파(형식 재생성 루프가 처리)."""
    for attempt in range(max_tries):
        try:
            return fn()
        except Exception as ex:
            s = str(ex)
            is_rl = "429" in s or "RESOURCE_EXHAUSTED" in s or "rate limit" in s.lower()
            if not is_rl:
                raise
            if attempt == max_tries - 1:
                raise RateLimitError(f"레이트리밋 재시도 소진: {s[:200]}")
            wait = min(_parse_retry_delay(s, base * (2 ** attempt)), cap)
            print(f"  429 레이트리밋 → {wait:.1f}s 대기 후 재시도({attempt+1}/{max_tries})")
            time.sleep(wait + 0.5)


# ── 모델 클라이언트 ──────────────────────────────────────────────
class GeminiClient:
    """Gemini 3.5 Flash. thinking=low, top_p=1.0 고정. temperature 인자.
    google-genai SDK 사용. 키: 환경변수 GEMINI_API_KEY."""
    MODEL = "gemini-3.5-flash"
    def __init__(self, temperature=1.0):
        from google import genai
        from google.genai import types
        self._types = types
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.temperature = temperature
    def generate(self, system, user):
        cfg = self._types.GenerateContentConfig(
            system_instruction=system,
            temperature=self.temperature,
            top_p=1.0,
            thinking_config=self._types.ThinkingConfig(thinking_level="low"),
            response_mime_type="application/json",
        )
        r = call_with_backoff(
            lambda: self.client.models.generate_content(
                model=self.MODEL, contents=user, config=cfg))
        return r.text


class ExaoneClient:
    """EXAONE 오픈웨이트. OpenAI 호환 엔드포인트(vLLM 등) 가정.
    키/URL: 환경변수 EXAONE_API_KEY, EXAONE_BASE_URL, EXAONE_MODEL."""
    def __init__(self, temperature=1.0):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ.get("EXAONE_API_KEY", "EMPTY"),
                             base_url=os.environ["EXAONE_BASE_URL"])
        self.model = os.environ.get("EXAONE_MODEL", "exaone")
        self.temperature = temperature
    def generate(self, system, user):
        # 추론(thinking) 비활성화: EXAONE 추론 모델의 과도추론·미수렴 방지.
        # Gemini thinking=low 와 정합(최소 사고). FriendliAI 챗 템플릿 인자로 전달.
        r = call_with_backoff(
            lambda: self.client.chat.completions.create(
                model=self.model, temperature=self.temperature, top_p=1.0,
                max_tokens=4096,  # 전체 문항 JSON 출력 절단 방지(Tier2 출력 16K 내)
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user + "\n\nJSON 객체만 출력."}],
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            ))
        return r.choices[0].message.content


# ── 파싱·검증 ────────────────────────────────────────────────────
def parse_json(text):
    """모델 출력에서 JSON 객체 추출(코드펜스 제거 포함)."""
    t = text.strip().replace("```json", "").replace("```", "").strip()
    s, e = t.find("{"), t.rfind("}")
    if s == -1 or e == -1:
        raise ValueError("JSON 객체 없음")
    return json.loads(t[s:e + 1])


def validate(ans, items, conditional_skip):
    """응답 dict 검증: 응답 대상 문항이 모두 있고 허용 코드인지.
    위반 항목 리스트 반환(빈 리스트면 통과)."""
    bad = []
    for code, item_def in items.items():
        if code in conditional_skip:
            continue
        if code not in ans:
            bad.append(f"{code} 누락"); continue
        try:
            v = int(ans[code])
        except (ValueError, TypeError):
            bad.append(f"{code} 비정수"); continue
        if v not in allowed_codes(item_def):
            bad.append(f"{code}={ans[code]} 허용외")
    return bad


def conditional_skips(items, prior):
    """조건부 문항 중 선행 응답이 미충족(이용=없다)인 코드 집합."""
    skip = set()
    for child, parent in CONDITIONAL.items():
        if child in items and prior.get(parent) not in (1,):  # 1=있다일 때만 응답
            skip.add(child)
    return skip


def generate_one(client, persona, wave, max_retries=3):
    """페르소나 1명 응답 생성(2단계: 핵심 문항 → 조건부 반영 재구성).
    여기서는 단일 호출 + 사후 조건부 스킵 검증으로 단순화."""
    items = ITEMS_BY_WAVE[wave]
    # map_persona 가 생성한 1인칭 프롬프트를 우선 사용, 없으면 속성 요약으로 대체
    persona_block = persona.get("persona_prompt") or persona_description(persona)
    system = SYSTEM_TMPL.format(persona=persona_block)
    skip = set()  # 1차에는 전체 제시(조건부 포함), 사후 정합화
    for attempt in range(max_retries):
        user = build_user_prompt(items, skip)
        try:
            raw = client.generate(system, user)
            ans = parse_json(raw)
        except Exception as ex:
            if attempt == max_retries - 1:
                return {"_error": f"parse_fail:{ex}"}
            continue
        # 조건부 정합: 이용=없다이면 하위 문항 제거
        skip = conditional_skips(items, ans)
        ans = {k: v for k, v in ans.items() if k not in skip}
        bad = validate(ans, items, skip)
        if not bad:
            return {k: int(v) for k, v in ans.items() if k in items}
        # 형식 위반 → 재시도(위반 항목 안내)
        system_retry = system + "\n이전 응답에 형식 오류가 있었습니다: " + "; ".join(bad)
        system = system_retry
    return {"_error": "format_violation:" + ";".join(bad)}


# ── 페르소나 추출(층화) ──────────────────────────────────────────
def sample_personas(panel_csv, persona_csv, wave, multiplier=2, seed=42, limit=None,
                    cell_floor=200, cell_cap=600):
    """실측 차수의 세그먼트 분포에 맞춰 NVIDIA 페르소나를 층화 추출.
    panel_csv: analysis_ready.csv (실측), persona_csv: NVIDIA 페르소나.
    반환: 페르소나 속성 dict 리스트(키: uuid·gender·age·persona_prompt·segments).

    세그먼트(성별 라벨·연령대 코드)는 벡터화로 값싸게 계산하고, 실제 프롬프트는
    추출된 레코드에만 map_persona 로 생성한다(100만 행 전체 매핑 회피).
    성별="남성"/"여성", 연령대=코드 1~8 로 실측 패널 컬럼과 직접 정합한다.

    표본 배분(floor+cap): 셀별 n = clip(실측_cnt × multiplier, cell_floor, cell_cap).
    소형 셀 정밀도를 하한으로 보장하고 대형 셀 과표집을 상한으로 차단한다.
    cell_floor/cell_cap 을 None 으로 두면 순수 비례(실측×multiplier)로 동작한다.
    limit 지정 시 층화 비율을 유지한 채 총 표본을 limit 규모로 축소(시범 실행용)."""
    rng = random.Random(seed)
    panel = pd.read_csv(panel_csv, encoding="utf-8-sig")
    panel = panel[panel.YEAR == wave]
    # 세그먼트 셀 비율(성별×연령대) 기준 층화(필요 시 학력 추가)
    cells = panel.groupby(["성별", "연령대"]).size()
    persona = pd.read_csv(persona_csv)  # NVIDIA Nemotron-Personas-Korea
    # 세그먼트 라벨/코드 벡터화(프롬프트 미생성 → 대용량에서도 빠름).
    # 실측 패널의 연령대는 라벨(예: "20대")이므로, 매칭 키도 라벨 공간으로 맞춘다.
    # (출력 행의 연령대는 코드 1~8 유지 — 규약 준수)
    seg_gender = persona["sex"].map(SEX_MAP).fillna(persona["sex"])
    seg_age_label = persona["age"].map(age_to_code).map(PERSONA_AGE)
    pools = defaultdict(list)
    for ridx, g, a in zip(persona.index, seg_gender, seg_age_label):
        pools[(g, a)].append(ridx)

    # 셀별 목표 n 산정: floor+cap
    cell_n = {}
    for (g, age), cnt in cells.items():
        n = int(round(cnt * multiplier))
        if cell_floor is not None:
            n = max(cell_floor, n)
        if cell_cap is not None:
            n = min(cell_cap, n)
        cell_n[(g, age)] = n
    # limit(시범): 셀별 목표를 동일 비율로 축소
    if limit:
        tot = sum(cell_n.values())
        scale = limit / tot if tot else 0
        cell_n = {k: max(1, int(round(v * scale))) for k, v in cell_n.items()}

    out = []
    for (g, age), n in cell_n.items():
        pool = pools.get((g, age), [])
        if not pool or n <= 0:
            continue
        for _ in range(n):
            ridx = pool[rng.randrange(len(pool))]
            m = map_persona(dict(persona.loc[ridx]))  # 추출된 레코드만 프롬프트 생성
            seg = m["segments"]
            out.append({
                "uuid": m["uuid"],
                "gender": seg["성별"],          # 라벨(남성/여성) — 실측 정합
                "age": seg["연령대"],            # 코드 1~8 — 실측 정합
                "persona_prompt": m["persona_prompt"],
                "segments": seg,
            })
    return out


# ── 실행 ─────────────────────────────────────────────────────────
def run(personas, model, wave, temperature, out_csv, workers=12):
    """스레드 병렬로 페르소나별 응답 생성. 사전등록 파라미터(모델·온도·top_p·
    thinking)는 불변, 처리 속도만 향상. 429는 클라이언트 백오프가 흡수.
    50건마다 체크포인트 저장, 최종 _idx 순 정렬."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    client = GeminiClient(temperature) if model == "gemini" else ExaoneClient(temperature)
    total = len(personas)
    rows = []
    lock = threading.Lock()

    def work(i, p):
        ans = generate_one(client, p, wave)
        ans.update({"_idx": i, "_model": model, "_wave": wave,
                    "성별": p.get("gender"), "연령대": p.get("age")})
        return ans

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(work, i, p) for i, p in enumerate(personas)]
        done = 0
        for fut in as_completed(futures):
            ans = fut.result()
            with lock:
                rows.append(ans)
                done += 1
                if done % 50 == 0:
                    print(f"{done}/{total} 생성", flush=True)
                    df = pd.DataFrame(rows).sort_values("_idx")
                    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    pd.DataFrame(rows).sort_values("_idx").to_csv(out_csv, index=False, encoding="utf-8-sig")
    n_err = sum(1 for r in rows if "_error" in r and r["_error"])
    print(f"완료: {out_csv} (총 {total}, 오류 {n_err})")


# ── Batch API 실행(대량·저비용) ──────────────────────────────────
def _batch_line(key, system, user, temperature):
    """Gemini Batch JSONL 한 줄(GenerateContentRequest). 사전등록 파라미터 고정."""
    return {"key": key, "request": {
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "systemInstruction": {"parts": [{"text": system}]},
        "generationConfig": {
            "temperature": temperature, "topP": 1.0,
            "responseMimeType": "application/json",
            "thinkingConfig": {"thinkingLevel": "low"},
        }}}


def _run_batch_chunk(client, types, chunk, personas, survey, items, temperature,
                     wave, tag, poll_interval, workdir):
    """단일 서브배치(≤인큐 한도)를 제출·수거. (성공 idx→응답, 재생성 대상 idx 리스트) 반환.
    동시 인큐 한도(≈1000)를 넘지 않도록 호출부에서 청크 크기를 통제한다."""
    jsonl = os.path.join(workdir, f"batch_w{wave}_{tag}.jsonl")
    with open(jsonl, "w", encoding="utf-8") as fp:
        for idx in chunk:
            p = personas[idx]
            system = SYSTEM_TMPL.format(
                persona=p.get("persona_prompt") or persona_description(p))
            fp.write(json.dumps(_batch_line(f"i{idx}", system, survey, temperature),
                                ensure_ascii=False) + "\n")
    up = call_with_backoff(lambda: client.files.upload(
        file=jsonl, config=types.UploadFileConfig(mime_type="jsonl")))
    job = call_with_backoff(lambda: client.batches.create(
        model=GeminiClient.MODEL, src=up.name,
        config={"display_name": f"synth_w{wave}_{tag}"}))
    print(f"    배치 {job.name} 대기…", flush=True)
    while True:
        job = call_with_backoff(lambda: client.batches.get(name=job.name))
        st = str(job.state)
        if any(x in st for x in ["SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED"]):
            break
        time.sleep(poll_interval)
    if "SUCCEEDED" not in st:
        raise RuntimeError(f"배치 실패: {st} / {getattr(job,'error',None)}")
    data = call_with_backoff(
        lambda: client.files.download(file=job.dest.file_name)).decode("utf-8")
    ok, retry = {}, []
    for line in data.strip().splitlines():
        o = json.loads(line)
        idx = int(o["key"][1:])
        resp = o.get("response")
        if not resp:
            retry.append(idx); continue
        try:
            txt = resp["candidates"][0]["content"]["parts"][0]["text"]
            ans = parse_json(txt)
        except Exception:
            retry.append(idx); continue
        skip = conditional_skips(items, ans)
        ans = {k: v for k, v in ans.items() if k not in skip}
        if validate(ans, items, skip):
            retry.append(idx)  # 형식 위반 → 다음 라운드 재생성
        else:
            ok[idx] = {k: int(v) for k, v in ans.items() if k in items}
    return ok, retry


def run_batch(personas, wave, temperature, out_csv, poll_interval=30,
              max_rounds=3, workdir="outputs", chunk_size=1000):
    """Gemini Batch API로 대량 생성(주 모델 전용). 사전등록 파라미터 불변.
    조건부 제외·형식 위반 재생성(최대 max_rounds회)을 배치 라운드로 보존한다.
    동시 인큐 한도(≈1000요청)를 넘지 않도록 chunk_size 단위 서브배치를 순차 처리한다."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    items = ITEMS_BY_WAVE[wave]
    survey = build_user_prompt(items, set())  # 공통 설문(조건부 포함, 사후 정합)

    def checkpoint(results):
        rows = []
        for idx, p in enumerate(personas):
            r = dict(results.get(idx) or {"_error": "pending_or_failed"})
            r.update({"_idx": idx, "_model": "gemini", "_wave": wave,
                      "성별": p.get("gender"), "연령대": p.get("age")})
            rows.append(r)
        pd.DataFrame(rows).sort_values("_idx").to_csv(out_csv, index=False, encoding="utf-8-sig")

    results = {}   # idx -> 최종 응답 dict(성공)
    pending = list(range(len(personas)))
    for rnd in range(max_rounds):
        if not pending:
            break
        chunks = [pending[i:i + chunk_size] for i in range(0, len(pending), chunk_size)]
        print(f"[라운드 {rnd+1}] 대상 {len(pending)}건 → {len(chunks)}개 서브배치", flush=True)
        next_pending = []
        for ci, chunk in enumerate(chunks):
            print(f"  서브배치 {ci+1}/{len(chunks)} ({len(chunk)}건)", flush=True)
            ok, retry = _run_batch_chunk(
                client, types, chunk, personas, survey, items, temperature,
                wave, f"r{rnd}c{ci}", poll_interval, workdir)
            results.update(ok)
            next_pending.extend(retry)
            checkpoint(results)  # 서브배치마다 체크포인트 저장
            print(f"    성공 {len(ok)} / 재생성 {len(retry)} (누적 성공 {len(results)})", flush=True)
        pending = next_pending

    # 결과 조립(미완/실패 표기)
    for idx in pending:
        results.setdefault(idx, {"_error": "format_violation_after_batch_retries"})
    rows = []
    for idx, p in enumerate(personas):
        r = results.get(idx) or {"_error": "format_violation_after_batch_retries"}
        r = dict(r)
        r.update({"_idx": idx, "_model": "gemini", "_wave": wave,
                  "성별": p.get("gender"), "연령대": p.get("age")})
        rows.append(r)
    pd.DataFrame(rows).sort_values("_idx").to_csv(out_csv, index=False, encoding="utf-8-sig")
    n_err = sum(1 for r in rows if "_error" in r and r.get("_error"))
    print(f"완료: {out_csv} (총 {len(rows)}, 오류 {n_err})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["gemini", "exaone"], default="gemini")
    ap.add_argument("--wave", type=int, choices=[2024, 2025], default=2024)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--panel", default="analysis_ready.csv")
    ap.add_argument("--personas", default="nemotron_personas_korea.csv")
    ap.add_argument("--multiplier", type=float, default=2)
    ap.add_argument("--cell-floor", type=int, default=200,
                    help="셀별 최소 표본 하한(0이면 미적용)")
    ap.add_argument("--cell-cap", type=int, default=600,
                    help="셀별 최대 표본 상한(0이면 미적용)")
    ap.add_argument("--limit", type=int, default=None,
                    help="시범 실행용: 층화 비율 유지하며 총 표본을 이 규모로 축소")
    ap.add_argument("--out", default="synthetic_responses.csv")
    ap.add_argument("--workers", type=int, default=12, help="동시 실행 스레드 수(live)")
    ap.add_argument("--mode", choices=["live", "batch"], default="live",
                    help="live=실시간 병렬, batch=Gemini Batch API(대량·저비용, gemini 전용)")
    ap.add_argument("--poll", type=int, default=30, help="batch 상태 폴링 간격(초)")
    ap.add_argument("--chunk", type=int, default=1000,
                    help="batch 서브배치 크기(동시 인큐 한도 ≈1000)")
    ap.add_argument("--conditioning", choices=["full", "demographic"], default="full",
                    help="full=페르소나 서사 / demographic=성별·연령만(ablation 대조군)")
    a = ap.parse_args()
    ps = sample_personas(a.panel, a.personas, a.wave, a.multiplier, limit=a.limit,
                         cell_floor=a.cell_floor or None, cell_cap=a.cell_cap or None)
    if a.conditioning == "demographic":
        # M2 ablation: 페르소나 서사 제거, 성별·연령대만으로 조건화
        for p in ps:
            p["persona_prompt"] = f"성별 {p['gender']}, 연령대 {PERSONA_AGE.get(p['age'], p['age'])}"
    print(f"페르소나 {len(ps)}명 추출, {a.model}/{a.mode}/{a.conditioning} 시작(temp={a.temperature})")
    if a.mode == "batch":
        if a.model != "gemini":
            raise SystemExit("batch 모드는 gemini 전용입니다.")
        run_batch(ps, a.wave, a.temperature, a.out, poll_interval=a.poll, chunk_size=a.chunk)
    else:
        run(ps, a.model, a.wave, a.temperature, a.out, workers=a.workers)
