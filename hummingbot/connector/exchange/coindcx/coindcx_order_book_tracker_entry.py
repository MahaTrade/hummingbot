from hummingbot.core.data_type.order_book import OrderBook
from hummingbot.core.data_type.order_book_tracker_entry import OrderBookTrackerEntry
from hummingbot.connector.exchange.coindcx.coindcx_active_order_tracker import CoindcxActiveOrderTracker


class CoindcxOrderBookTrackerEntry(OrderBookTrackerEntry):
    def __init__(self,
                 trading_pair: str,
                 timestamp: float,
                 order_book: OrderBook,
                 active_order_tracker: CoindcxActiveOrderTracker):
        self._active_order_tracker = active_order_tracker
        super(CoindcxOrderBookTrackerEntry, self).__init__(trading_pair, timestamp, order_book)

    def __repr__(self) -> str:
        return (
            f"CoindcxOrderBookTrackerEntry(trading_pair='{self._trading_pair}', timestamp='{self._timestamp}', "
            f"order_book='{self._order_book}')"
        )

    @property
    def active_order_tracker(self) -> CoindcxActiveOrderTracker:
        return self._active_order_tracker
