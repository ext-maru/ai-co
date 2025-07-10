# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability within Elders Guild CodeFlow, please follow these steps:

1. **Do NOT** create a public GitHub issue for the vulnerability
2. Email your findings to security@aicompany.dev
3. Include as much information as possible:
   - Type of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- We will acknowledge receipt of your report within 48 hours
- We will provide a detailed response within 7 days
- We will work on a fix and coordinate disclosure

## Security Best Practices

When using Elders Guild CodeFlow:

1. **API Keys and Secrets**
   - Never store API keys in your code
   - Use environment variables for sensitive data
   - Do not commit secrets to version control

2. **Command Execution**
   - Be cautious with commands that have system-level access
   - Review commands before execution
   - Use appropriate permission levels

3. **Extension Permissions**
   - Only grant necessary permissions
   - Review extension settings regularly
   - Keep the extension updated

## Security Features

Elders Guild CodeFlow includes several security features:

- Command timeout protection
- Permission-based access control
- Secure communication with AI system
- Input validation and sanitization
- Error message sanitization

## Updates

Security updates will be released as soon as possible after a vulnerability is confirmed. Users will be notified through:

- GitHub Security Advisories
- Extension update notifications
- Release notes

## Contact

For security concerns, contact: security@aicompany.dev

For general support: support@aicompany.dev