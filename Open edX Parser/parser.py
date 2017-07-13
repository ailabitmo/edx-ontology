import pymongo
import re
import uuid
import rake
import operator
import urllib2
from bson.objectid import ObjectId
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import MySQLdb
import sys
import nltk
from nltk.stem import WordNetLemmatizer


def upcase_first_letter(s):
    return s[0].upper() + s[1:].lower()
    
def is_number(s):
    try:
        float(s) if '.' in s else int(s)
        return True
    except ValueError:
        return False


def load_stop_words(stop_word_file):
    """
    Utility function to load stop words from a file and return as a list of words
    @param stop_word_file Path and file name of a file containing stop words.
    @return list A list of stop words.
    """
    stop_words = []
    for line in open(stop_word_file):
        if line.strip()[0:1] != "#":
            for word in line.split():  # in case more than one per line
                stop_words.append(word)
    return stop_words


def separate_words(text, min_word_return_size):
    """
    Utility function to return a list of all words that are have a length greater than a specified number of characters.
    @param text The text that must be split in to words.
    @param min_word_return_size The minimum no of characters a word must have to be included.
    """
    splitter = re.compile('[^a-zA-Z0-9_\\+\\-/]')
    words = []
    for single_word in splitter.split(text):
        current_word = single_word.strip().lower()
        #leave numbers in phrase, but don't count as words, since they tend to invalidate scores of their phrases
        if len(current_word) > min_word_return_size and current_word != '' and not is_number(current_word):
            words.append(current_word)
    return words


def split_sentences(text):
    """
    Utility function to return a list of sentences.
    @param text The text that must be split in to sentences.
    """
    sentence_delimiters = re.compile(u'[.!?,;:\t\\\\"\\(\\)\\\'\u2019\u2013]|\\s\\-\\s')
    sentences = sentence_delimiters.split(text)
    return sentences


def build_stop_word_regex(stop_word_file_path):
    stop_word_list = load_stop_words(stop_word_file_path)
    stop_word_regex_list = []
    for word in stop_word_list:
        word_regex = r'\b' + word + r'(?![\w-])'  # added look ahead for hyphen
        stop_word_regex_list.append(word_regex)
    stop_word_pattern = re.compile('|'.join(stop_word_regex_list), re.IGNORECASE)
    return stop_word_pattern


def generate_candidate_keywords(sentence_list, stopword_pattern):
    phrase_list = []
    for s in sentence_list:
        tmp = re.sub(stopword_pattern, '|', s.strip())
        phrases = tmp.split("|")
        for phrase in phrases:
            phrase = phrase.strip().lower()
            if phrase != "":
                phrase_list.append(phrase)
    st = WordNetLemmatizer()
    i=0
    for w in phrase_list:
        phrase_list[i]=st.lemmatize(w)
        i+=1
    return phrase_list


def calculate_word_scores(phraseList):
    word_frequency = {}
    word_degree = {}
    for phrase in phraseList:
        word_list = separate_words(phrase, 0)
        word_list_length = len(word_list)
        word_list_degree = word_list_length - 1
        #if word_list_degree > 3: word_list_degree = 3 #exp.
        for word in word_list:
            word_frequency.setdefault(word, 0)
            word_frequency[word] += 1
            word_degree.setdefault(word, 0)
            word_degree[word] += word_list_degree  #orig.
            #word_degree[word] += 1/(word_list_length*1.0) #exp.
    for item in word_frequency:
        word_degree[item] = word_degree[item] + word_frequency[item]

    # Calculate Word scores = deg(w)/frew(w)
    word_score = {}
    for item in word_frequency:
        word_score.setdefault(item, 0)
        word_score[item] = word_degree[item] / (word_frequency[item] * 1.0)  #orig.
    #word_score[item] = word_frequency[item]/(word_degree[item] * 1.0) #exp.
    return word_score


