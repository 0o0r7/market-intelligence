from __future__ import annotations
import io
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas
from charts.overlays import apply_overlays
from charts.themes import dark_style
from config.logging import get_logger
from config.settings import get_settings
from models.analysis import LiquidationResult, LiquidityResult, MarketStructureResult
from models.market_data import CandleSeries
log = get_logger(__name__)

class ChartRenderer:
    def __init__(self) -> None:
        self.settings = get_settings(); self.blob_service_client: Optional[BlobServiceClient] = None
        if self.settings.azure_storage_connection_string:
            try: self.blob_service_client = BlobServiceClient.from_connection_string(self.settings.azure_storage_connection_string); log.info("chart_renderer.blob_storage_initialized")
            except Exception as e: log.error("chart_renderer.blob_storage_failed", error=str(e))

    async def generate_chart_url(self, candles: CandleSeries, structure: MarketStructureResult, liquidity: LiquidityResult, liquidations: LiquidationResult, symbol: str, timeframe: str) -> str:
        if candles.empty: return ""
        df = pd.DataFrame([c.model_dump() for c in candles.candles])
        df["Date"] = pd.to_datetime(df["open_time"], unit="ms"); df.set_index("Date", inplace=True)
        df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)
        fig, axes = mpf.plot(df, type="candle", style=dark_style, volume=True, returnfig=True, figsize=(16, 9), title=f"{symbol} - {timeframe}")
        ax_main = axes[0]
        current_price = float(candles.last_price or 0.0)
        apply_overlays(ax_main, structure, liquidity, liquidations, current_price)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100, facecolor="#121212"); buf.seek(0); plt.close(fig)
        if self.blob_service_client: return await self._upload_and_get_sas(buf, symbol, timeframe)
        log.warning("chart_renderer.no_storage_configured", msg="Returning base64 placeholder.")
        import base64
        return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"

    async def _upload_and_get_sas(self, data: io.BytesIO, symbol: str, timeframe: str) -> str:
        container_name = self.settings.chart_container_name; blob_name = f"{symbol}_{timeframe}_{uuid.uuid4().hex}.png"
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            blob_client.upload_blob(data, overwrite=True)
            sas_token = generate_blob_sas(account_name=blob_client.account_name, container_name=container_name, blob_name=blob_name, account_key=blob_client.credential.account_key, permission=BlobSasPermissions(read=True), expiry=datetime.now(timezone.utc) + timedelta(minutes=self.settings.chart_sas_ttl_minutes))
            return f"{blob_client.url}?{sas_token}"
        except Exception as e:
            log.error("chart_renderer.upload_failed", error=str(e), exc_info=True); return ""