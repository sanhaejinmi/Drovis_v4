# core/services/llm_explainer.py
import os
from typing import Dict, Any, Optional, Tuple

# --- LLM 클라이언트(예외 안전) ---
_client = None
_client_err = None
try:
    from dotenv import load_dotenv
    load_dotenv()
    from openai import OpenAI
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    _client_err = e  # 임포트/키 실패하더라도 아래 함수들은 항상 존재하게 함

def _format_basis_table() -> str:
    return (
        "| 조건 | 판단 결과 |\n"
        "| --- | --- |\n"
        "| 배회, 전달, 재접근 **세 가지 행동 모두 20% 이상** | 상 |\n"
        "| **두 가지 행동** 모두 20% 이상 | 중 |\n"
        "| **한 가지 행동이 80% 이상** | 중 |\n"
        "| **한 가지 행동이 20% 이상** | 하 |\n"
        "| 그 외 | 하 |\n"
    )

def _compute_reliability(success_frames: int, fail_frames: int) -> Optional[float]:
    total = success_frames + fail_frames
    if total <= 0:
        return None
    return round((success_frames / total) * 100.0, 1)

def _extract_numbers(context: Dict[str, Any]) -> Dict[str, Any]:
    ev = (context.get("evidence") or {}) if isinstance(context, dict) else {}
    pct = ev.get("overlap_summary") or context.get("behavior_pct") or {}
    normal   = float(pct.get("Normal", pct.get("normal", 0.0)))
    loiter   = float(pct.get("Loitering", pct.get("loitering", 0.0)))
    handover = float(pct.get("Handover", pct.get("handover", 0.0)))
    reapp    = float(pct.get("Reapproach", pct.get("reapproach", 0.0)))

    success_frames = int(ev.get("success_frames", context.get("success_frames", 0)))
    fail_frames    = int(ev.get("fail_frames", context.get("fail_frames", 0)))

    risk = str(
        context.get("risk")
        or (context.get("prediction") or {}).get("label")
        or "하"
    )
    filename = (
        context.get("filename")
        or (context.get("prediction") or {}).get("filename")
        or ev.get("filename")
        or "-"
    )
    return dict(
        filename=filename,
        normal=normal, loiter=loiter, handover=handover, reapp=reapp,
        success_frames=success_frames, fail_frames=fail_frames, risk=risk
    )

# ===== ExplanationWindow가 임포트하는 4개 공개 함수 =====

def build_prompt_from_evidence(record: Dict[str, Any]) -> str:
    nums = _extract_numbers(record)
    basis = _format_basis_table()
    rel = _compute_reliability(nums["success_frames"], nums["fail_frames"])
    if rel is not None and nums["fail_frames"] > 0:
        rel_line = (
            f"- 총 **{nums['success_frames'] + nums['fail_frames']}**개 프레임 중 "
            f"**성공 {nums['success_frames']} / 실패 {nums['fail_frames']}** → "
            f"**신뢰도 {rel:.1f}%** (추가 확인 필요 가능)"
        )
    else:
        rel_line = "- 실패 프레임이 없어 신뢰도 경고는 생략됩니다."

    return f"""
너는 수사보조 시스템 Drovis의 '설명 생성기'다.
아래 수치를 기반으로 사실만 사용해, 정확히 지정한 구조로 마크다운을 작성하라.

[입력]
- 파일명: {nums['filename']}
- 성공 프레임: {nums['success_frames']}
- 실패 프레임: {nums['fail_frames']}
- Normal: {nums['normal']:.1f}%
- Loitering: {nums['loiter']:.1f}%
- Handover: {nums['handover']:.1f}%
- Reapproach: {nums['reapp']:.1f}%
- 최종 위험도(내부 규칙 결과): {nums['risk']}

[판단 기준(고정)]
- Drovis에서의 행동 등장 기준은 20% 이상.
- 세 행동 모두 20% 이상 → '상'
- 두 행동 20% 이상 또는 한 행동 80% 이상 → '중'
- 한 행동 20% 이상 또는 그 외 → '하'

[출력 형식(그대로 준수)]
1. **한 줄 요약**
    - "이 영상은 정상 행동(Normal)이 {nums['normal']:.1f}%, 배회 행동(Loitering)이 {nums['loiter']:.1f}%, 전달(Handover) {nums['handover']:.1f}%, 재접근(Reapproach) {nums['reapp']:.1f}%로 분류되었습니다. 최종 위험도는 '{nums['risk']}'입니다."

2. **판단 근거**
    - "Drovis에서의 행동 등장 기준은 **20% 이상**을 의미하며,"
    - "**세 행동**이 모두 나타나면 '**상**', **두 행동 중첩** 또는 **한 행동**이 **80% 이상**이면 '**중**', **한 행동이 20% 이상이거나 그 외의 경우 '**하**'로 판단합니다."
    {basis}
    - "이번 경우는 **최종 위험도가 '{nums['risk']}'**로 분류되었습니다."

3. **주의**
    - "분석 수치와 규칙 기반 설명으로 제공되며, 법적 판단이 아닙니다."
    {rel_line}

문장 내 숫자는 위 입력을 그대로 사용(반올림 외 임의 변경 금지).
""".strip()

