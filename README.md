# Information Retrieval & Classification

## Description

An Information Retrieval system that is capable of accommodating
*   Boolean search queries
*   Positional search queries
*   Free text queries
*   Naive Bayes Classification
*   K Nearest Neighbor Classification

## Class values for Naive Bayes Classification

The Naive Bayes classifier classifies documents into 5 class values namely

* Business
* Entertainment
* Politics
* Technology
* Sports

## Output of Search Engines

On using the search engine, only the first 100 characters of each found 
document will be printed in the command line. The entire output will be 
written to a text file called `query_results.txt`.

## Dependencies Required

All the dependencies required can be installed using pip

* Pandas
* Numpy
* Nltk
    * After installing NLTK, uncomment 3rd line in program to download 
    essential dependent files.
* Pickle

## Command Line Parameters

| Parameter     | Feature                                     | 
| ------------- |:-------------------------------------------:|
| --bs          | Boolean Search using Inverted Index         |
| --ps          | Positional Search using Inverted Index      |
| --vsm         | Free text search using Vector Space Model   |
| --nb          | Naive Bayes Classification (Multinomial)    |
| --knn         | K Nearest Neighbor Classification           |

## How To Run

Currently this is a command line application and the following commands can 
be used to utilize the features of the system.

### Boolean Search

`python3 search_engine.py --bs *query`

### Positional Search

`python3 search_engine.py --ps *query`

### Free Text Search

`python3 search_engine.py --vsm *query`

### Naive Bayes Classification

`python3 search_engine.py --nb document_path`

### K Nearest Neighbour Classification

`python3 search_engine.py --knn document_path`


## Test Queries to check functionality

A set of test queries that can be used to check the functionality of the 
system are given below.

**AND Queries**
* Jackie Ballard Parliament
* Research and Development

**Positional Queries**

* flattered and honoured
* printed with registered trademarks

**Free text Queries**

* Cyber computers government
* Actress actor theatre


**Test Classification Documents**

A set of test documents are available in `testing_documents` folder that 
can be used to test the functionality of the naive bayes classifier. These 
documents were not used to train the model and are from the testing set of 
documents.

Some examples are 
* politics_1.txt
* sport_1.txt
* entertainment_1.txt
* business_1.txt
* tech_1.txt 

## Link to full set of documents if required

[https://drive.google.com/drive/folders/1tqJWz7wUYaVPhLadqFEhh4Rq8rt3kkkM?usp=sharing]

## Examples

> python3 search_engine.py --bs Anderson country

The above command will search for documents containing both "Anderson" and 
"country".

> python3 search_engine.py --ps New York

The above command will search for documents that contain "New" and "York" in
 the same order.
 
 > python3 search_engine.py --vsm Today in politics
 
 The above command will search and provides top 10 documents that are 
 similar to the query.
 
 > python3 search_engine.py --knn test_documents/tech/tech_1.txt
 
 It classifies the tech_1.txt document using K nearest neighbors classifier.
 
 > python3 search_engine.py --nb test_documents/tech/tech_2.txt
 
 It classifies the tech_1.txt document using Naive Bayes classifier.
 