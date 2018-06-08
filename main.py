from binance.client import Client
import time
import sys, getopt
import datetime
import requests


try:
    #Read keys
    f = open("keys.txt", "r")
    key = f.readline().strip('\n')
    secret = f.readline()

    if (key or secret) == "":
        print(key+"\n")
        print(secret)
        print("Missing API Key or Secret, exit.")
        exit(1)

    client = Client(key, secret)
except Exception as e:
    print(e)
    raise
finally:
    f.close()

def marketPrice(ticker):
    return client.get_orderbook_ticker(symbol=ticker)
def orderBook(ticker):
    return client.get_order_book(symbol=ticker)

def checkConnection():
    r = requests.get('https://api.binance.com/api/v1/ping')
    print(r.status_code)
    if(r.status_code == 200):
        return True
    return False

def historicalData(pair, p):

    """
    :param pair: Pair for historical data
    :param p: interval period
    :return: kline data from interval period :param p to now.

    Example response:
    [
      [
        1499040000000,      // Open time
        "0.01634790",       // Open
        "0.80000000",       // High
        "0.01575800",       // Low
        "0.01577100",       // Close
        "148976.11427815",  // Volume
        1499644799999,      // Close time
        "2434.19055334",    // Quote asset volume
        308,                // Number of trades
        "1756.87402397",    // Taker buy base asset volume
        "28.46694368",      // Taker buy quote asset volume
        "17928899.62484339" // Ignore
      ]
    ]
    """
    interval = {
        1: Client.KLINE_INTERVAL_1MINUTE,
        5: Client.KLINE_INTERVAL_5MINUTE,
        15: Client.KLINE_INTERVAL_15MINUTE,
        30: Client.KLINE_INTERVAL_30MINUTE,
        '1h': Client.KLINE_INTERVAL_1HOUR
    }
    return client.get_historical_klines(pair, interval[p], "1 day ago UTC")

def arbitrage(btcprice, ethprice, tickerBTCp, tickerETHp):
    global quantity

    btcp = float(tickerBTCp['bidPrice']) * float(btcprice['askPrice'])
    ethp = float(tickerETHp['bidPrice']) * float(ethprice['askPrice'])

    if (btcp-ethp) > 0:
        print ('SELL TO BTC > BTC TO ETH > ETH TO TICKER')
        x = (quantity * float(tickerBTCp['bidPrice']))*0.999
        p = (float(btcprice['askPrice']) * x)
        #print 'Now we have BTC '+str(x)+' worth $'+str(p)
        y = (p / float(ethprice['askPrice']))*0.999
        #print 'Now we have ETH '+str(y)
        if quantity < (y / float(tickerETHp['askPrice']))*0.999:
            quantity = (y / float(tickerETHp['askPrice']))*0.999
            print ('Now we have NANO '+str(quantity))
        else:
            print ('Trade at loss')
    else:
        print ('SELL TO ETH > ETH TO BTC > BTC TO TICKER')
        x = (quantity * float(tickerETHp['bidPrice']))*0.999
        p = (float(ethprice['askPrice']) * x)
        #print 'Now we have ETH '+str(x)+' worth $'+str(p)
        y = (p / float(btcprice['askPrice']))*0.999
        #print 'Now we have BTC '+str(y)
        if quantity < (y / float(tickerBTCp['askPrice']))*0.999:
            quantity = (y / float(tickerBTCp['askPrice']))*0.999
            print ('Now we have NANO '+str(quantity))
        else:
            print ('Trade at loss')


def main(argv):
    global quantity

    ticker = 'REQ'
    period = 1

    try:
        opts, args = getopt.getopt(argv,"hp:c:",["period=","currency="])
    except getopt.GetoptError:
        print ('main.py -p <period> -c <currency pair>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print ('main.py -p <period> -c <currency pair>')
            sys.exit()
        elif opt in ("-p", "--period"):
            if (int(arg) in [1,10,300,900]):
                period = arg
            else:
                print ('Binance requires periods in 10,300,900 s')
                sys.exit(2)
        elif opt in ("-c", "--currency"):
            ticker = arg

    pair = ticker+'BTC'

    totalKlines = 0
    total = 0.0
    for f in historicalData(pair, 5):
        total += (float(f[2]) + float(f[3]))/2
        totalKlines += 1
    dayAverage = total/totalKlines
    print ("Average past day: "+ str (dayAverage))

    movingAvg = 0.0
    counterMovingAvg = 0

    while 1:
        pairDetails = client.get_ticker(symbol=pair)
        lastPairPrice = pairDetails['lastPrice']

        print ("{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now()) + " Period: %ss %s: %s" % (period, pair, lastPairPrice))
        movingAvg += float(lastPairPrice)
        counterMovingAvg += 1
        print ("Moving Average: "+str(movingAvg/counterMovingAvg))
        time.sleep(int(period))

if __name__ == "__main__":
    main(sys.argv[1:])