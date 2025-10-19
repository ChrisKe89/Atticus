# Enterprise SSO Boundary — Atticus

Atticus operates strictly behind the enterprise SSO and network perimeter. The
application trusts the identity context supplied by the upstream gateway and
never prompts users for credentials. This runbook captures the operational
expectations for the split chat/admin deployment model.

---

## Gateway Responsibilities

The upstream gateway (e.g., Cloudflare Access, Okta, Azure AD App Proxy) must:

- Terminate TLS, enforce device posture, and perform MFA/SSO.
- Append identity headers (`X-Request-Id`, `X-User-Id`, `X-User-Email`) after
  authentication.
- Forward only the required ports to the internal network:
  - `:8000` — API + chat workspace
  - `:9000` — admin workspace
- Strip any inbound cookies or session headers that were not issued by the
  gateway itself.

## Atticus Trust Model

Inside the trusted network Atticus makes the following assumptions:

- Requests already belong to authenticated enterprise users; no login or token
  exchange occurs within Atticus.
- All direct access originates from the gateway or the internal CIDR ranges
  declared in `ALLOWED_PROXY_IPS`.
- Chat and admin workspaces remain isolated at the network layer; cross-port
  calls must include the forwarded identity headers.
- Service-to-service calls propagate the gateway supplied `request_id` so that
  downstream logs and escalations share the same correlation handle.

## Operational Guardrails

- Treat missing identity headers as a deployment misconfiguration and return
  `403` until the gateway is fixed.
- Deny requests that arrive without `X-Forwarded-Proto=https` or originate
  outside the approved CIDR list.
- Monitor the access logs published by the gateway; Atticus only retains
  minimally scoped request metadata (`request_id`, route, latency).
- Document the gateway contact procedure in the support playbook so operations
  teams can escalate perimeter incidents immediately.

## Related Documents

- `docs/OPERATIONS.md` — support playbook and day-to-day procedures.
- `docs/SECURITY.md` — trusted network assumptions and secret policies.
- `docs/TROUBLESHOOTING.md` — diagnostics for misconfigured proxies or ports.
