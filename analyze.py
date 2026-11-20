"""Summarize a CSV of chatbot evaluation attempts."""

import argparse
import csv
import math
import statistics
from pathlib import Path

DEMO_FILE = Path(__file__).parent / "data" / "demo_results.csv"
REQUIRED_FIELDS = (
    "attempt_id",
    "category",
    "expected_behavior",
    "outcome",
    "latency_ms",
    "answer_grade",
    "data_origin",
)


def read_results(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = set(REQUIRED_FIELDS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")

        results = []
        seen_ids = set()
        for raw_row in reader:
            try:
                if None in raw_row or any(raw_row[field] is None for field in REQUIRED_FIELDS):
                    raise ValueError("row does not match the header")
                row = {field: raw_row[field].strip() for field in REQUIRED_FIELDS}
                attempt_id = row["attempt_id"]
                if not attempt_id or attempt_id in seen_ids:
                    raise ValueError("attempt_id must be nonempty and unique")
                if not row["category"]:
                    raise ValueError("category is required")
                if row["expected_behavior"] not in {"answer", "abstain"}:
                    raise ValueError("expected_behavior must be answer or abstain")
                if row["outcome"] not in {"answered", "abstained", "error"}:
                    raise ValueError("outcome must be answered, abstained or error")
                if row["answer_grade"] not in {"", "correct", "incorrect"}:
                    raise ValueError("answer_grade must be correct, incorrect or blank")
                if row["answer_grade"] and (
                    row["outcome"] != "answered" or row["expected_behavior"] != "answer"
                ):
                    raise ValueError("grade only answers to answerable questions")
                if row["data_origin"] not in {"demo", "measured"}:
                    raise ValueError("data_origin must be demo or measured")

                latency = float(row["latency_ms"])
                if not math.isfinite(latency) or latency < 0:
                    raise ValueError("latency_ms must be a finite, nonnegative number")
                row["latency_ms"] = latency
            except ValueError as error:
                raise ValueError(f"CSV line {reader.line_num}: {error}") from error

            results.append(row)
            seen_ids.add(attempt_id)

    if not results:
        raise ValueError("CSV contains no attempt rows")
    if len({row["data_origin"] for row in results}) != 1:
        raise ValueError("analyze demo and measured rows in separate files")
    return results


def rate(count, total):
    if not total:
        return "n/a (0 eligible attempts)"
    return f"{count}/{total} ({count / total:.1%})"


def attempt_counts(results):
    errors = sum(row["outcome"] == "error" for row in results)
    unsupported = [row for row in results if row["expected_behavior"] == "abstain"]
    answerable = [row for row in results if row["expected_behavior"] == "answer"]
    correct_abstentions = sum(row["outcome"] == "abstained" for row in unsupported)
    graded = [row for row in answerable if row["answer_grade"]]
    correct_answers = sum(row["answer_grade"] == "correct" for row in graded)
    return {
        "attempts": len(results),
        "errors": errors,
        "unsupported": len(unsupported),
        "answerable": len(answerable),
        "correct_abstentions": correct_abstentions,
        "reviewed": len(graded),
        "correct_answers": correct_answers,
    }


def reply_latency(results):
    times = sorted(row["latency_ms"] for row in results if row["outcome"] != "error")
    if not times:
        return 0, None, None
    # Nearest rank uses the actual reply at rank ceil(0.95 * n).
    return len(times), statistics.median(times), times[math.ceil(0.95 * len(times)) - 1]


def summarize(results):
    counts = attempt_counts(results)
    response_count, median, p95 = reply_latency(results)

    print(f"Attempts: {counts['attempts']}")
    print(f"Request error rate: {rate(counts['errors'], counts['attempts'])}")
    if response_count:
        print(f"Response latency (n={response_count}): p50 {median:.0f} ms, p95 {p95:.0f} ms")
    else:
        print("Response latency: n/a (0 responses)")
    print(f"Correct abstentions: {rate(counts['correct_abstentions'], counts['unsupported'])}")
    print(f"Correct reviewed answers: {rate(counts['correct_answers'], counts['reviewed'])}")
    print(f"Reviewed answers / answerable attempts: {counts['reviewed']}/{counts['answerable']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("csv_path", type=Path, nargs="?", help="path to a results CSV")
    source.add_argument("--demo", action="store_true", help="use the bundled practice data")
    args = parser.parse_args()

    try:
        results = read_results(DEMO_FILE if args.demo else args.csv_path)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(2, f"Error: {error}\n")

    origin = "synthetic demo data" if results[0]["data_origin"] == "demo" else "measured data"
    print(f"Chatbot performance summary | {origin}")
    print("\nOverall")
    summarize(results)
    for category in sorted({row["category"] for row in results}):
        print(f"\n{category}")
        summarize([row for row in results if row["category"] == category])


if __name__ == "__main__":
    main()
