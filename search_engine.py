import numpy as np
import nltk
# nltk.download() #!!!Run this the first time you run your script!!!
import os
from string import punctuation
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import operator
import pandas as pd
import pickle
from sklearn.metrics import f1_score, precision_score, recall_score, \
    accuracy_score
from sklearn.model_selection import StratifiedShuffleSplit


"""
    Stores term weight, term frequency and document ids for
    Inverted Index usage.
"""


class Document:
    def __init__(self, document_id, *args, store_term_weights=False):
        """
        Stores document_id, position if store_term_weights is False and
        term weights if chosen to be stored
        :param document_id: Unique ID of each document
        :param args: Position of a term if term weights are not stored
        :param store_term_weights: Store term weights or positions
        """
        self.id = document_id
        self.positions = []
        if store_term_weights is True:
            self.term_weight = 1
        else:
            self.positions = []
            self.add_position(args[0])

    def add_position(self, position):
        """
        Add another position of a term to storage
        :param position: Position of the term
        :return: None
        """
        self.positions.append(position)

    def increment_frequency(self):
        """
        Increment term frequency of the document
        :return: None
        """
        self.term_weight += 1


""" Parent class for InvertedIndex and SearchEngine.
Deals with pre-processing queries and document text as well as retrieving
posting lists."""


class DocumentProcessing():

    def pre_process(self, document_content, remove_stopwords=False,
                    stemming=True):
        """
        Tokenize, remove stopwords, stem tokens
        :param document_content: Entire document text
        :param remove_stopwords: If stop words should be removed
        :param stemming: If tokens should be stemmed
        :return: Processed tokens
        """
        preprocessed_tokens = nltk.word_tokenize(document_content)
        preprocessed_tokens = [word.lower() for word in preprocessed_tokens]
        if remove_stopwords:
            stop_words = set(stopwords.words('english') + list(punctuation))
            preprocessed_tokens = [word for word in preprocessed_tokens
                                   if not word in stop_words]
        if stemming:
            stemmer = PorterStemmer()
            preprocessed_tokens = [stemmer.stem(word)
                                   for word in preprocessed_tokens]
        return preprocessed_tokens

    def get_postings_list(self, term):
        """
        Retrieve postings list of a particular term
        :param term: Term whose postings list is required
        :return: Postings list of term supplied
        """
        term_index = self.terms.index(term)
        return self.posting_lists[term_index]


""" Inverted Index used to store contents of documents after parsing and
preprocessing them. """


