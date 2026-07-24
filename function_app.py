from __future__ import annotations
from typing import Optional
import azure.functions as func
from config.logging import configure_logging, get_logger
from config.settings import get_settings
from models.response import ChartResponse, ErrorResponse, HealthResponse, MarketIntelligenceResponse, MarketScanResponse
from services.orchestrator import Orchestrator

configure_logging(level="INFO")
log = get_logger("function_app")
settings = get_settings()

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
_orchestrator: Optional[Orchestrator] = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None: _orchestrator = Orchestrator()
    return _orchestrator

@app.route(route="health", methods=[func.HttpMethod.GET], auth_level=func.AuthLevel.ANONYMOUS)
async def health(req: func.HttpRequest) -> func.HttpResponse:
    log.info("health.check")
    payload = HealthResponse(environment=settings.environment, components={"settings": "ok", "logging": "ok", "coinglass_key_present": "yes" if settings.coinglass_api_key else "no", "key_vault_configured": "yes" if settings.key_vault_url else "no"})
    return func.HttpResponse(body=payload.model_dump_json(), status_code=200, mimetype="application/json")

@app.route(route="market_intelligence", methods=[func.HttpMethod.POST], auth_level=func.AuthLevel.FUNCTION)
async def market_intelligence(req: func.HttpRequest) -> func.HttpResponse:
    try: body = req.get_json()
    except ValueError: return _error_response(400, "Invalid JSON payload")
    symbol = body.get("symbol"); timeframe = body.get("timeframe", "4h")
    if not symbol: return _error_response(400, "Missing required field: 'symbol'")
    try:
        orch = get_orchestrator(); result: MarketIntelligenceResponse = await orch.get_market_intelligence(symbol, timeframe)
        return func.HttpResponse(body=result.model_dump_json(), status_code=200, mimetype="application/json")
    except ValueError as ve: return _error_response(400, str(ve))
    except Exception as exc:
        log.error("market_intelligence_failed", error=str(exc), exc_info=True)
        return _error_response(500, "Internal server error during market intelligence.", detail=str(exc))

@app.route(route="market_scan", methods=[func.HttpMethod.POST], auth_level=func.AuthLevel.FUNCTION)
async def market_scan(req: func.HttpRequest) -> func.HttpResponse:
    try: body = req.get_json()
    except ValueError: return _error_response(400, "Invalid JSON payload")
    symbols = body.get("symbols", []); timeframe = body.get("timeframe", "4h")
    if not symbols or not isinstance(symbols, list): return _error_response(400, "Missing or invalid 'symbols' (must be a list)")
    try:
        orch = get_orchestrator(); result: MarketScanResponse = await orch.get_market_scan(symbols, timeframe)
        return func.HttpResponse(body=result.model_dump_json(), status_code=200, mimetype="application/json")
    except ValueError as ve: return _error_response(400, str(ve))
    except Exception as exc:
        log.error("market_scan_failed", error=str(exc), exc_info=True)
        return _error_response(500, "Internal server error during market scan.", detail=str(exc))

@app.route(route="chart", methods=[func.HttpMethod.POST], auth_level=func.AuthLevel.FUNCTION)
async def chart(req: func.HttpRequest) -> func.HttpResponse:
    try: body = req.get_json()
    except ValueError: return _error_response(400, "Invalid JSON payload")
    symbol = body.get("symbol"); timeframe = body.get("timeframe", "4h")
    if not symbol: return _error_response(400, "Missing required field: 'symbol'")
    try:
        orch = get_orchestrator(); chart_url = await orch.generate_chart(symbol, timeframe)
        if not chart_url: return _error_response(500, "Failed to generate chart URL.")
        payload = ChartResponse(chart_url=chart_url, symbol=symbol, timeframe=timeframe)
        return func.HttpResponse(body=payload.model_dump_json(), status_code=200, mimetype="application/json")
    except ValueError as ve: return _error_response(400, str(ve))
    except Exception as exc:
        log.error("chart_generation_failed", error=str(exc), exc_info=True)
        return _error_response(500, "Internal server error during chart generation.", detail=str(exc))

def _error_response(status_code: int, message: str, detail: Optional[str] = None) -> func.HttpResponse:
    err = ErrorResponse(error=message, detail=detail, request_id=None)
    return func.HttpResponse(body=err.model_dump_json(), status_code=status_code, mimetype="application/json")