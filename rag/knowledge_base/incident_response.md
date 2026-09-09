# Ransomware Incident Response Guide (NIST SP 800-61 / SANS)

## 1. Preparation & Detection
- Establish baseline filesystem operations and real-time behavioral alerting.
- Configure write-protected audit logging and isolated communication channels for the security team.
- Regularly validate incident response runbooks and recovery scenarios.

## 2. Identification & Rapid Triage
- Correlate behavioral filesystem alerts with active process telemetry (PID, parent process, command line, open file descriptors).
- Determine the scope of affected files, compromised network shares, and potential lateral movement indicators.
- Classify severity based on business impact, directory criticality, and encryption velocity.

## 3. Emergency Containment Procedures
- **Network Isolation**: Immediately disconnect affected endpoints from both physical Ethernet and wireless networks to prevent lateral spread (`T1021`) and network share encryption.
- **Process Suspension**: Suspend (pause) the offending process tree instead of immediately terminating it. This preserves volatile RAM artifacts and cryptographic keys that may reside in memory.
- **Network Share Disconnection**: Temporarily sever SMB/NFS connections and revoke compromised credential tokens.
- **Preserve Volatile Memory**: Capture a full RAM dump (e.g., via LiME on Linux or WinPmem on Windows) for digital forensics.

## 4. Eradication & Clean-Up
- Identify persistence mechanisms: scheduled tasks, cron jobs, registry run keys, systemd services, and web shells.
- Terminate malicious processes once memory forensics are captured.
- Revoke all privileged accounts and access tokens suspected of being compromised.

## 5. Recovery & Validation
- Restore critical data from offline, immutable, or air-gapped backups (verify backup integrity prior to restoration).
- Re-image or reconstruct affected operating systems from verified golden images.
- Monitor restored systems under heightened behavioral surveillance for re-infection attempts.

## 6. Post-Incident Activity & Lessons Learned
- Compile forensic timeline of events and root cause analysis.
- Share Indicators of Compromise (IoCs) and update detection rules and machine learning baselines.
