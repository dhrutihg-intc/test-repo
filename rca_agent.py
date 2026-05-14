from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request

import pandas as pd


SYSTEM_PROMPT = """You analyze defect records for root cause analysis.
Return JSON with keys: summary, root_cause, preventive_actions.
Rules:
- summary must be 1-2 concise sentences describing the bug.
- root_cause must be one concise sentence.
- preventive_actions must be a JSON array with 2-4 short action items.
- Use only the provided defect content.
- If evidence is weak, say likely or possible instead of inventing certainty.
- If not enough evidence is available, explicitly mention: further human validation of this data required.
- You can use all fields if needed, but prioritize deep analysis of Title, description, and comments.
"""

# Default runtime settings so repeated PowerShell setup is not required each run.
DEFAULT_HTTPS_PROXY = "http://proxy-dmz.intel.com:912"
DEFAULT_OPENAI_BASE_URL = "https://models.inference.ai.azure.com"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def parse_args() -> argparse.Namespace:
    """Why: supports both interactive and scripted runs.
    What: reads command-line arguments and returns parsed values.
    Inputs: none.
    """
    parser = argparse.ArgumentParser(
        description="Generate RCA summaries from an Excel defect sheet."
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        help="Path to the source Excel file. If omitted, the script prompts for it.",
    )
    return parser.parse_args()


def prompt_for_input_path(initial_path: str | None) -> Path:
    """Why: the script needs a valid Excel source file before processing.
    What: accepts a passed path or prompts the user, then validates it.
    Inputs: initial_path (optional CLI input file path).
    """
    raw_path = initial_path or input("Enter the full path to the defect Excel file: ").strip()
    if not raw_path:
        raise ValueError("No Excel file path was provided.")

    file_path = Path(raw_path.strip('"')).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    if file_path.suffix.lower() not in {".xlsx", ".xls"}:
        raise ValueError("Input file must be an Excel file with .xlsx or .xls extension.")
    return file_path


def normalize_columns(frame: pd.DataFrame) -> dict[str, str]:
    """Why: input files may vary in header casing/spacing.
    What: creates a normalized-to-original column lookup map.
    Inputs: frame (source DataFrame read from Excel).
    """
    return {str(column).strip().lower(): str(column) for column in frame.columns}


def required_column_map(frame: pd.DataFrame) -> dict[str, str]:
    """Why: RCA generation depends on specific defect fields.
    What: verifies required headers exist and returns their mapped names.
    Inputs: frame (source DataFrame with input columns).
    """
    normalized = normalize_columns(frame)
    required = ["id", "title", "description", "comments"]
    missing = [column for column in required if column not in normalized]
    if missing:
        raise KeyError(
            "Missing required columns: " + ", ".join(missing)
        )
    return {column: normalized[column] for column in required}


def clean_text(value: Any) -> str:
    """Why: raw cell values can include nulls and irregular whitespace.
    What: converts values into safe, compact strings for prompting/output.
    Inputs: value (any cell value from the DataFrame or model output).
    """
    if value is None or pd.isna(value):
        return ""
    return " ".join(str(value).split())


def build_bug_context(row: pd.Series, column_map: dict[str, str]) -> dict[str, str]:
    """Why: each row must be transformed into a consistent defect record.
    What: extracts ID, title, description, and comments from one row.
    Inputs: row (one defect record), column_map (normalized required column mapping).
    """
    return {
        "id": clean_text(row[column_map["id"]]),
        "title": clean_text(row[column_map["title"]]),
        "description": clean_text(row[column_map["description"]]),
        "comments": clean_text(row[column_map["comments"]]),
    }


def truncate_text(text: str, limit: int = 2000) -> str:
    """Why: long text can exceed model limits or increase latency/cost.
    What: shortens text to a max length and appends an ellipsis when needed.
    Inputs: text (raw string), limit (maximum allowed length, default 2000).
    """
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def prompt_if_missing(env_name: str, prompt_text: str, secret: bool = False) -> str:
    """Why: sensitive/runtime config should not be hardcoded in source.
    What: reads an env var or prompts the user and stores the result.
    Inputs: env_name (variable key), prompt_text (terminal prompt), secret (hide typing).
    """
    existing = os.getenv(env_name)
    if existing:
        return existing

    if secret:
        print("Note: input is hidden while typing. Type your key and press Enter.")
        try:
            value = getpass.getpass(prompt_text)
        except (EOFError, KeyboardInterrupt):
            raise
        except Exception:
            print("Hidden input is not available in this terminal. Falling back to visible input.")
            value = input(prompt_text).strip()
    else:
        value = input(prompt_text).strip()

    value = value.strip().strip('"').strip("'")
    if not value:
        raise RuntimeError(f"{env_name} is required to continue.")
    os.environ[env_name] = value
    return value


def prompt_provider_selection() -> str:
    """Why: keeps backward compatibility with old call sites.
    What: returns the only supported provider value: openai.
    Inputs: none.
    """
    return "openai"


