"""TO-DO: Write a description of what this XBlock is."""
from __future__ import unicode_literals

import pkg_resources
import urllib2
import json
from xblock.core import XBlock
from xblock.fields import List, Scope
from xblock.fragment import Fragment
from SPARQLWrapper import SPARQLWrapper, JSON, XML, N3, RDF

COURSE_BLOCKS_API = '/api/courses/v1/blocks/'


class QuoteOfTheDayXBlock(XBlock):
    """
    TO-DO: document what your XBlock does.
    """
 
    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    
    # TO-DO: change this view to display your data your own way.
    def student_view(self, context=None):
        """
        The primary view of the QuoteOfTheDayXBlock, shown to students
        when viewing courses.
        """
        html = self.resource_string("static/html/quote_of_the_day.html")
        quote = str(self.location.name)
        author = unicode(getattr(self.runtime, 'course_id', 'course_id'))
        context = {"quote": quote, "author": author}
        frag = Fragment(html.format(self=self, **context))
        frag.add_css(self.resource_string("static/css/quote_of_the_day.css"))
        frag.add_javascript(self.resource_string("static/js/src/quote_of_the_day.js"))
        frag.initialize_js('QuoteOfTheDayXBlock')
        return frag

    def studio_view(self, context=None):
        """
        View for editing QuoteOfTheDayXBlock in Studio.
        """
        return Fragment(u'<p>This block is missing some settings. Add them by changing this view!</p>')

    # Test handler. SPARQL Endpoint connection.
    @XBlock.json_handler
    def get_url(self, data, suffix=''):
        self.unit_id = data['URL']
        self.unit_id=self.unit_id[-32:]
        domain="http://192.168.33.10/"
        concepts={}
        sparql_select = SPARQLWrapper("http://192.168.33.10:8080/rdf4j-server/repositories/1")
        sparql_select.setReturnFormat(JSON)
        select_start="""select ?html where { ?unit_url <http://www.semanticweb.org/EdxOntology/Main#consistsOf> ?html filter (contains(str(?unit_url), '"""
        select_what = self.unit_id
        select_end="'))}"
        sparql_select.setQuery(select_start+select_what+select_end)
        results = sparql_select.query()
        res = results.convert()
        for result in res["results"]["bindings"]:
            html_id=result["html"]["value"].split("#")
        # html_id[1]
        
        select_start="""select ?concept_url where { ?html <http://www.semanticweb.org/EdxOntology/Main#hasConcept> ?concept_url filter (contains(str(?html), '"""
        select_what = html_id[1]
        select_end="'))}"
        
        sparql_select.setQuery(select_start+select_what+select_end)
        results = sparql_select.query()
        res = results.convert()
        for result in res["results"]["bindings"]:
            concept_id=result["concept_url"]["value"]
            select_start="""select ?concept where { ?concept_url rdfs:label ?concept filter (contains(str(?concept_url), '"""
            select_what = concept_id
            select_end="'))}"
            sparql_select.setQuery(select_start+select_what+select_end)
            results = sparql_select.query()
            res = results.convert()
            for result in res["results"]["bindings"]:
                concept_label=result["concept"]["value"]
                #print result["concept"]["value"]
            
            select_start="""PREFIX Main: <http://www.semanticweb.org/EdxOntology/Main#> select ?unit where { ?unit Main:hasConcept ?concept filter (contains(str(?concept), '"""
            select_what = concept_id
            select_end="'))}"
            sparql_select.setQuery(select_start+select_what+select_end)
            results = sparql_select.query()
            res = results.convert()
            concept_units=[]
            for result in res["results"]["bindings"]:
                unit_id=result["unit"]["value"].split("#")[1]
                if unit_id!=html_id[1]:
                    #course_name = res["results"]["bindings"][0]["url"]["value"]
                    select_start="""PREFIX Main: <http://www.semanticweb.org/EdxOntology/Main#> select ?vertical
        where { ?vertical Main:consistsOf ?unit filter (contains(str(?unit), '"""
                    select_what = unit_id
                    select_end="'))}"
                    sparql_select.setQuery(select_start+select_what+select_end)
                    results = sparql_select.query()
                    res = results.convert()
                    for result in res["results"]["bindings"]:
                        #course_name=unicode(getattr(self.runtime, 'course_id', 'course_id'))
                        select_start="""PREFIX Main: <http://www.semanticweb.org/EdxOntology/Main#> select ?url where { ?course rdf:type Main:Course. ?course Main:consistsOf ?chapters. ?course <http://www.w3.org/1999/02/22-rdf-syntax-ns#Alt> ?url. ?chapters Main:consistsOf ?seq. ?seq Main:consistsOf ?vertical. filter (contains(str(?vertical), '"""
                        external_unit_id=result["vertical"]["value"].split("#")[1]
                        select_what = external_unit_id
                        select_end="'))}"
                        sparql_select.setReturnFormat(JSON)
                        sparql_select.setQuery(select_start+select_what+select_end)
                        results = sparql_select.query()
                        main = results.convert()
                        course_name=main["results"]["bindings"][0]["url"]["value"]
                        concept_units.append("http://192.168.33.10/courses/course-v1:"+course_name+"/jump_to/block-v1:"+course_name+"+type@vertical+block@"+external_unit_id)
            concepts[concept_label]=concept_units
        return {"unit_id" : json.dumps(concepts)}


    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("QuoteOfTheDayXBlock",
             """<quote_of_the_day/>
             """),
            ("Multiple QuoteOfTheDayXBlock",
             """<vertical_demo>
                <quote_of_the_day/>
                <quote_of_the_day/>
                <quote_of_the_day/>
                </vertical_demo>
             """),
        ]
