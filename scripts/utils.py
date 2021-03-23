import codecs
from glob import glob
import os
from collections import defaultdict
from typing import Optional, Union

from langdetect import detect
from lxml import etree

nationalities = {
    "bg": ['Bulgaria'],
    "es": ['Spain'],
    "cs": ['Czech Republic', 'Slovakia'],
    "da": ['Denmark'],
    "de": ['Germany', 'Austria', 'Belgium', 'Luxembourg', 'Italy'],
    "et": ['Estonia'],
    "el": ['Greece'],
    "en": ['United Kingdom', 'Ireland', 'Malta'],
    "fr": ['France', 'Belgium', 'Luxembourg', 'Italy'],
    "ga": ['Ireland', 'United Kingdom'],
    "hr": ['Croatia'],
    "it": ['Italy', 'Croatia', 'Slovenia'],
    "lv": ['Latvia'],
    "lt": ['Lituania'],
    "hu": ['Hungary'],
    "mt": ['Malta'],
    "nl": ['Netherlands'],
    "pl": ['Poland'],
    "pt": ['Portugal'],
    "ro": ['Romania'],
    "sk": ['Slovakia', 'Czech Republic'],
    "sl": ['Slovenia'],
    "fi": ['Finland'],
    "sv": ['Sweden', 'Finland'],
}


def read_xml(ifile):
    # print("Extracting from " + ifile)
    with codecs.open(ifile, 'r', 'utf8') as f:
        tree = etree.parse(f)
        root = tree.getroot()
    return root


def extract_originals(xml_file, langs:Union[list, str], native: Optional[str] = None, direct: int = 0):
    # get intervention date and language
    if isinstance(langs, str):
        langs = [langs]
    for lang in langs:
        idate, ilang = xml_file.get("id").split(".")
        extracts = defaultdict(dict)
        ilang = ilang.lower()
        lang = lang.lower()
        if ilang != lang:
            return extracts
        if (direct == 1 and int(idate[:4]) > 2003) or (direct == 2 and int(idate[:4]) < 2004):
            return extracts
        interventions = xml_file.findall('.//intervention[@id]')  # get interventions

        for el in interventions:
            iid = el.get("id")
            nationality = el.get("nationality")

            native_speaker = nationality in nationalities[ilang]
            if native == "ns" and not native_speaker:
                continue
            if native == "nns" and native_speaker:
                continue

            paragraphs = el.findall(f'.//p[@sl="{lang}"]')  # get paragraphs
            plen = len(paragraphs)
            # filter for desired source language(s)
            for i, p in enumerate(paragraphs):
                try:
                    if not detect(p.text) == ilang:
                        continue
                except:
                    pass
                else:
                    extracts[f"{idate}:{iid}:{i}:{plen}"] = {"iid": f"{idate}:{iid}:{i}:{plen}",
                                                             # "lang": ilang,
                                                             "src": ilang,
                                                             "native_speaker": int(
                                                                 nationality in nationalities[ilang]),
                                                             # "label": int(ilang != lang),
                                                             "original": p.text}
    return extracts


def extract_text(xml_file, lang, src_langs:Optional[Union[list, str]]=None, native:Optional[str]=None, direct:int=0):
    # get intervention date and language
    if src_langs is None:
        src_langs = []
    if isinstance(src_langs, str):
        src_langs = [src_langs]
    idate, ilang = xml_file.get("id").split(".")
    extracts = defaultdict(dict)
    ilang = ilang.lower()
    lang = lang.lower()
    if ilang != lang:
        return extracts
    if (direct == 1 and int(idate[:4]) > 2003) or (direct == 2 and int(idate[:4]) < 2004):
        return extracts
    interventions = xml_file.xpath('.//intervention') #get interventions

    for el in interventions:
        iid = el.get("id")
        nationality = el.get("nationality")

        if src_langs:
            for src_lang in src_langs:
                native_speaker = nationality in nationalities[src_lang]
                if native == "ns" and not native_speaker:
                    continue
                if native == "nns" and native_speaker:
                    continue

                paragraphs = el.findall(f'.//p[@sl="{src_lang}"]') #get paragraphs
                plen = len(paragraphs)

                # filter for desired source language(s)
                for i, p in enumerate(paragraphs):
                    try:
                        if not detect(p.text) == ilang:
                            continue
                    except:
                        pass
                    else:
                        extracts[f"{idate}:{iid}:{i}:{plen}"] = {"iid": f"{idate}:{iid}:{i}:{plen}",
                                                                 # "lang": ilang,
                                                                 "src": src_lang,
                                                                 "native_speaker": int(nationality in nationalities[src_lang]),
                                                                 # "label": int(ilang != src_lang),
                                                                 "text": p.text}

        else:
            paragraphs = el.findall(f'.//p[@sl]')  # get paragraphs
            plen = len(paragraphs)
            sl = p.get("sl")
            extracts[f"{idate}:{iid}:{i}:{plen}"] = {"iid": f"{idate}:{iid}:{i}:{plen}",
                                                     # "lang": ilang,
                                                     "src": sl,
                                                     "native_speaker": int(nationality in nationalities[sl]),
                                                     # "label": int(ilang != sl),
                                                     "text": p.text}
    return extracts


def extract_parallel(text:dict, xml_path:str, parallel_lang:str=None, xml_tree=None):
    idate, iid, par_no, plen = text["iid"].split(":")


def get_xml_file(path, idate, lang):
    path = os.join(path, f"{idate}.{lang.upper()}.xml")
    return read_xml(path)


def get_intervention_from_xml(xml_file, iid):
    return xml_file.find(f".//intervention[@id]={iid}")


def get_paragraphs_from_intervention(intervention, sl:Optional[str]=None):
    if sl:
        return intervention.findall(f".//p[@sl={sl}]")
    else:
        return intervention.findall(f".//p[@sl]")


def get_paragraph(paragraphs, idx):
    return paragraphs[idx]


def get_parallel(paragraph, xml_dir, lang):
    idate, iid, par_no, plen = paragraph["iid"].split(":")
    xml_file = get_xml_file(xml_dir, idate, lang)
    interventions = get_intervention_from_xml(xml_file, iid)
    return get_paragraphs_from_intervention(interventions, paragraph["src"])


def get_parallels(extracts:list, xml_path:str, parallel_lang:Optional[Union[list, str]]=None):
    parallels = []
    for paragraph in extracts.values():
        parallels.append(get_parallel(paragraph, xml_path, parallel_lang))
    return parallels


def get_xml_file_paths(file_dir):
    return glob(os.path.join(file_dir, "*.xml"))


def get_paths(xml_dir, src_lang, parallel_langs:Optional[list]=None):
    path_dict = {}
    if isinstance(src_lang, str):
        src_lang = [src_lang]
    for l in src_lang:
        path_dict[l] = get_xml_file_paths(os.path.join(xml_dir, l))
    if parallel_langs:
        for lang in parallel_langs:
            path_dict[lang] = get_xml_file_paths(os.path.join(xml_dir, lang))
    return path_dict