def call_llm(prompt: str) -> str:
    if _client is None:
        return f"[LLM 비활성화] 클라이언트 초기화 실패: {repr(_client_err)}"
    try:
        resp = _client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            temperature=0.2,
            max_output_tokens=900,
        )
        try:
            return resp.output_text
        except Exception:
            return str(resp)
    except Exception as e:
        return f"[LLM 호출 실패]: {e}"

def validate_llm_output(text: str, context: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    ok = ("1." in text or "한 줄 요약" in text) and ("2." in text or "판단 근거" in text) and ("3." in text or "주의" in text)
    lines = text.splitlines()
    section = 0
    b1, b2, b3 = [], [], []
    for ln in lines:
        s = ln.strip()
        if s.startswith("1.") or "한 줄 요약" in s:
            section = 1; continue
        if s.startswith("2.") or "판단 근거" in s:
            section = 2; continue
        if s.startswith("3.") or "주의" in s:
            section = 3; continue
        if section == 1: b1.append(ln)
        elif section == 2: b2.append(ln)
        elif section == 3: b3.append(ln)
    return ok, {
        "one_liner":  ("\n".join(b1).strip()) or "자동 요약 없음",
        "reason_text": ("\n".join(b2).strip()) or "근거 없음",
        "caution_text":("\n".join(b3).strip()) or "주의 없음",
    }

def render_fallback_text(context: Dict[str, Any]) -> str:
    nums = _extract_numbers(context)
    basis = _format_basis_table()
    rel = _compute_reliability(nums["success_frames"], nums["fail_frames"])
    if rel is not None and nums["fail_frames"] > 0:
        rel_line = (
            f"- 총 **{nums['success_frames'] + nums['fail_frames']}**개 프레임 중 "
            f"**성공 {nums['success_frames']} / 실패 {nums['fail_frames']}** → "
            f"**신뢰도 {rel:.1f}%** (추가 확인 필요 가능)"
        )
    else:
        rel_line = "- 실패 프레임이 없어 신뢰도 경고는 생략됩니다."
    return f"""1. **한 줄 요약**
- "이 영상은 Normal {nums['normal']:.1f}%, Loitering {nums['loiter']:.1f}%, Handover {nums['handover']:.1f}%, Reapproach {nums['reapp']:.1f}%입니다. 최종 위험도는 '{nums['risk']}'입니다."

2. **판단 근거**
- Drovis의 행동 등장 기준은 **20% 이상**.
- 규칙 요약:
{basis}
- 내부 규칙에 따라 '{nums['risk']}'로 분류.

3. **주의**
- 분석 수치와 규칙 기반 설명으로 제공되며, 법적 판단이 아님.
{rel_line}
""".strip()
