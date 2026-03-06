import logging
import gate_api
from gate_api.exceptions import ApiException
from config import GATE_API_KEY, GATE_API_SECRET, RISK_PERCENT, LEVERAGE, DEFAULT_STOP_PERCENT, DEFAULT_TP_PERCENT

logger = logging.getLogger(__name__)

configuration = gate_api.Configuration(
    host="https://api.gateio.ws/api/v4",
    key=GATE_API_KEY,
    secret=GATE_API_SECRET
)


def get_futures_api():
    return gate_api.FutureApi(gate_api.ApiClient(configuration))


def symbol_to_contract(symbol: str) -> str:
    """Convert BTCUSDT -> BTC_USDT"""
    if "_" in symbol:
        return symbol
    if symbol.endswith("USDT"):
        coin = symbol[:-4]
        return f"{coin}_USDT"
    return symbol


def get_balance() -> float:
    try:
        api = get_futures_api()
        account = api.list_futures_accounts(settle="usdt")
        balance = float(account.available)
        logger.info(f"Available balance: {balance} USDT")
        return balance
    except ApiException as e:
        logger.error(f"Failed to get balance: {e}")
        return 0.0


def execute_trade(signal: dict) -> bool:
    try:
        symbol = signal.get("symbol", "")
        direction = signal.get("direction", "long")
        entry = signal.get("entry")
        stop_loss = signal.get("stop_loss")
        take_profit_list = signal.get("take_profit")

        contract = symbol_to_contract(symbol)
        api = get_futures_api()

        # Set leverage
        try:
            api.update_position_leverage(settle="usdt", contract=contract, leverage=str(LEVERAGE))
            logger.info(f"Leverage set to {LEVERAGE}x for {contract}")
        except ApiException as e:
            logger.warning(f"Could not set leverage: {e}")

        # Get balance and calculate size
        balance = get_balance()
        if balance <= 0:
            logger.error("Zero balance, skipping trade")
            return False

        risk_usdt = balance * RISK_PERCENT / 100

        # Get contract info for size calculation
        try:
            contract_info = api.get_futures_contract(settle="usdt", contract=contract)
            quanto_multiplier = float(contract_info.quanto_multiplier or 0.0001)
        except Exception:
            quanto_multiplier = 0.0001

        if entry:
            size = int(risk_usdt * LEVERAGE / (entry * quanto_multiplier))
        else:
            # Get current price
            try:
                ticker = api.list_futures_tickers(settle="usdt", contract=contract)
                entry = float(ticker[0].last)
                size = int(risk_usdt * LEVERAGE / (entry * quanto_multiplier))
            except Exception as e:
                logger.error(f"Could not get market price: {e}")
                return False

        if size <= 0:
            logger.error(f"Calculated size is 0, balance too low or wrong config")
            return False

        # Direction: long = positive size, short = negative size
        if direction == "short":
            size = -size

        logger.info(f"Opening {direction} {contract}: size={size}, entry={entry}")

        # Create main order
        order = gate_api.FuturesOrder(
            contract=contract,
            size=size,
            price=str(entry) if entry else "0",
            tif="gtc" if entry else "ioc",
            reduce_only=False,
        )
        if not entry:
            order.tif = "ioc"
            order.price = "0"

        result = api.create_futures_order(settle="usdt", futures_order=order)
        logger.info(f"Main order created: {result.id}")

        # Calculate stop loss
        if stop_loss is None:
            if direction == "long":
                stop_loss = round(entry * (1 - DEFAULT_STOP_PERCENT / 100), 4)
            else:
                stop_loss = round(entry * (1 + DEFAULT_STOP_PERCENT / 100), 4)

        # Calculate take profit
        if not take_profit_list:
            if direction == "long":
                tp = round(entry * (1 + DEFAULT_TP_PERCENT / 100), 4)
            else:
                tp = round(entry * (1 - DEFAULT_TP_PERCENT / 100), 4)
            take_profit_list = [tp]

        # Create stop loss order
        try:
            sl_order = gate_api.FuturesPriceTriggeredOrder(
                initial=gate_api.FuturesInitialOrder(
                    contract=contract,
                    size=-size,  # close position
                    price="0",
                    tif="ioc",
                    reduce_only=True,
                ),
                trigger=gate_api.FuturesPriceTrigger(
                    strategy_type=0,
                    price_type=0,
                    price=str(stop_loss),
                    rule=2 if direction == "long" else 1,
                    expiration=86400,
                )
            )
            api.create_price_triggered_order(settle="usdt", futures_price_triggered_order=sl_order)
            logger.info(f"Stop loss set at {stop_loss}")
        except ApiException as e:
            logger.warning(f"Could not set stop loss: {e}")

        # Create take profit order (first target only)
        try:
            tp_price = take_profit_list[0]
            tp_order = gate_api.FuturesPriceTriggeredOrder(
                initial=gate_api.FuturesInitialOrder(
                    contract=contract,
                    size=-size,
                    price="0",
                    tif="ioc",
                    reduce_only=True,
                ),
                trigger=gate_api.FuturesPriceTrigger(
                    strategy_type=0,
                    price_type=0,
                    price=str(tp_price),
                    rule=1 if direction == "long" else 2,
                    expiration=86400,
                )
            )
            api.create_price_triggered_order(settle="usdt", futures_price_triggered_order=tp_order)
            logger.info(f"Take profit set at {tp_price}")
        except ApiException as e:
            logger.warning(f"Could not set take profit: {e}")

        logger.info(f"Trade executed successfully: {direction} {contract} x{LEVERAGE}")
        return True

    except ApiException as e:
        logger.error(f"Gate.io API error: {e}")
        return False
    except Exception as e:
        logger.error(f"Trade execution error: {e}")
        return False
