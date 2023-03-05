import logging
from optibook.synchronous_client import Exchange
import time

logging.getLogger('client').setLevel('ERROR')
logger = logging.getLogger(__name__)

BASKET_INSTRUMENT_ID = 'C2_GREEN_ENERGY_ETF'
STOCK_INSTRUMENT_IDS = ['C2_SOLAR_CO', 'C2_WIND_LTD']

VERBOSE = False

def auto_trader(e):
    
    stock_book = e.get_last_price_book(STOCK_INSTRUMENT_IDS[0])
    ask_list = stock_book.asks
    bid_list = stock_book.bids
    
    current_ask_price_1 = [x.price for x in ask_list]
    if current_ask_price_1 == []:
        return
    
    current_ask_price_1 = current_ask_price_1[0]
    current_ask_volume_1 = [x.volume for x in ask_list][0]
    
    current_bid_price_1 = [x.price for x in bid_list]
    if current_bid_price_1 == []:
        return 
    
    current_bid_price_1 = current_bid_price_1[0]
    current_bid_volume_1 = [x.volume for x in bid_list][0]
    
    basket_book = e.get_last_price_book(STOCK_INSTRUMENT_IDS[1])
    ask_list = basket_book.asks
    bid_list = basket_book.bids
    
    current_ask_price_2 = [x.price for x in ask_list]
    if current_ask_price_2 == []:
        return
    current_ask_price_2 = current_ask_price_2[0]
    current_ask_volume_2 = [x.volume for x in ask_list][0]
    
    current_bid_price_2 = [x.price for x in bid_list]
    if current_bid_price_2 == []:
        return
    current_bid_price_2 = current_bid_price_2[0]
    current_bid_volume_2 = [x.volume for x in bid_list][0]
    
    # Prepare ETF bid and ask from the Stocks
    etf_as_stock_bid_price = (0.5 * current_bid_price_1) + (0.5 * current_bid_price_2)
    etf_as_stock_ask_price = (0.5 * current_ask_price_1) + (0.5 * current_ask_price_2)
    bid_spread = etf_as_stock_ask_price - etf_as_stock_bid_price  
    
    # asket_price_1_list = e.get_trade_history(STOCK_INSTRUMENT_IDS[0])
    # basket_price_2_list = e.get_trade_history(STOCK_INSTRUMENT_IDS[1])

    basket_book = e.get_last_price_book(BASKET_INSTRUMENT_ID)
    ask_list = basket_book.asks
    bid_list = basket_book.bids
    
    current_etf_ask_price = [x.price for x in ask_list]
    if current_etf_ask_price == []:
        return
    
    current_etf_ask_price = current_etf_ask_price[0]
    current_etf_ask_volume = [x.volume for x in ask_list][0]
    
    current_etf_bid_price = [x.price for x in bid_list]
    if current_etf_bid_price == []:
        return
    current_etf_bid_price = current_etf_bid_price[0]
    current_etf_bid_volume = [x.volume for x in bid_list][0]

    pos = e.get_positions()
    
    if pos == {}:
        pos[BASKET_INSTRUMENT_ID] = 0
        pos[STOCK_INSTRUMENT_IDS[0]] = 0
        pos[STOCK_INSTRUMENT_IDS[1]] = 0

    etf_pos = pos[BASKET_INSTRUMENT_ID]
    stock_1_pos = pos[STOCK_INSTRUMENT_IDS[0]]
    stock_2_pos = pos[STOCK_INSTRUMENT_IDS[1]]
    
    # 1st case: The ETF has a higher bid price than the individual stock ask price
    if current_etf_bid_price > etf_as_stock_ask_price:
        if current_etf_bid_volume == 1:
            return
        
        FIRST_VOLUME = min(min(current_ask_volume_1,current_ask_volume_2)*2, current_etf_bid_volume)
        VOLUME = min(500-abs(etf_pos), FIRST_VOLUME)
        
        if VOLUME == 0 and etf_pos == -500:
            return
        
        elif VOLUME == 0 and etf_pos == 500:
            VOLUME = min(FIRST_VOLUME, 500)
        
        logger.info(f'buying stocks at {current_ask_price_1} and {current_ask_price_2} V {VOLUME//2} and selling etf at {current_etf_bid_price} V {VOLUME}')
        try:
            # BUY STOCKS INDIVIDUALLY
            e.insert_order(STOCK_INSTRUMENT_IDS[0], price = current_ask_price_1, volume = VOLUME//2, side = 'bid', order_type = 'limit')
            e.insert_order(STOCK_INSTRUMENT_IDS[1], price = current_ask_price_2, volume = VOLUME//2, side = 'bid', order_type = 'limit')
            # SELL ETF
            e.insert_order(BASKET_INSTRUMENT_ID, price = current_etf_bid_price, volume = VOLUME//2*2, side = 'ask', order_type = 'limit')
            
            return
        except:
            pass
        
    #logging.info(f"etf ask: {current_etf_ask_price} etf as stock bid: {etf_as_stock_bid_price} etf bid: {current_etf_bid_price} etf as stock ask: {etf_as_stock_ask_price}")
    # 2nd case: The ETF has a lower ask price then the individual stock bid price
    # IF the buy price of the etf is less than the sell price of the constructed etf then we sell individual stocks and buy the etf
    if current_etf_ask_price < etf_as_stock_bid_price:
        if current_etf_bid_volume == 1:
            return
        
        FIRST_VOLUME = min(min(current_ask_volume_1,current_ask_volume_2)*2, current_etf_bid_volume)
        VOLUME = min(500-abs(etf_pos), FIRST_VOLUME)
        
        if VOLUME == 0 and etf_pos == 500:
            return
        
        elif VOLUME == 0 and etf_pos == -500:
            VOLUME = min(FIRST_VOLUME, 500)
        
        if VERBOSE: logger.info(f'buying etf at {current_etf_ask_price} v {VOLUME} and selling stocks at {current_bid_price_1} and {current_bid_price_2} v {VOLUME//2}')
        # BUY ETF
        try:
            e.insert_order(BASKET_INSTRUMENT_ID, price = current_etf_ask_price, volume = VOLUME//2*2, side = 'bid', order_type = 'limit')
            # SELL STOCKS INDIVIDUALLY
            e.insert_order(STOCK_INSTRUMENT_IDS[0], price = current_bid_price_1, volume = VOLUME//2, side = 'ask', order_type = 'limit')
            e.insert_order(STOCK_INSTRUMENT_IDS[1], price = current_bid_price_2, volume = VOLUME//2, side = 'ask', order_type = 'limit')
            
            return
        except:
            pass


def main():
    
    do_sleep = False
    sleep_duration_sec = 0.05
    exchange = Exchange()
    exchange.connect()
    
    pos = exchange.get_positions()
    for instrument_name in ["C2_GREEN_ENERGY_ETF", "C1_FOSSIL_FUEL_ETF", "C2_SOLAR_CO", "C2_WIND_LTD", "C1_GAS_INC", "C1_OIL_CORP"]:
        history = exchange.get_trade_history(instrument_name)
        if len(history) != 0:
            price = history[0].price
            for price_mod, side in [(0, "ask"), (0, "bid")]:
                exchange.insert_order(instrument_name, price = price + price_mod, volume = abs(pos[instrument_name]), side = side)

    
        while True:
            
            BASKET_INSTRUMENT_ID = 'C2_GREEN_ENERGY_ETF'
            STOCK_INSTRUMENT_IDS = ['C2_SOLAR_CO', 'C2_WIND_LTD']
            auto_trader(exchange)
    
            BASKET_INSTRUMENT_ID = 'C1_FOSSIL_FUEL_ETF'
            STOCK_INSTRUMENT_IDS = ['C1_GAS_INC', 'C1_OIL_CORP']
            auto_trader(exchange)
            if do_sleep: time.sleep(sleep_duration_sec)

        

if __name__ == '__main__':
    main()