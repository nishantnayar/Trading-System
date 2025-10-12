"""
Yahoo Finance API Client

Client for fetching market data from Yahoo Finance using yfinance library.
"""

from datetime import date, datetime, timezone
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf
from loguru import logger

from .exceptions import (
    YahooAPIError,
    YahooConnectionError,
    YahooDataError,
    YahooSymbolNotFoundError,
)
from .models import (
    AnalystRecommendation,
    CompanyInfo,
    CompanyOfficer,
    Dividend,
    EarningsCalendar,
    ESGScore,
    FinancialStatement,
    InstitutionalHolder,
    KeyStatistics,
    StockSplit,
    YahooBar,
    YahooHealthCheck,
)


class YahooClient:
    """Yahoo Finance API Client"""

    def __init__(self) -> None:
        """Initialize Yahoo Finance client"""
        logger.info("Yahoo Finance client initialized")

    async def get_historical_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        interval: str = "1d",
    ) -> List[YahooBar]:
        """
        Get historical OHLCV data

        Args:
            symbol: Stock symbol
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval ('1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo')

        Returns:
            List of OHLCV bars
        """
        try:
            ticker = yf.Ticker(symbol)

            # Fetch history
            if start_date and end_date:
                hist = ticker.history(
                    start=start_date, end=end_date, interval=interval, auto_adjust=False
                )
            else:
                # Default to 1 month if no dates provided
                hist = ticker.history(
                    period="1mo", interval=interval, auto_adjust=False
                )

            if hist.empty:
                raise YahooDataError(f"No historical data available for {symbol}")

            # Convert to YahooBar objects
            bars = []
            for timestamp, row in hist.iterrows():
                try:
                    bar = YahooBar(
                        symbol=symbol,
                        timestamp=timestamp.to_pydatetime().replace(
                            tzinfo=timezone.utc
                        ),
                        open=float(row["Open"]),
                        high=float(row["High"]),
                        low=float(row["Low"]),
                        close=float(row["Close"]),
                        volume=int(row["Volume"]),
                        dividends=float(row.get("Dividends", 0.0)),
                        stock_splits=float(row.get("Stock Splits", 0.0)),
                    )
                    bars.append(bar)
                except Exception as e:
                    logger.warning(f"Failed to parse bar for {symbol}: {e}")
                    continue

            logger.info(f"Fetched {len(bars)} bars for {symbol}")
            return bars

        except YahooDataError:
            raise
        except Exception as e:
            raise YahooAPIError(f"Failed to get historical data for {symbol}: {str(e)}")

    async def get_company_info(self, symbol: str) -> CompanyInfo:
        """
        Get company profile and basic information

        Args:
            symbol: Stock symbol

        Returns:
            Company information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or len(info) == 0:
                raise YahooSymbolNotFoundError(f"No info available for {symbol}")

            # Extract core fields
            company_info = CompanyInfo(
                symbol=symbol,
                name=info.get("longName") or info.get("shortName"),
                sector=info.get("sector"),
                industry=info.get("industry"),
                description=info.get("longBusinessSummary"),
                website=info.get("website"),
                phone=info.get("phone"),
                address=info.get("address1"),
                city=info.get("city"),
                state=info.get("state"),
                zip=info.get("zip"),
                country=info.get("country"),
                employees=info.get("fullTimeEmployees"),
                market_cap=info.get("marketCap"),
                currency=info.get("currency"),
                exchange=info.get("exchange"),
                quote_type=info.get("quoteType"),
                additional_data=info,  # Store full info dict
            )

            logger.info(f"Fetched company info for {symbol}")
            return company_info

        except YahooSymbolNotFoundError:
            raise
        except Exception as e:
            raise YahooAPIError(f"Failed to get company info for {symbol}: {str(e)}")

    async def get_company_officers(self, symbol: str) -> List[CompanyOfficer]:
        """
        Get company officers/executives

        Args:
            symbol: Stock symbol

        Returns:
            List of company officers
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            officers_data = info.get("companyOfficers", [])
            if not officers_data:
                logger.warning(f"No officers data available for {symbol}")
                return []

            officers = []
            for officer_data in officers_data:
                try:
                    officer = CompanyOfficer(
                        symbol=symbol,
                        name=officer_data.get("name", "Unknown"),
                        title=officer_data.get("title"),
                        age=officer_data.get("age"),
                        year_born=officer_data.get("yearBorn"),
                        fiscal_year=officer_data.get("fiscalYear"),
                        total_pay=officer_data.get("totalPay"),
                        exercised_value=officer_data.get("exercisedValue"),
                        unexercised_value=officer_data.get("unexercisedValue"),
                    )
                    officers.append(officer)
                except Exception as e:
                    logger.warning(f"Failed to parse officer data: {e}")
                    continue

            logger.info(f"Fetched {len(officers)} officers for {symbol}")
            return officers

        except Exception as e:
            raise YahooAPIError(f"Failed to get officers for {symbol}: {str(e)}")

    async def get_key_statistics(self, symbol: str) -> KeyStatistics:
        """
        Get key financial statistics

        Args:
            symbol: Stock symbol

        Returns:
            Key statistics
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                raise YahooDataError(f"No statistics available for {symbol}")

            stats = KeyStatistics(
                symbol=symbol,
                date=date.today(),
                market_cap=info.get("marketCap"),
                enterprise_value=info.get("enterpriseValue"),
                trailing_pe=info.get("trailingPE"),
                forward_pe=info.get("forwardPE"),
                peg_ratio=info.get("pegRatio"),
                price_to_book=info.get("priceToBook"),
                price_to_sales=info.get("priceToSalesTrailing12Months"),
                enterprise_to_revenue=info.get("enterpriseToRevenue"),
                enterprise_to_ebitda=info.get("enterpriseToEbitda"),
                profit_margin=info.get("profitMargins"),
                operating_margin=info.get("operatingMargins"),
                return_on_assets=info.get("returnOnAssets"),
                return_on_equity=info.get("returnOnEquity"),
                gross_margin=info.get("grossMargins"),
                ebitda_margin=info.get("ebitdaMargins"),
                revenue=info.get("totalRevenue"),
                revenue_per_share=info.get("revenuePerShare"),
                earnings_per_share=info.get("trailingEps"),
                total_cash=info.get("totalCash"),
                total_debt=info.get("totalDebt"),
                debt_to_equity=info.get("debtToEquity"),
                current_ratio=info.get("currentRatio"),
                quick_ratio=info.get("quickRatio"),
                free_cash_flow=info.get("freeCashflow"),
                operating_cash_flow=info.get("operatingCashflow"),
                revenue_growth=info.get("revenueGrowth"),
                earnings_growth=info.get("earningsGrowth"),
                beta=info.get("beta"),
                fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
                fifty_two_week_low=info.get("fiftyTwoWeekLow"),
                fifty_day_average=info.get("fiftyDayAverage"),
                two_hundred_day_average=info.get("twoHundredDayAverage"),
                average_volume=info.get("averageVolume"),
                dividend_yield=info.get("dividendYield"),
                dividend_rate=info.get("dividendRate"),
                payout_ratio=info.get("payoutRatio"),
                shares_outstanding=info.get("sharesOutstanding"),
                float_shares=info.get("floatShares"),
                shares_short=info.get("sharesShort"),
                short_ratio=info.get("shortRatio"),
                held_percent_insiders=info.get("heldPercentInsiders"),
                held_percent_institutions=info.get("heldPercentInstitutions"),
            )

            logger.info(f"Fetched key statistics for {symbol}")
            return stats

        except YahooDataError:
            raise
        except Exception as e:
            raise YahooAPIError(f"Failed to get statistics for {symbol}: {str(e)}")

    async def get_dividends(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dividend]:
        """
        Get dividend history

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            List of dividends
        """
        try:
            ticker = yf.Ticker(symbol)

            # Fetch dividends
            if start_date and end_date:
                divs = ticker.dividends.loc[str(start_date) : str(end_date)]  # type: ignore[misc]
            else:
                divs = ticker.dividends

            if divs.empty:
                logger.info(f"No dividends available for {symbol}")
                return []

            dividends = []
            for timestamp, amount in divs.items():
                try:
                    div = Dividend(
                        symbol=symbol,
                        ex_date=timestamp.date(),
                        amount=float(amount),
                    )
                    dividends.append(div)
                except Exception as e:
                    logger.warning(f"Failed to parse dividend: {e}")
                    continue

            logger.info(f"Fetched {len(dividends)} dividends for {symbol}")
            return dividends

        except Exception as e:
            raise YahooAPIError(f"Failed to get dividends for {symbol}: {str(e)}")

    async def get_splits(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[StockSplit]:
        """
        Get stock split history

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            List of stock splits
        """
        try:
            ticker = yf.Ticker(symbol)

            # Fetch splits
            if start_date and end_date:
                splits = ticker.splits.loc[str(start_date) : str(end_date)]  # type: ignore[misc]
            else:
                splits = ticker.splits

            if splits.empty:
                logger.info(f"No splits available for {symbol}")
                return []

            split_list = []
            for timestamp, ratio in splits.items():
                try:
                    split = StockSplit(
                        symbol=symbol,
                        split_date=timestamp.date(),
                        split_ratio=float(ratio),
                        ratio_str=(
                            f"{int(ratio)}:1" if ratio >= 1 else f"1:{int(1/ratio)}"
                        ),
                    )
                    split_list.append(split)
                except Exception as e:
                    logger.warning(f"Failed to parse split: {e}")
                    continue

            logger.info(f"Fetched {len(split_list)} splits for {symbol}")
            return split_list

        except Exception as e:
            raise YahooAPIError(f"Failed to get splits for {symbol}: {str(e)}")

    async def get_institutional_holders(self, symbol: str) -> List[InstitutionalHolder]:
        """
        Get institutional holders

        Args:
            symbol: Stock symbol

        Returns:
            List of institutional holders
        """
        try:
            ticker = yf.Ticker(symbol)
            holders_df = ticker.institutional_holders

            if holders_df is None or holders_df.empty:
                logger.info(f"No institutional holders data for {symbol}")
                return []

            holders = []
            for _, row in holders_df.iterrows():
                try:
                    holder = InstitutionalHolder(
                        symbol=symbol,
                        date_reported=pd.to_datetime(row["Date Reported"]).date(),
                        holder_name=row["Holder"],
                        shares=int(row["Shares"]) if pd.notna(row["Shares"]) else None,
                        value=int(row["Value"]) if pd.notna(row["Value"]) else None,
                        percent_held=(
                            float(row["% Out"]) if pd.notna(row.get("% Out")) else None
                        ),
                    )
                    holders.append(holder)
                except Exception as e:
                    logger.warning(f"Failed to parse holder: {e}")
                    continue

            logger.info(f"Fetched {len(holders)} institutional holders for {symbol}")
            return holders

        except Exception as e:
            raise YahooAPIError(
                f"Failed to get institutional holders for {symbol}: {str(e)}"
            )

    async def get_analyst_recommendations(
        self, symbol: str
    ) -> List[AnalystRecommendation]:
        """
        Get analyst recommendations

        Args:
            symbol: Stock symbol

        Returns:
            List of analyst recommendations
        """
        try:
            ticker = yf.Ticker(symbol)
            recs_df = ticker.recommendations_summary

            if recs_df is None or recs_df.empty:
                logger.info(f"No recommendations data for {symbol}")
                return []

            recommendations = []
            for _, row in recs_df.iterrows():
                try:
                    rec = AnalystRecommendation(
                        symbol=symbol,
                        date=date.today(),
                        period=row["period"],
                        strong_buy=int(row["strongBuy"]),
                        buy=int(row["buy"]),
                        hold=int(row["hold"]),
                        sell=int(row["sell"]),
                        strong_sell=int(row["strongSell"]),
                    )
                    recommendations.append(rec)
                except Exception as e:
                    logger.warning(f"Failed to parse recommendation: {e}")
                    continue

            logger.info(f"Fetched {len(recommendations)} recommendations for {symbol}")
            return recommendations

        except Exception as e:
            raise YahooAPIError(f"Failed to get recommendations for {symbol}: {str(e)}")

    async def get_financial_statements(
        self, symbol: str, statement_type: str, period_type: str = "annual"
    ) -> List[FinancialStatement]:
        """
        Get financial statements

        Args:
            symbol: Stock symbol
            statement_type: 'income', 'balance_sheet', or 'cash_flow'
            period_type: 'annual' or 'quarterly'

        Returns:
            List of financial statements
        """
        try:
            ticker = yf.Ticker(symbol)

            # Get appropriate statement
            if statement_type == "income":
                df = (
                    ticker.quarterly_financials
                    if period_type == "quarterly"
                    else ticker.financials
                )
            elif statement_type == "balance_sheet":
                df = (
                    ticker.quarterly_balance_sheet
                    if period_type == "quarterly"
                    else ticker.balance_sheet
                )
            elif statement_type == "cash_flow":
                df = (
                    ticker.quarterly_cashflow
                    if period_type == "quarterly"
                    else ticker.cashflow
                )
            else:
                raise ValueError(f"Invalid statement type: {statement_type}")

            if df is None or df.empty:
                logger.info(f"No {statement_type} data for {symbol}")
                return []

            statements = []
            for col in df.columns:
                try:
                    # Convert column data to dict
                    data_dict = df[col].to_dict()
                    # Convert any NaN to None
                    data_dict = {
                        k: (
                            None
                            if pd.isna(v)
                            else float(v) if isinstance(v, (int, float)) else v
                        )
                        for k, v in data_dict.items()
                    }

                    stmt = FinancialStatement(
                        symbol=symbol,
                        period_end=pd.to_datetime(col).date(),
                        statement_type=statement_type,
                        period_type=period_type,
                        data=data_dict,
                    )
                    statements.append(stmt)
                except Exception as e:
                    logger.warning(f"Failed to parse statement: {e}")
                    continue

            logger.info(
                f"Fetched {len(statements)} {period_type} {statement_type} statements for {symbol}"
            )
            return statements

        except Exception as e:
            raise YahooAPIError(
                f"Failed to get {statement_type} for {symbol}: {str(e)}"
            )

    async def get_esg_scores(self, symbol: str) -> Optional[ESGScore]:
        """
        Get ESG scores

        Args:
            symbol: Stock symbol

        Returns:
            ESG scores or None if not available
        """
        try:
            ticker = yf.Ticker(symbol)
            esg_df = ticker.sustainability

            if esg_df is None or esg_df.empty:
                logger.info(f"No ESG data for {symbol}")
                return None

            esg_data = esg_df.iloc[:, 0].to_dict() if not esg_df.empty else {}

            esg = ESGScore(
                symbol=symbol,
                date=date.today(),
                total_esg=esg_data.get("totalEsg"),
                environment_score=esg_data.get("environmentScore"),
                social_score=esg_data.get("socialScore"),
                governance_score=esg_data.get("governanceScore"),
                controversy_level=esg_data.get("highestControversy"),
                esg_performance=esg_data.get("esgPerformance"),
                peer_group=esg_data.get("peerGroup"),
                peer_count=esg_data.get("peerCount"),
            )

            logger.info(f"Fetched ESG scores for {symbol}")
            return esg

        except Exception as e:
            logger.warning(f"Failed to get ESG scores for {symbol}: {e}")
            return None

    async def health_check(self, test_symbol: str = "AAPL") -> YahooHealthCheck:
        """
        Check if Yahoo Finance API is accessible

        Args:
            test_symbol: Symbol to test with

        Returns:
            Health check result
        """
        try:
            ticker = yf.Ticker(test_symbol)
            info = ticker.info

            healthy = bool(info and len(info) > 0)

            return YahooHealthCheck(
                healthy=healthy,
                symbol_tested=test_symbol,
                data_available=healthy,
                timestamp=datetime.now(timezone.utc),
            )

        except Exception as e:
            return YahooHealthCheck(
                healthy=False,
                symbol_tested=test_symbol,
                data_available=False,
                error_message=str(e),
                timestamp=datetime.now(timezone.utc),
            )
