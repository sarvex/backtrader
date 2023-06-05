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
    params = (
    )

    def __init__(self):
        self.psar0 = bt.ind.ParabolicSAR(self.data0)
        self.psar1 = bt.ind.ParabolicSAR(self.data1)

    def next(self):
        txt = [
            '{:04d}'.format(len(self)),
            '{:04d}'.format(len(self.data0)),
            self.data0.datetime.datetime(),
        ]
        txt.extend(
            (
                '{:.2f}'.format(self.data0.close[0]),
                'PSAR',
                '{:04.2f}'.format(self.psar0[0]),
            )
        )
        if len(self.data1):
            txt.append('{:04d}'.format(len(self.data1)))
            txt.extend(
                (
                    self.data1.datetime.datetime(),
                    '{:.2f}'.format(self.data1.close[0]),
                    'PSAR',
                    '{:04.2f}'.format(self.psar1[0]),
                )
            )
        print(','.join(str(x) for x in txt))


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed kwargs
    kwargs = dict(
        timeframe=bt.TimeFrame.Minutes,
        compression=5,
    )

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):
        if a:
            strpfmt = dtfmt + tmfmt * ('T' in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    # Data feed
    data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **kwargs)
    cerebro.adddata(data0)

    cerebro.resampledata(data0, timeframe=bt.TimeFrame.Minutes, compression=15)

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

    parser.add_argument('--data0', default='../../datas//2006-min-005.txt',
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
