# Architectural choices

## Data ingestion

Data would be ingested through a 3-layer pipeline. Each layer passes data forward only if it is potentially relevant,
prioritizing false positives over false negatives in early stages.

### Parsing layer

As the email data received is... messy, an LLM will be used to turn the messy data into structured data.
For this the system uses LangChain and a mini LLM that is locally runnable, prompted to extract structured data and use
output parsing for schema enforcement.

Inspiration:
https://medium.com/@juanc.olamendy/parsing-llm-structured-outputs-in-langchain-a-comprehensive-guide-f05ffa88261f

### Filtering layer

Polars is used as the primary dataframe engine for this and the signaling layer due to its superior performance and
memory efficiency compared to pandas or Pandarallel. It offers blazing-fast filtering, native support for datetime and
string operations, and better scalability on modern CPUs. Unlike Pandarallel, which uses multiprocessing over pandas and
increases memory usage linearly, Polars is optimized in Rust and avoids unnecessary duplication, making it ideal for
thread-level operations across thousands of records.

This is where we filter out obvious garbage data using lightweight, deterministic logic. The goal is to eliminate
clearly irrelevant threads while allowing ambiguous or potentially important ones to continue downstream.

Technologies used:

* `re`, `string`, and regex filters for spam, signatures, calendar invites, etc.
* `email` module or custom parser for metadata extraction (subject, sender, timestamp)
* Basic word-count, verb-detection heuristics
* Role mapping dictionary to parse sender roles from headers

Examples of filters:

* Spam or promotional phrases
* System-generated notifications (CI/CD, calendar invites, Jira bot)
* Threads with no subject or with < 2 lines and non-action content
* Emails with subject lines like "Lunch", "FYI", "Reminder"

> Design principle: Better to have a false positive than drop a possible issue too early. "No replies" does not imply "
> not important."

### Signaling layer

Polars continues to be used in this stage for efficient grouping, aggregation, and time delta computations. It allows
for quick analysis of gaps between replies, participant role scoring, and structural signal extraction without
bottlenecks. Its ability to process large batches with minimal overhead ensures that signaling logic remains scalable
even on standard engineering laptops.

This layer identifies data with structural signals that suggest risk, delay, or project friction. Logic is still
rule-based and deterministic, but uses timestamps and role-weight metadata.

Technologies used:

* `datetime`, `pandas`, `numpy` for delay, gap, and thread duration calculations
* Static role-weight config (JSON or YAML) to assign influence scores (e.g., PM > Junior Dev)
* Optional: `networkx` for participant graphs, or `sentence-transformers` to group recurring threads

Signals identified:

* Reply gap > 48h between key roles (e.g., PM → Dev)
* Thread duration > 5 days
* Repeated follow-ups without reply
* Threads initiated by high-weight participants with no response
* Escalations (multiple roles, growing participant set)

### Interpretation layer

This is the only layer allowed to use computationally expensive models. It receives a narrow set of filtered and flagged
threads from the previous layer and performs semantic interpretation.

Goals:

* Detect whether the thread involved an ask or request
* Determine if the issue was resolved
* Identify emerging blockers or risks
* Attribute accountability

Technologies used:

* Local lightweight LLMs (e.g., `flan-t5-small`, `mistral-7B.Q4` via `llama-cpp`) for CPU-safe inference
* Cloud-based LLM APIs (e.g., OpenAI GPT-3.5 Turbo) with JSON-format prompts if external calls are allowed
* Structured output validation via JSON schema or regex
* Optional: `scikit-learn` or `lightGBM` classifiers for resolution/importance detection

Output example:

```json
{
  "subject": "Blocked API deploy",
  "attention_flag": "emerging_risk",
  "responsible": "Kiss Béla (PM)",
  "confidence": 0.91,
  "trigger": "Env mismatch reported with no response",
  "duration_days": 6.5
}
```

> All components are optimized for local execution on standard hardware. The system runs on an average engineering
> laptop with 4–8 cores and 8–16GB RAM. Quantized models via `llama-cpp` and lightweight classifiers ensure responsive
> analysis without requiring cloud APIs or dedicated GPUs.

## Analytical Engine: Problem Framing & Justification

### What We Detect

We detect two types of "Attention Flags":

1. **Unresolved High-Priority Action Items**

    * Triggered by requests or tasks from high-weight roles that are not responded to or closed.
2. **Emerging Risks or Blockers**

    * Triggered by mentions of blockers, dependencies, or unresolved issues with no visible mitigation or ownership.

### Why These Matter

These categories offer the highest signal for leadership attention. They map directly to delivery risks and breakdowns
in ownership or coordination.

