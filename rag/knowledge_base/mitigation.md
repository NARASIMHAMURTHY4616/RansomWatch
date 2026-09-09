# Defensive Ransomware Mitigation and Hardening

## Defense-in-Depth Architecture
A resilient defensive posture assumes breach and establishes multiple complementary containment layers so that a single failure does not lead to enterprise-wide data loss.

## 1. Immutable and Isolated Backups
- **3-2-1-1-0 Rule**:
  - Maintain 3 copies of important data.
  - Store copies on 2 different media types.
  - Keep 1 copy in an offsite location.
  - Ensure 1 copy is completely offline, immutable (WORM - Write Once Read Many), or air-gapped.
  - Verify 0 errors during regular automated restore drills.
- Restrict backup management access with separate, dedicated authentication domains and hardware MFA.

## 2. Principle of Least Privilege (PoLP)
- Restrict write permissions on shared network drives to only the folders individual users specifically need.
- Enforce strict user privilege separation: standard users must never have local administrator privileges on production endpoints.
- Apply Linux capabilities or Windows AppLocker / Software Restriction Policies to prevent executable launches from writable temp paths (`/tmp`, `AppData`).

## 3. Network Micro-Segmentation
- Segment IT and OT networks, workstation subnets, and sensitive data clusters using firewalls and access control lists (ACLs).
- Disable or restrict SMBv1/v2 and inbound remote desktop (RDP) connections from external and untrusted networks.
- Enforce Zero Trust Network Access (ZTNA) with continuous device health verification.

## 4. Endpoint Behavioral Protections
- Deploy behavioral monitoring agents (like RansomWatch) to detect high-velocity file transformations before entire volumes are impacted.
- Protect Volume Shadow Copies and system restore points with immutable access controls.
- Implement canary decoy directories that trigger automated host network isolation upon unauthorized write access.
