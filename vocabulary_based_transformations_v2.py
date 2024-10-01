# -*- coding: utf-8 -*-

"""
Python module to approximate bits of words to German or Luxembourgian,
replacing them in the corpus and tokenise the corpus.
Transformation based on vocabulary.
@author: Franka Wurps (franka.wurps@etu.unistra.fr / franka.wurps@gmail.com)
Last modified : 13/02/2024
"""
# Doing the necessary imports
from alsatian_tokeniser import RegExpTokeniser
import csv
import argparse
import textwrap
from difflib import SequenceMatcher
import re


def normalize_accents(form):
    """
    Normalise the accents in the form
    :param form: alsatian word not translated before in create_vocabulary
    :return: alsatian word without (alsatian) accents
    """
    form = re.sub(r'[àáâ]', 'a', form)
    # form = re.sub(r'[èéêë]', 'e', form)  # non-existing accents in german
    form = re.sub(r'[èê]', 'e', form) # non-existing accents in luxembourgian
    form = re.sub(r'[ìíîï]', 'i', form)
    form = re.sub(r'[òóô]', 'o', form)
    form = re.sub(r'[ùúû]', 'u', form)
    form = re.sub(r'[ÀÁÂ]', 'A', form)
    # form = re.sub(r'[ÈÉÊË]', 'E', form)  # non-existing accents in german
    form = re.sub(r'[ÈÊ]', 'E', form) # non-existing accents in luxembourgian
    form = re.sub(r'[ÌÍÎÏ]', 'I', form)
    form = re.sub(r'[ÒÓÔ]', 'O', form)
    form = re.sub(r'[ÙÚÛ]', 'U', form)
    form = re.sub(r'[’‘]', "'", form)
    return form


def create_vocabulary(vocabulary_file_path, language):
    """
    Creating a dictionary with the vocabulary given by files
    :param vocabulary_file_path: alsatian_french_german_lod_aligned.txt
    :return: dictionary of vocabulary
    """

    vocab_language = {}
    # define threshold, value based on standard use/value ; 1 = identical
    threshold = 0.8  # similarity ratio threshold (if the ratio is lower than this, the user will be asked to choose)

    with open(vocabulary_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Split the line by '\t'
            columns = line.strip().split('\t')

            # Check if there are multiple words in the third column (alsatian)
            alsatian_words = columns[2].split(';')

            # Check the language and get the translations
            if language == 'de':
                translations = columns[3]
            elif language == 'ltz':
                translations = columns[0]
            else:
                print("The language you entered is not supported. Please try again.")
                return None

            # Translations into German or Luxembourgish are separated by a semicolon
            translations_tab = translations.split(';')

            # Iterate through the words and create key-value pairs, putting the
            # words in lowercase and adding the POS
            for aw in alsatian_words:
                trad = ''
                # If there are multiple translations, compare them and choose
                # the most similar one
                if len(translations_tab) > 0:
                    max_sim_ratio = 0.0
                    for translation in translations_tab:
                        sim_ratio = SequenceMatcher(None, aw, translation).ratio()
                        if sim_ratio > max_sim_ratio:
                            max_sim_ratio = sim_ratio
                            trad = translation
                else:
                    trad = translations_tab[0]
                vocab_language[aw] = trad, columns[1]

    return vocab_language


def translate_token(token):
    """
    Translate the token to the target language if it is in the vocabulary
    :param token:
    :return: modified vocabulary with token in the target language
    """
    # Translate token, then normalise it and compare possible translations with SequenceMatcher.ratio() to look for
    # the orthographically closest translation.
    return vocab_language.get(token.lower(), token)


def process_corpus(corpus_file_path, vocab_language , output_file_path, column_width=50):
    """
    :param corpus_file_path: Path to the input corpus file
    :param vocab_language: Vocabulary dictionary
    :param output_file_path: Path to the output CSV file
    :param column_width: Maximum column width for text wrapping
    :return:
    """
    # Opening the output csv file here and writing the header row
    with open(output_file_path, 'w', newline='', encoding='utf8') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(["ID", "Alsatian_transformed"])  # Header row

        with open(corpus_file_path, 'r', encoding='utf8') as f:
            # data = f.readline()
            for i, line in enumerate(f, 1):
                columns = line.strip().split(';')
                text = columns[1]

                # initialise the tokeniser and tokenise the text
                tokeniser = RegExpTokeniser()
                text_tokenized = tokeniser.tokenise(text)
                tokens = [str(token) for token in text_tokenized.get_tokens()]
                # Translate each token with function translate_token
                translation = [translate_token(token) for token in tokens]

                unaccented_tokens = []
                for token, translated_token in zip(tokens, translation):
                    if isinstance(translated_token, tuple):
                        # if translation is a tuple, keep it as it is (translation found)
                        unaccented_tokens.append(translated_token[0])
                    else:
                        # if translation is a string, normalize it
                        unaccented_tokens.append(normalize_accents(token))

                # combine translated and unaccented tokens into modified text
                modified_text = ' '.join(unaccented_tokens)

                # Remove the last space if it exists
                if modified_text[-2] == ' ':
                    modified_text = modified_text[:-2] + modified_text[-1]

                # Wrap the text to the specified column width
                wrapped_text = textwrap.fill(modified_text, column_width)

                # Write the ID and linked_text as a row in the CSV file
                csvwriter.writerow([i, wrapped_text])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Transforms the corpus based on vocabulary "
                                                 "to German or Luxembourgian and tokenize it")
    parser.add_argument("-v", "--vocabulary", help="Name of the vocabulary file to create the dictionary", required=True)
    parser.add_argument("-o", "--output", help="Name of the output file", required=True)
    parser.add_argument("-l", "--language", help="Name of the target language", required=True)
    args = parser.parse_args()
    language = args.language
    vocabulary_file_path = args.vocabulary
    output_file_path = args.output
    corpus_file_path = '../input/smallcorpus.txt'

    # Call create_vocabulary and store the result in vocab_language_als
    vocab_language = create_vocabulary(vocabulary_file_path, language)

    # Call process_corpus and store the result in modified_corpus
    process_corpus(corpus_file_path, vocab_language, output_file_path)
