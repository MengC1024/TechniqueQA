# TechniqueQA

Code for **TechniqueQA: Technique-Guided Knowledge Construction
for Detection Rule Generation**.

TechniqueQA builds reusable QA pairs from technical documents, guided by MITRE
ATT&CK Techniques and Procedures. It then retrieves relevant QA pairs to help
generate KQL and SPL detection rules.

## Setup

Use Python 3.10 or later and an OpenAI-compatible API that supports tool calling.
Run the commands below from the repository root.

```bash
python3 -m pip install -r requirements.txt
```

Create a `.env` file using [`.env.example`](.env.example) as a template, and
fill in your API key, base URL, and model name. Then load the settings into
your shell:

```bash
set -a
. ./.env
set +a
```

Use the API base URL without the `/chat/completions` suffix. You can choose a
different model for either script with `--model`.

## Build QA

`build_qa.py` takes a Technique, its Procedures, and a document corpus. The agent
searches and reads the documents, then saves the QA pairs and their source
references. Each run handles one Technique and target language.

Prepare two input files:

- Technique JSON with `technique_id`, `technique_name`, `technique_description`,
  `target_language` (`kql` or `spl`), and a `procedures` list. Each procedure
  contains a `procedure_description` string.
- Document JSONL with `id`, `title`, `url`, and `text` in each record.

```bash
python3 build_qa.py \
  --technique /path/to/technique.json \
  --documents /path/to/documents.jsonl \
  --output outputs/qa.jsonl
```

## Generate a rule

`generate_rule.py` takes an attack description and environment, retrieves QA
pairs with BM25, and generates a rule. The input JSON contains `target_language`
(`kql` or `spl`), `behavior` (text), and `environment` (an object describing the
platform, telemetry, and available fields). Set `--tokenizer` to a local
`tokenizer.json` file to count the tokens in the retrieved context.

```bash
python3 generate_rule.py \
  --input /path/to/input.json \
  --qa outputs/qa.jsonl \
  --tokenizer /path/to/tokenizer.json \
  --output outputs/rule.kql \
  --max-output-tokens 8192
```

Both scripts support `--help` and `--dry-run`. Each run saves a trace alongside
its output. Choose a new `--output` path when rerunning.

## Prompts

- [`prompts/kql.md`](prompts/kql.md) and [`prompts/spl.md`](prompts/spl.md) guide QA construction for each language.
- [`prompts/generate_rule.md`](prompts/generate_rule.md) guides rule generation.
