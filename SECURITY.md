# Security policy

OpsBoard is a teaching project. Report security vulnerabilities privately to the repository owner using GitHub's **Report a vulnerability** option when enabled. If unavailable, contact the maintainer through a private, mutually agreed channel; do not publish credentials or exploit data in a public issue.

## Minimum security posture

- Never commit tokens, passwords, Kubernetes Secrets with actual sensitive values, or private TLS keys.
- Use fictitious values for TP 7 and TP 8.
- Build unprivileged images and avoid hostPath, privileged containers and mounting Docker sockets.
- Review CVEs reported by Trivy. CI blocks fixable HIGH/CRITICAL vulnerabilities.
- Do not treat Base64 encoding as encryption; encrypt Kubernetes Secrets at rest where appropriate.
- GitHub Actions publish images only after the test and security jobs succeed.
- Use image digests and verify signatures in environments that enforce supply-chain policy.

## Intentional vulnerabilities and faults

Laboratory scenarios can deliberately return HTTP 503 from health endpoints. This is **teaching behavior**, not authorization to introduce real insecure defaults, bind sensitive data to public endpoints, or skip CI checks.
