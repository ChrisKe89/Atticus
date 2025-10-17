# REMOTE ACCESS - Atticus

This guide explains how to reach a local Atticus instance from another PC without exposing the machine to
the internet. It presents three supported approaches so you can choose the level of automation, security,
and tooling that fits your environment.

---

## Quick Decision Matrix

<!-- markdownlint-disable-next-line MD013 -->

| Option | Best For | Security Posture | What You Need |

<!-- markdownlint-disable-next-line MD013 -->

| ---------------------- | ------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------- |

<!-- markdownlint-disable-next-line MD013 -->

| **Tailscale** | Always-on secure mesh between office/home devices | Zero-trust, device-based auth, automatic key rotation | Personal/enterprise Tailscale account (free tier works) |

<!-- markdownlint-disable-next-line MD013 -->

| **Cloudflare Tunnel** | Sharing access with vendors or short-term demos | One-time tokens, granular routes, no inbound firewall rules | Cloudflare account with a free zone + `cloudflared` binary |

<!-- markdownlint-disable-next-line MD013 -->

| **SSH Reverse Tunnel** | One-off troubleshooting from a trusted jump host | Depends on SSH key hygiene | Any VPS or machine reachable from the remote PC |

---

## Option 1 - Tailscale (Recommended)

1. Install Tailscale on the Atticus host and the remote PC: <https://tailscale.com/download>.
2. Authenticate each device with the same account (or organization SSO).
3. Tag the Atticus host (optional but recommended) with `atticus-server` to simplify ACLs.
4. Start Atticus locally:

   ```bash
   make api
   ```

5. Connect from the remote PC using the Tailscale IP shown in the admin console:

   ```bash
   # Example assuming the host advertises 100.101.102.103
   curl http://100.101.102.103:8000/health
   ```

6. Lock down access with an ACL snippet:

   ```json
   {
     "ACLs": [
       {
         "Action": "accept",
         "Users": ["group:sales", "user:you@example.com"],
         "Ports": ["tag:atticus-server:8000"]
       }
     ]
   }
   ```

**Pros**: 2-minute setup, device-level revocation, auto-generated DNS names like
`atticus-hostname.tailnet.ts.net`.

**Cons**: Requires installing the client on every participating machine.

---

## Option 2 - Cloudflare Tunnel

1. Install `cloudflared` on the Atticus host:

   ```powershell
   winget install Cloudflare.cloudflared
   ```

2. Authenticate and select the zone that will front your tunnel (e.g. `yourcompany.com`):

   ```bash
   cloudflared login
   ```

3. Create a dedicated tunnel:

   ```bash
   cloudflared tunnel create atticus-local
   ```

4. Route a DNS record to the tunnel:

   ```bash
   cloudflared tunnel route dns atticus-local atticus.yourcompany.com
   ```

5. Run the connector while Atticus is active:

   ```bash
   make api &
   cloudflared tunnel run --url http://localhost:8000 atticus-local
   ```

6. Protect access with Cloudflare Access (SSO, one-time PINs, or service tokens).

**Pros**: No inbound firewall rules, audited access logs, granular policies per path.

**Cons**: Outbound tunnel must stay alive; run it as a service for long-lived usage.

---

## Option 3 - SSH Reverse Tunnel (Minimal Dependencies)

1. Pick a jump host reachable from the remote PC (a lightweight VPS works).
2. Create an SSH key for the Atticus host and add it to the jump host `authorized_keys`.
3. Start the tunnel from the Atticus host:

   ```bash
   ssh -N -R 18080:localhost:8000 user@jump-host.example.com
   ```

4. From the remote PC, connect to the jump host and forward traffic locally:

   ```bash
   ssh -L 8000:localhost:18080 user@jump-host.example.com
   ```

5. Visit `http://localhost:8000` on the remote PC—traffic traverses the secure SSH tunnel.

**Pros**: Uses built-in tooling; no extra accounts required.

**Cons**: You must maintain the intermediate host and manage SSH keys carefully.

---

## Operational Checklist

- Treat every remote-access path as production: use MFA, rotate credentials, and log access.
- Update `.env` with `ALLOWED_ORIGINS` if you front Atticus with a different hostname (CORS).
- Enable `LOG_VERBOSE=1` during rollout so access logs capture remote IPs.
- Tear down tunnels when demos finish to avoid orphaned exposure.

---

## Related Documents

- [OPERATIONS.md](OPERATIONS.md) - runbooks, evaluation workflow, and rollback steps.
- [SECURITY.md](SECURITY.md) - IAM, SES policies, and secrets guidance.
- [README.md](README.md) - setup instructions and Make targets.
