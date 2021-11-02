'''
 extracts monolingual corpus from xml
'''
import argparse
import os
from math import floor
from typing import Optional, Union

import numpy
import pandas
from tqdm import tqdm

from utils import get_paths, read_xml, extract_text, extract_originals
     
    
def read_corpus(filepath, src_langs:Union[list, str, None]=None, 
                parallel_langs:Union[list, str, None]=None, 
                direct=None, native=None, sep="\t"):
    
    if isinstance(parallel_langs, str):
        parallel_langs = [parallel_langs]
        
    if isinstance(src_langs, str):
        src_langs = [src_langs]
    
    cols = ["iid", "src", "native_speaker", "original"]
    
    df = pd.read_table(filepath, sep="\t")
    
    if parallel_langs is None:
        parallel_langs = list(set(df.columns.tolist()) - set(cols))
        
    if src_langs is None:
        src_langs = df.src.values().tolist()
        
    columns = cols + parallel_langs
    
    df = df[columns]
    df = df.melt(id_vars=cols, value_vars=parallel_langs, var_name="dest", value_name="text")
    df = df.dropna()
    df['direct'] = numpy.where(df.iid.str[:4].astype(int) < 2004, 1, 0)
    df['label'] = numpy.where(df.src == df.dest, 0, 1)
    if direct is not None:
        df = df[df.direct == direct]
    if native is not None:
        df = df[df.native_speaker == native]
    if src_langs:
        df = df[df.src.isin(src_langs)]
#     df = df.drop(subset, axis = 1)
    return df


def balance_classes(df, train_ratio=0.7, dev_ratio=0.15, random_state=None):
    import math
    orig = df[df.src == df.dest]
    trans = df[df.src != df.dest]
    src = orig[['src', 'dest']].agg('-'.join, axis=1).value_counts()
    dest = trans[['src', 'dest']].agg('-'.join, axis=1).value_counts()
    num_src = src.min()
    num_dest = dest.min()
    num_src = min(num_src, num_dest)
    num_src = num_src if num_src % 2 == 0 else num_src - 1
    len_src = len(src.index)
    tr_proportion = len_src - 1 if len(src.index) > 1 else 1
    num_dest = num_src // tr_proportion if tr_proportion > 1 else num_src
    
    train, dev, test = [], [], []
    
    test_ratio = 1 - (train_ratio + dev_ratio)
    num_train = math.floor(train_ratio * num_src)
    num_dev = math.floor(dev_ratio * num_src)
    
    if tr_proportion > 0:
        num_train = num_train if num_train % tr_proportion == 0 else num_train - (num_train % tr_proportion)
        num_dev = num_dev if num_dev % tr_proportion == 0 else num_dev - (num_dev % tr_proportion)
    
    for i in src.index:
        s = i.split('-')[0]
        origs = orig[(orig.src == s) & (orig.dest == s)].sample(num_src, random_state=random_state)
        tr = origs.sample(num_train, random_state=random_state)
        origs.drop(tr.index, inplace=True)
        dv = origs.sample(num_dev, random_state=random_state)
        origs.drop(dv.index, inplace=True)
        train.append(tr)
        dev.append(dv)
        test.append(origs)
        
    if len(src) > 2:
        num_train = num_train // tr_proportion
        num_dev = num_dev // tr_proportion
        
    for i in dest.index:
        s, d = i.split('-')
        tran = trans[(trans.src == s) & (trans.dest == d)].sample(num_dest, random_state=random_state)
        tr = tran.sample(num_train, random_state=random_state)
        tran.drop(tr.index, inplace=True)
        dv = tran.sample(num_dev, random_state=random_state)
        tran.drop(dv.index, inplace=True)
        train.append(tr)
        dev.append(dv)
        test.append(tran)
        
    return pd.concat(train), pd.concat(dev), pd.concat(test)


def main(infile, outfile_prefix, src_langs, parallel_langs, 
         native=None, direct=None, sep="\t", train_ratio=0.7, 
         dev_ratio=0.15, random_state=1):
    
    df = read_corpus(filepath=infile, src_langs=src_langs, 
                     parallel_langs=parallel_langs, direct=direct, 
                     native=native, sep=sep):
    train, dev, test = balance_classes(df, train_ratio=train_ratio, 
                                       dev_ratio=dev_ratio, random_state=random_state)
    
    get_stats(train)
    get_stats(dev)
    get_stats(test)
    
    train_df.to_csv(os.path.join(f"{outfile_prefix}_train.tsv"), sep="\t", index=False)
    dev_df.to_csv(os.path.join(f"{outfile_prefix}_dev.tsv"), sep="\t", index=False)
    test_df.to_csv(os.path.join(f"{outfile_prefix}_test.tsv"), sep="\t", index=False)
    print(f"Data split successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract text from xml files')
    parser.add_argument("-i", "--input", required=True, help="path to input data file")
    parser.add_argument("-o", "--output", required=True, help="output file path and name prefix")
    parser.add_argument("-s", "--src", required=False, nargs='*', help="source/original language of text")
    parser.add_argument("-p", "--parallels", required=False, nargs='*', help="parallel language(s) to extract")
    parser.add_argument("-n", "--native", required=False, type=int, choices=[0, 1],
                        help="pass [1] to extract text from native speakers only, \
                        [0] for text from non-native speakers only. \
                        Leave out this argument to extract everything.")
    parser.add_argument("-d", "--direct", required=False, type=int, choices=[0, 1],
                        help="pass [1] to extract only texts with direct translations, \
                        [0] for texts with translations not guaranteed to be direct.\
                        Leave this argument out to extract everything.")
    parser.add_argument("-t", "--train_ratio", required=False, type=float, default=0.7,
                        help="fraction of data for train split. Test size is calculated from train and dev splits.")
    parser.add_argument("-v", "--dev_ratio", required=False, type=float, default=0.15,
                        help="fraction of data for dev split. Test size is calculated from train and dev splits.")
    parser.add_argument('-r', "--random_state", action='store_true',
                        help="if not specified, originals are kept for each translation")

    args = parser.parse_args()
    infile = args.input
    outfile_prefix = args.output
    src_langs = args.src
    parallel_langs = args.parallels
    native = args.native
    direct = args.direct
    train_ratio = args.train_ratio
    dev_ratio = args.dev_ratio
    random_state = args.random_state

    main(infile=infile, outfile_prefix=outfile_prefix, 
         src_langs=src_langs, parallel_langs=parallel_langs, 
         native=native, direct=direct, sep=sep, train_ratio=train_ratio, 
         dev_ratio=dev_ratio, random_state=random_state)

#TODO: Create splits
