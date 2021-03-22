'''
 extracts monolingual corpus from xml
'''
import argparse
import os
from typing import Optional, Union

from google_trans_new import google_translator
from tqdm import tqdm

from scripts.utils import get_paths, read_xml, extract_text


def get_backtranslations(xml_dir, lang, src_lang, parallel_langs:Optional[Union[list, str]]=None, native=None, direct=0):
    path_dict = get_paths(xml_dir, lang, parallel_langs)
    translator = google_translator()
    print("Extracting text")
    for filepath in tqdm(path_dict[lang][:2], position=0, leave=True):
        xml_tree = read_xml(filepath)
        extracted = extract_text(xml_tree, lang, src_lang, native)

        filename = os.path.basename(filepath)
        parallel_filename = os.path.splitext(filename)[0].split(".")[0]

        if parallel_langs is not None:
            for l in parallel_langs:
                parallel_filepath = os.path.join(xml_dir, l, f"{parallel_filename}.{l.upper()}.xml")
                if parallel_filepath in path_dict[l]:
                    parallel_xml_tree = read_xml(parallel_filepath)
                    parallels = extract_text(parallel_xml_tree, l, src_lang, native=None, direct=direct)

                    for k in extracted.keys():
                        if k in parallels.keys():
                            # print(parallels[k]['text'])
                            extracted[k][l] = translator.translate(text=extracted[k]['text'], lang_src=lang, lang_tgt=l)
                        else:
                            extracted[k][l] = ""
                else:
                    for k in extracted.keys():
                        extracted[k][l] = ""
    return extracted


def write_to_tsv(data, file, sep="\t", **kwargs):
    lines = list(data.values())
    print("Writing data to file")
    with open(file, **kwargs) as f:
        f.write(sep.join(lines[0].keys())+"\n")
        for line in tqdm(lines, position=0, leave=True):
            f.write(sep.join(f"{x}" for x in line.values())+"\n")
    print(f"{len(data.keys())} data written successfully")

def main(xml_dir, outdir, lang, src_lang, parallel_langs, native, direct):
    comparable = get_backtranslations(xml_dir, lang, src_lang, parallel_langs, native, direct)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    outfile = os.path.join(outdir, f"{lang}.tsv")
    write_to_tsv(comparable, outfile, sep="\t", mode='w', encoding="utf8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract text from xml files')
    parser.add_argument("-i", "--input", required=True, help="path to proceeedings xml directory")
    parser.add_argument("-o", "--output", required=True, help="path to output directory")
    parser.add_argument("-l", "--lang", required=True, help="language of text to extract")
    parser.add_argument("-s", "--src", required=False, help="source/original language of text")
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
    lang = args.lang
    src = args.src
    parallel_langs = args.parallels
    native_speaker = args.native
    direct = args.direct
    main(input_dir, output_dir, lang, src, parallel_langs, native_speaker, direct)


#TODO: Separate direct and pivot
#TODO: Add backtranslations
#TODO: Add machine translations