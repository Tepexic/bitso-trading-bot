<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Pi Trader - Copilot Instructions

This is a Python cryptocurrency trading bot project for Raspberry Pi using the Bitso API to trade Ethereum.

## Project Context

- **Target Platform**: Raspberry Pi (ARM architecture)
- **Exchange**: Bitso (Mexican cryptocurrency exchange)
- **Primary Asset**: Ethereum (ETH/MXN pair)
- **Language**: Python 3.8+
- **Architecture**: Modular design with separate components for API, strategies, portfolio management

## Code Style Guidelines

- Follow PEP 8 Python style guidelines
- Use type hints for function parameters and return values
- Include comprehensive docstrings for all classes and methods
- Implement proper error handling with try/catch blocks
- Use logging instead of print statements for debugging
- Keep functions focused and modular

## Key Components

1. **bitso_api.py**: Bitso API client with authentication and rate limiting
2. **trading_bot.py**: Main bot orchestration and scheduling
3. **strategies.py**: Trading algorithms (MA, RSI, combined strategies)
4. **portfolio.py**: Position tracking and P&L calculation
5. **analyzer.py**: Performance analysis and reporting

## Security Considerations

- Never hardcode API credentials
- Use environment variables for sensitive configuration
- Implement proper API key validation
- Add rate limiting to prevent API abuse
- Include dry run mode for testing

## Trading Logic

- Focus on risk management (stop loss, take profit)
- Implement multiple timeframes for analysis
- Use conservative position sizing
- Include proper logging for all trading decisions
- Validate market conditions before placing orders

## Error Handling

- Handle network timeouts gracefully
- Implement retry logic for API calls
- Log all errors with context
- Fail safely without losing state
- Include comprehensive error messages

## Performance Considerations

- Optimize for low-resource environments (Raspberry Pi)
- Minimize API calls to reduce latency
- Use efficient data structures (pandas for time series)
- Implement caching where appropriate
- Keep memory usage low

When suggesting code improvements or new features, prioritize:

1. Safety and risk management
2. Code reliability and error handling
3. Performance on resource-constrained devices
4. Clear logging and debugging capabilities
5. Maintainability and modularity
