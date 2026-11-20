"""Browse the two saved benchmark runs in Streamlit."""

import sqlite3
from contextlib import closing

import streamlit as st

from analyze import attempt_counts, rate, reply_latency
from import_benchmarks import DATABASE


RUN_NAMES = {"first": "First run", "second": "Second run"}
CACHE_LABELS = {1: "Hit", 0: "Miss", None: "Unknown"}


def load_attempts():
    # Open read-only so the dashboard can only display the imported records.
    with closing(sqlite3.connect(f"{DATABASE.as_uri()}?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute("SELECT * FROM attempts ORDER BY run_id, attempt_id").fetchall()


def show_comparison(runs):
    comparison = {}
    for run_id, attempts in runs.items():
        counts = attempt_counts(attempts)
        comparison[RUN_NAMES[run_id]] = {
            "Attempts": str(counts["attempts"]),
            "Request errors": rate(counts["errors"], counts["attempts"]),
            "Correct reviewed answers": rate(counts["correct_answers"], counts["reviewed"]),
            "Review coverage": rate(counts["reviewed"], counts["answerable"]),
            "Correct abstentions": rate(counts["correct_abstentions"], counts["unsupported"]),
        }
    metrics = next(iter(comparison.values()))
    st.dataframe([
        {"Metric": metric, **{run: values[metric] for run, values in comparison.items()}}
        for metric in metrics
    ], hide_index=True)
    st.caption(
        "Review coverage is graded answers out of answerable attempts. Correct abstentions "
        "are measured on questions outside document coverage. The first run had four "
        "database access errors, and the second run reused five cached replies."
    )


def show_latency(runs):
    summary = []
    individual_replies = []
    chart_columns = st.columns(len(runs))
    for column, (run_id, attempts) in zip(chart_columns, runs.items()):
        run_name = RUN_NAMES[run_id]
        replies = [attempt for attempt in attempts if attempt["outcome"] != "error"]
        for label in ["All replies", *CACHE_LABELS.values()]:
            group = replies if label == "All replies" else [
                reply for reply in replies if CACHE_LABELS[reply["cached"]] == label
            ]
            count, median, p95 = reply_latency(group)
            summary.append({
                "Run": run_name,
                "Cache status": label,
                "Replies": count,
                "Median": f"{median:,.0f} ms" if count else "—",
                "p95": f"{p95:,.0f} ms" if count else "—",
            })
        points = [
            {
                "Run": run_name,
                "Attempt": reply["attempt_id"],
                "Cache status": CACHE_LABELS[reply["cached"]],
                "Reply time (ms)": reply["latency_ms"],
            }
            for reply in replies
        ]
        individual_replies.extend(points)
        with column:
            st.subheader(run_name)
            if points:
                st.scatter_chart(
                    points, x="Attempt", y="Reply time (ms)", color="Cache status", height=240
                )
            else:
                st.caption("No replies.")

    st.caption(
        "Latency includes answers and abstentions. Each chart scales to its own replies. "
        "The nearest-rank p95 is the slowest reply in these small samples."
    )
    st.dataframe(summary, hide_index=True)
    if individual_replies:
        st.dataframe(individual_replies, hide_index=True)


def question_result(attempt):
    outcome = attempt["outcome"].capitalize()
    if attempt["answer_grade"]:
        outcome += f" · {attempt['answer_grade']}"
    cache_status = CACHE_LABELS[attempt["cached"]].lower()
    return f"{outcome} · cache {cache_status}"


def show_questions(runs):
    by_run = {
        run_id: {attempt["attempt_id"]: attempt for attempt in attempts}
        for run_id, attempts in runs.items()
    }
    first_run = by_run["first"]
    st.dataframe([
        {
            "ID": attempt_id,
            "Question": attempt["question"],
            **{
                RUN_NAMES[run_id]: question_result(attempts[attempt_id])
                for run_id, attempts in by_run.items()
            },
        }
        for attempt_id, attempt in first_run.items()
    ], hide_index=True, column_config={"Question": st.column_config.TextColumn(width="large")})

    for attempt_id, label in (("R005", "Winter vacation"), ("R008", "Result amendment")):
        st.subheader(f"{attempt_id} · {label}")
        expected = first_run[attempt_id]
        st.markdown(f"**Expected answer** · {expected['expected_answer']}")
        st.caption(expected["pdf_reference"])
        for column, (run_id, attempts) in zip(st.columns(len(runs)), by_run.items()):
            attempt = attempts[attempt_id]
            with column:
                st.markdown(f"**{RUN_NAMES[run_id]}**")
                st.caption(question_result(attempt))
                st.write(attempt["reply_text"] or attempt["request_error"] or "No reply recorded.")


def main():
    st.set_page_config(page_title="Chatbot Performance Analytics", layout="wide")
    st.title("Chatbot Performance Analytics")
    st.caption("CampusIQ benchmark · 20 November 2026")
    if not DATABASE.is_file():
        st.error("Run import_benchmarks.py to create the local database.")
        return

    attempts = load_attempts()
    runs = {
        run_id: [attempt for attempt in attempts if attempt["run_id"] == run_id]
        for run_id in RUN_NAMES
    }
    comparison, latency, questions = st.tabs(
        ["Run comparison", "Reply latency", "Question outcomes"]
    )
    with comparison:
        show_comparison(runs)
    with latency:
        show_latency(runs)
    with questions:
        show_questions(runs)


if __name__ == "__main__":
    main()