class InvertedIndex(DocumentProcessing):
    def __init__(self, document_loc=None, purpose="bs",
                 is_dir=True, auto_load=True):
        """
        Load documents for directory, update inverted index and split into
        testing and training set if auto load is True.
        :param document_loc: Location of documents.
        :param purpose: If the index will be used for boolean search
        of vector space model.
        :param is_dir: If the given document location is a directory.
        :param auto_load: If the documents should be automatically loaded.
        """
        self.num_documents = 0
        self.documents = list()
        self.terms = list()
        self.posting_lists = list()
        self.purpose = purpose
        self.auto_load = auto_load
        self.classifier_df = ClassifierDataFrame()
        self.docLengths = dict()
        if self.auto_load:
            if self.purpose == "vsm":
                if is_dir:
                    self.load_data(document_loc, ignore_stopwords=False)
                else:
                    self.load_data(document_loc,
                                   ignore_stopwords=False, is_text=True)
                self.calculate_tfidf()
            else:
                if is_dir:
                    self.load_data(document_loc)
                else:
                    self.load_data(document_loc, is_text=True)
            self.classifier_df.split_training_testing_set(t_size=0.1)

    def save_index(self, filename):
        """
        Save Inverted Index as a pickle object to be retrieved and reused later
        :param filename: Intended name for the pickle file including
        absolute path
        :return: None
        """
        pickle.dump(self, open(filename, "wb"))

    def load_index(filename):
        """
        Load Inverted Index from pickled objects
        :param filename: Absolute path of pickled file
        :return: Indexed Inverted Index.
        """
        obj = pickle.load(open(filename, "rb"))
        return obj
    load_index = staticmethod(load_index)

    def load_data(self, directory, ignore_stopwords=True, is_text=False):
        """
        Go through each document in the directory specified
        and load it into the inverted index.
        :param directory: Location of documents or document content
        :param ignore_stopwords: If stop words should be kept or removed.
        :param is_text: If input is text of document location
        :return: None
        """
        if is_text:
            self.parse_document(directory, ignore_stopwords, is_text=True)
        else:
            current_directory = os.getcwd()
            doc_directory = os.path.join(current_directory, directory)
            for class_ in os.listdir(doc_directory):
                class_docs_loc = os.path.join(doc_directory, class_)
                if os.path.isdir(class_docs_loc):
                    for class_document in os.listdir(class_docs_loc):
                        if not class_document.startswith("."):
                            doc_location = os.path.join(class_docs_loc,
                                                        class_document)
                            self.classifier_df.add_document(doc_location,
                                                            class_)
                            self.parse_document(doc_location, ignore_stopwords)

    def assign_document_id(self):
        """
        Assign a new unique document ID to the document
        :return: Unique Document ID
        """
        self.num_documents += 1
        return self.num_documents - 1

    def parse_document(self, file_name, ignore_stopwords, is_text=False):
        """
        Parse a document and update inverted index with its terms.
        :param file_name: Path to document
        :param ignore_stopwords: If stopwords should be excluded or included
        :param is_text: If document give in text of a path
        :return: None
        """
        document_id = self.assign_document_id()
        if is_text:
            document_text = file_name
        else:
            document_text = self.read_text_file(file_name)
        self.add_document(document_text)
        if ignore_stopwords is True:
            processed_tokens = self.pre_process(document_text,
                                                remove_stopwords=True,
                                                stemming=True)
        else:
            processed_tokens = self.pre_process(document_text, stemming=True)
        self.update_inv_index(processed_tokens, document_id)

    def add_document(self, document_content):
        """
        Add document's entire content as a whole to inverted index.
        :param document_content: Content of document as text.
        :return: None
        """
        self.documents.append(document_content)

    def read_text_file(self, filename):
        """
        Open text file and read its contents into an entire string
        :param filename: Path to file
        :return: Text content of document
        """
        current_dir = os.getcwd()
        doc_path = os.path.join(current_dir, filename)
        try:
            with open(doc_path, "r") as doc:
                whole_doc = doc.read()
        except:
            print("Error reading file: {}".format(filename))
            return None
        return whole_doc

    def update_inv_index(self, processed_tokens, document_id):
        """
        Update Inverted Index with new document contents
        :param processed_tokens: Processed tokens of new document's content
        :param document_id: Unique document ID of the new document
        :return: None
        """
        for token_index in range(0, len(processed_tokens)):
            if processed_tokens[token_index] not in self.terms:
                self.terms.append(processed_tokens[token_index])
                new_postings_list = list()
                if self.purpose == "vsm":
                    new_doc = Document(document_id, store_term_weights=True)
                else:
                    new_doc = Document(document_id, token_index + 1)
                new_postings_list.append(new_doc)
                self.posting_lists.append(new_postings_list)
            else:
                existing_posting_list = self.get_postings_list(
                    processed_tokens[token_index])
                doc_exists = False
                for i in range(len(existing_posting_list)):
                    if existing_posting_list[i].id == document_id:
                        if self.purpose == "vsm":
                            existing_posting_list[i].increment_frequency()
                        else:
                            existing_posting_list[i].add_position(
                                token_index + 1)
                        doc_exists = True
                if doc_exists is False:
                    if self.purpose == "vsm":
                        new_doc = Document(
                            document_id, store_term_weights=True)
                    else:
                        new_doc = Document(document_id, token_index + 1)
                    existing_posting_list.append(new_doc)

    def calculate_tfidf(self):
        """
        Calculate term frequency * inverted document frequency for each term
        and update each document in respective postings list with the new
        term weight.
        :return: None
        """
        total_num_docs = len(self.documents)
        for term in self.terms:
            term_posting_list = self.get_postings_list(term)
            num_docs_term = len(term_posting_list)
            invert_doc_frequency = np.log10(total_num_docs/(num_docs_term*1.0))
            for indiv_doc in term_posting_list:
                tfidf = (1 + np.log10(indiv_doc.term_weight)) \
                    * invert_doc_frequency
                indiv_doc.term_weight = tfidf
                if indiv_doc.id in self.docLengths.keys():
                    self.docLengths[indiv_doc.id] += np.square(tfidf)
                else:
                    self.docLengths[indiv_doc.id] = np.square(tfidf)
        for i in self.docLengths.keys():
            self.docLengths[i] = np.sqrt(self.docLengths[i])

    def __repr__(self):
        """
        Representable form of inverted index
        :return: String format of object to display
        """
        output = ""
        for i in range(0, len(self.terms)):
            output += "{:>12}\t".format(self.terms[i])
            doclist = self.posting_lists[i]
            for j in range(0, len(doclist)):
                output += "[{}]".format(doclist[j].id)
                output += " <"
                output += "{}, ".format(str(doclist[j].positions))
                output += ">\t"
            output += "\n"
        return output


"""Search Engine that seaches for documents matching a certain criteria and
provides the user with those documents.
."""


