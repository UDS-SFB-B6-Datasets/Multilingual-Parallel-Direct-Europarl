# europarl_uds
A multilingual and multitask adaption of the Europarl Corpus

## Generating the corpus
Run parallel_from_xml.py to extract parallel text from xmls

### Requirements
tqdm

### parameters
-i -> input directory: path to proceeedings xml
-o -> output file path
-s -> source language(s)
-p -> parallel language(s)
-n -> native/non-native speaker filter
-d -> direct/pivot translation(s) filter
-h -> help

#### Sample input
python parallel_from_xml.py -i proceedings/xml/ -o extracted/parallels_ns.tsv -s de en es fr it nl pt -p de en es fr it nl pt -n ns -d 0
