import json
import re


def extract_json_action(text: str) -> dict | None:
    json_patterns = [
        r'```json\s*\n?(.*?)\n?\s*```',
        r'```\s*\n?(.*?)\n?\s*```',
        r'\{[^{}]*"action"\s*:\s*"[^"]*"[^{}]*\}',
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            raw = match.strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "action" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue

    brace_start = text.find("{")
    while brace_start != -1:
        brace_end = text.find("}", brace_start)
        while brace_end != -1:
            candidate = text[brace_start:brace_end + 1]
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict) and "action" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
            brace_end = text.find("}", brace_end + 1)
        brace_start = text.find("{", brace_start + 1)

    return None


def strip_json_from_response(text: str, action: dict) -> str:
    cleaned = text

    for pattern in [
        r'```json\s*\n?.*?\n?\s*```',
        r'```\s*\n?.*?\n?\s*```',
    ]:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)

    action_json = json.dumps(action, ensure_ascii=False)
    cleaned = cleaned.replace(action_json, "")

    lines = cleaned.strip().split("\n")
    lines = [l for l in lines if l.strip()]
    return "\n".join(lines).strip()
