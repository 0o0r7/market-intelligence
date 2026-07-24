# Crypto Market Intelligence Backend

Production-grade Azure Functions backend powering the Crypto Market Intelligence Platform exposed via Microsoft Copilot Studio.

## Stack
- Python 3.11 . Azure Functions (Flex Consumption, Linux)
- aiohttp + websockets for exchange connectivity
- Pydantic v2 for typed contracts
- numpy / pandas / ta for analytics
- matplotlib + mplfinance for chart rendering
- Azure Key Vault + Managed Identity for secrets
- Azure Blob Storage for chart PNG hosting
- Application Insights via OpenCensus

## Local Development
1. python -m venv .venv
2. .\.venv\Scripts\Activate.ps1
3. pip install -r requirements.txt
4. cp .env.example .env and fill secrets
5. unc start