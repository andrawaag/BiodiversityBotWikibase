import pandas as pd
import pprint
import os
from wikidataintegrator import wdi_core, wdi_login

mediawiki_api_url = "https://biodiversity.wiki.opencura.com/w/api.php" # <- change to applicable wikibase
sparql_endpoint_url = "https://biodiversity.wiki.opencura.com/query/sparql"  # <- change to applicable wikibase

if "WDUSER" in os.environ and "WDPASS" in os.environ:
    WBUSER = os.environ['WDUSER']
    WBPASS = os.environ['WDPASS']
else:
    raise ValueError("WDUSER and WDPASS must be specified in local.py or as environment variables")

login = wdi_login.WDLogin(WBUSER, WBPASS, mediawiki_api_url=mediawiki_api_url)
print("==Loading the data....")
df = pd.read_csv("observations-75360.csv")

print("=Look at current content in WB....")
query = """
PREFIX wdt: <http://biodiversity.wiki.opencura.com/prop/direct/>
SELECT DISTINCT ?name WHERE {
  ?item wdt:P9 ?name .
  FILTER NOT EXISTS {
      ?name wdt:P13 ?wikidata .
  }
}
"""
todo = []
results = wdi_core.WDItemEngine.execute_sparql_query(query, endpoint=sparql_endpoint_url)
for result in results["results"]["bindings"]:
    todo.append(result["name"]["value"].replace("http://biodiversity.wiki.opencura.com/entity/", ""))
print("==remove duplicates")
taxondf = df[['scientific_name', 'taxon_id']].drop_duplicates()
pprint.pprint(taxondf)
pprint.pprint(todo)
taxon_ids = dict()
for index, row in taxondf.iterrows():
    wikibase_search = wdi_core.WDItemEngine.get_wd_search_results(search_string=row["scientific_name"], mediawiki_api_url = mediawiki_api_url)
    for wbid in wikibase_search:
        if wbid in todo:
            data = []
            if wdi_core.WDItemEngine(wd_item_id=wbid, mediawiki_api_url=mediawiki_api_url).get_label(lang="en") == row["scientific_name"]:
                print(wbid, row["scientific_name"].encode('utf-8'))
                data.append(wdi_core.WDItemID("Q131918", prop_nr="P13"))
                data.append(wdi_core.WDExternalID(str(row["taxon_id"]), prop_nr="P10"))
                item = wdi_core.WDItemEngine(wd_item_id=wbid, data=data, mediawiki_api_url=mediawiki_api_url)
                item.write(login=login)
        else:
            print(wbid+"already covered")










