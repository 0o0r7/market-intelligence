from __future__ import annotations
from models.analysis import LiquidationResult, LiquidityResult, MarketStructureResult

def apply_overlays(ax, structure: MarketStructureResult, liquidity: LiquidityResult, liquidations: LiquidationResult, current_price: float) -> None:
    for sh in structure.swing_highs:
        ax.axhline(y=sh.price, color="#ef5350", linestyle="--", alpha=0.4, linewidth=1)
        ax.text(ax.get_xlim()[0], sh.price, f" SH", color="#ef5350", fontsize=8, va="bottom")
    for sl in structure.swing_lows:
        ax.axhline(y=sl.price, color="#26a69a", linestyle="--", alpha=0.4, linewidth=1)
        ax.text(ax.get_xlim()[0], sl.price, f" SL", color="#26a69a", fontsize=8, va="top")
    if structure.bos_detected and structure.last_bos_price:
        ax.axhline(y=structure.last_bos_price, color="#2196f3", linestyle="-", alpha=0.6, linewidth=1.5)
        ax.text(ax.get_xlim()[1], structure.last_bos_price, f" BOS", color="#2196f3", fontsize=8, va="center", ha="right")
    if liquidity.nearest_support: ax.axhspan(liquidity.nearest_support * 0.998, liquidity.nearest_support, facecolor="#26a69a", alpha=0.2)
    if liquidity.nearest_resistance: ax.axhspan(liquidity.nearest_resistance, liquidity.nearest_resistance * 1.002, facecolor="#ef5350", alpha=0.2)
    for cluster in liquidations.clusters:
        price = float(cluster.get("price", 0)); vol = float(cluster.get("volUsd", 0))
        if price == 0 or vol == 0: continue
        color = "#9c27b0" if price > current_price else "#ff9800"
        ax.axhline(y=price, color=color, linestyle=":", alpha=0.5, linewidth=1)
        vol_str = f"{vol/1e6:.1f}M" if vol >= 1e6 else f"{vol/1e3:.0f}K"
        ax.text(ax.get_xlim()[1], price, f" Liq {vol_str}", color=color, fontsize=7, va="center", ha="right")