class SearchEngine(DocumentProcessing):
    def __init__(self, inverted_index):
        """
        Derive purpose, terms, documents, posting_lists and docLengths from
        the inverted index supplied.
        :param inverted_index: Inverted Index object that contains loaded
        data.
        """
        self.purpose = inverted_index.purpose
        self.terms = inverted_index.terms
        self.documents = inverted_index.documents
        self.posting_lists = inverted_index.posting_lists
        if self.purpose == "vsm":
            self.docLengths = inverted_index.docLengths

    def boolean_and_query(self, query):
        """
        Provides documents that match the given boolean query
        :param query: Boolean search query
        :return: list of documents (Document) that match the criteria
        """
        tokenized_query = self.pre_process(
            query, remove_stopwords=True, stemming=True)
        processed_query = self.sort_on_tf(tokenized_query)
        query_results = None
        all_terms_exist = True
        for token in processed_query:
            if self.check_existence(token) is False:
                all_terms_exist = False
        if all_terms_exist:
            if len(processed_query) == 1:
                query_results = self.get_postings_list(processed_query[0])
            elif len(processed_query) == 2:
                posting_list_one = self.get_postings_list(processed_query[0])
                posting_list_two = self.get_postings_list(processed_query[1])
                query_results = self.merge_intersect(posting_list_one,
                                                     posting_list_two)
            elif len(processed_query) > 2:
                posting_list_one = self.get_postings_list(
                    processed_query.pop(0))
                posting_list_two = self.get_postings_list(
                    processed_query.pop(0))
                query_results = self.merge_intersect(posting_list_one,
                                                     posting_list_two)
                while len(query_results) > 0 and len(processed_query) > 0:
                    posting_list_ = self.get_postings_list(
                        processed_query.pop(0))
                    query_results = self.merge_intersect(query_results,
                                                         posting_list_)
        else:
            return None
        return query_results

    def sort_on_tf(self, query_tokens):
        """
        Sort terms according to the number of documents that contain them.
        :param query_tokens: List of terms that need to be sorted
        :return: List of sorted terms
        """
        tf_info = {}
        sorted_terms = []
        for token in query_tokens:
            tf_info[token] = len(self.get_postings_list(token))
        sorted_words = sorted(tf_info.items(), key=operator.itemgetter(1))
        for term_info in sorted_words:
            sorted_terms.append(term_info[0])
        return sorted_terms

    def positional_search(self, query):
        """
        Accomodates free text search returning documents that contain terms
        in the same order as the query.
        :param query: Search query
        :return: List of documents that match the search criteria
        """
        processed_query = self.pre_process(query, remove_stopwords=True,
                                           stemming=True)
        query_results = None
        all_terms_exist = True
        for token in processed_query:
            if self.check_existence(token) is False:
                all_terms_exist = False
        if all_terms_exist:
            if len(processed_query) == 2:
                posting_list_one = self.get_postings_list(processed_query[0])
                posting_list_two = self.get_postings_list(processed_query[1])
                query_results = self.positional_intersect(posting_list_one,
                                                          posting_list_two)
            elif len(processed_query) > 2:
                posting_list_one = self.get_postings_list(
                    processed_query.pop(0))
                posting_list_two = self.get_postings_list(
                    processed_query.pop(0))
                query_results = self.positional_intersect(posting_list_one,
                                                          posting_list_two)
                while len(query_results) > 0 and len(processed_query) > 0:
                    posting_list_ = self.get_postings_list(
                        processed_query.pop(0))
                    query_results = self.positional_intersect(query_results,
                                                              posting_list_)
        else:
            return None
        return query_results

    def merge_intersect(self, post_list_one, post_list_two):
        """
        Use merge algorithm to find documents existing in both posting lists.
        :param post_list_one: Posting list of first term
        :param post_list_two: Posting List of second term
        :return: Posting List containing documents existing in both input
        posting lists.
        """
        intersect_documents = []
        pointer_one = 0
        pointer_two = 0
        while pointer_one < len(post_list_one) and pointer_two < len(
                post_list_two):
            if post_list_one[pointer_one].id == post_list_two[pointer_two].id:
                intersect_documents.append(post_list_two[pointer_two])
                pointer_one += 1
                pointer_two += 1
            elif post_list_one[pointer_one].id > post_list_two[pointer_two].id:
                pointer_two += 1
            else:
                pointer_one += 1
        return intersect_documents

    def ranked_search(self, query, k=10):
        """
        Search for top 10 documents that match the query using Vector Space
        Model scores.
        :param query: Search query
        :param k: number of documents to be retrieved
        :return: Top 10 documents that match the search criteria
        """
        vsm_scores = dict()
        if self.purpose == "bs":
            print("Cannot proceed as Inverted Index supplied does not "
                  "contain term weights.")
            raise Exception
        else:
            query_tokens = self.pre_process(query, remove_stopwords=False,
                                            stemming=True)
            for q_token in query_tokens:
                if q_token not in self.terms:
                    continue
                else:
                    q_posting_list = self.get_postings_list(q_token)
                    query_token_tfidf = (1 + np.log10(1)) * \
                                        np.log10(len(self.documents) *
                                         1.0 / len(q_posting_list))
                    for document_ in q_posting_list:
                        score = document_.term_weight * query_token_tfidf
                        if document_.id in vsm_scores.keys():
                            vsm_scores[document_.id] += score
                        else:
                            vsm_scores[document_.id] = score
            for document_id_ in vsm_scores.keys():
                vsm_scores[document_id_] = vsm_scores[document_id_] / \
                    self.docLengths[document_id_]
            ranked_results = sorted(vsm_scores.items(),
                                    key=operator.itemgetter(1), reverse=True)
            if len(ranked_results) > k:
                result_docs = [ranked_results[rank][0]
                               for rank in range(0, k)]
            else:
                result_docs = [ranked_results[rank][0]
                               for rank in range(0, len(ranked_results))]
            return result_docs

    def check_existence(self, term):
        """
        Check if a term exists in memory
        :param term: Term to be searched for
        :return: True / False based on whether it exists
        """
        if (term in self.terms):
            return True
        return False

    def positional_intersect(self, post_list_one, post_list_two):
        """
        Use merge algorithm to find documents that contain two terms in order.
        :param post_list_one: Posting list of first term
        :param post_list_two: Posting list of second term
        :return: Posting List containing documents that have the two terms
        in order
        """
        intersect_documents = []
        pointer_one = 0
        pointer_two = 0
        while pointer_one < len(post_list_one) and \
                pointer_two < len(post_list_two):
            if post_list_one[pointer_one].id == post_list_two[pointer_two].id:
                position_list_1 = post_list_one[pointer_one].positions
                position_list_2 = post_list_two[pointer_two].positions
                pos_point_1 = 0
                pos_point_2 = 0
                match_found = False
                while pos_point_1 < len(position_list_1) and match_found is \
                        False:
                    while pos_point_2 < len(position_list_2) and match_found is False:
                        if position_list_1[pos_point_1] - \
                                position_list_2[pos_point_2] == -1:
                            intersect_documents.append(
                                post_list_two[pointer_two])
                            match_found = True
                            break
                        pos_point_2 += 1
                    pos_point_2 = 0
                    pos_point_1 += 1
                pointer_one += 1
                pointer_two += 1
            elif post_list_one[pointer_one].id > post_list_two[pointer_two].id:
                pointer_two += 1
            else:
                pointer_one += 1
        return intersect_documents

    def save_engine(self, filename):
        """
        Save Search Engine as pickled object
        :param filename: Absolute path of Search Engine
        :return: None
        """
        pickle.dump(self, open(filename, "wb"))

    def load_engine(filename):
        """
        Load indexed search engine from a pickle file
        :param filename: Absolute path of pickle file
        :return: Indexed Search Engine
        """
        obj = pickle.load(open(filename, "rb"))
        return obj
    load_engine = staticmethod(load_engine)


