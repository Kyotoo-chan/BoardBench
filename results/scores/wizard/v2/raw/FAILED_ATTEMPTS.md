# Unscored pre-evaluation attempts

`failed_attempts.tar.gz` compactly retains the raw bytes of failed generation and runner attempts required for the audit trail. These attempts were never evaluated, are not conditions in `iteration_manifest.json`, and do not contribute to any score.

The small JSON/agentic files kept outside the bundle are referenced by the successful run evidence. The scored conditions are only `original` and `clarified`.
