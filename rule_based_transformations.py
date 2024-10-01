# -*- coding: utf-8 -*-

"""
Python module to link/approximate bits of words to German or Luxembourgian,
replacing them in the corpus and tokenise the corpus.
Transformation based on rules.
@author: Franka Wurps (franka.wurps@etu.unistra.fr / franka.wurps@gmail.com)
Last modified : 29/11/2023
"""
# Doing the necessary imports
from alsatian_tokeniser import RegExpTokeniser
import re
import csv
import argparse


def create_dictionary(dictionary_file_path):
    """
    Create a dictionary with the links and target links from the file_dict
    :param dictionary_file_path: als_deu_rules.txt or als_ltz_rules.txt
    :return: dictionary with the target links as keys and the links as values
    """
    # initialise a dictionary to get the regular expressions (link --> target_link)
    dictionary = {}  # key: target link, value: link
    linked_dict = {}  # key: target link, value: regular expression consisting of links
    try:
        with open(dictionary_file_path, 'r', encoding='utf8') as f:
            for line in f:
                columns = line.strip().split('\t')
                link = columns[0]
                target_link = columns[1]
                nbr_cases = int(columns[2])

                # only using the links that appeared in at least 10 cases
                if nbr_cases >= 10:
                    # Check if the key is already in the dictionary
                    if target_link in dictionary:
                        dictionary[target_link].add(link)  # Add the value to the existing set
                    else:
                        dictionary[target_link] = {link}  # Create a new set with the value
        # print(dictionary)

        # Convert the sets of links to sets of regular expression patterns
        for key, value in dictionary.items():
            pattern = r'(' + '|'.join(value) + ')'
            linked_dict[key] = {pattern}
        # print(linked_dict)

    except FileNotFoundError:
        print(f"File '{dictionary_file_path}' not found.")

    return linked_dict


def process_corpus(corpus_file_path, linked_dict, output_file_path):
    """
    :param corpus_file_path: Path to the input corpus file
    :param output_file_path: Path to the output CSV file
    :param linked_dict: Dictionary with the target links as keys and the links as values
    :return:
    """
    # Opening the output csv file here and writing the header row
    with open(output_file_path, 'w', newline='', encoding='utf8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["ID", "Alsatian_transformed"])  # Header row

        with open(corpus_file_path, 'r', encoding='utf8') as f:
            # data = f.readline()
            for i, line in enumerate(f, 1):
                columns = line.strip().split(';')
                text = columns[1]
                # print(text)

                # initialise the tokeniser and tokenise the text
                tokeniser = RegExpTokeniser()
                text_tokenized = tokeniser.tokenise(text)
                tokens = [str(token) for token in text_tokenized.get_tokens()]
                # print(tokens)
                # Initialize a list to store linked tokens
                linked_tokens = []

                # Process each token
                for token in tokens:
                    # Initialize a variable to store the modified token
                    modified_token = token

                    # Iterate over the keys and patterns in linked_dict
                    for key, pattern_set in linked_dict.items():
                        for pattern in pattern_set:
                            # Use re.search to find a match in the token
                            match = re.search(pattern, modified_token)
                            if match:
                                # Replace the matched part with the key
                                modified_token = modified_token.replace(match.group(), key)

                    # Append the modified token to the list
                    linked_tokens.append(modified_token)

                    # Apply normalize_accents to the entire list of linked_tokens
                    unaccented_tokens = [normalize_accents(token) for token in linked_tokens]

                # Join the modified tokens back into a text
                linked_text = ' '.join(unaccented_tokens)

                # Check if the last character is a space and remove it in case it is
                if linked_text[-2] == ' ':
                    linked_text = linked_text[:-2] + linked_text[-1]

                # Write the ID and linked_text as a row in the CSV file
                csvwriter.writerow([i, linked_text])


def normalize_accents(form):
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Replace links in the corpus to approximate it to german "
                                                 "or luxembourgian and tokenize it")
    parser.add_argument("-d", "--dictionary", help="Name of the file containing rules to create dictionary", required=True)
    parser.add_argument("-o", "--output", help="Name of the output file", required=True)
    args = parser.parse_args()
    dictionary_file_path = args.dictionary
    output_file_path = args.output
    corpus_file_path = '../input/smallcorpus.txt'
    process_corpus(corpus_file_path, create_dictionary(dictionary_file_path), output_file_path)

