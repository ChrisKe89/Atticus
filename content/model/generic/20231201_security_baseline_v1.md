# Multifunction Device Security Baseline

1. **User Authentication**
   - Enforce Azure AD single sign-on with conditional access policies.
   - Require PIN fallback for offline scenarios and log all overrides.
2. **Data Protection**
   - Enable automatic disk encryption using FIPS 140-2 certified modules.
   - Schedule nightly disk overwrite for temporary queues and scans.
3. **Network Controls**
   - Restrict management interfaces to HTTPS with TLS 1.2 or later.
   - Configure syslog streaming to the centralized SIEM with JSON formatting.
4. **Compliance**
   - Document firmware provenance and maintain signed packages in OneDrive storage.
   - Review access logs weekly; escalate if confidence in event classification drops below 70%.
5. **Incident Response**
   - Hotline escalations must occur after three unsuccessful remote remediation steps.
