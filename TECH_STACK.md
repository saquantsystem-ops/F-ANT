# Tech Stack Analysis: F-Antigravity (Rebranded Jesse Engine)

This document provides a comprehensive breakdown of the technology stack utilized in the **F-Antigravity** trading application.

---

## [Backend Technology Stack]

The backend is engineered for high-frequency data processing and parallel financial simulation.

- **Core Language**: **Python 3.12+**
  - Leverages modern features like type hinting and asynchronous programming.
- **Web Interface (API)**: **FastAPI**
  - High performance, asynchronous standard for building APIs with Python.
  - Handles real-time requests for backtest status, data imports, and log streaming.
- **Mathematical & Data Processing**:
  - **NumPy & Pandas**: Essential for vectorised operations on time-series candle data.
  - **Numba (JIT)**: Accelerates Python functions to near-C speeds by compiling them to machine code at runtime.
  - **SciPy / Statsmodels**: Used for advanced statistical analysis and metric calculation.
- **Database Architecture**:
  - **Peewee ORM**: Lightweight and efficient Object-Relational Mapper.
  - **SQLite**: Primary project-level database for local strategy testing.
  - **PostgreSQL**: Supported for larger, production-grade deployments.
- **Parallel Computing**:
  - **Python Multiprocessing**: Utilized for running parallel optimization sessions and multi-asset backtests.
- **Real-time Operations**:
  - **Redis**: High-speed, in-memory data store for caching and WebSocket Pub/Sub messaging.

---

## [Frontend Technology Stack]

The frontend is designed to provide a premium, low-latency trading experience.

- **Structure & Layout**: **Semantic HTML5**
  - Ensures structural integrity and accessibility.
- **Design System**: **Custom Vanilla CSS3**
  - **Aesthetics**: Premium Dark Mode with Glassmorphism effects.
  - **Responsiveness**: Fluid layouts for various display sizes.
  - **Animations**: Subtle micro-interactions for enhanced UX.
- **Core Logic**: **JavaScript (ES6+)**
  - Manages asynchronous state and real-time UI updates.
- **Financial Visualization**: **Lightweight Charts (TradingView)**
  - Sector-leading, high-performance library for rendering interactive OHLCV and Equity Curve charts.
- **Communication Layer**: **WebSockets**
  - Bi-directional, real-time communication for live progress bars and trading logs.

---

## [Infrastructure & Tooling]

- **Authentication**: **JWT (JSON Web Tokens)**
  - Secure, stateless authentication for both dashboard and WebSocket connections.
- **Encryption**: **Cryptography / PyJWT**
  - Ensures secure password hashing and token generation.
- **Environment Management**: **python-dotenv**
  - Management of sensitive keys and configurations via `.env`.
- **External APIs**: Integration with **YFinance**, **MT5**, and **Angel One** for live market data.

---

## [System Directory Structure]

1. **`jesse-ai/`**: The core framework and engine logic.
2. **`jesse-project/`**: User-specific workspace.
   - `strategies/`: Custom algorithmic logic.
   - `storage/`: Database files and backtest logs.
   - `routes.py`: Mapping of trading symbols to specific strategies.
   - `config.py`: Centralized application and exchange configuration.
