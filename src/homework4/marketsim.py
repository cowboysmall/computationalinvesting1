import sys
import csv

import datetime as dt
import pandas   as pd
import numpy    as np

import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.DataAccess as da

from collections import defaultdict


def write_output(output_file, cash):
    with open(output_file, 'w') as csvfile:
        writer = csv.writer(csvfile)
        for index, row in cash.iterrows():
            writer.writerow([index.year, index.month, index.day, row['Total']])


def read_orders(input_file):
    symbols = []
    dates   = []
    orders  = defaultdict(list)

    with open(input_file, 'rU') as csvfile:
        for line in csv.reader(csvfile):
            date = dt.datetime(int(line[0]), int(line[1]), int(line[2]), 16)
            dates.append(date)
            symbols.append(line[3])
            orders[date].append((line[3], line[4], int(line[5])))

    symbols = list(set(symbols))
    dates   = list(set(dates))
    dates.sort()

    return symbols, dates, orders


def read_prices(start, end, symbols):
    timestamps = du.getNYSEdays(start, end, dt.timedelta(hours = 16))
    dataobj    = da.DataAccess('Yahoo')

    return timestamps, dataobj.get_data(timestamps, symbols, ['close'])[0]


def create_matrices(timestamps, symbols, orders):
    trades   = pd.DataFrame(index = timestamps, columns = symbols)
    trades   = trades.fillna(0)

    holdings = pd.DataFrame(index = timestamps, columns = symbols)
    holdings = holdings.fillna(0)

    for date, items in orders.items():
        for order in items:
            if order[1] == 'Buy':
                trades[order[0]].ix[date] += -order[2]
                holdings[order[0]].ix[date:timestamps[-1]] +=  order[2]
            else:
                trades[order[0]].ix[date] +=  order[2]
                holdings[order[0]].ix[date:timestamps[-1]] += -order[2]

    return trades, holdings


def create_cash(timestamps, trades, prices, cash_value):
    cash = pd.DataFrame(index = timestamps, columns = ['Cash'])

    for timestamp in timestamps:
        cash_value += np.sum(trades.ix[timestamp] * prices.ix[timestamp], axis = 1)
        cash['Cash'].ix[timestamp] = cash_value

    return cash


def calculate_total(timestamp, cash, holdings, prices):
    prices['Cash']   = 1
    holdings['Cash'] = cash
    cash['Total']    = holdings.mul(prices, 1).sum(1)
    return cash


def main(argv):
    starting_cash = int(argv[0])
    input_file    = argv[1]
    output_file   = argv[2]

    symbols, dates, orders = read_orders(input_file)
    timestamps, prices     = read_prices(dates[0], dates[-1], symbols)
    trades, holdings       = create_matrices(timestamps, symbols, orders)
    cash                   = create_cash(timestamps, trades, prices, starting_cash)
    totals                 = calculate_total(dates[-1], cash, holdings, prices)

    write_output(output_file, totals)


if __name__ == "__main__":
    main(sys.argv[1:])
