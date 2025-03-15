
import os
import tqdm.auto as tqdm
import yfinance as yf
import datetime as dt
import pandas as pd
import numpy as np
from pathlib import Path

from loader import get_processed_history, load_history


SNP_LIST_TSV = Path('resources/sp500_250312.tsv')
OUTPUT_DIR = Path('data')


def load_snp500(path, sep='\t'):
    snp_list = pd.read_csv(path, sep=sep)
    return snp_list

def main():
    snp_list = load_snp500(SNP_LIST_TSV)
    print(len(snp_list))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    it = tqdm.tqdm((snp_list['Symbol']))
    for i, sym in enumerate(it):
        if sym in ('BRK.B', 'BF.B'):
            sym = sym.replace('.', '-')
        elif sym in ('CTAS',):
            continue

        hist = load_history(sym, refresh=True)


if __name__ == '__main__':
    main()

