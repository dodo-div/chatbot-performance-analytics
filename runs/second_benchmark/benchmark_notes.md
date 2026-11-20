# Second CampusIQ benchmark — 20 November 2026

This run used the exact ten questions, expected facts, PDF pages, and grading rules in the [first benchmark notes](../../benchmark_notes.md). The question text sent to the API is also in the [raw replies](benchmark_replies.jsonl).

## Preflight

The existing CampusIQ 1.9.0 backend on port 8000 passed its health check. A separate chat request asked for the last instructional day of Semester II for second-year students in the 2026–27 academic calendar. CampusIQ returned HTTP 200 in 66 ms and answered **8 May 2027**, which matches page 2 of `Academic-Calendar-2026-27.pdf`. The API reported `cached: false`. The [preflight record](preflight.json) is outside the ten benchmark attempts and all summary metrics.

## Method

The original runner sent one POST per question to `http://127.0.0.1:8000/api/chat`, in the same order, with an empty history each time. It used the original 120-second HTTP timeout and measured from immediately before the request until the full body arrived or the request failed. The benchmark client sent no retries. The backend stayed running with its existing cache. The cache column below comes from the API's `cached` field.

To reproduce the timed portion, follow the backend setup in the [README](../../README.md) and run the original client with a new output folder. From the project folder, set `$campusPython` to the Python executable as shown in the README, then run:

```powershell
@'
from pathlib import Path
import run_benchmark

run_benchmark.DATA = Path("runs/repeat_benchmark")
run_benchmark.DATA.mkdir(parents=True, exist_ok=True)
run_benchmark.main()
'@ | & $campusPython -B -
```

Review the new raw replies using the first benchmark's grading rules. The command used to analyze this run was `& $campusPython -B analyze.py runs/second_benchmark/my_results.csv`.

## Review

| ID | Outcome | Time (ms) | Cache hit | Grade | Review |
| --- | --- | ---: | --- | --- | --- |
| R001 | Answered | 1,735 | No | Correct | Gave 3 August 2026 for first-year Semester I commencement, as on calendar page 1. |
| R002 | Answered | 17 | No | Correct | Gave 5 November 2026 for the last instructional day for students other than first-year students, as on calendar page 2. |
| R003 | Answered | 12 | No | Correct | Gave 4 January 2027 for Semester II commencement for students other than first-year students, which includes second-year students. Calendar page 2 agrees. |
| R004 | Abstained | 9,818 | No | | Withheld the dates because its date check failed. Calendar page 1 gives 7–28 December 2026 for the first-year term-end exams. |
| R005 | Answered | 19 | Yes | Incorrect | Gave the last instructional day, 5 November 2026. The winter vacation row on calendar page 2 gives 19 December 2026 through 3 January 2027 and says the actual days depend on the exam timetable. |
| R006 | Answered | 15 | Yes | Correct | Said the answer sheets are digitally masked, matching ordinance page 12, section 7.6.3. |
| R007 | Answered | 13 | Yes | Correct | Said the declared result appears in the student's login, matching ordinance page 12, section 8.1. |
| R008 | Abstained | 10 | Yes | | Said it could not verify who approves an amendment and mentioned the course chairman for result declaration. Ordinance page 13, section 8.3, gives the Vice Chancellor's approval for an amendment. |
| R009 | Abstained | 10 | Yes | | Declined to give a personal attendance percentage. It added the general 75% rule from ordinance page 15. |
| R010 | Abstained | 5 | No | | Said the requested 2024–25 calendar was unavailable. The local calendar covers 2026–27. |

## Comparison

| Metric | First run | Second run |
| --- | ---: | ---: |
| Attempts | 10 | 10 |
| Request errors | 4/10 (40.0%) | 0/10 (0.0%) |
| Answers reviewed out of answerable attempts | 3/8 | 6/8 |
| Correct out of reviewed answers | 2/3 (66.7%) | 5/6 (83.3%) |
| Abstentions on answerable questions | 1/8 | 2/8 |
| Correct abstentions on outside-coverage questions | 2/2 | 2/2 |
| Cache hits out of replies | 0/6 | 5/10 |
| Median reply latency | 8,904 ms (6 replies) | 14 ms (10 replies) |
| p95 reply latency | 16,500 ms (6 replies) | 9,818 ms (10 replies) |

The first run's four errors came from a ChromaDB write restriction. On those same questions, the second run returned three correct calendar answers and one abstention after the date check failed. The winter vacation question (R005) repeated the incorrect last-instructional-day answer from cache, at 19 ms versus 2,068 ms. The result-amendment question (R008) repeated the abstention from cache, at 10 ms versus 16,500 ms. The changed backend access, five cache hits, and small set of questions limit what the latency and accuracy differences say about typical performance.
