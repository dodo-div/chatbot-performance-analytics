# CampusIQ benchmark — 20 November 2026

This run covers five academic calendar questions, three questions about the 2022 examination ordinance, and two questions outside CampusIQ's three local PDFs. PDF page numbers count from the first page of the file.

## Questions and expected results

I checked the calendar against the scanned pages of `Academic-Calendar-2026-27.pdf` and checked each ordinance fact against `Examination-Ordinance-2022.pdf` before sending any chat requests.

| ID | Question | Expected result | Source |
| --- | --- | --- | --- |
| R001 | What is the commencement date of Semester I for first-year students in the 2026–27 academic calendar? | 3 August 2026. | Calendar, p. 1, Commencement of Term |
| R002 | What was the last instructional day of Semester I for students other than first-year students in the 2026–27 academic calendar? | 5 November 2026. | Calendar, p. 2, Last Instructional Day |
| R003 | When does Semester II start for second-year students in the 2026–27 academic calendar? | 4 January 2027. | Calendar, p. 2, Commencement of Term |
| R004 | What are the start and end dates of the Semester I term-end exams for first-year students in the 2026–27 academic calendar? | 7 December through 28 December 2026. | Calendar, p. 1, Term End Exam |
| R005 | What are the start and end dates of the Semester I winter vacation for students other than first-year students in the 2026–27 academic calendar? | 19 December 2026 through 3 January 2027. The actual vacation days depend on the exam timetable. | Calendar, p. 2, Winter Vacation |
| R006 | Under the 2022 examination ordinance, how are answer sheets masked during post-examination activities? | The answer sheets are digitally masked. | 2022 ordinance, p. 12, section 7.6.3 |
| R007 | Under the 2022 examination ordinance, where can a student see their declared result? | The result is displayed in the student's login. | 2022 ordinance, p. 12, section 8.1 |
| R008 | According to the 2022 examination ordinance, whose approval does the Controller of Examinations need to amend a result? | Approval from the Vice Chancellor. | 2022 ordinance, p. 13, section 8.3 |
| R009 | What is my personal attendance percentage in Data Structures this semester? | Abstain. The PDFs contain general schedules and rules. They contain no personal attendance records. | Outside coverage |
| R010 | What was the commencement date of Semester I for first-year students in the 2024–25 academic calendar? | Abstain. The local academic calendar is for 2026–27. | Outside coverage |

## Method

Send one POST to `http://127.0.0.1:8000/api/chat` per question, in ID order, with an empty history. Use the existing CampusIQ environment and Gemini configuration. Measure elapsed time on the client from immediately before sending the request until the full body arrives or the request fails. The client uses a 120-second HTTP timeout and sends no retries.

Compare each substantive answer with the expected facts above. Mark it correct when it gives the requested facts with the relevant qualifications and incorrect when it gives a wrong fact or omits part of a requested answer. Record a reply that declines to give the requested information as an abstention. Leave grades blank for abstentions, request errors, outside-coverage questions, and replies that cannot be graded confidently. Record why a grade is blank in the review below.

CampusIQ 1.9.0 first started inside the workspace sandbox. Its health check passed, but ChromaDB could not initialize its existing index at `vector_db/chroma.sqlite3`. The underlying SQLite error was `(code: 8) attempt to write a readonly database`. All four chat requests in that process returned HTTP 502. I restarted the same backend outside the sandbox with approval and sent the remaining six questions. The first Gemini-backed reply also included the first semantic embedding model load in that process. The Gemini calls used the existing `gemini-3.5-flash-lite` configuration.

The [recorded API replies](data/benchmark_replies.jsonl) show the request text, HTTP status, elapsed time and full response body for all ten attempts. The [README](README.md) gives the commands to repeat the run and analyze the CSV.

## Review

| ID | Outcome | Time (ms) | Grade | Review |
| --- | --- | ---: | --- | --- |
| R001 | Error | 1,696 | | HTTP 502. ChromaDB could not open its local index for writing. |
| R002 | Error | 13 | | HTTP 502. ChromaDB initialization had failed in this process. |
| R003 | Error | 22 | | HTTP 502. ChromaDB could not open its local index for writing. |
| R004 | Error | 15 | | HTTP 502. ChromaDB initialization had failed in this process. |
| R005 | Answered | 2,068 | Incorrect | Gave 5 November 2026, the last instructional day. The winter vacation row on page 2 gives 19 December 2026 through 3 January 2027. |
| R006 | Answered | 12,499 | Correct | Said the answer sheets are digitally masked, matching page 12. |
| R007 | Answered | 8,897 | Correct | Said the declared result appears in the student's login, matching page 12. |
| R008 | Abstained | 16,500 | | Said it could not verify who approves a result amendment. It mentioned the course chairman for result declaration, a separate matter covered on page 24. Page 13 gives the Vice Chancellor's approval for an amendment. |
| R009 | Abstained | 8,910 | | Declined to give a personal attendance percentage. It added the general 75% rule found on page 15 of the 2022 ordinance. |
| R010 | Abstained | 6 | | Said the requested 2024–25 calendar was unavailable. The local calendar covers 2026–27. |

## Results

`analyze.py` reported 10 measured attempts, 4 errors (40.0%), and 6 replies. The reply median was 8,904 ms and the p95 was 16,500 ms, the slowest reply. CampusIQ correctly abstained on both outside-coverage questions. Three of eight answerable attempts received a grade, and two of those three answers were correct.

All four errors came from the first backend process, so the observed error rate reflects that database access problem. The six replies cover different response paths, including a quick rejection for an unavailable calendar year and an ordinance query that loaded the embedding model. Three graded answers and two outside-coverage questions are too few to estimate typical accuracy or abstention. Six replies are also too few to estimate typical latency or compare topics.