""" Stores training and testing set documents and their class values in a
Pandas Data Frame.
"""


class ClassifierDataFrame:
    def __init__(self):
        self.columns = ["document_contents", "class"]
        self.df = pd.DataFrame(columns=self.columns)
        self.features = None
        self.target = None
        self.X_train = None
        self.y_train = None
        self.X_test = None
        self.y_test = None

    def save_dataframe(self, filename):
        """
        Save Dataframe containing training and test set as a pickled object
        :param filename: Absolute location of pickled file with intended
        pickle file name
        :return: None
        """
        pickle.dump(self, open(filename, "wb"))

    def load_dataframe(filename):
        """
        Load Dataframe with testing and training set loaded
        :param filename: Absolute location of pickled object
        :return: Dataframe with training and testing set
        """
        obj = pickle.load(open(filename, "rb"))
        return obj
    load_dataframe = staticmethod(load_dataframe)

    def add_document(self, file_name, class_value):
        """
        Add document to memory
        :param file_name: Path to document
        :param class_value: Class value it belongs to
        :return:None
        """
        try:
            with open(file_name) as document:
                data_instance = pd.DataFrame([[document.read(), class_value]],
                                             columns=self.columns)
                self.df = pd.concat([self.df, data_instance]
                                    ).reset_index(drop=True)
        except:
            print("Error reading file {} in class {}".format(file_name,
                                                             class_value))

    def split_target_features(self):
        """
        Split data frame into target and features
        :return: None
        """
        self.features = self.df["document_contents"].copy()
        self.target = self.df["class"].copy()

    def split_training_testing_set(self, t_size):
        """
        Split data set into training and testing data
        :param t_size: Size of testing set
        :return: None
        """
        self.split_target_features()
        stratified_split = StratifiedShuffleSplit(n_splits=1,
                                                  test_size=t_size, random_state=7)
        for train_index, test_index in stratified_split.split(self.features, self.target):
            self.X_train = pd.DataFrame(np.reshape(self.features.loc[train_index].values, (-1, 1)),
                                        columns=["document_contents"]).reset_index(drop=True)
            self.y_train = pd.DataFrame(np.reshape(self.target.loc[train_index].values, (-1, 1)),
                                        columns=["class"]).reset_index(drop=True)
            self.X_test = pd.DataFrame(np.reshape(self.features.loc[test_index].values, (-1, 1)),
                                       columns=["document_contents"]).reset_index(drop=True)
            self.y_test = pd.DataFrame(np.reshape(self.target.loc[test_index].values, (-1, 1)),
                                       columns=["class"]).reset_index(drop=True)


