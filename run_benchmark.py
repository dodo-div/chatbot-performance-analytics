"""Send the CampusIQ questions from benchmark_notes.md and save each reply."""

import argparse
import json
import time
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


PROJECT = Path(__file__).resolve().parent
DATA = PROJECT / "data"
API = "http://127.0.0.1:8000/api/chat"
TIMEOUT_SECONDS = 120


def read_questions():
    questions = {}
    for line in (PROJECT / "benchmark_notes.md").read_text(encoding="utf-8").splitlines():
        if line == "## Method":
            break
        if line.startswith("| R"):
            attempt_id, question = (cell.strip() for cell in line.split("|")[1:3])
            questions[attempt_id] = question
    return questions


def ask(question):
    request = Request(
        API,
        data=json.dumps({"message": question, "history": []}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    start = time.perf_counter()
    try:
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                status = response.status
                body = response.read()
        except HTTPError as error:
            with error:
                status = error.code
                body = error.read()
        elapsed_ms = round((time.perf_counter() - start) * 1000)
    except (OSError, HTTPException) as error:
        # Keep the elapsed time when a timeout or connection failure ends the attempt.
        elapsed_ms = round((time.perf_counter() - start) * 1000)
        return {"latency_ms": elapsed_ms, "error": str(error)}

    try:
        reply = json.loads(body)
    except (ValueError, UnicodeError):
        reply = body.decode("utf-8", errors="replace")
    record = {"latency_ms": elapsed_ms, "http_status": status, "reply": reply}
    if not 200 <= status < 300:
        record["error"] = f"HTTP {status}"
    elif not isinstance(reply, dict) or not isinstance(reply.get("answer"), str) or not reply["answer"].strip():
        record["error"] = "API reply has no answer text"
    return record


def main():
    questions = read_questions()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt_ids", nargs="*", metavar="ID", help="question IDs, in request order")
    args = parser.parse_args()
    attempt_ids = args.attempt_ids or list(questions)
    if len(set(attempt_ids)) != len(attempt_ids) or any(key not in questions for key in attempt_ids):
        parser.error("supply distinct question IDs from benchmark_notes.md")

    output = DATA / "benchmark_replies.jsonl"
    previous = (
        {json.loads(line)["attempt_id"] for line in output.read_text(encoding="utf-8").splitlines()}
        if output.exists() else set()
    )
    if previous.intersection(attempt_ids):
        parser.error("one or more IDs already have a recorded attempt")

    with output.open("a", encoding="utf-8") as file:
        for attempt_id in attempt_ids:
            result = ask(questions[attempt_id])
            record = {"attempt_id": attempt_id, "question": questions[attempt_id], **result}
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
            file.flush()
            status = result.get("error", "reply received")
            print(f"{attempt_id} {result['latency_ms']} ms | {status}", flush=True)


if __name__ == "__main__":
    main()
