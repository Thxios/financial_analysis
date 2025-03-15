

import os
import re
import glob
import yfinance as yf
import datetime as dt
import pandas as pd
import numpy as np
from pathlib import Path



DATA_DIR = Path('data')
HIST_START = dt.date(2005, 1, 1)
HIST_END = dt.date(2025, 3, 14)


def parse_name(s):
    pat = r'([A-Z\-.]{1,})_([0-9]{6})-([0-9]{6}).csv'
    search = re.search(pat, s)
    if search is None:
        return None
    try:
        sym, st, ed = search.groups()
    except ValueError:
        return None
    return {
        'sym': sym,
        'st': st,
        'ed': ed
    }


def get_price_history_raw(
        sym,
        start=HIST_START,
        end=HIST_END,
        interval='1d',
):
    ticker = yf.Ticker(sym)
    hist_raw: pd.DataFrame = ticker.history(
        interval=interval,
        start=start,
        end=end,
    )
    if hist_raw.empty:
        raise ValueError(f'invalid ticker {sym}')
    return hist_raw


def adjust_dividend_reinvest(df: pd.DataFrame, price_col='Close', div_col='Dividends'):
    cur_share = 1
    adj_ = []
    shares_ = []
    for dividend, price in zip(df[div_col], df[price_col]):
        if dividend > 0:
            cur_share += (cur_share * dividend) / price

        adj_.append(cur_share * price)
        shares_.append(cur_share)

    return adj_, shares_


def process_history(hist: pd.DataFrame):
    hist.drop(['Stock Splits', 'Capital Gains'], axis=1, inplace=True, errors='ignore')

    hist.index = pd.to_datetime(hist.index.date)
    hist.index.name = 'date'
    rename = lambda s: s.lower().replace(' ', '_')
    hist.columns = map(rename, hist.columns)

    hist['hlc3'] = (hist['open'] + hist['high'] + hist['close']) / 3
    adj, shares = adjust_dividend_reinvest(hist, 'hlc3', 'dividends')
    hist['adj_hlc3'] = adj
    hist['shares'] = shares

    hist.drop(['dividends'], axis=1, inplace=True, errors='ignore')
    return hist


def get_processed_history(sym):
    return process_history(get_price_history_raw(sym))


def load_history(sym, save=True, refresh=False):
    ext = not refresh and glob.glob(str(DATA_DIR / f'{sym}_*.csv'))
    if ext:
        # print('read ext')
        def key(s):
            par = parse_name(s)
            return par['ed'] if par else ''

        latest = max(ext, key=key)
        df = pd.read_csv(latest, index_col='date', parse_dates=['date'])
    else:
        # print('load new')
        df = get_processed_history(sym)
        if save:
            st, ed = df.index.min(), df.index.max()
            name = f"{sym}_{st.strftime('%y%m%d')}-{ed.strftime('%y%m%d')}"
            df.to_csv(DATA_DIR / f'{name}.csv')

    return df



def _main():
    target = [
        'SPY',  # s&p 500
        'SCHD',
        'QQQ',  # 나스닥 100
        'VTI',  # 뱅가드 미국전체
        'VUG',  # 뱅가드 성장주
        'VIV',  # 뱅가드 가치주
        'VGK',  # 뱅가드 유럽주
        'SOXX', # 반도체지수
        'GLD',  # 금
        'BND',  # 뱅가드 미국채
        'TLT',  # 장기 미국채
    ]
    for sym in target:
        a = load_history(sym, refresh=True, save=True)
        print(f'=== {sym} ===')
        print(a)
        print(a.info())
        print(a.index.dtype)
        print('\n')
        # b = load_history(sym, refresh=False, save=False)
        # print(b)
        # print(b.info())
        # print(b.index.dtype)



if __name__ == '__main__':
    _main()
