import numpy as np
import nltk
#nltk.download() #!!!Run this the first time you run your script!!!
import os
from string import punctuation
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer


test_filename = "test.txt"
class InvertedIndex:
    def __init__(self):
        self.documents = list()
        self.terms = None
        self.posting_lists = None

    def parse_document(self, file_name):
        document_text = self.read_text_file(file_name)
        self.add_document(document_text)
        processed_tokens = self.pre_process(document_text)
        print(processed_tokens)
        pass

    def add_document(self, document_content):
        self.documents.append(document_content)

    def read_text_file(self, filename):
        current_dir = os.getcwd()
        doc_path = os.path.join(current_dir, filename)
        with open(doc_path, "r") as doc:
            whole_doc = doc.read()
        return whole_doc

    def pre_process(self, document_content):
        stop_words = set(stopwords.words('english') + list(punctuation))
        tokens = nltk.word_tokenize(document_content)
        filtered_words = [word.lower() for word in tokens if not word in stop_words]
        stemmer = PorterStemmer()
        stemmed_words = [stemmer.stem(word) for word in filtered_words]
        return stemmed_words

    def update_inv_index(self):
        pass



class SearchEngine:
    def __init__(self):
        self.InvertedIndex = None

    def boolean_query(self):
        pass

    def merge_intersect(self):
        pass

    def positional_intersect(self):
        pass

if __name__ == "__main__":
    inv_index = InvertedIndex()
    inv_index.parse_document(test_filename)
    print(inv_index.documents)
