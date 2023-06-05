#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2023 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import argparse
import datetime

import backtrader as bt


class St(bt.Strategy):
    params = dict(
        ma=bt.ind.SMA,
        p1=5,
        p2=15,
        limit=0.005,
        limdays=3,
        limdays2=1000,
        hold=10,
        usebracket=False,  # use order_target_size
        switchp1p2=False,  # switch prices of order1 and order2
    )

    def notify_order(self, order):
        print(
            f"{self.data.datetime.date(0)}: Order ref: {order.ref} / Type {'Buy' * order.isbuy() or 'Sell'} / Status {order.getstatusname()}"
        )

        if order.status == order.Completed:
            self.holdstart = len(self)

        if not order.alive() and order.ref in self.orefs:
            self.orefs.remove(order.ref)

    def __init__(self):
        ma1, ma2 = self.p.ma(period=self.p.p1), self.p.ma(period=self.p.p2)
        self.cross = bt.ind.CrossOver(ma1, ma2)

        self.orefs = []

        if self.p.usebracket:
            print('-' * 5, 'Using buy_bracket')

    def next(self):
        if self.orefs:
            return  # pending orders do nothing

        if self.cross > 0.0:
            if not self.position:  # crossing up

                close = self.data.close[0]
                p1 = close * (1.0 - self.p.limit)
                p2 = p1 - 0.02 * close
                p3 = p1 + 0.02 * close

                valid1 = datetime.timedelta(self.p.limdays)
                valid2 = valid3 = datetime.timedelta(self.p.limdays2)

                if self.p.switchp1p2:
                    p1, p2 = p2, p1
                    valid1, valid2 = valid2, valid1

                if self.p.usebracket:
                    os = self.buy_bracket(
                        price=p1, valid=valid1,
                        stopprice=p2, stopargs=dict(valid=valid2),
                        limitprice=p3, limitargs=dict(valid=valid3),)

                    self.orefs = [o.ref for o in os]

                else:
                    o1 = self.buy(exectype=bt.Order.Limit,
                                  price=p1,
                                  valid=valid1,
                                  transmit=False)

                    print(f'{self.datetime.date()}: Oref {o1.ref} / Buy at {p1}')

                    o2 = self.sell(exectype=bt.Order.Stop,
                                   price=p2,
                                   valid=valid2,
                                   parent=o1,
                                   transmit=False)

                    print(f'{self.datetime.date()}: Oref {o2.ref} / Sell Stop at {p2}')

                    o3 = self.sell(exectype=bt.Order.Limit,
                                   price=p3,
                                   valid=valid3,
                                   parent=o1,
                                   transmit=True)

                    print(f'{self.datetime.date()}: Oref {o3.ref} / Sell Limit at {p3}')

                    self.orefs = [o1.ref, o2.ref, o3.ref]


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed kwargs
    kwargs = {}

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):
        if a:
            strpfmt = dtfmt + tmfmt * ('T' in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    # Data feed
    data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **kwargs)
    cerebro.adddata(data0)

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval(f'dict({args.broker})'))

    # Sizer
    cerebro.addsizer(bt.sizers.FixedSize, **eval(f'dict({args.sizer})'))

    # Strategy
    cerebro.addstrategy(St, **eval(f'dict({args.strat})'))

    # Execute
    cerebro.run(**eval(f'dict({args.cerebro})'))

    if args.plot:  # Plot if requested to
        cerebro.plot(**eval(f'dict({args.plot})'))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'Sample Skeleton'
        )
    )

    parser.add_argument('--data0', default='../../datas/2005-2006-day-001.txt',
                        required=False, help='Data to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--sizer', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()
