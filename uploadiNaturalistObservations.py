from wikidataintegrator import wdi_core, wdi_login, wdi_config
import requests
import pandas as pd
import pprint
import os


mediawiki_api_url = "https://biodiversity.wiki.opencura.com/w/api.php" # <- change to applicable wikibase
sparql_endpoint_url = "https://biodiversity.wiki.opencura.com/query/sparql"  # <- change to applicable wikibase

wdi_config.config["SPARQL_ENDPOINT_URL"] = sparql_endpoint_url
wdi_config.config["MEDIAWIKI_API_URL"] = mediawiki_api_url
if "WDUSER" in os.environ and "WDPASS" in os.environ:
    WDUSER = os.environ['WDUSER']
    WDPASS = os.environ['WDPASS']
    INATURALISTDOWNLOAD = os.environ['INATURALISTDOWNLOAD']
else:
    raise ValueError("WDUSER and WDPASS and INATURALISTDOWNLOAD must be specified in local.py or as environment variables")
login = wdi_login.WDLogin(WDUSER, WDPASS, mediawiki_api_url=mediawiki_api_url)

def get_or_createItem(label, description="", data=[], lang="en"):
   label_search = wdi_core.WDItemEngine.get_wd_search_results(search_string=label, mediawiki_api_url=mediawiki_api_url)
   if len(label_search) == 0:
      localEntityEngine = wdi_core.WDItemEngine.wikibase_item_engine_factory(mediawiki_api_url,sparql_endpoint_url)
      item = localEntityEngine(data=data)
      item.set_label(label, lang=lang)
      item.set_description(description, lang=lang)
      return item.write(login)
   else:
      return label_search[0]

def sparql(query, endpoint):
   print(query)
   return wdi_core.WDItemEngine.execute_sparql_query(query, endpoint=endpoint)

print("Downloading from iNaturalist")
df=pd.read_csv(INATURALISTDOWNLOAD, compression="zip")
pprint.pprint(df)

observations = {}
for row in df.itertuples():
  if str(row.id) not in observations.keys():
    observations[str(row.id)] = {}
    observations[str(row.id)]["observed_on"] = row.observed_on
    observations[str(row.id)]["user_login"] = row.user_login
    observations[str(row.id)]["quality_grade"] = row.quality_grade
    observations[str(row.id)]["license"] = row.license
    observations[str(row.id)]["url"] = row.url
    observations[str(row.id)]["latitude"] = row.latitude
    observations[str(row.id)]["longitude"] = row.longitude
    observations[str(row.id)]["scientific_name"] = row.scientific_name
    observations[str(row.id)]["taxon_id"] = row.taxon_id
    observations[str(row.id)]["image_url"] = []
  observations[str(row.id)]["image_url"].append(row.image_url)

wikibaseEntityEngine = wdi_core.WDItemEngine.wikibase_item_engine_factory(mediawiki_api_url, sparql_endpoint_url)
for observation in observations.keys():
    try:
        data = []
        data.append(wdi_core.WDString(value=observation, prop_nr="P1"))
        print("+" + str(observations[observation]["observed_on"]) + "T00:00:00Z")

        data.append(wdi_core.WDTime("+" + str(observations[observation]["observed_on"]) + "T00:00:00Z", prop_nr="P2"))
        data.append(
            wdi_core.WDUrl("https://www.inaturalist.org/people/" + observations[observation]["user_login"], prop_nr="P3"))
        data.append(wdi_core.WDItemID(value=get_or_createItem(label=observations[observation]["quality_grade"]),
                                      prop_nr="P4"))  # P4)
        data.append(
            wdi_core.WDItemID(value=get_or_createItem(label=observations[observation]["license"], description="License"),
                              prop_nr="P5"))
        data.append(wdi_core.WDUrl(observations[observation]["url"], prop_nr="P6"))
        for image_url in observations[observation]["image_url"]:
            try:
                data.append(wdi_core.WDUrl(image_url.split("?")[0].replace("medium", "original"), prop_nr="P7"))
            except:
                pass
        data.append(wdi_core.WDGlobeCoordinate(latitude=observations[observation]["latitude"],
                                               longitude=observations[observation]["longitude"],
                                               precision=0.016666666666667, prop_nr="P8"))
        data.append(wdi_core.WDItemID(
            value=get_or_createItem(observations[observation]["scientific_name"], description="Scientific taxon name"),
            prop_nr="P9"))
        # data.append(wdiobservations[observation]["taxon_id"], prop_nr="P10")

        item = wikibaseEntityEngine(data=data)
        item.set_label("iNaturalist observation " + observation, lang="en")
        item.set_description("Observation of " + observations[observation]["scientific_name"], lang="en")
        # pprint.pprint(item.get_wd_json_representation())
        obslabel_search = wdi_core.WDItemEngine.get_wd_search_results(
            search_string="iNaturalist observation " + observation, mediawiki_api_url=mediawiki_api_url)
        if len(obslabel_search) == 0:
            try:
                print(item.write(login))
            except:
                pass
        else:
            print(obslabel_search[0])
    except:
        continue
