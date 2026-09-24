#!/usr/bin/env python3
"""Retrieve complete QA pairs and generate one KQL/SPL rule with the main setting."""

import argparse
import json
import math
import os
import re
import sys
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

from build_qa import complete


USE_QA = (
    "The following items are ranked candidate QA memories. Match each candidate "
    "question and answer against both the visible attack behavior and environment. "
    "Return exactly one rule under the system instruction.\n"
)
PROFILES = {
    "api": {"temperature": 0.0},
    "qwen": {"temperature": 1.0, "top_p": 0.95, "top_k": 20,
             "chat_template_kwargs": {"enable_thinking": False}},
    "ministral": {"temperature": 0.0, "seed": 20260909},
}


def words(text):
    return re.findall(r"[a-z0-9]+", text.casefold())


def load_qa(path, language):
    """Accept build_qa output or the original paper's retrieval-unit JSONL."""
    entries, seen = [], set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("Each QA row must be an object")
            if row.get("target_language", row.get("rule_language")) != language:
                continue
            entry = {"qa_id": row.get("qa_id", row.get("unit_id")),
                     "question": row.get("question", row.get("question_key")),
                     "answer": row.get("answer", row.get("answer_text"))}
            if not all(isinstance(v, str) and v.strip() for v in entry.values()):
                raise ValueError("Each QA needs a nonempty qa_id, question and answer")
            if entry["qa_id"] in seen:
                raise ValueError(f"Duplicate QA ID: {entry['qa_id']}")
            seen.add(entry["qa_id"])
            entries.append(entry)
    if not entries:
        raise ValueError(f"No {language.upper()} QA entries found")
    return entries


def rank_qa(entries, query):
    """Match the main experiment's BM25, including query frequency and tie breaks."""
    postings, lengths = defaultdict(list), []
    for index, row in enumerate(entries):
        terms = words(row["question"].rstrip() + "\n" + row["answer"].lstrip())
        lengths.append(len(terms))
        for term, frequency in Counter(terms).items():
            postings[term].append((index, frequency))
    average = sum(lengths) / len(entries) or 1
    scores = defaultdict(float)
    for term, query_frequency in Counter(words(query)).items():
        matches = postings.get(term, [])
        idf = math.log(1 + (len(entries) - len(matches) + 0.5) / (len(matches) + 0.5))
        for index, frequency in matches:
            norm = 1.2 * (0.25 + 0.75 * lengths[index] / average)
            scores[index] += query_frequency * idf * (frequency * 2.2 / (frequency + norm))
    return [(entries[i], scores[i]) for i in sorted(
        range(len(entries)), key=lambda i: (-scores[i], entries[i]["qa_id"]))]


def task_text(task, *, retrieval=False):
    visible = {"behavior": task["behavior"], "environment": dict(task["environment"])}
    if retrieval:
        # CTI-REALM includes schema in generation, but excludes it from retrieval.
        visible["environment"].pop("kusto_schema", None)
    return (f"TARGET RULE LANGUAGE\n{task['target_language']}\n\nVISIBLE BENCHMARK INPUT\n"
            + json.dumps(visible, ensure_ascii=False, sort_keys=True))


def prepare(task, entries, tokenizer, budget=2048, max_qa=5):
    count = lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids)
    query = task_text(task, retrieval=True)
    selected, payloads = [], []
    bound, separator = count("[") + count("]"), count(", ")
    for row, score in rank_qa(entries, query):
        if len(selected) >= max_qa:
            break
        payload = f"Question: {row['question'].strip()}\nAnswer: {row['answer'].strip()}"
        added = count(json.dumps(payload, ensure_ascii=False)) + (separator if payloads else 0)
        if bound + added <= budget:
            selected.append({"qa_id": row["qa_id"], "bm25_score": score})
            payloads.append(payload)
            bound += added
    if not selected:
        raise ValueError(f"No complete QA fits the {budget}-token knowledge budget")
    rendered = json.dumps(payloads, ensure_ascii=False)
    exact = count(rendered)
    if exact > bound or exact > budget:
        raise ValueError("Token accounting invariant failed with this tokenizer")
    user = task_text(task) + "\n\nKNOWLEDGE CONTEXT\n" + USE_QA + rendered
    return user, {"query": query, "selected": selected, "knowledge_tokens": exact,
                  "packing_token_bound": bound, "knowledge_budget": budget, "max_qa": max_qa}