def generate_candidate_keyword_scores(phrase_list, word_score):
    keyword_candidates = {}
    for phrase in phrase_list:
        keyword_candidates.setdefault(phrase, 0)
        word_list = separate_words(phrase, 0)
        candidate_score = 0
        for word in word_list:
            candidate_score += word_score[word]
        keyword_candidates[phrase] = candidate_score
    return keyword_candidates


class Rake(object):
    def __init__(self, stop_words_path):
        self.stop_words_path = stop_words_path
        self.__stop_words_pattern = build_stop_word_regex(stop_words_path)

    def run(self, text):
        sentence_list = split_sentences(text)

        phrase_list = generate_candidate_keywords(sentence_list, self.__stop_words_pattern)

        word_scores = calculate_word_scores(phrase_list)

        keyword_candidates = generate_candidate_keyword_scores(phrase_list, word_scores)

        sorted_keywords = sorted(keyword_candidates.iteritems(), key=operator.itemgetter(1), reverse=True)
        return sorted_keywords
        
def concept_search(some_text):
    #key_file = open('Many_text.txt')
    #text = key_file.read()
    # Split text into sentences
    sentenceList = split_sentences(some_text)
    stoppath = "SmartStoplist.txt"
    stopwordpattern = build_stop_word_regex(stoppath)
    
    # generate candidate keywords
    phraseList = generate_candidate_keywords(sentenceList, stopwordpattern)
    wordscores = calculate_word_scores(phraseList)
    
    # generate candidate keyword scores
    keywordcandidates = generate_candidate_keyword_scores(phraseList, wordscores)
    #print keywordcandidates
    sortedKeywords = sorted(keywordcandidates.iteritems(), key=operator.itemgetter(1), reverse=True)
    #print sortedKeywords.pop(1)
    reg = re.compile('[^a-zA-Z]') #0-9 
    
    n=0
    condidat_terms = []
    good_terms = [] 
    print "-------------"
    
    #print sortedKeywords
    for cond_terms in sortedKeywords:
        find=reg.sub(' ', cond_terms[0])
        if  cond_terms[1]>1:
            sparql_dbpedia = SPARQLWrapper("https://dbpedia.org/sparql")
            sparql_dbpedia.setReturnFormat(JSON)
            select_start="ASK {?uri rdfs:label ?label . filter(?label='"
            find=upcase_first_letter(find)
            select_end="'@en)}"
            sparql_dbpedia.setQuery(select_start+find+select_end)
            results = sparql_dbpedia.query()
            res = results.convert()
            #print(n,find,res['boolean'])
            #print(find," - ",res['boolean'])
            if res['boolean']==False:
                #print (n," - DELETE")
                condidat_terms.append(cond_terms)
            else:    
                good_terms.append(find)
                #n-=1
            n+=1
    totalKeywords = len(good_terms)
    #print "-------------"
    #print "AFTER DELETE"
    print len(condidat_terms)
    print len(good_terms)
    return good_terms

sql_db = MySQLdb.connect(host="localhost",    
                     user="root",        
                     passwd="",  
                     db="edxapp")   
edxapp = sql_db.cursor()

#Connection to MongoDB and DB & Collection choice
conn = pymongo.Connection('localhost', 27017)
db = conn.edxapp
coll = db.modulestore.structures
published = db.modulestore.active_versions
defin = db.modulestore.definitions

#array of ObjectID of all active courses
published_courses_array=[]
published_courses_uniq_names={}
for published_courses in published.find({}):
    published_courses_uniq_names[published_courses["versions"]["published-branch"]]=(published_courses["org"]+"+"+published_courses["course"]+"+"+published_courses["run"])
    published_courses_array.append(published_courses["versions"]["published-branch"])
#print published_courses_uniq_names

definitions_array=[]