def ensure_openai_configuration() -> None:
    """Why: ensures the script can run without repeated terminal setup.
    What: asks for API key and applies default model/base-url/proxy settings.
    Inputs: none (reads/writes process environment variables).
    """
    prompt_if_missing("OPENAI_API_KEY", "Enter OPENAI_API_KEY: ", secret=True)
    # Apply defaults directly so users do not need to set these in PowerShell every run.
    os.environ.setdefault("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    os.environ.setdefault("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)
    os.environ.setdefault("HTTPS_PROXY", DEFAULT_HTTPS_PROXY)
    os.environ.setdefault("HTTP_PROXY", os.environ["HTTPS_PROXY"])


def build_prompt_context(context: dict[str, str]) -> dict[str, str]:
    """Why: the model should receive only the relevant, bounded fields.
    What: builds a compact JSON-ready defect payload for prompting.
    Inputs: context (dict with id, title, description, comments).
    """
    return {
        "id": context["id"],
        "title": context["title"],
        "description": truncate_text(context["description"]),
        "comments": truncate_text(context["comments"]),
    }


def openai_payload(context: dict[str, str]) -> dict[str, Any]:
    """Why: request format must be consistent for reliable structured output.
    What: creates the chat-completions payload with JSON response constraints.
    Inputs: context (clean defect fields for one row).
    """
    user_prompt = build_prompt_context(context)
    return {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Analyze this bug record and return JSON only.\n"
                    + json.dumps(user_prompt, ensure_ascii=True)
                ),
            },
        ],
        "temperature": 0.2,
    }


def build_opener() -> request.OpenerDirector:
    """Why: enterprise networks often require traffic through a proxy.
    What: builds a urllib opener that uses HTTP(S)_PROXY when present.
    Inputs: none (reads HTTP_PROXY/HTTPS_PROXY from environment).
    """
    # Respect HTTPS_PROXY or HTTP_PROXY environment variables set in the terminal.
    proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    if proxy_url:
        proxy_handler = request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    else:
        proxy_handler = request.ProxyHandler({})
    return request.build_opener(proxy_handler)


def call_openai_compatible(context: dict[str, str]) -> dict[str, Any]:
    """Why: RCA content is generated by an LLM call per defect row.
    What: sends one request, validates JSON response, and returns parsed fields.
    Inputs: context (single defect payload sent to the model).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for the openai provider.")

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = openai_payload(context)
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    req = request.Request(endpoint, data=data, headers=headers, method="POST")
    opener = build_opener()

    try:
        with opener.open(req, timeout=45) as response:
            body = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 401:
            raise RuntimeError(
                "OpenAI-compatible request failed: Unauthorized (401). "
                "Check that your token is valid, not expired/revoked, and pasted without quotes. "
                f"Server message: {message}"
            ) from exc
        raise RuntimeError(f"OpenAI-compatible request failed: {message}") from exc
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"OpenAI-compatible request failed: {exc}") from exc

    try:
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("LLM response was not valid JSON.") from exc

    preventive_actions = parsed.get("preventive_actions") or []
    if isinstance(preventive_actions, str):
        preventive_actions = [preventive_actions]

    return {
        "summary": clean_text(parsed.get("summary", "")),
        "root_cause": clean_text(parsed.get("root_cause", "")),
        "preventive_actions": [clean_text(item) for item in preventive_actions if clean_text(item)],
    }


def call_llm(context: dict[str, str]) -> dict[str, Any]:
    """Why: isolates the model invocation behind a single helper.
    What: delegates RCA generation to the OpenAI-compatible caller.
    Inputs: context (single defect payload).
    """
    return call_openai_compatible(context)


def summarize_bug(context: dict[str, str]) -> dict[str, str]:
    """Why: output Excel requires fixed business columns.
    What: maps parsed model output into Summary/Root Cause/Preventive Actions.
    Inputs: context (single defect payload).
    """
    rca = call_llm(context)
    actions = "; ".join(rca["preventive_actions"])
    return {
        "Summary": rca["summary"],
        "Root Cause": rca["root_cause"],
        "Preventive Actions": actions,
    }


def generate_output(frame: pd.DataFrame) -> pd.DataFrame:
    """Why: the input workbook must be converted row-by-row into RCA records.
    What: iterates all defects and builds the final output DataFrame schema.
    Inputs: frame (entire input defects DataFrame).
    """
    column_map = required_column_map(frame)
    output_rows: list[dict[str, str]] = []

    for _, row in frame.iterrows():
        # Each input row is treated as one bug record identified by its ID column.
        context = build_bug_context(row, column_map)
        rca_columns = summarize_bug(context)
        output_rows.append(
            {
                "ID": context["id"],
                "Title": context["title"],
                "Summary": rca_columns["Summary"],
                "Root Cause": rca_columns["Root Cause"],
                "Preventive Actions": rca_columns["Preventive Actions"],
            }
        )

    return pd.DataFrame(
        output_rows,
        columns=["ID", "Title", "Summary", "Root Cause", "Preventive Actions"],
    )


def main() -> None:
    """Why: provides one clear execution path for CLI usage.
    What: wires configuration, input read, RCA generation, and Excel export.
    Inputs: none directly (uses CLI args and terminal prompts).
    """
    args = parse_args()
    ensure_openai_configuration()
    input_path = prompt_for_input_path(args.input_path)
    frame = pd.read_excel(input_path)
    output_frame = generate_output(frame)
    output_path = input_path.with_name("RCA.xlsx")
    output_frame.to_excel(output_path, index=False)
    print(f"RCA output written to: {output_path}")


if __name__ == "__main__":
    main()