# DRA + Kueue KWOK-only raw data

Each timestamped child directory is produced by
`scripts/dra-kueue-kwok/poc.sh`. A publishable #285 dataset contains functional
and scale profile directories with three complete rounds each, plus generated
JSON summaries and Markdown reports.

Raw JSONL is append-only while a round is running. Reusing an existing round
directory is rejected to prevent accidental mixing of measurements.

The data measures KWOK control-plane behavior only, not real GPU performance.

The accepted dataset is [`20260813T063105Z`](./20260813T063105Z/). It contains
three functional and three scale rounds plus per-profile and combined summaries
and reports. Both profile verifications and the combined verification passed.
