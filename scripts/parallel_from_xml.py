'''
 extracts monolingual corpus from xml
'''
import argparse
import os
from typing import Optional, Union
from datetime import datetime
from tqdm import tqdm

from utils import get_paths, read_xml, extract_text, extract_originals


def get_comparable(xml_dir, src_lang, parallel_langs:Optional[Union[list, str]]=None,
                   native=None, direct=0, start_date=None, end_date=None):
    path_dict = get_paths(xml_dir, src_lang, parallel_langs)
    extracts = []
    if isinstance(src_lang, str):
        src_lang = [src_lang]

    for sl in src_lang:
        print(f"Extracting parallel text for {sl} originals")
        for filepath in tqdm(path_dict[sl], position=0, leave=True):
            xml_tree = read_xml(filepath)
            extracted = extract_originals(xml_tree, sl, native, direct=direct,
                                          start_date=start_date, end_date=end_date)
            # print(len(extracted))

            filename = os.path.basename(filepath)
            parallel_filename = os.path.splitext(filename)[0].split(".")[0]

            if parallel_langs is not None:
                for l in parallel_langs:
                    if l == sl:
                        for k in extracted.keys():
                            extracted[k][sl] = extracted[k]['original']
                        continue
                    parallel_filepath = os.path.join(xml_dir, l, f"{parallel_filename}.{l.upper()}.xml")
                    if parallel_filepath in path_dict[l]:
                        parallel_xml_tree = read_xml(parallel_filepath)
                        parallels = extract_text(parallel_xml_tree, l, sl, native=native, direct=direct,
                                                 start_date=start_date, end_date=end_date)

                        for k in extracted.keys():
                            if k in parallels.keys():
                                extracted[k][l] = parallels[k]['text']
                            else:
                                extracted[k][l] = ""
                    else:
                        for k in extracted.keys():
                            extracted[k][l] = ""
            extracts.extend(extracted.values())
    return extracts


def write_to_tsv(data, file, sep="\t", **kwargs):
    import pandas as pd
    
    print("Writing data to file")
    if len(data) > 0:
        header = data[0].keys()
    else:
        header = None
        
    rows = []
    for line in tqdm(data, position=0, leave=True):
        rows.append(line.values())
        
    df = pd.DataFrame(rows, columns=header)
    df = df.drop_duplicates(subset=["iid"], keep=False)
    
    df.to_csv(file, sep=sep, index=False)
    
    print(f"{df} data written successfully")

def main(xml_dir, outfile, src_lang, parallel_langs, native,
         direct, start_date, end_date):
    comparable = get_comparable(xml_dir, src_lang, parallel_langs,
                                native, direct, start_date, end_date)
    outdir = os.path.dirname(outfile)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    write_to_tsv(comparable, outfile, sep="\t", mode='w', encoding="utf8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract text from xml files')
    parser.add_argument("-i", "--input", required=True, help="path to proceeedings xml directory")
    parser.add_argument("-o", "--output", required=True, help="output file path")
    # parser.add_argument("-l", "--lang", required=True, help="language of text to extract")
    parser.add_argument("-s", "--src", required=False, nargs='*', help="source/original language of text")
    parser.add_argument("-p", "--parallels", required=False, nargs='*', help="parallel language(s) to extract")
    parser.add_argument("-n", "--native", required=False, default="None",
                        help="pass [ns] to extract text from native speakers only, \
                        [nns] for text from non-native speakers only. \
                        Leave out this argument to extract everything.")
    parser.add_argument("-d", "--direct", required=False, type=int, default=0,
                        help="pass [1] to extract only texts with direct translations, \
                        [2] for texts with translations not guaranteed to be direct\
                        [0] or leave this argument out to extract everything.")
    parser.add_argument("-f", "--fromdate", required=False, default=None,
                        type=lambda s: datetime.strptime(s, '%Y%m%d'),
                        help="optional start date for time range from which to extract data.\
                             Format as YYYYMMDD")
    parser.add_argument("-t", "--todate", required=False, default=None,
                        type=lambda s: datetime.strptime(s, '%Y%m%d'),
                        help="optional end date for time range from which to extract data.\
                             Format as YYYYMMDD")

    args = parser.parse_args()
    input_dir = args.input
    output_dir = args.output
    # lang = args.lang
    src = args.src
    parallel_langs = args.parallels
    native_speaker = args.native
    direct = args.direct
    start_date = args.fromdate
    end_date = args.todate
    if start_date is not None:
        start_date = start_date.date()
    end_date = args.todate
    if end_date is not None:
        end_date = end_date.date()

    main(input_dir, output_dir, src, parallel_langs, native_speaker, direct, start_date, end_date)
