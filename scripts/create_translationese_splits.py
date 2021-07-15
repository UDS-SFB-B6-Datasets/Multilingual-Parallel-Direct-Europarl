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

from scripts.utils import get_paths, read_xml, extract_text, extract_originals


def read_table_with_pandas(filepath, **kwargs):
    df = pandas.read_table(filepath, **kwargs)
    return df


def read_corpus(filepath, parallel_langs:Union[list, str, None]=None,
                native=None, remove_originals=False, **kwargs):
    if isinstance(parallel_langs, str):
        parallel_langs = [parallel_langs]

    if parallel_langs is not None:
        subset = ["iid", "src"]
        if not remove_originals:
            subset.append("original")
        if native is not None:
            subset.append("native_speaker")
        subset.extend(parallel_langs)
        df = read_table_with_pandas(filepath, usecols=subset, **kwargs)

    else:
        subset = []
        if remove_originals:
            subset.append("original")
        if native is None:
            subset.append("native_speaker")
        df = read_table_with_pandas(filepath, **kwargs)
        df = df.drop(subset, axis = 1)
    return df


def filter(df, src_langs:Optional[list]=None, native=None, direct=0):
    if direct == 1:
        df = df[df.iid.str[:4].astype(int) < 2004]
    elif direct == 2:
        df = df[df.iid.str[:4].astype(int) > 2003]
    if native is not None:
        df = df[df.native_speaker == native]
    if src_langs:
        df = df[df.src.isin(src_langs)]
    return df

def add_translationese_label(df, parallel_langs:Optional[list], remove_originals=False):
    sub = ["iid", "src"]
    if not remove_originals:
        sub.append("original")
    id_vars = []
    id_vars.extend(sub)
    if parallel_langs is None:
        parallel_langs = list(set(df.columns.tolist()) - set(sub))
    df = df.melt(id_vars=id_vars, value_vars=parallel_langs, var_name="dest", value_name="text")
    df['label'] = numpy.where(df.src == df.dest, 0, 1)
    return df

def get_data(filepath, src_langs:Union[list, str, None]=None,
             parallel_langs:Union[list, str, None]=None, native=None, direct=0, remove_originals=False, **kwargs):
    if "usecols" in kwargs.keys():
        subset = kwargs.pop("usecols")

    df = read_corpus(filepath, parallel_langs, native, **kwargs)
    df = filter(df, src_langs, native, direct)
    df = add_translationese_label(df, parallel_langs, remove_originals)
    return df.dropna()


def get_proportions(L, proportions:list=[0.7, 0.15]):
    if sum(proportions) > 1:
        raise Exception("Sum of train and dev ratios should be <= 1")
    tr, dev = tuple(proportions)
    train_size = floor(L * tr)
    dev_size = floor(L * dev)
    test_size = L - train_size - dev_size
    return train_size, dev_size, test_size


def split(df, n_train, n_dev, n_test):
    train = df.sample(n_train)
    df = df.drop(train.index)
    dev = df.sample(n_dev)
    test = df.drop(dev.index).sample(n_test)
    return train, dev, test


def main(infile, outdir, src_langs, parallel_langs, native, direct,
         tsplit, dsplit, remove_originals, **kwargs):
    df = get_data(infile, src_langs, parallel_langs, native, direct, remove_originals, **kwargs)
    
    originals = df[df.src == df.dest]
    translations = df[df.src != df.dest]
    series_o = originals['src'] + originals['dest']
    series_t = translations.src + translations.dest
    O = (series_o).value_counts().min()
    P = (series_t).value_counts().min()

    a, b, c = get_proportions(O, [tsplit, dsplit])
    d, e, f = get_proportions(P, [tsplit, dsplit])

    L = len(parallel_langs)
    if L > 1:
        L -= 1

    O = a + b + c
    P = d + e + f

    if O < L * P:
        P = O//L
    if a < L * d:
        d = a//L
    if b < L * e:
        e = b//L
    if c < L * f:
        f = c//L
    a = d * L
    b = e * L
    c = f * L
    O = P * L

    a, b, c = (get_proportions(O))
    train_splits, dev_splits, test_splits = {}, {}, {}
    for k in (series_o).unique():
        train_splits[k], dev_splits[k], test_splits[k] = split(originals[series_o == k].sample(O), a, b, c)

    a, b, c = (get_proportions(P))
    for k in (series_t).unique():
        train_splits[k], dev_splits[k], test_splits[k] = split(translations[series_t == k].sample(P), d, e, f)

    train_df = pandas.concat(train_splits.values())
    dev_df = pandas.concat(dev_splits.values())
    test_df = pandas.concat(test_splits.values())

    outdir = os.path.dirname(outdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    train_df.to_csv(os.path.join(outdir, "train.tsv"), sep="\t", index=False)
    dev_df.to_csv(os.path.join(outdir, "dev.tsv"), sep="\t", index=False)
    test_df.to_csv(os.path.join(outdir, "test.tsv"), sep="\t", index=False)
    print(f"Data split successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract text from xml files')
    parser.add_argument("-i", "--input", required=True, help="path to input data file")
    parser.add_argument("-o", "--output", required=True, help="output directory")
    # parser.add_argument("-l", "--lang", required=True, help="language of text to extract")
    parser.add_argument("-s", "--src", required=False, nargs='*', help="source/original language of text")
    parser.add_argument("-p", "--parallels", required=False, nargs='*', help="parallel language(s) to extract")
    parser.add_argument("-n", "--native", required=False, type=int, choices=[0, 1],
                        help="pass [1] to extract text from native speakers only, \
                        [0] for text from non-native speakers only. \
                        Leave out this argument to extract everything.")
    parser.add_argument("-d", "--direct", required=False, type=int, default=0, choices=[0, 1, 2],
                        help="pass [1] to extract only texts with direct translations, \
                        [2] for texts with translations not guaranteed to be direct\
                        [0] or leave this argument out to extract everything.")
    parser.add_argument("-t", "--train_split", required=False, type=float, default=0.7,
                        help="fraction of data for train split. Test size is calculated from train and dev splits.")
    parser.add_argument("-v", "--dev_split", required=False, type=float, default=0.15,
                        help="fraction of data for dev split. Test size is calculated from train and dev splits.")
    parser.add_argument('-r', "--remove", action='store_true',
                        help="if not specified, originals are kept for each translation")

    args = parser.parse_args()
    infile = args.input
    outdir = args.output
    # lang = args.lang
    src_langs = args.src
    parallel_langs = args.parallels
    native = args.native
    direct = args.direct
    tsplit = args.train_split
    dsplit = args.dev_split
    remove_originals = args.remove

    main(infile, outdir, src_langs, parallel_langs, native, direct,
         tsplit, dsplit, remove_originals)

#TODO: Create splits
