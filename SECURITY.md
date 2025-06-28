# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please email the details to the maintainer rather than opening a public issue.

## Security Best Practices

### For Users:

1. **Never commit `.env` files** with real credentials
2. **Keep your Telegram token secret** - anyone with it can control your bot
3. **Use environment variables** for all sensitive data
4. **Regularly update** the Docker image for security patches

### For Contributors:

1. **Never hardcode** credentials or tokens
2. **Always use** environment variables for configuration
3. **Test with** dummy credentials
4. **Review** `.gitignore` before committing

## Secure Configuration

```bash
# Good - Using environment variables
docker run -e TELEGRAM_BOT_TOKEN="$TOKEN" ...

# Bad - Token in command
docker run -e TELEGRAM_BOT_TOKEN="7104880156:..." ...
```

## Token Security

If your Telegram token is compromised:
1. Immediately revoke it via @BotFather
2. Generate a new token
3. Update your configuration

## API Keys

Currently, this project uses public Euskalmet endpoints that don't require authentication. If API keys are added in the future:
- Store them in environment variables
- Never commit them to the repository
- Document them in `.env.example` without real values