#mongo query's
''' 
db.getCollection('modulestore.structures').
find({"blocks.block_id" : "d8a6192ade314473a78242dfeedfbf5b", "blocks.block_type" : "course"}, 
{"blocks.fields.display_name":1, "blocks.fields.children":1, "blocks.block_type":1, 
 "blocks.definition":1})
//db.getCollection('modulestore.structures').distinct("blocks.definition", {"blocks.block_id" : "d8a6192ade314473a78242dfeedfbf5b","blocks.block_type" : "course"})
'''



#automatic Collection creation by data insert
'''import datetime
post = {"author": "Mike", "text": "My first blog post!", "tags": ["mongodb", "python", "pymongo"],"date": datetime.datetime.utcnow()}
coll.insert(post)'''
course_structure_array=[]

sparql = SPARQLWrapper("http://95.161.165.103:8080/rdf4j-workbench/repositories/2/update")
sparql_select = SPARQLWrapper("http://95.161.165.103:8080/rdf4j-server/repositories/2")
sparql_select.setReturnFormat(JSON)
select_start="""select ?a where { ?a <http://www.w3.org/2000/01/rdf-schema#label> ?c FILTER (str(?c) = '"""
select_end="')}"
sparql.method = 'POST'
sem_link = "<http://www.semanticweb.org/EdxOntology/Main#"
w3_type = "> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
w3_label = "> <http://www.w3.org/2000/01/rdf-schema#label> "
consistsOf = "> <http://www.semanticweb.org/EdxOntology/Main#consistsOf> "
hasConcept = "> <http://www.semanticweb.org/EdxOntology/Main#hasConcept> "
w3_seeAlso = "> <http://www.w3.org/2000/01/rdf-schema#seeAlso> "
w3_Alt = "> <http://www.w3.org/1999/02/22-rdf-syntax-ns#Alt> "
content = "> <http://www.semanticweb.org/EdxOntology/Main#content> "