""" Naive Bayes classifier that classifies documents into class values based on
Bayes Rule
"""


class NaiveBayesClassifier(DocumentProcessing):
    def __init__(self, classifier_df):
        self.raw_data = None
        self.raw_training_documents = classifier_df.X_train
        self.training_class_labels = classifier_df.y_train
        self.priors = dict()
        self.conditional_probabilities = dict()
        self.total_vocab_count = 0
        self.class_vocab_count = dict()
        self.class_values = ["business", "sport", "politics",
                             "entertainment", "tech"]
        self.metrics = dict()
        self.consolidate_training_set()
        self.parse_vocabulary()
        self.N = self.raw_data.shape[0]
        self.bernoulli_index = dict()

    def save_model(self, filename):
        """
        Save Classifier as a pickled object
        :param filename: Absolute path of destination with intended name
        :return: None
        """
        pickle.dump(self, open(filename, "wb"))

    def load_model(filename):
        """
        Load trained classifier
        :param filename: Absolute location of pickled object
        :return: Trained Naive Bayes classifier
        """
        obj = pickle.load(open(filename, "rb"))
        return obj
    load_model = staticmethod(load_model)

    def consolidate_training_set(self):
        """
        Combine target and features into a single data frame.
        :return: None
        """
        consolidated_df = pd.concat([self.raw_training_documents,
                                     self.training_class_labels], axis=1)
        self.raw_data = consolidated_df

    def get_conditional_probability(self, word, class_value):
        """
        Get P(word|class) for a term.
        :param word: Term
        :param class_value: Class value
        :return: Conditional Probability P(term|class)
        """
        class_df = self.conditional_probabilities[class_value]
        return float(class_df[class_df.terms == word].loc[:,
                     "conditional_probability"])

    def get_bernoulli_condition_probability(self, word, class_value):
        """
        Get P(term|class) for bernoulli model
        :param word: Term
        :param class_value: Class Value
        :return: Conditional probability
        """
        class_df = self.conditional_probabilities[class_value]
        return float(class_df[class_df.terms == word].loc[:,
                     "bernoulli_probability"])

    def fit(self):
        """
        Train the model on training data set
        :return: None
        """
        for class_value in self.class_values:
            self.build_bernoulli_index(class_value)
            self.calculate_probabilities(class_value)

    def build_bernoulli_index(self, class_value):
        """
        Parse through documents in specified class value and determine
        number of documents containing each term.
        :param class_value: Class Value
        :return: None
        """
        class_docs = list(self.raw_data[self.raw_data["class"] == class_value]
                          .copy()["document_contents"])
        inverted_index = InvertedIndex(auto_load=False)
        for class_doc in class_docs:
            inverted_index.load_data(class_doc, is_text=True)
        self.bernoulli_index[class_value] = inverted_index

    def parse_vocabulary(self):
        """
        Calculate total number of words in the entire data set.
        :return: None
        """
        for class_value_ in self.class_values:
            class_docs = list(self.raw_data[self.raw_data["class"] ==
                                            class_value_].copy()[
                              "document_contents"])
            for class_doc in class_docs:
                tokens = self.pre_process(class_doc, remove_stopwords=True,
                                          stemming=True)
                self.total_vocab_count += len(tokens)

    def calculate_probabilities(self, class_value):
        """
        Calculate conditional probabilities based on term frequency for
        multinomial naive bayes model and number of documents containing
        each term for bernoulli naive bayes model.
        :param class_value: Class Value
        :return: None
        """
        terms = list()
        voc_count = 0
        num_instances = list()
        bernoulli_inv_index = self.bernoulli_index[class_value]
        num_docs = list()
        class_docs = list(self.raw_data[self.raw_data["class"] == class_value]
                          .copy()["document_contents"])
        N_c = len(class_docs)
        prior = np.log(N_c / self.N)
        self.priors[class_value] = prior
        for class_doc in class_docs:
            tokens = self.pre_process(class_doc, remove_stopwords=True,
                                      stemming=True)
            for token in tokens:
                voc_count += 1
                if token not in terms:
                    terms.append(token)
                    num_instances.append(0)
                    num_docs.append(0)
        for class_doc_ in class_docs:
            tokens_ = self.pre_process(class_doc_, remove_stopwords=True,
                                       stemming=True)
            for token_ in tokens_:
                term_index = terms.index(token_)
                posting_list_ = bernoulli_inv_index.get_postings_list(token_)
                num_docs[term_index] = len(posting_list_)
                num_instances[term_index] += 1
        self.class_vocab_count[class_value] = voc_count
        conditional_probs = np.array([terms, num_instances, num_docs])
        conditional_probs = conditional_probs.T
        conditional_df = pd.DataFrame(conditional_probs,
                                      columns=["terms",
                                               "number_of_instances",
                                               "number_of_docs"])
        conditional_df["number_of_instances"] = \
            conditional_df.number_of_instances.astype(int)
        conditional_df["number_of_docs"] = \
            conditional_df.number_of_docs.astype(int)
        conditional_df["conditional_probability"] = (
            conditional_df["number_of_instances"] + 1)/(voc_count +
                                                        self.total_vocab_count * 1.0)
        conditional_df["bernoulli_probability"] = (conditional_df[
                                                       "number_of_docs"] + 1
                                                   * 1.0)/(N_c + 2)
        conditional_df["bernoulli_complement"] = 1 - conditional_df[
            "bernoulli_probability"]
        conditional_df["bernoulli_complement"] = np.log(conditional_df[
            "bernoulli_complement"])
        conditional_df["bernoulli_probability"] = np.log(conditional_df["bernoulli_probability"])
        self.conditional_probabilities[class_value] = conditional_df

    def calculate_metrics(self, predictions, testing_labels):
        """
        Calculate Performance metrics such as precision, recall, accuracy,
         and F1 score.
        :param predictions: Predictions made by the model
        :param testing_labels: Actual labels
        :return: Precision, Recall, F_score, Accuracy
        """
        precision = precision_score(
            testing_labels, predictions, average="weighted")
        recall = recall_score(testing_labels, predictions, average="weighted")
        f_score = f1_score(testing_labels, predictions, average="weighted")
        accuracy = accuracy_score(testing_labels, predictions)
        return precision, recall, f_score, accuracy

    def predict_single(self, pred_doc, mode):
        """
        Predict class value for a single document
        :param pred_doc: Document text
        :param mode: Use bernoulli or multinomial model
        :return: Predicted class value
        """
        tokens = self.pre_process(
            pred_doc, remove_stopwords=True, stemming=True)
        argmax = dict()
        if mode == "b":  # bernoulli
            for class_value in self.class_values:
                class_df = self.conditional_probabilities[class_value]
                output = self.priors[class_value]
                probs = class_df.copy()
                existing_terms_indices = list(probs[probs.terms.isin(
                    tokens)].index)
                for existing_term_index in existing_terms_indices:
                    probs.iloc[existing_term_index, 2] = probs.iloc[
                        existing_term_index, 1]
                output += np.sum(probs["bernoulli_complement"])

                # for word in np.array(class_df.terms):
                #     instance = self.get_bernoulli_condition_probability(
                #         word, class_value)
                #     if word in tokens:
                #         output += np.log(instance)
                #     else:
                #         output += np.log(1 - instance)
                argmax[class_value] = output
            return max(argmax, key=argmax.get)
        elif mode == "m":  # multinomial
            for class_value in self.class_values:
                class_df = self.conditional_probabilities[class_value]
                output = self.priors[class_value]
                for word in tokens:
                    if word in class_df.terms.unique():
                        instance = self.get_conditional_probability(
                            word, class_value)
                        output += np.log(instance)
                    else:
                        output += np.log(
                            1/(self.class_vocab_count[class_value] +
                               self.total_vocab_count))
                argmax[class_value] = output
            return max(argmax, key=argmax.get)

    def predict_multiple(self, testing_df, mode):
        """
        Predict class values for a number of input documents
        :param testing_df: Pandas Dataframe containing document text and
        class values
        :param mode: Bernoulli or Multinomial mode
        :return: Predicted class values for all input documents.
        """
        predictions = []
        if mode == "m":  # multinomial
            for document_content in testing_df["document_contents"].values:
                tokens = self.pre_process(str(document_content), stemming=True)
                maxima = dict()
                for class_value in self.class_values:
                    class_df = self.conditional_probabilities[class_value]
                    output = self.priors[class_value]
                    for word in tokens:
                        if word in class_df.terms.unique():
                            instance = self.get_conditional_probability(
                                word, class_value)
                            output += np.log(instance)
                        else:
                            output += np.log(1.0 /
                                             (self.class_vocab_count[
                                                  class_value] + self.total_vocab_count))
                    maxima[class_value] = output
                predictions.append(max(maxima, key=maxima.get))
            predictions_df = pd.DataFrame(
                predictions, columns=["class_predictions"])
            return predictions_df
        elif mode == "b":  # bernoulli
            for document_content in testing_df["document_contents"].values:
                tokens = self.pre_process(str(document_content))
                maxima = dict()
                for class_value in self.class_values:
                    class_df = self.conditional_probabilities[class_value]
                    output = self.priors[class_value]
                    for word in np.array(class_df.terms):
                        instance = self.get_bernoulli_condition_probability(
                            word, class_value)
                        if word in tokens:
                            output += np.log(instance)
                        else:
                            output += np.log(1-instance)
                    maxima[class_value] = output
                    print(maxima)
                predictions.append(max(maxima, key=maxima.get))
            predictions_df = pd.DataFrame(
                predictions, columns=["class_predictions"])
            return predictions_df


