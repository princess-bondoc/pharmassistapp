import json
import numpy as np
import nltk
from nltk.stem.lancaster import LancasterStemmer
import time

stemmer = LancasterStemmer()

def classify_intent(sentence, project_file='intent_json', show_details=False):
    
    def sigmoid(x):
        """Returns sigmoid-processed nonlinearity

        Parameters
        ----------
        x : input values
        """
        return 1 / (1 + np.exp(-x))

    def clean_up_sentence(sentence):
        #tokenize the pattern
        sentence_words = nltk.word_tokenize(sentence)
        #stem each word
        sentence_words=[stemmer.stem(word.lower()) for word in sentence_words]
        return sentence_words

    #return bag of words array: 0 or 1 for each word in the bag that exists in the sentence
    def bow(sentence, words, show_details=False):
        #tokenize the pattern
        sentence_words=clean_up_sentence(sentence)
        #bag of words
        bag=[0]*len(words)
        for s in sentence_words:
            for i,w in enumerate(words):
                if w == s: 
                    bag[i] = 1
                    if show_details:
                        print ("found in bag: %s" % w)
        return(np.array(bag))

    def think(sentence, show_details=False):
        x=bow(sentence.lower(),words,show_details)
        if show_details:
            print("sentence:", sentence, "\n bow:", x)
        #input layer is our bag of words
        l0 = x
        # matrix multiplication of input and hidden layer
        l1 = sigmoid(np.dot(l0, synapse_0))
        # output layer
        l2 = sigmoid(np.dot(l1, synapse_1))
        return l2

    # probability threshold
    ERROR_THRESHOLD = 0
    # load our calculated synapse values

    with open("{0}.json".format(project_file), encoding='utf-8') as data_file: 
        synapse = json.load(data_file) 
        synapse_0 = np.asarray(synapse['synapse0']) 
        synapse_1 = np.asarray(synapse['synapse1'])
        words = np.asarray(synapse['words'])
        classes = np.asarray(synapse['classes'])
        
    results = think(sentence, show_details)

    results = [[i,r] for i,r in enumerate(results) if r>ERROR_THRESHOLD ] 
    results.sort(key=lambda x: x[1], reverse=True) 
    return_results =[[classes[r[0]],r[1]] for r in results]
    # print ("%s \n classification: %s" % (sentence, return_results))
    # print ("\n classification: ", return_results[1][0])

    # if (float(return_results[0][1]) >= 0.0):
        
    #      return_results = ({'input:':sentence},{'classification':return_results[0][0]}, {'confidence':return_results[0][1]})

    return return_results
	
#sympt = input("Symptom: ")
#result = classify_intent(sympt)
#print(result[0][0], result[0][1])