# QBR Analysis System: Blueprint

## Executive Summary

This system processes raw project email threads to extract high-signal risks and unresolved items for a Director of
Engineering preparing for a Quarterly Business Review (QBR). It uses a 5-layer architecture—**Data Loading**, **Parsing
**, **Filtering**, **Signaling**, and **Interpretation**—optimized for local execution on standard engineering hardware,
with optional cloud-based LLM inference. The goal is to deliver a concise, trustworthy Portfolio Health Report that
flags project blockers and unresolved action items.

---

## 1. Architectural Choices

### 1.1 Data Ingestion Pipeline

Data is ingested through a **5-stage pipeline**:

```text
[Raw Emails] 
   ↓
[Data Loading Layer]
   ↓
[Parsing Layer]
   ↓
[Filtering Layer] → [Dropped Threads]
   ↓
[Signaling Layer]
   ↓
[Interpretation Layer (LLM)]
   ↓
[Attention Flags for QBR Report]
```

### 1.2 Data Loading Layer

Handles raw file loading, email threading, and metadata extraction.

* **Responsibilities**:

    * Load raw `.txt` files from project folders
    * Split messages into threads based on subject lines & metadata
    * Normalize encodings, clean up control characters, identify participants

* **Technologies**:

    * Python standard libraries (`os`, `email`, `pathlib`)
    * Optional libraries: `mailparser`, `email_reply_parser`

> This layer is isolated from LLMs and ensures deterministic, safe ingestion.

### 1.3 Parsing Layer

Transforms semi-clean threads into structured representations using a local LLM and schema enforcement.

* **Technologies**: `LangChain`, `llama-cpp-python`, `PydanticOutputParser`, `jsonschema`
* **Example outputs**: structured threads with sender, role, timestamp, cleaned message body
* **Security**: prompt uses strict delimiters to isolate untrusted input

### 1.4 Filtering Layer

Lightweight logic to aggressively eliminate clearly irrelevant threads.

* **Technologies**: Python `re`, dictionaries of known spam/notification formats
* **Heuristics**:

    * Spam phrases
    * CI/CD and calendar bot detections
    * Threads under 2 lines without verbs/actions

### 1.5 Signaling Layer

Detects interaction patterns suggestive of risk or breakdown in communication.

* **Technologies**: `polars`, `datetime`, YAML config with role weights
* **Signals**:

    * Gaps > 48h between key roles (PM → Dev)
    * Long durations without resolution
    * Growing participant sets suggesting escalation

### 1.6 Interpretation Layer

Filtered threads undergo semantic LLM analysis to generate final structured outputs for reporting.

* **LLMs**: `flan-t5-small`, `mistral-7B.Q4`, served locally via `llama-cpp`
* **Output format**: fixed JSON schema containing action/request detection, blocker detection, accountability
* **System**: Local-first, CPU-friendly, fallback-capable with AzureOpenAI

---

## 2. Analytical Engine: Problem Framing & Justification

### 2.1 Attention Flags

1. **Unresolved High-Priority Action Items**: missed responses to important asks
2. **Emerging Risks or Blockers**: escalation or roadblocks without mitigation

### 2.2 Prompt Template

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

---

## 3. Security Considerations

* All sensitive operations are local-first by design
* If AzureOpenAI is used:

    * Prefer **Managed Identity**
    * Otherwise, inject keys via **env vars** or **Azure Key Vault**
* Always define the required output with Pydantic models and validate LLM responses through LangChain. Retry 3 times and
  fail only after that

Technologies:

* `ollama`, `LangChain`, `pydantic`, `dotenv`
* Use delimiters to defend against prompt injection

---

## 4. Cost Management

* Due to well scoped tasks, smaller, cheaper models can be used without significant costs
* All LLMs quantized and local by default
* Each step persist its data so if a step fails, the new run will use the persisted data (CLI must allow the overriding
  of this feature)

---

## 5. Monitoring & Trust

| Component       | Metric                        |
|-----------------|-------------------------------|
| Filtering Layer | % threads dropped             |
| LLM Output      | Confidence score distribution |
| LLM Errors      | Invalid/malformed JSONs       |
| Timing          | Processing time per batch     |
| Auditability    | Thread ID trace per flag      |

* Manual review dashboard
* Exportable JSONL logs
* LLM tracebacks logged for retraining/debugging
* Output data always contains enough data to trace back signal sources and decisions data using SourceTrace data

---

## 6. Architectural Risk & Mitigation

**Risk**: LLM hallucination or false negatives on unresolved threads

**Mitigations**:

* Require both signal + LLM match to elevate a thread
* Confidence threshold fallback to rule-based methods
* Use strict schema + output parser to block malformed JSON