def extract_rule(text):
    """Keep the first fenced block, or plain text, without editing the query."""
    lines = text.strip().splitlines()
    markers = [i for i, line in enumerate(lines) if re.fullmatch(r"[ \t]*```[^`]*[ \t]*", line)]
    if markers:
        lines = lines[markers[0] + 1:markers[1] if len(markers) > 1 else len(lines)]
    return "\n".join(lines).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSON with target_language, behavior, environment")
    parser.add_argument("--qa", type=Path, required=True, help="QA JSONL from build_qa.py or the frozen corpus")
    parser.add_argument("--tokenizer", type=Path, required=True, help="tokenizer.json used to measure the knowledge budget")
    parser.add_argument("--output", type=Path, default=Path("outputs/rule.txt"))
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL"))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    parser.add_argument("--profile", choices=PROFILES, default="api", help="Generation parameters; qwen/ministral match paper runs")
    parser.add_argument("--knowledge-budget", type=int, default=2048)
    parser.add_argument("--max-qa", type=int, default=5)
    parser.add_argument("--max-output-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--api-options", type=json.loads, default={})
    parser.add_argument("--dry-run", action="store_true", help="Show retrieval and API messages without a model call")
    args = parser.parse_args()
    try:
        from tokenizers import Tokenizer
    except ImportError:
        raise RuntimeError("Install the tokenizer dependency: python3 -m pip install -r requirements.txt") from None
    task = json.loads(args.input.read_text(encoding="utf-8"))
    if isinstance(task, dict) and "visible_input" in task:
        if not isinstance(task["visible_input"], dict):
            raise ValueError("visible_input must be an object")
        task = {**task["visible_input"], "target_language": task.get("target_language")}
    if (not isinstance(task, dict) or task.get("target_language") not in ("kql", "spl")
            or not isinstance(task.get("behavior"), str) or not task["behavior"].strip()
            or not isinstance(task.get("environment"), dict)):
        raise ValueError("Input needs target_language (kql/spl), behavior text and an environment object")
    if min(args.knowledge_budget, args.max_qa, args.max_output_tokens, args.timeout) <= 0:
        raise ValueError("Budgets, max-qa and timeout must be positive")
    url = urllib.parse.urlsplit(args.base_url)
    if (url.scheme not in ("http", "https") or not url.netloc or url.username or url.password
            or url.query or url.fragment):
        raise ValueError("Use an HTTP(S) base URL without credentials, query or fragment")
    if not isinstance(args.api_options, dict) or {"model", "messages", "tools", "tool_choice", "stream", "n"} & args.api_options.keys():
        raise ValueError("api-options cannot override model, messages, tools, tool_choice, stream or n")
    args.api_options = {**PROFILES[args.profile], **args.api_options}
    if not {"max_tokens", "max_completion_tokens"} & args.api_options.keys():
        args.api_options["max_tokens"] = args.max_output_tokens
    if {"max_tokens", "max_completion_tokens"} <= args.api_options.keys():
        raise ValueError("Use only one of max_tokens and max_completion_tokens")
    entries = load_qa(args.qa, task["target_language"])
    tokenizer = Tokenizer.from_file(str(args.tokenizer))
    user, retrieval = prepare(task, entries, tokenizer, args.knowledge_budget, args.max_qa)
    system = (Path(__file__).resolve().parent / "prompts/generate_rule.md").read_text(encoding="utf-8").strip()
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    trace = {"model": args.model, "profile": args.profile, "api_options": args.api_options,
             "tokenizer": str(args.tokenizer), "retrieval": retrieval, "messages": messages}
    if args.dry_run:
        print(json.dumps(trace, ensure_ascii=False, indent=2))
        return
    if not args.model:
        raise ValueError("Set --model or OPENAI_MODEL")
    trace_path = args.output.with_suffix(args.output.suffix + ".trace.json")
    if args.output.exists() or trace_path.exists():
        raise ValueError("Output or trace already exists. Choose a new --output path")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("x", encoding="utf-8") as handle:
        json.dump(trace, handle, ensure_ascii=False, indent=2)
    response = complete(args, messages, tools=None)
    trace["response"] = response
    trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not isinstance(response["choices"], list) or not isinstance(response["choices"][0], dict):
        raise ValueError("Malformed API choices. See the trace")
    choice = response["choices"][0]
    message = choice.get("message", {})
    if not isinstance(message, dict):
        raise ValueError("Malformed API message. See the trace")
    if choice.get("finish_reason") != "stop" or message.get("refusal") or message.get("tool_calls"):
        raise RuntimeError("Generation did not finish normally. Raw response retained in the trace")
    if not isinstance(message.get("content"), str) or not message["content"].strip():
        raise RuntimeError("The API returned an empty rule. See the trace")
    rule = extract_rule(message["content"])
    if not rule:
        raise RuntimeError("No rule text found. See the trace")
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(rule + "\n")
    print(f"Wrote {args.output}; retrieved {len(retrieval['selected'])} QA, "
          f"{retrieval['knowledge_tokens']} knowledge tokens. Trace: {trace_path}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, RuntimeError) as exc:
        sys.exit(f"Error: {exc}")