class KNN(DocumentProcessing):
    def __init__(self, vsm_engine, cl_df):
        self.search_engine = vsm_engine
        self.classifier_df = cl_df
        self.id_matching = dict()

    def fit(self):
        """
        Consolidate training set from Classifer_DataFrame and compute id
        matching from the search engine document index
        :return: None
        """
        consolidated_train_set = pd.concat([self.classifier_df.X_train,
                                            self.classifier_df.y_train],
                                           axis=1)
        documents = self.search_engine.documents
        for row in consolidated_train_set.values:
            doc_id = documents.index(row[0])
            self.id_matching[doc_id] = row[1]

    def predict_single(self, document, is_dir=False):
        """
        Use vector space model to retrieve closest documents and classify
        new document based on majority of class values from k close documents.
        :param document: Absolute path of document to be classified
        :return: Class label predicted by the classifier
        """
        class_value_counts = dict()
        if is_dir == True:
            doc_text = open(document, "r").read()
        else:
            doc_text = document
        nearest_docs = self.search_engine.ranked_search(doc_text, k=5)
        for doc_id in nearest_docs:
            class_ = self.id_matching[doc_id]
            if class_ in self.id_matching.keys():
                class_value_counts[class_] += 1
            else:
                class_value_counts[class_] = 1
        return max(class_value_counts, key=class_value_counts.get)

    def save_model(self, filename):
        """
        Save trained model to a pickled object
        :param filename: Absolute path of destination with intended filename
        :return: None
        """
        pickle.dump(self, open(filename, "wb"))

    def load_model(filename):
        """
        Load trained KNN model from pickle file
        :param filename: Absolute path of pickled file
        :return: Trained KNN classifier
        """
        obj = pickle.load(open(filename, "rb"))
        return obj
    load_model = staticmethod(load_model)


