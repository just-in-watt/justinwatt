# Contributing to JustInWatt

Thank you for helping improve JustInWatt. The project coordinates real energy
equipment, so a seemingly small change can affect privacy, safety or device
lifespan.

## Before you start

1. Read this guide, `docs/CONSTITUTION.md` and the public architecture or
   decision documents relevant to the area you plan to change.
2. Open a feature request before implementing a new capability, hardware
   integration or durable architectural decision.
3. Work from the public `main` branch in a dedicated branch or fork and keep the
   pull request focused.
4. Record an accepted decision in the relevant documentation before its code.

The first public scope is intentionally small. Offline contracts, deterministic
logic, simulations, tests and generic documentation are welcome. A hardware
transport, physical executor, deployment recipe or household-specific proof
needs a separate scope and security review before implementation.

## Never include real household data

Do not submit secrets, tokens, cookies, credentials, coordinates, home
addresses, real private-network addresses, MAC addresses, serial numbers,
tailnet names, personal file paths, personal screenshots or raw household logs.
Use RFC 5737 documentation networks, locally administered example MAC addresses
and explicitly fictitious data in examples and tests.

The maintainer explicitly authorized the published moderation contact on
2026-09-21. The publication audit permits only that exact email in the root
SECURITY.md and CODE_OF_CONDUCT.md files; it does not allow other addresses,
other paths or secrets on the same line. This exception does not apply to
household data. Changing the contact requires renewed consent and review.

Do not disclose a vulnerability in an issue or pull request. Follow
`SECURITY.md`; the public contribution cycle will remain closed until a private
reporting channel has been enabled and verified.

## Safety boundary

A pull request must not contact a real installation, trigger a physical command,
bypass a manufacturer protection or raise an autonomy level. Tests use fakes,
simulators or reviewed sanitized traces. Hardware qualification remains a
private, supervised and separate procedure.

Preserve the project boundaries:

- `observe → understand → decide → explain → act`;
- capability contracts instead of brand-specific decisions in the core;
- fail closed when data is missing, stale or ambiguous;
- keep observation, decision, execution and independent confirmation separate;
- never turn a successful simulation or CI run into permission to control a
  device.

## Development and validation

Add tests proportional to the risk and run the relevant checks locally. The
standard offline checks are:

```bash
python3 -m modules.audit_publication
python3 -m modules.audit_securite
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Update documentation, functional coverage and release notes when their contract
changes. Declare the origin and licence of every dependency or asset. If a test
cannot reproduce an observed failure, explain the closest sanitized proof and
the remaining gap in the pull request.

## Pull request expectations

Complete the pull request template. It asks for the problem and decision, scope,
risks, privacy impact, rollback, modified files and tests actually run. A green
CI does not replace human review. Maintainers may request additional evidence or
decline any change that implicitly expands permissions, public scope or claimed
compatibility.

The public repository and the private operational repository have separate
histories. Maintainers import accepted public commits into a clean private
worktree and rerun the private suite; no pull request is automatically deployed
to a home, host or device.

By submitting a contribution for inclusion, you agree that it is provided under
the project's Apache-2.0 licence unless a different written agreement is made
before submission.
