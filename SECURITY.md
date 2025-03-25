# Security Policy

## Reporting a Vulnerability

We appreciate and encourage responsible vulnerability disclosure from our users and the security research community. To ensure vulnerabilities are handled securely and efficiently, we request that all vulnerabilities be reported through GitHub's secure vulnerability reporting feature.

![Report Vulnerability Button](https://raw.githubusercontent.com/OmenApps/OmenApps/refs/heads/main/media/security_reporting.png)

### How to Report a Vulnerability

1. Visit the **Security** tab on the GitHub repository.
2. Click **Report a vulnerability**.
3. Provide detailed information including:
   - A clear description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Any recommendations for mitigation

### Handling Your Report

Once your vulnerability report is submitted, we will:

- Acknowledge receipt within **2 business days**.
- Investigate and validate the reported vulnerability.
- Provide regular updates approximately every **7 business days** until resolution.

### Vulnerability Acceptance

- If the vulnerability is **accepted**, we will:
  - Coordinate privately to develop and test a fix.
  - Aim to resolve critical vulnerabilities within **14 days** and lower severity issues within **30 days**.
  - Publicly disclose the vulnerability after a fix is available, providing credit to the reporter (unless anonymity is requested).

- If the vulnerability is **declined**, we will:
  - Clearly explain our reasoning.
  - Suggest alternative actions if applicable.

### PyPI Package Management

We follow best practices for managing packages published on PyPI, including the "yanking" of vulnerable package versions. Yanked versions remain available for users to download, but are hidden from new installations by default, preventing further propagation of vulnerabilities.

Thank you for helping us keep our packages secure!
