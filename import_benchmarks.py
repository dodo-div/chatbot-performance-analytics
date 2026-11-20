"""Import the two saved CampusIQ benchmarks into a local SQLite database."""

import csv
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from analyze import read_results


PROJECT = Path(__file__).resolve().parent
DATABASE = PROJECT / "data" / "benchmarks.sqlite3"
RUN_FOLDERS = {
    "first": PROJECT / "data",
    "second": PROJECT / "runs" / "second_benchmark",
}
CREATE_ATTEMPTS = """
    CREATE TABLE IF NOT EXISTS attempts (
        run_id TEXT NOT NULL,
        attempt_id TEXT NOT NULL,
        category TEXT NOT NULL,
        expected_behavior TEXT NOT NULL,
        outcome TEXT NOT NULL,
        latency_ms REAL NOT NULL,
        answer_grade TEXT NOT NULL,
        data_origin TEXT NOT NULL,
        cached INTEGER CHECK (cached IN (0, 1)),
        question TEXT NOT NULL,
        expected_answer TEXT NOT NULL,
        pdf_reference TEXT NOT NULL,
        reply_text TEXT,
        request_error TEXT,
        PRIMARY KEY (run_id, attempt_id)
    )
"""
INSERT_ATTEMPT = """
    INSERT INTO attempts (
        run_id, attempt_id, category, expected_behavior, outcome, latency_ms,
        answer_grade, data_origin, cached, question, expected_answer, pdf_reference,
        reply_text, request_error
    ) VALUES (
        :run_id, :attempt_id, :category, :expected_behavior, :outcome, :latency_ms,
        :answer_grade, :data_origin, :cached, :question, :expected_answer, :pdf_reference,
        :reply_text, :request_error
    )
"""


def read_question_notes(path):
    """Read the question table before the Method heading in the original notes."""
    questions = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line == "## Method":
            break
        if line.startswith("| R"):
            attempt_id, question, expected, reference = (
                cell.strip() for cell in line.strip("|").split("|")
            )
            questions[attempt_id] = {
                "question": question,
                "expected_answer": expected,
                "pdf_reference": reference
                .replace("Calendar, p.", "Academic-Calendar-2026-27.pdf, p.")
                .replace("2022 ordinance, p.", "Examination-Ordinance-2022.pdf, p."),
            }
    return questions


def read_raw_replies(path):
    records = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        attempt_id = record["attempt_id"]
        if attempt_id in records:
            raise ValueError(f"{path.name} has duplicate attempt ID {attempt_id}")
        records[attempt_id] = record
    return records


def read_local_run(run_id, results, raw_replies, questions):
    attempt_ids = {row["attempt_id"] for row in results}
    if attempt_ids != raw_replies.keys() or attempt_ids != questions.keys():
        raise ValueError(f"{run_id} run has different attempt IDs in the CSV, replies, or notes")

    for row in results:
        attempt_id = row["attempt_id"]
        raw = raw_replies[attempt_id]
        notes = questions[attempt_id]
        if row["data_origin"] != "measured":
            raise ValueError(f"{run_id} {attempt_id} must contain measured data")
        if raw["question"] != notes["question"] or raw["latency_ms"] != row["latency_ms"]:
            raise ValueError(f"{run_id} {attempt_id} has a mismatched question or latency")
        reply = raw.get("reply")
        reply_fields = reply if isinstance(reply, dict) else {}
        cache_flag = reply_fields.get("cached")
        # A missing cache flag stays NULL. False is an explicit cache miss.
        yield {
            **row,
            **notes,
            "run_id": run_id,
            "cached": cache_flag if isinstance(cache_flag, bool) else None,
            "reply_text": reply_fields.get("answer"),
            "request_error": reply_fields.get("detail") or raw.get("error"),
        }


def read_shared_run(run_id, questions):
    path = PROJECT / "data" / f"dashboard_{run_id}.csv"
    results = read_results(path)
    with path.open(encoding="utf-8-sig", newline="") as file:
        details = {row["attempt_id"]: row for row in csv.DictReader(file)}
    if {row["attempt_id"] for row in results} != questions.keys():
        raise ValueError(f"{path.name} has different attempt IDs from the question notes")

    cache_flags = {"": None, "0": False, "1": True}
    for row in results:
        attempt_id = row["attempt_id"]
        detail = details[attempt_id]
        if row["data_origin"] != "measured" or detail["cached"] not in cache_flags:
            raise ValueError(f"{path.name} has invalid data for {attempt_id}")
        yield {
            **row,
            **questions[attempt_id],
            "run_id": run_id,
            "cached": cache_flags[detail["cached"]],
            "reply_text": detail["reply_summary"] or None,
            "request_error": None,
        }


def read_run(run_id, folder, questions):
    results_path = folder / "my_results.csv"
    replies_path = folder / "benchmark_replies.jsonl"
    if results_path.is_file() and replies_path.is_file():
        return read_local_run(run_id, read_results(results_path), read_raw_replies(replies_path), questions)
    # A fresh checkout has sanitized measurements and short reply summaries.
    return read_shared_run(run_id, questions)


def import_benchmarks():
    questions = read_question_notes(PROJECT / "benchmark_notes.md")
    attempts = [
        attempt
        for run_id, folder in RUN_FOLDERS.items()
        for attempt in read_run(run_id, folder, questions)
    ]
    with closing(sqlite3.connect(DATABASE)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(CREATE_ATTEMPTS)
        # Refresh the derived table in one transaction so readers see a complete import.
        connection.execute("DELETE FROM attempts")
        connection.executemany(INSERT_ATTEMPT, attempts)
    return len(attempts)


if __name__ == "__main__":
    count = import_benchmarks()
    print(f"Imported {count} attempts into {DATABASE.relative_to(PROJECT)}")