def run(mode, input):
    """
    Provide query or document to be searched or classified and retrieve
    results using search engines and classifiers from this module
    :param mode: Type of classifier or search algorithm
    :param input: Query or document to be searched or classified
    :return: Class label or retrieved documents
    """

    if mode == "--bs":
        classifications = {
            "all": set(),
            "politics": set(),
            "business": set(),
            "sport": set(),
            "entertainment": set(),
            "tech": set()
        }
        search_engine = SearchEngine.load_engine("pickled_objects/Boolean_Search_Engine.pickle")
        query = input
        processed_query = search_engine.pre_process(query,
                                                    remove_stopwords=True,
                                                    stemming=True)
        all_terms_exists = True
        for q in processed_query:
            if q not in search_engine.terms:
                all_terms_exists = False
                break
        if len(processed_query) == 0 or all_terms_exists is False:
            classifications["all"].add(0)
            classifications["politics"].add(0)
            classifications["business"].add(0)
            classifications["sport"].add(0)
            classifications["entertainment"].add(0)
            classifications["tech"].add(0)
            temp_docs = ["No documents found"]
            return classifications, temp_docs
        results = search_engine.boolean_and_query(query)

        with open("query_result.txt", "w+") as handle:
            for result in results:
                handle.write("Document Number: {}\n".format(result.id))
                handle.write(search_engine.documents[result.id] + "\n\n")
            handle.write("Documents IDs : \n {}".format([doc.id for doc in results]))
            handle.write("Total Number of Documents found: {}\n".format
                         (len(results)))
        for result in results:
            document_content = search_engine.documents[result.id]
            classifications["all"].add(result.id)
            nb_classifications = pickle.load(open(
                "pickled_objects/nb_classifications.pickle", "rb"))
            nb_class = nb_classifications[document_content]
            knn_classifications = pickle.load(open(
                "pickled_objects/knn_classifications.pickle", "rb"))
            knn_class = knn_classifications[document_content]
            if nb_class == knn_class:
                classifications[nb_class].add(result.id)
            else:
                classifications[nb_class].add(result.id)
                classifications[knn_class].add(result.id)
        return classifications, search_engine.documents
    elif mode == "--ps":
        classifications = {
            "all": set(),
            "politics": set(),
            "business": set(),
            "sport": set(),
            "entertainment": set(),
            "tech": set()
        }
        search_engine = SearchEngine.load_engine("pickled_objects/Boolean_Search_Engine.pickle")
        query = input
        results = search_engine.positional_search(query)
        with open("query_result.txt", "w+") as handle:
            for result in results:
                handle.write("Document Number: {}\n".format(result.id))
                handle.write(search_engine.documents[result.id] + "\n\n")
            handle.write("Documents IDs : \n {}".format([doc.id for doc in results]))
            handle.write("Total Number of Documents found: {}\n".format
                         (len(results)))
        for result in results:
            document_content = search_engine.documents[result.id]
            classifications["all"].add(result.id)
            nb_classifications = pickle.load(open(
                "pickled_objects/nb_classifications.pickle", "rb"))
            nb_class = nb_classifications[document_content]
            knn_classifications = pickle.load(open(
                "pickled_objects/knn_classifications.pickle", "rb"))
            knn_class = knn_classifications[document_content]
            if nb_class == knn_class:
                classifications[nb_class].add(result.id)
            else:
                classifications[nb_class].add(result.id)
                classifications[knn_class].add(result.id)
        return classifications, search_engine.documents
    elif mode == "--vsm":
        classifications = {
            "all": set(),
            "politics": set(),
            "business": set(),
            "sport": set(),
            "entertainment": set(),
            "tech": set()
        }
        # nb = NaiveBayesClassifier.load_model("pickled_objects/Naive_Bayes.pickle")
        # knn_model = KNN.load_model("pickled_objects/KNN.pickle")
        search_engine = SearchEngine.load_engine(
            "pickled_objects/VSM_Search_Engine.pickle")
        query = input
        existing_term = False
        processed_query = search_engine.pre_process(query,
                                                    remove_stopwords=False,
                                                    stemming=True)
        for q in processed_query:
            if q in search_engine.terms:
                existing_term = True
                break
        if (len(processed_query) == 0 or existing_term is False):
            classifications["all"].add(0)
            classifications["politics"].add(0)
            classifications["business"].add(0)
            classifications["sport"].add(0)
            classifications["entertainment"].add(0)
            classifications["tech"].add(0)
            temp_docs = ["No documents found"]
            return classifications, temp_docs
        results = search_engine.ranked_search(query, k=50)
        with open("query_result.txt", "w+") as handle:
            for result in results:
                handle.write("Document Number: {}\n".format(result))
                handle.write(search_engine.documents[result] + "\n\n")
            handle.write("Documents IDs : \n {}".format(results))
        for result in results:
            document_content = search_engine.documents[result]
            classifications["all"].add(result)
            nb_classifications = pickle.load(open(
                "pickled_objects/nb_classifications.pickle", "rb"))
            nb_class = nb_classifications[document_content]
            knn_classifications = pickle.load(open(
                "pickled_objects/knn_classifications.pickle", "rb"))
            knn_class = knn_classifications[document_content]
            if nb_class == knn_class:
                classifications[nb_class].add(result)
            else:
                classifications[nb_class].add(result)
                classifications[knn_class].add(result)
        return classifications, search_engine.documents


