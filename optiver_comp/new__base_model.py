import logging
from optibook.synchronous_client import Exchange
import time

logging.getLogger('client').setLevel('ERROR')
logger = logging.getLogger(__name__)

# MANUALLY TWEAKED PARAMETERES
VERBOSE = True 
DO_SLEEP = True 
SLEEP_FOR = 0.004

# Delete the previous instruments and clear orders
def delete_orders(e, instrument):
    
    # Clear  previous orders
    outstanding = e.get_outstanding_orders(instrument)
    for a in outstanding.values(): result = a.delete_order(instrument, order_id = a.order_id)
    
    # Close any remaining open positions
    pos = e.get_positions()
    for instrument_name in ["C2_GREEN_ENERGY_ETF", "C1_FOSSIL_FUEL_ETF", "C2_SOLAR_CO", "C2_WIND_LTD", "C1_GAS_INC", "C1_OIL_CORP"]:
        history = e.get_trade_history(instrument_name)
        if len(history) != 0:
            price = history[0].price
            for price_mod, side in [(0, "ask"), (0, "bid")]:
                exchange.insert_order(instrument_name, price = price + price_mod, volume = abs(pos[instrument_name]), side = side)

# Extract information from the order book
def extract_orderbook(e, instrument):
    orderBook = e.get_last_price_book(instrument)
    asks, bids = orderBook.asks, orderBook.bids
    
    # If no bid or ask data, then no trade
    if len(orderBook.asks) == 0 or len(orderBook.bids) == 0: return
    
    # Get best available ask and bid data
    ask, bid = asks[0], bids[0]
    
    # Get price and volume of best available ask and bid
    ask_p, ask_v = ask.price, ask.volume
    bid_p, bid_v = bid.price, bid.volume
    return (ask_p, ask_v, bid_p, bid_v)
    
# Auto Trader Algorithm (Pairs Trading)
def attempt_trade(e, etf, stock_1, stock_2):
    # Get data for correlated pairs (etf and relevant stocks)
    stock_1_data = extract_orderbook(e, stock_1)
    stock_2_data = extract_orderbook(e, stock_2)
    etf_data = extract_orderbook(e, etf)
    
    # Check that all relevant data exists
    if stock_1_data and stock_2_data and etf_data:
        #(c)urrent (a)sk/(b)id (p)rice/(v)olume
        stock_1_cap, stock_1_cav, stock_1_cbp, stock_1_cbv = stock_1_data 
        stock_2_cap, stock_2_cav, stock_2_cbp, stock_2_cbv = stock_2_data
        etf_cap, etf_cav, etf_cbp, etf_cbv = etf_data
    else: return
    
    # if the volume of the trade is 1 we return as our algorithm does not deal with them
    if etf_cbv == 1: return
    
    # here we get our expected etf bid and ask price
    #(e)tf (p)lanned (b)id (p)rice
    etf_pbp = 0.5 * stock_1_cbp + 0.5 * stock_2_cbp 
    etf_pap = 0.5 * stock_1_cap + 0.5 * stock_2_cap
    # here we calculate the spread
    spread = etf_pap - etf_pbp
    
    # we get the positions of our account
    pos = e.get_positions()
    
    # the positions exist we get the position for each instrument
    if pos: etf_pos, stock_1_pos, stock_2_pos = pos[etf], pos[stock_1], pos[stock_2]
    else: etf_pos, stock_1_pos, stock_2_pos = 0, 0, 0
    
    # we calculate the volume of the trades we will make, we save the first volume calculation for later
    first_vol = min(2 * min(stock_1_cav , stock_2_cav), etf_cbv)
    vol = min(500 - abs(etf_pos), first_vol)
        
    # 1st case: The ETF has a higher bid price than the individual stock ask price
    if etf_cbp > etf_pap:
        # check if we have reached holding capactity and calculating final volume
        if vol == 0 and etf_pos == -500:  return
        elif vol == 0 and etf_pos == 500: vol = min(first_vol, 500)
        vol //= 2
        
        # long and shorting our instruments
        if VERBOSE: print(f'buying stocks at {stock_1_cap} and {stock_2_cap} V {vol} and selling etf at {etf_cbp} V {2*vol}')
        e.insert_order(stock_1, price = stock_1_cap, volume = vol, side = 'bid', order_type = 'limit')
        e.insert_order(stock_2, price = stock_2_cap, volume = vol, side = 'bid', order_type = 'limit')
        e.insert_order(etf, price = etf_cbp, volume = 2 * vol, side = 'ask', order_type = 'limit')

        
    #logging.info(f"etf ask: {current_etf_ask_price} etf as stock bid: {etf_as_stock_bid_price} etf bid: {current_etf_bid_price} etf as stock ask: {etf_as_stock_ask_price}")
    
    # 2nd case: The ETF has a lower ask price then the individual stock bid price
    # if the buy price of the etf is less than the sell price of the constructed etf then we sell individual stocks and buy the etf
    if etf_cap < etf_pbp:
        # check if we have reached holding capactity and calculating final volume
        if vol == 0 and etf_pos == 500:  return
        elif vol == 0 and etf_pos == -500: vol = min(first_vol, 500)
        vol //= 2
        
        # long and shorting our instruments
        if VERBOSE: print(f'buying etf at {etf_cap} v {2*vol} and selling stocks at {stock_1_cbp} and {stock_2_cbp} v {vol}')
        e.insert_order(etf, price = etf_cap, volume = 2 * vol, side = 'bid', order_type = 'limit')
        e.insert_order(stock_1, price = stock_1_cbp, volume = vol, side = 'ask', order_type = 'limit')
        e.insert_order(stock_2, price = stock_2_cbp, volume = vol, side = 'ask', order_type = 'limit')
            

# our main function
def main():
    # defining our list of instruments
    instruments = ["C2_GREEN_ENERGY_ETF", "C2_SOLAR_CO", "C2_WIND_LTD", "C1_FOSSIL_FUEL_ETF", "C1_GAS_INC", "C1_OIL_CORP"]
    
    # initialising our exchange and connection
    e = Exchange()
    e.connect()
    # reseting our account (closing all positions and clearing orders)
    for instrument in instruments: delete_orders(e, instrument)
    
    # main trading loop
    while True:
        
        # we check for trades and attempt to trade our instruments 
        attempt_trade(e, "C2_GREEN_ENERGY_ETF", "C2_SOLAR_CO", "C2_WIND_LTD")
        attempt_trade(e, "C1_FOSSIL_FUEL_ETF", "C1_GAS_INC", "C1_OIL_CORP")
        
        # if we are using a time lag we sleep
        if DO_SLEEP: time.sleep(SLEEP_FOR)
        
# when program runs, we run the main
if __name__ == '__main__':
    main()