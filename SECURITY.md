# Security

## Reporting
Open a private security advisory on the repository host, or contact the maintainer directly. Please do not file public issues for vulnerabilities.

## Design notes
- Credentials come only from environment variables; none are stored in the repo.
- `Settings.api_key` is excluded from `repr()`, and the logging filter redacts key/token/password-looking values.
- TLS verification is on by default; disabling it requires an explicit `EXAMPLE_API_VERIFY_TLS=false`.
- CSV output neutralises spreadsheet formula injection.
- All fixtures are synthetic (`*.example.test` hosts, invented tenant names). Never commit real cluster data, reports, or keys.
