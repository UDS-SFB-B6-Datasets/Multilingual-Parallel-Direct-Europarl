'''
 extracts monolingual corpus from xml
'''
import argparse
import os
from math import floor
from typing import Union

import numpy
import pandas as pd


def read_corpus(filepath, src_langs:Union[list, str, None]=None, 
                parallel_langs:Union[list, str, None]=None, 
                direct=None, native=None, sep="\t"):
    
    if isinstance(parallel_langs, str):
        parallel_langs = [parallel_langs]
        
    if isinstance(src_langs, str):
        src_langs = [src_langs]
    
    cols = ["iid", "src", "native_speaker", "original"]
    
    print("Reading data")
    df = pd.read_table(filepath, sep="\t")
    
    if parallel_langs is None:
        parallel_langs = list(set(df.columns.tolist()) - set(cols))
        
    if src_langs is None:
        src_langs = df.src.values().tolist()
        
    columns = cols + parallel_langs
    
    df = df[columns]
    df = df.dropna()
    
    df['direct'] = numpy.where(df.iid.str[:4].astype(int) < 2004, 1, 0)
    if direct is not None:
        print("Filtering translation type: direct or undefined")
        df = df[df.direct == direct]
    if native is not None:
        print("Applying (non) native speaker filter")
        df = df[df.native_speaker == native]
    if src_langs:
        print("Extracting selected source languages and parallels")
        df = df[df.src.isin(src_langs)]
#     df = df.drop(subset, axis = 1)
    return df


def balance_classes(df, train_ratio=0.7, dev_ratio=0.15, random_state=None):
    import math
    print("Creating train-dev-test splits")
    src = df.src.value_counts()
    num_src = src.min()
    
    train, dev, test = [], [], []
    
    test_ratio = 1 - (train_ratio + dev_ratio)
    num_train = math.floor(train_ratio * num_src)
    num_dev = math.floor(dev_ratio * num_src)
    
    for sl in src.index:
        source_lang = df[df.src == sl].sample(num_src, random_state=random_state)
        tr = source_lang.sample(num_train, random_state=random_state)
        source_lang.drop(tr.index, inplace=True)
        dv = source_lang.sample(num_dev, random_state=random_state)
        source_lang.drop(dv.index, inplace=True)
        train.append(tr)
        dev.append(dv)
        test.append(source_lang)
    
    print("Train-dev-test splits created")
    return pd.concat(train), pd.concat(dev), pd.concat(test)


def main(infile, outfile_prefix, src_langs, parallel_langs, 
         native=None, direct=None, sep="\t", train_ratio=0.7, 
         dev_ratio=0.15, random_state=1):
    
    df = read_corpus(filepath=infile, src_langs=src_langs, 
                     parallel_langs=parallel_langs, direct=direct, 
                     native=native, sep=sep)
    train_df, dev_df, test_df = balance_classes(df, train_ratio=train_ratio, 
                                       dev_ratio=dev_ratio, random_state=random_state)
    
    print(f"Saving splits to {outfile_prefix}_*.tsv")
    train_df.to_csv(os.path.join(f"{outfile_prefix}_train.tsv"), sep="\t", index=False)
    dev_df.to_csv(os.path.join(f"{outfile_prefix}_dev.tsv"), sep="\t", index=False)
    test_df.to_csv(os.path.join(f"{outfile_prefix}_test.tsv"), sep="\t", index=False)
    print(f"Data saved successfully")


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
    parser.add_argument('-r', "--random_state", required=False, type=int, default=1,
                        help="seed for randomly sampling examples"),
    parser.add_argument("--sep", required=False, default="\t", help="delimiter used in input file")

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
    sep = args.sep

    main(infile=infile, outfile_prefix=outfile_prefix, 
         src_langs=src_langs, parallel_langs=parallel_langs, 
         native=native, direct=direct, sep=sep, train_ratio=train_ratio, 
         dev_ratio=dev_ratio, random_state=random_state)
