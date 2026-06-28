# Security Policy

## Supported scope

Security reports are welcome for:
- auth-state handling
- secret exposure in logs/artifacts
- approval bypasses
- API auth issues
- isolation boundary failures
- takeover URL exposure
- unsafe file handling

## Out of scope

The following are not considered valid security goals for this project:
- anti-bot bypass
- CAPTCHA solving
- stealth / undetectable automation
- deceptive fingerprinting

## Reporting

Report security issues privately via GitHub's private vulnerability reporting:

**[Open a private security advisory](https://github.com/LvcidPsyche/auto-browser/security/advisories/new)**

Do not open a public issue for security problems. If you cannot use GitHub
advisories, open a regular issue saying only "security report — need a private
channel" with no details, and the maintainer will follow up.

Include:
- impact
- affected version/commit
- repro steps
- logs, screenshots, or PoC if available

## Handling goals

The project aims to:
- acknowledge reports quickly
- confirm severity and scope
- ship the smallest safe fix
- document user-facing mitigation steps when needed
