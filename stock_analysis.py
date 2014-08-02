#!/usr/bin/env python

import argparse
import datetime
import re

import pandas as pd
import pandas.io.data
from   pandas import Series, DataFrame

print "pandas version = {}" . format(pd.__version__)

import matplotlib.pyplot as plt
import matplotlib as mpl

print "matplotlib version = {}" . format(mpl.__version__)

#################################
# global variables
################################
ticker_trend        = 0          # 0 means no trend, 1 means upward trend, 2 means downward trend
ticker_trend_tostr  = {0 : "flat", 1 : "bullish", 2 : "bearish"}
mova_days_dict      = {"10_days" : 10, "40_days" : 40, "60_days" : 60, "100_days" : 100}
compr_tup           = (10, 60)   # tuple to compare moving averages between
trade_min           = 500000     # minium trade volume to remove less liquid stocks
compr_price_tup     = (50, 100)  # price range tuple
volume_check        = 0
price_check         = 0
#starttime           = datetime.datetime(2011, 01, 1)         # start time
starttime           = datetime.datetime(2014, 01, 01)
endtime             = datetime.datetime.now()                # end time is current time
plot_yes            = 1
verbose             = 0                                      # verbose mode


##############################################################
# Main loop. Iterate through each scripts and collect data
##############################################################
def main_loop(ticker_dict):
    assert(type(ticker_dict) == dict)

    for ticker in ticker_dict.keys():
        ## get_data_yahoo throws IOError exception is the ticker synmbol is not correct.
        ## catch it.
        try:
            stock_data       = pd.io.data.get_data_yahoo(ticker, starttime, endtime)
        except IOError:
            if verbose:
                print "yahoo doesn't identify the ticker symbol {}" . format(ticker)
            continue

        ## Calculate closing prices and volume data
        stock_close_data     = stock_data["Close"]
        stock_volume_data    = stock_data["Volume"]

        ## Check for average trade volumes for previous 100 days
        if volume_check and pd.rolling_mean(stock_volume_data, 100)[-1] < trade_min:
            if verbose:
                print "100 day average trade volume for {} is below {}" . format(ticker, trade_min)
            continue

        ## Check for price range
        if price_check and ((stock_close_data[-1] < min(compr_price_tup)) or (stock_close_data[-1] > max(compr_price_tup))):
            if verbose:
                print "{} has latest closing price {}, hence is not in the defined price range" . format(ticker, stock_close_data[-1])
            continue

        process_stock_graph_series(stock_close_data, ticker_dict[ticker])

    plt.show()

##########################################################################
# Process and plot the stock movement along with some moving averages
##########################################################################
def process_stock_graph_series(obj, label):
    assert(type(obj) == pd.core.series.Series)
    mov_avg_h = {};
    local_trend = 99;

    # Populate all rolling means in a hash
    for dindex in mova_days_dict.keys():
        rolling_mean = pd.rolling_mean(obj, mova_days_dict[dindex])
        mov_avg_h[mova_days_dict[dindex]] = rolling_mean

    # Calculate local trend based on global parameters specified
    if mov_avg_h[max(compr_tup)][-1] < mov_avg_h[min(compr_tup)][-1]:
        local_trend = 1
    elif mov_avg_h[max(compr_tup)][-1] > mov_avg_h[min(compr_tup)][-1]:
        local_trend = 2
    else:
        local_trend = 99

    # Do a trend check
    # If the speicifed trend doesn't match with that specified as control parameter
    # return
    if ticker_trend != 0:
        if ticker_trend == local_trend:
            print "-------- {} shows {} trend" . format(label, ticker_trend_tostr[local_trend])
        else:
            return;
    else:
        print "-------- {} shows {} trend" . format(label, ticker_trend_tostr[local_trend])
    
    # plotting not allowed
    if not plot_yes:
        return;

    title = " [with ";
    plt.figure()
    plt.plot(obj.index.tolist(), obj.tolist(), label=label)
        
    for dindex in mova_days_dict.keys():
        rolling_mean = pd.rolling_mean(obj, mova_days_dict[dindex])
       
        x_list       = rolling_mean.index.tolist()
        y_list       = rolling_mean.tolist()
        title        = title + dindex + " "

        plt.plot(x_list, y_list, label=dindex)

    title = title + " moving average]"
    plt.grid()
    plt.title(label + title)

############################################
# main
############################################
if __name__ == '__main__':
    ticker_dict_n    = {}
    ticker_dict_t    = {}
    regex_m          = re.compile(r'\s+"|"\s+')
    regex_h          = re.compile(r'(\w+)-\w+.NS')

    parser           = argparse.ArgumentParser()
    parser.add_argument("dfile", help="data description file generated by stock_list_pull script.", type=str)
    args             = parser.parse_args()

    f = open(args.dfile, "r");
    for line in f:
       words_list = regex_m.split(line)
       ticker_dict_n[words_list[0]] = words_list[1]

    ##########
    # hack required for script names with -EQ.NS subscript (for eg. PCJEWELLERS-EQ.NS).
    # They don't work with pandas yahoo api at this time.
    # Hackish solution is to derive the corresponding BSE name, which doesn't contain -EQ
    # substring.
    for index in ticker_dict_n.keys():
        name_new  = index
        res       = regex_h.search(index)
        if res:
            name_new = res.groups()[0] + ".BO"
        ticker_dict_t[name_new] = ticker_dict_n[index]

    print "............... stock analysis parameters ...................."
    print "configured ticker trend                       = {}" . format(ticker_trend_tostr[ticker_trend])
    print "configured moving averages                    = {}" . format(mova_days_dict.keys())
    print "configured moving averages for trend analysis = {}" . format(str(compr_tup))
    print "configured duration start time                = {}" . format(starttime)
    print "configured duration end time                  = {}" . format(endtime)
    print "configured plotting allowed                   = {}" . format(plot_yes)
    print ".............................................................."
    print "\n"

    main_loop(ticker_dict_t)
