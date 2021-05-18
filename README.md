# Multilingual Parallel Direct Europarl
A multilingual and multitask adaption of the Europarl Corpus

## Requirements
codecs\
glob\
langdetect\
lxml

## Generating the corpus
Run parallel_from_xml.py to extract parallel text from xmls

### Requirements
tqdm

### parameters
-i -> input directory: path to proceeedings xml\
-o -> output file path\
-s -> source language(s)\
-p -> parallel language(s)\
-n -> native/non-native speaker filter\
-d -> direct/undefined translation(s) filter\
-f -> start date (optional)\
-t -> end date (optional)\
-h -> help

#### Sample command
python parallel_from_xml.py -i proceedings/xml/ -o extracted/parallels_ns.tsv -s de en es fr it nl pt -p de en es fr it nl pt -n ns -d 0 -f 19990721 -t 19990723


## Create Translationese Dataset
This is created using the output of the extracted parallel corpus
Run create_translationese_splits.py to create train, dev and test splits.

### Requirements
tqdm\
numpy\
pandas

### parameters
-i -> input file\
-o -> output directory\
-s -> source language(s)\
-p -> parallel language(s)\
-n -> native/non-native speaker filter\
-d -> direct/undefined translation(s) filter\
-t -> fraction of data for train split\
-v -> fraction of data for dev split\
-r -> flag to either keep or retain original texts as part of dataset\
-h -> help

#### Sample command
python create_translationese_splits.py -i extracted/parallels_ns_undefined.tsv -o tr_splits_ns_undefined/ -s de en es fr it pt nl -p en es de fr it pt nl -n 1 -d 2 -t 0.7 -v 0.15

## Create Machine Translation Dataset
This is created using the output of the extracted parallel corpus
Run create_parallel_splits.py to create train, dev and test splits.

### Requirements
tqdm\
numpy\
pandas

-i -> input file\
-o -> output directory\
-s -> source language(s)\
-p -> parallel language(s)\
-n -> native/non-native speaker filter\
-d -> direct/undefined translation(s) filter\
-t -> fraction of data for train split\
-v -> fraction of data for dev split\
-r -> flag to either keep or retain original texts as part of dataset\
-h -> help

#### Sample command
python create_parallel_splits.py -i extracted/parallels_direct.tsv -o mt_splits_direct/ -s de en es fr it pt nl -p en es de fr it pt nl -n 0 -d 1 -t 0.7 -v 0.15


If you use this work please cite:

@InProceedings{AmponsahEtal:MOTRA:2021,
      author = {Amponsah-Kaakyire, Kwabena and Pylypenko, Daria and Espa{\~n}a-Bonet, Cristina and van Genabith, Josef},
      title = "Do not Rely on Relay Translations: Multilingual Parallel Direct Europarl",
      booktitle = "Proceedings of the Workshop on Modelling Translation: Translatology in the Digital Age (MoTra21)",
      month = may,
      year = "2021",
      address = "Iceland (Online)",
      publisher = "International Committee on Computational Linguistics",
      url = "https://www.aclweb.org/anthology/",
      pages = "--"
}
