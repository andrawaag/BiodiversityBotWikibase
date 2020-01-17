from wikidataintegrator import wdi_core, wdi_login
import pprint
import os

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

mediawiki_api_url = "https://biodiversity.wiki.opencura.com/w/api.php" # <- change to applicable wikibase
sparql_endpoint_url = "https://biodiversity.wiki.opencura.com/query/sparql"  # <- change to applicable wikibase

if "WDUSER" in os.environ and "WDPASS" in os.environ:
    WBUSER = os.environ['WDUSER']
    WBPASS = os.environ['WDPASS']
else:
    raise ValueError("WDUSER and WDPASS must be specified in local.py or as environment variables")

login = wdi_login.WDLogin(WBUSER, WBPASS, mediawiki_api_url=mediawiki_api_url)

query = """
PREFIX wdt: <http://biodiversity.wiki.opencura.com/prop/direct/>
SELECT * WHERE {
  ?item wdt:P10 ?taxonid .
  FILTER NOT EXISTS {
      ?item wdt:P11 ?wikidata .
  }
}
"""
results = wdi_core.WDItemEngine.execute_sparql_query(query, endpoint=sparql_endpoint_url)
pprint.pprint(results)
taxon_ids = []
for taxonid in results['results']["bindings"]:
    taxon_ids.append("\""+taxonid["taxonid"]["value"]+"\"")

for taxons in list(chunks(taxon_ids, 100)):
    wikidata_query = "SELECT * WHERE {VALUES ?taxonid {"
    wikidata_query += " ".join(taxons)
    wikidata_query += """} 
    ?item wdt:P3151 ?taxonid .
    }"""
    print(wikidata_query)

    results = wdi_core.WDItemEngine.execute_sparql_query(wikidata_query)
    for result in results["results"]["bindings"]:
        print(result["item"]["value"], result["taxonid"]["value"])
        query2 = """
            PREFIX wdt: <http://biodiversity.wiki.opencura.com/prop/direct/>
            SELECT * WHERE {
              ?item wdt:P10 """
        query2 += "\""+ result["taxonid"]["value"]+"\""
        query2 += """ .
            FILTER NOT EXISTS {
                  ?item wdt:P11 ?wikidata .
              }
            }
            """
        results3 = wdi_core.WDItemEngine.execute_sparql_query(query2, endpoint=sparql_endpoint_url)
        wbqid = results3["results"]["bindings"][0]["item"]["value"].replace("http://biodiversity.wiki.opencura.com/entity/", "")
        print(wbqid)
        data = [wdi_core.WDUrl(result["item"]["value"], prop_nr="P11")]
        updatedItem = wdi_core.WDItemEngine(wd_item_id=wbqid, data=data,mediawiki_api_url=mediawiki_api_url)
        updatedItem.write(login)