#Getting array of courses with their data
#for course_id in published_courses_array:
for course_id in published_courses_uniq_names:
    n_triple = "INSERT DATA { "+sem_link+str(course_id)+w3_type+"<http://www.w3.org/2002/07/owl#NamedIndividual> .}"
    sparql.setQuery(n_triple) 
    sparql.query()
    n_triple = "INSERT DATA { "+sem_link+str(course_id)+w3_type+sem_link+"Course> .}"
    sparql.setQuery(n_triple)
    sparql.query()
    n_triple = "INSERT DATA { "+sem_link+str(course_id)+w3_Alt+"'"+published_courses_uniq_names[course_id]+"' .}"
    sparql.setQuery(n_triple) 
    sparql.query()
    for whole_course_document in coll.find({"_id" : course_id}, {"blocks.fields.display_name":1, "blocks.fields.children":1,"blocks.block_type":1,"blocks.definition":1,"blocks.block_id":1 }):
        for course_block in whole_course_document["blocks"]:
            if course_block["block_type"]=="course":
                course_structure = {}
                course_structure["course_chapters"]=[]
                #!!!!!!!!!Narrow space, because block_id of course is "course", not objectID
                course_structure["course_id"]=course_block["block_id"]
                course_structure["course_name"]=course_block["fields"]["display_name"]
                #PRINT NAME
                print("Course = "+course_structure["course_name"])
                n_triple = "INSERT DATA { "+sem_link+str(course_id)+w3_label+"'"+course_structure["course_name"]+"'@en .}"
                sparql.setQuery(n_triple) 
                sparql.query()
                for course_chapters in course_block["fields"]["children"]:
                    chapter_structure1={}
                    chapter_structure1["chapter_id"]=course_chapters[1]
                    n_triple = "INSERT DATA { "+sem_link+str(course_id)+consistsOf+sem_link+chapter_structure1["chapter_id"]+"> .}"
                    sparql.setQuery(n_triple) 
                    sparql.query()
                    course_structure["course_chapters"].append(chapter_structure1)
                course_structure_array.append(course_structure.copy())
                #print "--------------Next course-----------------"
        
        for course_block in whole_course_document["blocks"]:
            if course_block["block_type"]=="chapter":
                for course in course_structure_array:
                    for chapter in course["course_chapters"]:
                        if course_block["block_id"] == chapter["chapter_id"]:
                            chapter["chapter_name"]=course_block["fields"]["display_name"]
                            n_triple = "INSERT DATA { "+sem_link+chapter["chapter_id"]+w3_type+"<http://www.w3.org/2002/07/owl#NamedIndividual> .}"
                            sparql.setQuery(n_triple) 
                            sparql.query()
                            n_triple = "INSERT DATA { "+sem_link+chapter["chapter_id"]+w3_type+sem_link+"Sections> .}"
                            sparql.setQuery(n_triple)
                            sparql.query()
                            n_triple = "INSERT DATA { "+sem_link+chapter["chapter_id"]+w3_label+"'"+chapter["chapter_name"]+"'@en .}"
                            sparql.setQuery(n_triple) 
                            sparql.query()
                            chapter["sequentials"]=[]
                            for chapter_sequentials in course_block["fields"]["children"]:
                                sequential_structure={}
                                sequential_structure["sequential_id"]=chapter_sequentials[1]
                                n_triple = "INSERT DATA { "+sem_link+chapter["chapter_id"]+consistsOf+sem_link+sequential_structure["sequential_id"]+"> .}"
                                sparql.setQuery(n_triple) 
                                sparql.query()
                                chapter["sequentials"].append(sequential_structure)

        for course_block in whole_course_document["blocks"]:
            if course_block["block_type"]=="sequential":
                for course in course_structure_array:
                    for chapter in course["course_chapters"]:
                        for sequential in chapter["sequentials"]:
                            if course_block["block_id"] == sequential["sequential_id"]:
                                sequential["sequential_name"]=course_block["fields"]["display_name"]
                                n_triple = "INSERT DATA { "+sem_link+sequential["sequential_id"]+w3_type+"<http://www.w3.org/2002/07/owl#NamedIndividual> .}"
                                sparql.setQuery(n_triple) 
                                sparql.query()
                                n_triple = "INSERT DATA { "+sem_link+sequential["sequential_id"]+w3_type+sem_link+"Subsections> .}"
                                sparql.setQuery(n_triple)
                                sparql.query()
                                n_triple = "INSERT DATA { "+sem_link+sequential["sequential_id"]+w3_label+"'"+sequential["sequential_name"]+"'@en .}"
                                sparql.setQuery(n_triple) 
                                sparql.query()
                                sequential["verticals"]=[]
                                for sequential_verticals in course_block["fields"]["children"]:
                                    vertical_structure={}
                                    vertical_structure["vertical_id"]=sequential_verticals[1]
                                    n_triple = "INSERT DATA { "+sem_link+sequential["sequential_id"]+consistsOf+sem_link+vertical_structure["vertical_id"]+"> .}"
                                    sparql.setQuery(n_triple) 
                                    sparql.query()
                                    sequential["verticals"].append(vertical_structure)

        for course_block in whole_course_document["blocks"]:
            if course_block["block_type"]=="vertical":
                for course in course_structure_array:
                    for chapter in course["course_chapters"]:
                        for sequential in chapter["sequentials"]:
                            for vertical in sequential["verticals"]:
                                if course_block["block_id"] == vertical["vertical_id"]:
                                    vertical["units"]=[]
                                    try:
                                        vertical["vertical_name"]=course_block["fields"]["display_name"]
                                        n_triple = "INSERT DATA { "+sem_link+vertical["vertical_id"]+w3_type+"<http://www.w3.org/2002/07/owl#NamedIndividual> .}"
                                        sparql.setQuery(n_triple) 
                                        sparql.query()
                                        n_triple = "INSERT DATA { "+sem_link+vertical["vertical_id"]+w3_type+sem_link+"Units> .}"
                                        sparql.setQuery(n_triple)
                                        sparql.query()
                                        n_triple = "INSERT DATA { "+sem_link+vertical["vertical_id"]+w3_label+"'"+vertical["vertical_name"]+"'@en .}"
                                        sparql.setQuery(n_triple) 
                                        sparql.query()
                                    except:
                                        print ""
                                    for vertical_units in course_block["fields"]["children"]:
                                        unit_structure={}
                                        unit_structure["unit_type"]=vertical_units[0]
                                        unit_structure["unit_id"]=vertical_units[1]
                                        for units_content in whole_course_document["blocks"]:
                                            if units_content["block_id"] == unit_structure["unit_id"] and units_content["block_type"] == "html":
                                                #ObjectID for Content from definitions collection
                                                for definitions in defin.find({"_id":ObjectId(units_content["definition"])}):
                                                    try:
                                                        unit_structure["data"]=re.sub(r'(\<(/?[^>]+)>)', ' ', definitions["fields"]["data"]) #Delete html tags
                                                        unit_structure["data"]=unit_structure["data"].rstrip('\r\n') #Delete string endings
                                                        unit_structure["data"]=unit_structure["data"].replace('\r\n',' ') #Delete new line endings
                                                        unit_structure["data"]=unit_structure["data"].replace('\n',' ') #Delete new line endings
                                                        unit_structure["data"]=unit_structure["data"].replace('&nbsp;',' ') #Delete spaces
                                                        unit_structure["data"]=re.sub(r'\s+', ' ', unit_structure["data"]) #Delete spaces
                                                        #print ">>>--------"
                                                        #print unit_structure["data"]
                                                        n_triple = "INSERT DATA { "+sem_link+vertical["vertical_id"]+consistsOf+sem_link+units_content["block_id"]+"> .}"
                                                        sparql.setQuery(n_triple) 
                                                        sparql.query()
                                                        n_triple = "INSERT DATA { "+sem_link+units_content["block_id"]+w3_type+"<http://www.w3.org/2002/07/owl#NamedIndividual> .}"
                                                        sparql.setQuery(n_triple) 
                                                        sparql.query()
                                                        n_triple = "INSERT DATA { "+sem_link+units_content["block_id"]+w3_type+sem_link+"HTML> .}"
                                                        sparql.setQuery(n_triple)
                                                        sparql.query()
                                                        n_triple = "INSERT DATA { "+sem_link+units_content["block_id"]+content+"'"+unit_structure["data"]+"' .}"
                                                        sparql.setQuery(n_triple) 
                                                        sparql.query()
                                                        # NLP - RAKE - WIKI 
                                                        unit_structure["concepts"]=concept_search(unit_structure["data"])
                                                        #print unit_structure["concepts"]
                                                        for concept in unit_structure["concepts"]:
                                                            sparql_select.setQuery(select_start+concept+select_end)
                                                            results = sparql_select.query()
                                                            res = results.convert()
                                                            if not res["results"]["bindings"]:
                                                                concept_id=str(uuid.uuid1())
                                                                n_triple = "INSERT DATA { "+sem_link+unit_structure["unit_id"]+hasConcept+sem_link+concept_id+"> .}"
                                                                sparql.setQuery(n_triple) 
                                                                sparql.query()
                                                                n_triple = "INSERT DATA { "+sem_link+concept_id+w3_type+"<http://www.w3.org/2002/07/owl#NamedIndividual> .}"
                                                                sparql.setQuery(n_triple) 
                                                                sparql.query()
                                                                n_triple = "INSERT DATA { "+sem_link+concept_id+w3_type+sem_link+"Concept> .}"
                                                                sparql.setQuery(n_triple)
                                                                sparql.query()
                                                                n_triple = "INSERT DATA { "+sem_link+concept_id+w3_label+"'"+concept+"'@en .}"
                                                                sparql.setQuery(n_triple) 
                                                                sparql.query()
                                                                print(concept_id+" - "+concept)
                                                                dbpedia_concept=concept.replace(' ','_')
                                                                dbpedia_concept=upcase_first_letter(dbpedia_concept)
                                                                #print(dbpedia_concept)
                                                                n_triple = "INSERT DATA { "+sem_link+concept_id+w3_seeAlso+"'http://dbpedia.org/page/"+dbpedia_concept+"'@en .}"
                                                                #print(n_triple)
                                                                sparql.setQuery(n_triple) 
                                                                sparql.query()
                                                            else:   
                                                                for result in res["results"]["bindings"]:
                                                                    link_id=result["a"]["value"].split("#")
                                                                concept_id=link_id[1]
                                                                print("Find concept: "+concept+" with id: "+concept_id)
                                                                n_triple = "INSERT DATA { "+sem_link+unit_structure["unit_id"]+hasConcept+sem_link+concept_id+"> .}"
                                                                sparql.setQuery(n_triple) 
                                                                sparql.query()
                                                    except:
                                                        unit_structure["data"]=""
                                                    vertical["units"].append(unit_structure)
                                                                                                                                            #INSERT NAME OF XBLOCK!!!
                                            if units_content["block_id"] == unit_structure["unit_id"] and units_content["block_type"] == "newone":
                                                try:
                                                    #unit_structure["data"]="xblock"
                                                    
                                                    edxapp.execute("SELECT value FROM courseware_xmoduleuserstatesummaryfield WHERE usage_id LIKE '%"+unit_structure["unit_id"]+"';")
                                                    for row in edxapp.fetchall():
                                                        unit_structure["concepts"]=row[0].replace('\\"','').replace('"','').replace('[','').replace(']','')
                                                        concepts_array=unit_structure["concepts"].split(',')
                                                        for concept in concepts_array:
                                                            concept=concept.lstrip()
                                                            sparql_select.setQuery(select_start+concept+select_end)
                                                            results = sparql_select.query()
                                                            res = results.convert()
                                                            if not res["results"]["bindings"]:
                                                                concept_id=str(uuid.uuid1())
                                                                n_triple = "INSERT DATA { "+sem_link+unit_structure["unit_id"]+hasConcept+sem_link+concept_id+"> .}"
                                                                sparql.setQuery(n_triple) 
                                                                sparql.query()
                                                                n_triple = "INSERT DATA { "+sem_link+concept_id+w3_type+"<http://www.w3.org/2002/07/owl#NamedIndividual> .}"
                                                                sparql.setQuery(n_triple) 
                                                                sparql.query()
                                                                n_triple = "INSERT DATA { "+sem_link+concept_id+w3_type+sem_link+"Concept> .}"
                                                                sparql.setQuery(n_triple)
                                                                sparql.query()
                                                                n_triple = "INSERT DATA { "+sem_link+concept_id+w3_label+"'"+concept+"'@en .}"
                                                                sparql.setQuery(n_triple) 
                                                                sparql.query()
                                                            else:   
                                                                for result in res["results"]["bindings"]:
                                                                    link_id=result["a"]["value"].split("#")
                                                                concept_id=link_id[1]
                                                                n_triple = "INSERT DATA { "+sem_link+unit_structure["unit_id"]+hasConcept+sem_link+concept_id+"> .}"
                                                                sparql.setQuery(n_triple) 
                                                                sparql.query()
                                                except:
                                                    unit_structure["concepts"]=""
                                                vertical["units"].append(unit_structure)

                                        


                



#5690cbf1457ebc0ba8429d4d - fail
#5690d6a8457ebc0ba9429d52
#5690d8ac457ebc0ba9429fb5


with open('output.txt', 'w') as outfile:
    json.dump(course_structure_array, outfile, indent=4, sort_keys=True, separators=(',', ':'))
    
#print json.dumps(course_structure_array, sort_keys=True, indent=4, separators=(',', ': '))
