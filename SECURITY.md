# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please send an email to hello@sensibleanalytics.co

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Security Best Practices

- **Never commit API keys or secrets** - Use environment variables
- **Validate all inputs** - Especially from external APIs (Basiq, Fance)
- **Sanitize data** - Before storing or displaying user data
- **Use HTTPS** - For all external communications
- **Rotate secrets** - Regularly update API keys and tokens

## Dependencies

- Keep dependencies updated
- Run security audits: `pip audit` and `npm audit`
- Use Snyk or Dependabot for automated updates