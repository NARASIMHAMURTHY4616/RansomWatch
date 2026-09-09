# MITRE ATT&CK Mapping for Ransomware Behaviors

## Overview
The MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge) framework provides a standardized taxonomy of cyber adversary actions. Ransomware operations map across several core tactics: Impact, Inhibit System Recovery, Defense Evasion, and Execution.

## Key Techniques & Sub-Techniques

### T1486: Data Encrypted for Impact
- **Description**: Adversaries encrypt data on target systems to interrupt availability to system and network resources. They often leave a ransom note directing victims to contact them for decryption keys.
- **Observed Behavioral Indicators**: Rapid burst of file write and modification events, extensive file renaming appending ransom-specific extensions (`.locked`, `.crypto`, `.rwenc`), accompanied by informational note drops.
- **Mitigation**: Automated behavioral file integrity monitoring, canary tokens, and immediate process quarantine upon detection.

### T1485: Data Destruction
- **Description**: Adversaries destroy data and files to disrupt availability. Often used in wiper malware disguised as ransomware (pseudoransomware).
- **Observed Behavioral Indicators**: Extreme file deletion rates, bulk truncation, or overwriting file contents with random zero-byte streams.

### T1490: Inhibit System Recovery
- **Description**: Adversaries delete or corrupt system recovery mechanisms, such as Volume Shadow Copies, Windows Backup catalogs, or Linux snapshot partitions, to force reliance on decryption keys.
- **Commands Observed**: `vssadmin.exe delete shadows /all /quiet`, `wbadmin delete catalog -quiet`, `bcdedit /set {default} recoveryenabled No`.

### T1083: File and Directory Discovery
- **Description**: Adversaries enumerate local file systems and network shared drives to locate target directories containing sensitive documents, source code, and financial data.
- **Observed Behavioral Indicators**: High directory traversal rates across multiple disparate directories within brief time windows.

### T1021: Remote Services (Lateral Movement)
- **Description**: Adversaries move laterally through network environments using valid credentials across protocols like SMB, SSH, or RDP to distribute ransomware across multiple hosts.

### T1562.001: Impair Defenses - Disable or Modify Tools
- **Description**: Disabling security software, endpoint detection agents, and local logging facilities to prolong dwell time before encryption.