## Final Engineered Prompt

```plaintext
You are a business analyst assistant. Given the following email thread, answer the following:

1. Was a specific action, task, or request made?
2. Was that request clearly resolved?
3. Does the thread involve a blocker or risk to the project?
4. Who seems responsible for the issue?
5. When was the last meaningful message?

Return your response in the following JSON format:

{
  "request_made": true/false,
  "resolved": true/false,
  "blocker": true/false,
  "responsible": "Name (Role)",
  "last_message_date": "YYYY-MM-DD",
  "confidence": float between 0 and 1
}

Thread:
---BEGIN EMAIL THREAD---
{thread_text}
---END EMAIL THREAD---
```

Used with: GPT-3.5-turbo, temperature = 0, prompt capped at \~2KB of cleaned text. Or executed locally using
`mistral-7B.Q4` with `llama-cpp`.

---

## Security

* **Confidentiality**: All data encrypted in transit and at rest (TLS, AES-256). Emails may contain sensitive
  information.
* **Prompt injection risk**: Quoted replies are cleaned; outputs are schema-validated.
* **Cloud exposure**: Use OpenAI/Anthropic enterprise APIs with logging disabled, or local inference for sensitive data.
* **Access control**: Role-based access for raw email threads vs. flagged reports. All actions auditable.

Tools:

* `presidio` or regex for redaction
* `llama-cpp-python` for safe local LLM use
* `jsonschema` or custom parser for output validation

---

## Cost Management

* LLM inference is applied only after aggressive filtering.
* 90%+ of threads are filtered before reaching semantic models.
* Prefer local, quantized models (`flan-t5-small`, `mistral-7B.Q4`) unless external API is required.
* Embedding caching avoids duplicate computation.
* Async, batched requests for all remote LLM use.

> The entire system is designed to run locally on an engineering-grade laptop — eliminating recurring cloud inference
> costs and improving security posture.

---

## Monitoring & Trust

### Metrics to Track:

* % of threads flagged per layer
* Confidence score distribution
* Types of flags: unresolved action vs risk vs noise
* Processing time per layer
* LLM failures or malformed outputs
* Accuracy of responsible role detection

### QA Process:

* Human-in-the-loop validation of edge cases
* Traceability from flag → signal → thread text
* Random sample review interface for manual auditing
* Exportable logs for retraining or debugging

### Observability Architecture:

* All major operations log event metadata (timestamp, thread ID, stage, result) to a lightweight SQLite or DuckDB store

* **Each thread is tagged with the layer in which it was filtered out (if applicable), the reason for filtering, and
  basic thread stats** such as:

    * Number of messages
    * Role-weighted importance score
    * Max and avg response delays
    * Duration from first to last message

* Logs are structured (e.g., JSON per thread) and can be aggregated for dashboards or debugging

* Logging done via `loguru` or structured `json` logging, optimized for async pipelines

* Optional in-memory dashboard (e.g. `Textual`, `Rich`, or `Streamlit`) for live insight

* Tracing decorators with timing and success/failure count

* All logging should be non-blocking, using file queues or batch flush to avoid latency on parallel workloads

* All major operations log event metadata (timestamp, thread ID, stage, result) to a lightweight SQLite or DuckDB store

* Logging done via `loguru` or structured `json` logging, optimized for async pipelines

* Optional in-memory dashboard (e.g. `Textual`, `Rich`, or `Streamlit`) for live insight

* Tracing decorators with timing and success/failure count

* All logging should be non-blocking, using file queues or batch flush to avoid latency on parallel workloads

### Metrics to Track:

* % of threads flagged per layer
* Confidence score distribution
* Types of flags: unresolved action vs risk vs noise
* Processing time per layer
* LLM failures or malformed outputs
* Accuracy of responsible role detection

### QA Process:

* Human-in-the-loop validation of edge cases
* Traceability from flag → signal → thread text
* Random sample review interface for manual auditing
* Exportable logs for retraining or debugging

---

## Architectural Risk & Mitigation

### Risk:

LLM misclassification in the interpretation layer — e.g., falsely marking unresolved threads as resolved, or missing
risk cues.

### Mitigation:

* Dual-confirmation: Require both timing signal (e.g., long delay) + semantic confirmation (unresolved ask)
* Confidence thresholding: fallback to rule-based outputs if LLM score < 0.7
* Human override interface for reviewed threads
* Logging and schema enforcement to catch hallucinated names, dates, or flags

> The system is designed to prioritize interpretability, precision, and cost efficiency — while ensuring that critical
> communication risks rise to the top of the Director's view.
