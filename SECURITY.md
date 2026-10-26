# Security policy

Please do not open a public issue containing credentials, customer documents,
personal data or exploit details. Send a private report to the repository
maintainer, including a minimal reproduction and affected version.

Before publishing a deployment:

- rotate any credentials that have ever appeared in the original AssistGen
  working tree;
- derive `tenant_id` from authenticated identity instead of request JSON;
- enforce document ACLs before retrieval and redact PII from traces;
- keep high-risk tools behind an approval queue;
- run `python scripts/check_open_source.py` and the evaluation suite in CI.
