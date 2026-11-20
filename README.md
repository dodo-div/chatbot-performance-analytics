# Chatbot Performance Analytics

A standalone project for analyzing the reliability and response times of a
document-grounded chatbot. The input is a results CSV. CampusIQ can provide
benchmark data, and the same schema works with other chatbots.

## Run the dashboard on Windows

Open a PowerShell terminal in the project folder that contains `dashboard.py`.
The dashboard reads the two completed runs from saved data and works without
CampusIQ or API calls. Internet access is needed to install Streamlit.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe import_benchmarks.py
.\.venv\Scripts\python.exe -m streamlit run dashboard.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

If the Windows `py` launcher is unavailable and `python` runs your installed
Python 3.14, use this first command:

```powershell
python -m venv .venv
```

Open [the dashboard](http://127.0.0.1:8501) in your browser. The three tabs
compare the run totals, show reply times by cache status, and show outcomes
side by side for each question. The question tab includes the replies and PDF
references for the winter vacation and result-amendment questions.

The import writes `data/benchmarks.sqlite3` with a key made from the run ID
and attempt ID. A fresh checkout uses the included sanitized CSVs. They
contain the measured outcomes, times, grades, cache flags, and short reply
summaries for R005 and R008. If the original CSV and JSONL are available
locally for a run, the import joins them by attempt ID and displays the
recorded replies. A missing cache flag appears as **Unknown**. The separate
preflight is outside the benchmark.

Check the dashboard totals from PowerShell:

```powershell
.\.venv\Scripts\python.exe analyze.py data\dashboard_first.csv
.\.venv\Scripts\python.exe analyze.py data\dashboard_second.csv
```

The first run recorded four request errors out of ten and the second had zero
out of ten. Five of the second run's ten replies were cache hits. The database
access issue in the first run, the cache hits in the second, and the small
sample limit comparisons of typical speed or accuracy.

## Run the command-line demo

Open PowerShell in the project folder. The command-line analyzer uses
Python's standard library. If you already ran the dashboard setup, reuse
its virtual environment.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe analyze.py --demo
```

The demo contains 12 synthetic attempts. It should report 1 error out of 12
attempts, a median response time of 980 ms, and 3 correct abstentions out of 4
unsupported attempts.

## Record your first benchmark

The CampusIQ run from 20 November 2026 used five calendar questions, three
2022 examination ordinance questions, and two questions outside the local
documents. The [first run notes](benchmark_notes.md) contain the questions,
expected facts, PDF pages, and review. The [second run notes](runs/second_benchmark/benchmark_notes.md)
compare both sets of results. The raw-file links in those notes refer to
local records. The shared [first-run CSV](data/dashboard_first.csv) and
[second-run CSV](data/dashboard_second.csv) contain one row per actual API attempt.

The analyzer counted 10 attempts, 4 request errors and 3 graded answers.
Two of the three graded answers were correct. CampusIQ correctly abstained
on both questions outside its documents. Across six replies, the median was
8,904 ms and the p95 was 16,500 ms. All four request errors occurred before a
backend restart that resolved a ChromaDB write restriction. This small run
gives a record of those attempts and is too small to estimate typical
accuracy or response time.

### Repeat the CampusIQ run

1. Start the existing CampusIQ backend on port 8000 using the steps in its
   README and its existing Gemini configuration. Check that
   `http://127.0.0.1:8000/api/health` returns a healthy status.
2. Use a fresh checkout to preserve previous runs. Run
   `.\.venv\Scripts\python.exe run_benchmark.py` from the project folder after
   creating the virtual environment. The runner sends the questions in order
   with an empty chat history and saves each full API reply and elapsed time
   to `data/benchmark_replies.jsonl`. To continue after an interruption, pass
   the remaining IDs as arguments.
3. Review the saved replies against the notes. Copy the template as shown
   below and enter the outcome, elapsed time, and grade for each attempt.
   Run `.\.venv\Scripts\python.exe analyze.py data\my_results.csv` to see the summary.

The historical second-run notes use `$campusPython`. To reproduce those steps, set it to the path of the Python executable in this project's virtual environment.

### Record and grade attempts

Copy the data template, then open the copy in Excel or VS Code.

```powershell
Copy-Item data\results_template.csv data\my_results.csv
```

1. Pick five academic calendar questions, three examination ordinance questions
   and two unsupported questions. A suitable unsupported question asks for an
   individual's attendance, which should be unavailable from public documents.
2. For each answerable question, verify the expected facts against a public PDF
   and record its title and page in a separate set of notes.
3. Ask each question once in a fresh chat. Measure elapsed time from sending
   the question until the full reply appears or the request fails. Use the
   same method throughout the run and record it in your notes. For example,
   1.2 seconds is 1200 ms.
4. Record one row per attempt and keep any request errors. For answerable
   questions that received an answer, compare the reply with the source and
   enter the grade. Use `measured` in your recorded rows.

| CSV field | Value |
| --- | --- |
| `attempt_id` | A unique label, such as `R001` |
| `category` | A consistent topic label, such as `Academic calendar` |
| `expected_behavior` | `answer` or `abstain`, set before testing |
| `outcome` | `answered`, `abstained` or `error` |
| `latency_ms` | Elapsed time in milliseconds |
| `answer_grade` | `correct` or `incorrect` for a reviewed answer to an answerable question. Leave blank otherwise. |
| `data_origin` | `measured` for your benchmark or `demo` for synthetic fixtures |

Save the file as comma-separated UTF-8 CSV, then run it.

```powershell
.\.venv\Scripts\python.exe analyze.py data\my_results.csv
```

## Metric definitions

- **Request error rate** is errors divided by all attempts.
- **Response latency** includes answers and abstentions. The script reports
  the median and nearest-rank p95 alongside the response count. With a small
  sample, the p95 may equal the slowest response.
- **Correct abstention rate** counts abstentions among all questions expected
  to be unsupported. An error on an unsupported question counts as a miss.
- **Correct reviewed answers** is the share of manually reviewed answers that
  are correct. The report also shows how many answerable attempts were reviewed.
  Review coverage drops when answers are ungraded, the bot abstains, or the
  request fails.
