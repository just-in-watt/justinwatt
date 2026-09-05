# JustInWatt

**Use energy at the right time.**

JustInWatt is a local-first, privacy-conscious project for understanding and
coordinating household energy. It is being built to observe energy flows,
explain decisions and progressively help flexible devices use electricity when
it makes the most sense.

> **Project status:** pre-1.0 and under active development. The first sanitized
> public source snapshot is still being prepared. JustInWatt is not currently a
> turnkey home-automation product or a safety-certified controller.

## Design principles

- **Local first:** household observations and decisions should remain on the
  user's own system whenever possible.
- **Explain before acting:** every recommendation or action needs an explicit
  reason and a visible confidence level.
- **Fail closed:** stale, missing or ambiguous data must never silently increase
  an equipment's level of autonomy.
- **Capabilities over brands:** the energy model depends on what equipment can
  safely do, not on vendor-specific assumptions.
- **Respect existing controls:** JustInWatt coordinates devices without
  bypassing manufacturer protections or duplicating their internal regulation.
- **Progressive consent:** observing, recommending, supervised control and
  autonomous control are separate permission levels.

## Intended architecture

```text
observe → understand → decide → explain → act
```

Equipment integrations translate vendor protocols into explicit capability
contracts. The decision layer works from qualified observations and user
intentions. Physical execution remains a separate boundary with its own
authorization, freshness and rollback requirements.

The private development repository also contains deployment evidence and
household-specific qualification records. Those records are deliberately kept
out of the future public snapshot. The public history will start from a new,
reviewed source tree rather than exposing the private Git history.

## What to expect from the first public snapshot

The planned first snapshot will focus on:

- the capability and observation contracts;
- deterministic decision logic and offline simulators;
- fictitious or anonymized scenarios and tests;
- the safety, contribution and architecture documentation needed to review the
  code responsibly.

Real deployment configuration, credentials, household logs, device identifiers
and private qualification evidence will not be included. Hardware integrations
will only enter the public scope after their examples and failure modes have
been reviewed independently.

The current candidate contains one deliberately small runnable slice: a
standard-library-only battery recommendation simulation. From a future public
snapshot root, it can be exercised with Python 3.9 or newer:

```bash
python3 -m modules.simulateur_batterie
python3 -m unittest \
  tests.test_modele_energie \
  tests.test_decision_batterie \
  tests.test_simulateur_batterie
python3 -m modules.audit_publication
python3 -m modules.audit_securite
```

This demonstration never connects to a battery and never sends a command. The
broader source selection still needs to be qualified and reproduced from a
clean snapshot, so this README does not yet describe a released package.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md), the
[Code of Conduct](CODE_OF_CONDUCT.md) and the
[Security Policy](SECURITY.md) before proposing a change.

Contributions must use fictitious data and simulated transports. Access to the
source code never grants access to a real installation, and a pull request must
not trigger a deployment or physical command.

The project's durable principles are recorded in the
[Constitution](docs/CONSTITUTION.md) and its values in the
[Manifesto](docs/MANIFESTO.md). Most detailed documentation is currently in
French; progressive English documentation is part of the public preparation.

## License

Original JustInWatt code and documentation selected for publication are
prepared under the [Apache License 2.0](LICENSE). Third-party components retain
their own licenses and attribution requirements.

The JustInWatt name and visual identity are not granted as product branding by
the source-code license. See the [trademark policy](TRADEMARKS.md); legal name
availability remains a separate publication gate.
