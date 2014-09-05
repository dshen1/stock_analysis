#!/usr/bin/env python

import argparse
import datetime
import re
import pickle
import sys

import pandas as pd
import pandas.io.data
from   pandas import Series, DataFrame

sys.path.append(".")
import analysis

############################################
# main
############################################
if __name__ == '__main__':
    params_local     = analysis.parameters()

    ticker_dict_n    = {}
    ticker_dict_t    = {}
    regex_m          = re.compile(r'([\w\.\-]+)[ \t\r\f\v]+"([ \w\W\t\r\f\v\-]+)"')       # match for valid line
    regex_h          = re.compile(r'(\w+)-\w+.NS')          # match for date format on command line
    regex_c          = re.compile(r'^#')                    # Match format for comment

    parser           = argparse.ArgumentParser()
    parser.add_argument("dfile", help="data description file generated by stock_list_pull script.", type=str)

    parser.add_argument("--vmin",     help="minimum volume limit",                      type=int)
    parser.add_argument("--pmin",     help="minimum price limit",                       type=int)
    parser.add_argument("--pmax",     help="maximum price limit",                       type=int)
    parser.add_argument("--tstart",   help="start time (day)",                          type=str)
    parser.add_argument("--tend",     help="end time (day)",                            type=str)
    parser.add_argument("--pfile",    help="pickle file",                               type=str)
    parser.add_argument("--trend",    help="ticker trend (0=all, 1=up, 2=down)",        type=int)
    parser.add_argument("--regex",    help="perl compatible regex for scrip search",    type=str)
    parser.add_argument("--plot",     help="plot graphs",                               action='store_true')
    parser.add_argument("--verbose",  help="verbose option",                            action='store_true')

    args             = parser.parse_args()

    # open description file
    f = open(args.dfile, "r");
    for line in f:
        # This means we encountered a comment
        if regex_c.match(line):
            continue

        res = regex_m.search(line)
        if res:
            ticker_dict_n[res.groups()[0]] = res.groups()[1]
        else:
            # This line is not recognised
            continue

    # check if pickle file was provided & redirect function pointer for
    # geting ticker values
    if args.pfile:
        params_local.set_input_pickle_file(args.pfile)

    # Check price limits
    if args.pmin:
        params_local.set_price_min(args.pmin)
    if args.pmax:
        params_local.set_price_max(args.pmax)
    # check trade limit
    if args.vmin:
        params_local.set_volume_min(args.vmin)

    # check time
    if args.tstart:
        params_local.set_date_start(args.tstart)
    if args.tend:
        params_local.set_date_end(args.tend)

    # trend
    if args.trend:
        params_local.set_ticker_trend(args.trend)

    # plot var
    if args.plot:
        params_local.enable_plot()

    # verbose
    if args.verbose:
        params_local.enable_verbose()

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

    # Clear the original list
    ticker_dict_n = {}

    # Check for the any passed regex
    if args.regex:
        regex_c      = re.compile('{}' . format(args.regex))
        for index in ticker_dict_t.keys():
            if regex_c.match(index) or regex_c.match(ticker_dict_t[index]):
                ticker_dict_n[index] = ticker_dict_t[index]
    else:
        ticker_dict_n = ticker_dict_t


    print "pandas version                                = {}" . format(pd.__version__)
    params_local.print_info()

    # Initialize parameters
    analysis.analysis_class.init_params(params_local)

    for index in ticker_dict_n:
        a = analysis.analysis_class(index)
        if a.check_price_range() and a.check_volumes() and a.check_trend():
            print "--------------> {} is following {} trend." . format(index, a.get_trend())


    ## Dump global data structure to pickle file
    #if pickle_file_passed == 0:
    #    pickle.dump(glb_data_struct, open(args.dfile + ".pkl", "wb"))
