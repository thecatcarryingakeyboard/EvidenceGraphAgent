# Security policy

Report credentials, personal documents or security vulnerabilities privately to the repository maintainer. Do not post secret values in public issues.

The repository contains synthetic documents and catalog rows. `.env.example` contains empty values. Real environment files, model/index caches, database exports and uploaded documents must stay outside Git. Run `python scripts/check_open_source.py --history` before publication; the scanner prints locations and rule names, never matched values. Pattern matching cannot guarantee detection of every possible secret or personal datum.

The local API accepts tenant_id from request input for experiments. It is not an authentication mechanism. Deployments must derive authorization from trusted identity, enforce document ACLs and protect the evidence endpoint. External Neo4j/GraphRAG adapters require separately authorized databases/indexes; they do not automatically add tenant filters.

Cypher keyword checks complement a read-only database account, read transaction and query timeout. They are not a complete Cypher parser. Persistent checkpoints and traces may contain business data and require access control and retention policies. Rotate credentials if they were ever disclosed, even if later deleted from Git.
