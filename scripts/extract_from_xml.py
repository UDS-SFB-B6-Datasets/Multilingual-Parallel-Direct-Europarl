'''
 extracts monolingual corpus from xml
'''
import argparse
import os
from typing import Optional, Union

from tqdm import tqdm

from scripts.utils import get_paths, read_xml, extract_text, extract_originals


def get_comparable(xml_dir, src_lang, parallel_langs:Optional[Union[list, str]]=None, native=None, direct=0):
    path_dict = get_paths(xml_dir, src_lang, parallel_langs)
    extracts = []
    if isinstance(src_lang, str):
        src_lang = [src_lang]

    for sl in src_lang:
        print(f"Extracting parallel text for {sl} originals")
        for filepath in tqdm(path_dict[sl][:5], position=0, leave=True):
            xml_tree = read_xml(filepath)
            extracted = extract_originals(xml_tree, sl, native, direct=direct)
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
                        parallels = extract_text(parallel_xml_tree, l, sl, native=native, direct=direct)

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
    print("Writing data to file")
    with open(file, **kwargs) as f:
        if len(data) > 0:
            header = sep.join((data[0].keys()))
        else:
            header = ""
        f.write(header+"\n")
        for line in tqdm(data, position=0, leave=True):
            f.write(sep.join(f"{x}" for x in line.values())+"\n")
    print(f"{len(data)} data written successfully")

def main(xml_dir, outfile, src_lang, parallel_langs, native, direct):
    comparable = get_comparable(xml_dir, src_lang, parallel_langs, native, direct)
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

    args = parser.parse_args()
    input_dir = args.input
    output_dir = args.output
    # lang = args.lang
    src = args.src
    parallel_langs = args.parallels
    native_speaker = args.native
    direct = args.direct
    main(input_dir, output_dir, src, parallel_langs, native_speaker, direct)


#TODO: Separate direct and pivot
#TODO: Add backtranslations
#TODO: Add machine translations