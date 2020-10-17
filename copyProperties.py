from wikidataintegrator import wdi_core, wdi_login, wdi_config
import requests
import pandas as pd
import pprint
import os

source_wikibase = "https://biodiversity.wiki.opencura.com/"
source_sparql = source_wikibase+"query/sparql"
target_wikibase = "https://wildlife-sme.semscape.org/"
target_api = target_wikibase+"w/api.php?"
target_sparql = target_wikibase + "query/sparql"

#copy properties from source wikibase
query = """
SELECT DISTINCT ?property ?propertyLabel ?propType WHERE {
   ?property wikibase:directClaim ?p ;
             wikibase:propertyType ?propType ;         
             rdfs:label ?propertyLabel .
   FILTER (lang(?propertyLabel) = 'en')
}
"""
propertiesSparql = wdi_core.WDItemEngine.execute_sparql_query(query, endpoint=source_sparql ,as_dataframe=True)

# login to target Wikibase
if "WDUSER" in os.environ and "WDPASS" in os.environ:
    WDUSER = os.environ['WDUSER']
    WDPASS = os.environ['WDPASS']
else:
    raise ValueError("WDUSER and WDPASS must be specified in local.py or as environment variables")

login = wdi_login.WDLogin(WDUSER, WDPASS, mediawiki_api_url=target_api)

# copy properties from source wikibase to target wikibase

def createProperty(login, label, description, property_datatype):
  s = []
  localEntityEngine = wdi_core.WDItemEngine.wikibase_item_engine_factory(mediawiki_api_url=target_api,sparql_endpoint_url=target_sparql)
  item = localEntityEngine(data=s)
  item.set_label(label)
  print(item.write(login, entity_type="property", property_datatype=property_datatype))

datatype_map = {'http://wikiba.se/ontology#CommonsMedia': 'commonsMedia',
                'http://wikiba.se/ontology#ExternalId': 'external-id',
                'http://wikiba.se/ontology#GeoShape': 'geo-shape',
                'http://wikiba.se/ontology#GlobeCoordinate': 'globe-coordinate',
                'http://wikiba.se/ontology#Math': 'math',
                'http://wikiba.se/ontology#Monolingualtext': 'monolingualtext',
                'http://wikiba.se/ontology#Quantity': 'quantity',
                'http://wikiba.se/ontology#String': 'string',
                'http://wikiba.se/ontology#TabularData': 'tabular-data',
                'http://wikiba.se/ontology#Time': 'time',
                'http://wikiba.se/ontology#Url': 'url',
                'http://wikiba.se/ontology#WikibaseItem': 'wikibase-item',
                'http://wikiba.se/ontology#WikibaseProperty': 'wikibase-property'}

for row in propertiesSparql.itertuples():
  print(datatype_map[row.propType])
  print(row)
  if row.propType in datatype_map.keys():
      createProperty(login, row.propertyLabel, datatype_map[row.propType])


