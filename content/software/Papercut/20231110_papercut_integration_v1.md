# Papercut MF Integration Checklist

- Install Papercut MF version 23.0 or later on Windows Server 2019.
- Configure the Atticus AC7070 device using the embedded Papercut application package `AC7070_PAPERCUT_4.2`.
- Enable secure print release with card authentication; map badge IDs to Azure AD users.
- Set default cost center rules and synchronize nightly using the Papercut API job `syncCostCenters`.
- For site resilience, enable the secondary Application Server and configure automatic failover.
- Validate end-to-end by printing the "Papercut Sample Job" and releasing from the device panel.
