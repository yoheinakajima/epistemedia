# Run Receipts

Accepted run receipts are append-only records of what an agent or service actually executed. A receipt includes task, run, actor and lineage, accepted base and candidate commits, commands or tool actions, environment and dependency versions, input and output digests, start/end UTC times, exit status, tests, observed results, artifacts, limitations, and external provider identities where relevant.

A receipt is evidence of execution, not evidence that represented claims are true. Never edit a merged receipt; append a correction or superseding receipt.
