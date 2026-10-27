# Market data and instrument configuration

Status as of 2026-10-27: real-provider integration is the next milestone, not an active feature.

## What works now

- Terminal watchlist stars select which of the four fictional instruments the current user follows.
- Strategy lab's Instrument field selects the fictional instrument a saved strategy will backtest.
- Portfolio proposals are manually approved fictional fills in the local simulator. Neither a watchlist nor a strategy activates trading.
- The server-only `.env` contains configured Alpaca key and secret entries. Presence was checked without showing their values; authentication and account entitlements have not been validated. The application currently makes no Alpaca requests.

## Next implementation

Add an observation-list editor with symbol lookup and explicit exchange/currency/provider identity, starting with Amazon (`AMZN`) and NVIDIA (`NVDA`). Store each user's observation choices in SQLite. Add provider status in Settings, with a read-only connection check and explicit feed selection. Keep credentials in the server environment.

Import bounded historical bars and display timestamped current observations with source, feed, adjustment policy, currency, retrieval time, and stale/error state. Use an explicit IEX feed initially; never substitute fictional bars after a provider failure. Current observations and historical bar availability must be distinguished from exchange timestamps, especially for replay. Real USD observations must not pass through the fictional EUR accounting path.

Create a separate trading-eligibility configuration only when execution adapters and their approval/risk tests are implemented. Watching an instrument does not grant trade permission. No live broker submission is part of the next observation milestone.

## Provider facts checked against official sources

Alpaca supports US stock historical and current market data. Free live IEX data represents one exchange; consolidated current SIP data requires the relevant subscription. Historical SIP queries can be made without that subscription when the end time is at least 15 minutes old. Feed permissions must be checked explicitly; no paid plan is required for the proposed IEX observation milestone. [Alpaca Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)

Amazon's Nasdaq ticker is `AMZN`; NVIDIA's is `NVDA`. These are observation examples, not investment recommendations. [Amazon investor FAQ](https://ir.aboutamazon.com/faqs/default.aspx), [NVIDIA investor FAQ](https://investor.nvidia.com/investor-resources/faqs/default.aspx?sh_print=yes)

Audi AG's shares were delisted after the 2020 squeeze-out; Audi became wholly owned by Volkswagen. Audi should be modeled as a company/research subject, not silently mapped to a current standalone listed stock or to Bank Audi. Any Volkswagen listing would need a separate, explicitly selected instrument and a provider supporting that market. [Audi FY2020 report, squeeze-out and delisting](https://media.audi.com/is/content/audi/microsites/audi-com/assets/downloads/report/interim-reports/2020/audi-quarterly-update-q4-2020.pdf)
