"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class BrokerSettings:
    """Settings related to the IBKR connection and FX contract."""

    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 123
    connect_timeout: int = 10
    symbol: str = "USD"
    currency: str = "KRW"
    exchange: str = "IDEALPRO"
    market_data_req_id: int = 1


@dataclass
class StrategySettings:
    """Settings used by trading strategies."""

    short_window: int = 5
    long_window: int = 20
    default_order_qty: float = 1000
    enable_rsi_filter: bool = True
    rsi_period: int = 14
    rsi_buy_max: float = 65.0
    enable_ma_gap_filter: bool = True
    min_ma_gap_pct: float = 0.00005


@dataclass
class RiskSettings:
    """Settings used by the risk manager."""

    stop_loss_pct: float = 0.005
    take_profit_pct: float = 0.01
    max_daily_loss: float = -50000


@dataclass
class LoggingSettings:
    """Settings related to CSV logging."""

    log_file: str = "logs/trading_log.csv"
    print_ticks: bool = False
    log_ticks: bool = False
    print_filter_reasons: bool = True
    log_system_messages: bool = False
    log_risk_checks: bool = False


@dataclass
class AppSettings:
    """Top-level application settings object."""

    broker: BrokerSettings
    strategy: StrategySettings
    risk: RiskSettings
    logging: LoggingSettings

    @classmethod
    def load(cls) -> "AppSettings":
        """Load settings from `.env` and environment variables."""
        load_dotenv()

        broker = BrokerSettings(
            host=os.getenv("IBKR_HOST", "127.0.0.1"),
            port=int(os.getenv("IBKR_PORT", "7497")),
            client_id=int(os.getenv("IBKR_CLIENT_ID", "123")),
            connect_timeout=int(os.getenv("IBKR_CONNECT_TIMEOUT", "10")),
            symbol=os.getenv("FX_SYMBOL", "USD"),
            currency=os.getenv("FX_CURRENCY", "KRW"),
            exchange=os.getenv("FX_EXCHANGE", "IDEALPRO"),
            market_data_req_id=int(os.getenv("MARKET_DATA_REQ_ID", "1")),
        )

        strategy = StrategySettings(
            short_window=int(os.getenv("SHORT_WINDOW", "5")),
            long_window=int(os.getenv("LONG_WINDOW", "20")),
            default_order_qty=float(os.getenv("DEFAULT_ORDER_QTY", "1000")),
            enable_rsi_filter=os.getenv("ENABLE_RSI_FILTER", "true").lower() == "true",
            rsi_period=int(os.getenv("RSI_PERIOD", "14")),
            rsi_buy_max=float(os.getenv("RSI_BUY_MAX", "65")),
            enable_ma_gap_filter=os.getenv("ENABLE_MA_GAP_FILTER", "true").lower() == "true",
            min_ma_gap_pct=float(os.getenv("MIN_MA_GAP_PCT", "0.00005")),
        )

        risk = RiskSettings(
            stop_loss_pct=float(os.getenv("STOP_LOSS_PCT", "0.005")),
            take_profit_pct=float(os.getenv("TAKE_PROFIT_PCT", "0.01")),
            max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "-50000")),
        )

        logging = LoggingSettings(
            log_file=os.getenv("LOG_FILE", "logs/trading_log.csv"),
            print_ticks=os.getenv("PRINT_TICKS", "false").lower() == "true",
            log_ticks=os.getenv("LOG_TICKS", "false").lower() == "true",
            print_filter_reasons=os.getenv("PRINT_FILTER_REASONS", "true").lower() == "true",
            log_system_messages=os.getenv("LOG_SYSTEM_MESSAGES", "false").lower() == "true",
            log_risk_checks=os.getenv("LOG_RISK_CHECKS", "false").lower() == "true",
        )

        return cls(
            broker=broker,
            strategy=strategy,
            risk=risk,
            logging=logging,
        )