def split_write_docs(df, set_="train"):
    """
    Write documents from search engine's document attribute to directories
    :param df: Classifier_DataFrame containing training and testing set
    :param set_: Whether its a training set or testing set
    :return: None
    """
    class_values = ["entertainment", "politics", "business", "tech", "sport"]
    total_docs = df.shape[0]
    cur_doc_no = 0
    for class_value in class_values:
        root_dir = os.getcwd()
        if set_ == "train":
            current_dir = os.path.join(root_dir, "training_set")
            if not os.path.exists(current_dir):
                os.makedirs(current_dir)
        else:
            current_dir = os.path.join(root_dir, "testing_set")
            if not os.path.exists(current_dir):
                os.makedirs(current_dir)
        class_dir = os.path.join(current_dir, class_value)
        if not os.path.exists(class_dir):
            os.makedirs(class_dir)
        class_df = df[df["class"] == class_value]
        for row in class_df.values:
            cur_doc_no += 1
            document_content = row[0]
            file_name = str(cur_doc_no) +".txt"
            file_loc = os.path.join(class_dir, file_name)
            with open(file_loc, "w") as handle:
                handle.write(document_content)
            print("Completed {} out of {} documents".format(cur_doc_no, total_docs))


def train_all_models():
    """
    Index inverted indexes using documents.
    Load Search Engines.
    Train classifiers.
    Save all indexes, search engines and models as pickled files
    :return:
    """
    boolean_inv_index = InvertedIndex("documents", purpose="bs")
    vsm_inv_index = InvertedIndex("documents", purpose="vsm")
    boolean_search_engine = SearchEngine(boolean_inv_index)
    VSM_search_engine = SearchEngine(vsm_inv_index)
    knn_inv_index = InvertedIndex("training_set", purpose="vsm")
    knn_engine = SearchEngine(knn_inv_index)
    cl_df = vsm_inv_index.classifier_df
    nb = NaiveBayesClassifier(cl_df)
    nb.fit()
    knn = KNN(knn_engine, cl_df)
    knn.fit()

    cl_df.save_dataframe("pickled_objects/Classifier_DF.pickle")
    boolean_inv_index.save_index(
        "pickled_objects/Boolean_Inverted_Index.pickle")
    boolean_search_engine.save_engine(
        "pickled_objects/Boolean_Search_Engine.pickle")
    vsm_inv_index.save_index("pickled_objects/VSM_Inverted_Index.pickle")
    VSM_search_engine.save_engine("pickled_objects/VSM_Search_Engine.pickle")
    nb.save_model("pickled_objects/Naive_Bayes.pickle")
    knn.save_model("pickled_objects/KNN.pickle")

# train_all_models()
# print(pd.__version__)