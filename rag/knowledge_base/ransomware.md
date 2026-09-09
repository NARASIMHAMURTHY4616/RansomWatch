# Ransomware Mechanics, Indicators, and Early Detection Concepts

## Overview
Ransomware is malicious software designed to deny access to a computer system or data by encrypting files until a ransom is paid. Modern ransomware operations often operate on a Ransomware-as-a-Service (RaaS) model and employ double or triple extortion tactics (combining encryption with exfiltration and DDoS threats).

## Core Operational Phases
1. **Initial Access & Reconnaissance**: Attackers gain entry through phishing, exploited vulnerabilities (e.g., edge VPNs), or brute-forced remote desktop protocol (RDP).
2. **Privilege Escalation & Defense Impairment**: Disabling security services, tampering with event logs, and acquiring administrative tokens.
3. **Internal Discovery**: Enumerating local storage drives, network shares, and accessible databases (`T1083`).
4. **Volume Shadow Copy Tampering**: Executing commands such as `vssadmin delete shadows /all /quiet` or `wmic shadowcopy delete` to inhibit system recovery (`T1490`).
5. **Rapid High-Throughput Encryption & Renaming**:
   - Traversal of high-value user directories (Documents, Desktop, Finance, Backups).
   - Reading files into memory, applying hybrid symmetric/asymmetric encryption (e.g., AES-256 or ChaCha20 for file payload, encrypted with attacker's public RSA/ECC key).
   - Writing back the encrypted stream and renaming the file with an appended extension (e.g., `.locked`, `.crypto`).
6. **Ransom Note Generation**: Dropping informational text/HTML files (e.g., `README_RESTORE.txt`) into touched directories.

## Early Behavioral Detection Indicators
- **Unusual Burst of File Renames**: A rapid surge in file renaming events within short sliding windows (5-10 seconds) strongly indicates extension transformation.
- **High File Modification Velocity**: Legitimate user interactions rarely modify more than a few files per second; ransomware frequently reaches dozens of modifications per second.
- **Cross-Directory Traversal**: Synchronous access and alteration spanning multiple unrelated subfolders simultaneously.
- **Canary File Alterations**: Placing hidden decoy files in common directories; any modification to these canary assets triggers instant containment alarms.
- **Process Entropy**: File modification streams exhibiting high Shannon entropy (close to 8.0 bits/byte), characteristic of encrypted data.
