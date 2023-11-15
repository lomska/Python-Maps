# The map shows the 43,000 witch trials that took place in Europe between 1300
# and 1850. The data was collected by T. Leeson and Jacob W. Russ for their 
# economic research and can be found on Russ’s repo: 
# https://github.com/JakeRuss/witch-trials.

# GeoJSON files' sources:
# Eurostat https://ec.europa.eu/eurostat/web/gisco
# leakyMirror's repo https://github.com/leakyMirror/map-of-europe


# IMPORTING THE PACKAGES ******************************************************
# *****************************************************************************

import pandas as pd
import numpy as np

import plotly.graph_objects as go
import plotly.io as pio

import geopandas as gpd
import chardet


# UPLOADING THE DATA **********************************************************
# *****************************************************************************

# 1. Eurostat GeoJSON files:

# EU country polygons
enc_p = chardet.detect(open('geo/eu_polygons_10_2021.geojson',
                            'rb').read())['encoding']
with open('geo/eu_polygons_10_2021.geojson', 'r', encoding=enc_p) as f:
    geojson = json.load(f)

# World's coastlines
enc_c = chardet.detect(open('geo/coast_10_2016.geojson', 'rb').read())['encoding']
with open('geo/coast_10_2016.geojson', 'r', encoding=enc_c) as f:
    json_coast_l = json.load(f)  # polygons --> to transform into lines
with open('geo/coast_10_2016.geojson', 'r', encoding=enc_c) as f:
    json_coast_p = json.load(f)  # polygons -- > to stay polygons :-)

# 2. Additional GeoJSON (to add Ukraine's, Belarus's, and Russia's boundaries):

enc_a = chardet.detect(open('geo/europe.geojson', 'rb').read())['encoding']
with open('geo/europe.geojson', 'r', encoding=enc_a) as f:
    geojson_add = json.load(f)

# 3. Datasets:

# EU geo data
nuts = gpd.read_file('geo/eu_dots_10_2021.geojson')

# Witch trials dataset
trials = pd.read_csv('data/trials.csv')


# WITCH TRIALS DATASET ********************************************************
# *****************************************************************************

# A FEW NOTES TO EXPLAIN THE FURTHER STEPS

# Looking at the dataset, witch trials are detailed to the level of countries, 
# regions, counties, and cities. There are also columns with latitude and 
# longitude. But country (gadm.adm0) is the only completely filled geovariable:

# 0   year           10009 non-null  float64
# 1   decade         10940 non-null  int64
# 2   century        10940 non-null  int64
# 3   tried          10940 non-null  int64
# 4   deaths         7114 non-null   float64
# 5   city           5727 non-null   object
# 6   gadm.adm2      9893 non-null   object --> subregion/county
# 7   gadm.adm1      10781 non-null  object --> region
# 8   gadm.adm0      10940 non-null  object --> country
# 9   lon            5137 non-null   float64
# 10  lat            5137 non-null   float64
# 11  record.source  10940 non-null  object

# Besides the many NaN values, regional division is messy: take the EU NUTS 
# division; some regions will correspond to the 1st level, others to the 2nd 
# and the 3rd, and the same with counties.

# In addition to that, some regions have been completely restructured since 
# the data on them was published (the authors collected the information from 
# multiple unrelated historical sources), so places are now absent from the map.

# That requires re-ordering and a compromise between the level of geographical 
# detail and the admissible amount of NaNs (= as much detail as possible, but
# with minimum value losses). I define them for each country individually. So, 
# for each country, detalization differs. 


# Fixing the data types and some mistakes *************************************

trials = trials.rename(columns={'gadm.adm0': 'country', 'deaths': 'executed'})

trials['executed'] = trials['executed'].fillna(0).astype('int')

trials = trials.drop_duplicates()


def fix_region_0(s):
    if s['gadm.adm1'] == 'Valais':  # Valais is in Switzerland, not in France.
        return 'Switzerland'
    else:
        return s['country']


trials['country'] = trials.apply(fix_region_0, axis=1)


def fix_region_1(s):
    if s['gadm.adm1'] == 'Appenzell':  # There's Appenzell Ausserrhoden and 
        # Appenzell Innerrhoden, and according to the data from surrounding 
        # years, "Appenzell" stands for Appenzell Ausserrhoden: 1) They 
        # have no intersectional years. 2) The death rate is 100% in both.
        return 'Appenzell Ausserrhoden'
    else:
        return s['gadm.adm1']


trials['gadm.adm1'] = trials.apply(fix_region_1, axis=1)


def fix_region_2(s):
    if s['gadm.adm1'] == 'Wallonie' and s[
            'gadm.adm2'] == 'Luxembourg':  # Luxembourg is also a region in 
                                           # Belgium.
        return 'Luxembourg (BE)'
    else:
        return s['gadm.adm2']


trials['gadm.adm2'] = trials.apply(fix_region_2, axis=1)

trials['city'] = trials['city'].replace('kotz', 'Kotz')


# Re-ordering the dataset *****************************************************

# The next column will do one of the following: 
# update the country's regional division in cases where it changes; 
# unite several territories into one in line with EU NUTS; 
# divide each country with the required detail (country, region, or county):

nuts_dict_1 = {
    
    # Denmark
    'Fyn': 'Southern Denmark', 
    'Ribe': 'Southern Denmark', 
    'South Jutland': 'Southern Denmark',
    'Ringkobing': 'Central Jutland',
    'Storstrom': 'Zealand',
    
    # Ireland
    'Cork': 'Southern', 
    'Kilkenny': 'Southern', 
    'Clare': 'Southern', 
    'Wexford': 'Southern',
    'Waterford': 'Southern', 
    'Tipperary': 'Southern', 
    'Limerick': 'Southern',
    'Louth': 'Eastern and Midland', 
    'Meath': 'Eastern and Midland', 
    'Dublin': 'Eastern and Midland',
    'Donegal': 'Northern and Western', 
    'Galway': 'Northern and Western',
    
    # Portugal
    'Faro': 'Algarve',
    'Grevenmacher': 'Luxembourg', 
    'Luxembourg': 'Luxembourg',
}

nuts_dict_2 = {
    
    # Germany
    'Magdeburg': 'Sachsen-Anhalt',
    'Dessau': 'Sachsen-Anhalt', 
    'Halle': 'Sachsen-Anhalt',

    # UK
    'Hertfordshire': 'Bedfordshire and Hertfordshire', 
    'Bedfordshire': 'Bedfordshire and Hertfordshire',
    'Oxfordshire': 'Berkshire, Buckinghamshire and Oxfordshire', 
    'Buckinghamshire': 'Berkshire, Buckinghamshire and Oxfordshire', 
    'Berkshire': 'Berkshire, Buckinghamshire and Oxfordshire',
    'Cornwall': 'Cornwall and Isles of Scilly',
    'Nottingham': 'Derbyshire and Nottinghamshire', 
    'Derby': 'Derbyshire and Nottinghamshire', 
    'Derbyshire': 'Derbyshire and Nottinghamshire',
    'Dorset': 'Dorset and Somerset', 
    'Somerset': 'Dorset and Somerset',
    'Norfolk': 'East Anglia', 
    'Cambridgeshire': 'East Anglia', 
    'Suffolk': 'East Anglia',
    'Cardiff': 'East Wales',
    'East Riding of Yorkshire': 'East Yorkshire and Northern Lincolnshire',
    'Fife': 'Eastern Scotland', 
    'Stirling': 'Eastern Scotland', 
    'Angus': 'Eastern Scotland',
    'Perthshire and Kinross': 'Eastern Scotland', 
    'Edinburgh': 'Eastern Scotland',
    'East Lothian': 'Eastern Scotland', 
    'West Lothian': 'Eastern Scotland', 
    'Clackmannanshire': 'Eastern Scotland',
    'Wiltshire': 'Gloucestershire, Wiltshire and Bristol/Bath area', 
    'Bristol': 'Gloucestershire, Wiltshire and Bristol/Bath area', 
    'Gloucestershire': 'Gloucestershire, Wiltshire and Bristol/Bath area',
    'Manchester': 'Greater Manchester',
    'Hampshire': 'Hampshire and Isle of Wight',
    'Southampton': 'Hampshire and Isle of Wight',
    'Worcestershire': 'Herefordshire, Worcestershire and Warwickshire',
    'Warwickshire': 'Herefordshire, Worcestershire and Warwickshire',
    'Highland': 'Highlands and Islands',
    'Orkney Islands': 'Highlands and Islands', 
    'Argyll and Bute': 'Highlands and Islands',
    'Shetland Islands': 'Highlands and Islands', 
    'Moray': 'Highlands and Islands',
    'Leicester': 'Leicestershire, Rutland and Northamptonshire',
    'Rutland': 'Leicestershire, Rutland and Northamptonshire',
    'Northamptonshire': 'Leicestershire, Rutland and Northamptonshire',
    'Aberdeenshire': 'North Eastern Scotland', 
    'Aberdeen': 'North Eastern Scotland',
    'York': 'North Yorkshire',
    'Newry and Mourne': 'Northern Ireland', 
    'Lisburn': 'Northern Ireland',
    'Dungannon': 'Northern Ireland',
    'Derry': 'Northern Ireland', 
    'Armagh': 'Northern Ireland',
    'Antrim': 'Northern Ireland',
    'Tyne and Wear': 'Northumberland and Tyne and Wear', 
    'Northumberland': 'Northumberland and Tyne and Wear',
    'Richmond upon Thames': 'Outer London — West and North West', 
    'Hounslow': 'Outer London — West and North West',
    'Shropshire': 'Shropshire and Staffordshire',
    'Staffordshire': 'Shropshire and Staffordshire',
    'Scottish Borders': 'Southern Scotland',
    'South Ayrshire': 'Southern Scotland',
    'Dumfries and Galloway': 'Southern Scotland',
    'South Lanarkshire': 'Southern Scotland',
    'East Ayrshire': 'Southern Scotland',
    'East Sussex': 'Surrey, East and West Sussex',
    'West Sussex': 'Surrey, East and West Sussex',
    'Brighton and Hove': 'Surrey, East and West Sussex',
    'Durham': 'Tees Valley and Durham',
    'Darlington': 'Tees Valley and Durham',
    'West Dunbartonshire': 'West Central Scotland',
    'Renfrewshire': 'West Central Scotland',
    'North Lanarkshire': 'West Central Scotland',
    'Carmarthenshire': 'West Wales and The Valleys', 
    'Pembrokeshire': 'West Wales and The Valleys'
}

def new_region(s):
    
    if s['gadm.adm1'] in list(nuts_dict_1.keys()):
        return nuts_dict_1[s['gadm.adm1']]
    
    elif s['gadm.adm2'] in list(nuts_dict_2.keys()):
        return nuts_dict_2[s['gadm.adm2']]
    
    elif s['country'] in ('Austria', 'Czech Republic', 'France', 'Italy',
                          'Netherlands', 'Poland', 'Spain', 'Sweden',
                          'Switzerland'):
        return s['gadm.adm1']  # detailing at the regional level

    elif s['country'] in ('Belgium', 'Germany', 'United Kingdom'):
        return s['gadm.adm2']  # detailing at the county level

    elif s['country'] in ('Estonia', 'Finland', 'Hungary', 'Norway'):
        return s['country']  # detailing at the country level

trials['new_region'] = trials.apply(new_region, axis=1)


# The next column assigns a corresponding NUTS code to each county, region, or 
# country in the new_region column:

new_id_dict = {
    'Niederosterreich': 'AT12',
    'Wien': 'AT13',
    'Steiermark': 'AT22',
    'Oberosterreich': 'AT31',
    'Salzburg': 'AT32',
    'Tirol': 'AT33',
    'Vorarlberg': 'AT34',
    'Namur': 'BE35',
    'Liege': 'BE33',
    'Hainaut': 'BE32',
    'Brabant Wallon': 'BE31',
    'Luxembourg (BE)': 'BE34',
    'Bruxelles': 'BE10',
    'West-Vlaanderen': 'BE25',
    'Oost-Vlaanderen': 'BE23',
    'Vlaams Brabant': 'BE24',
    'Antwerpen': 'BE21',
    'Plzensky': 'CZ032',
    'Jihocesky': 'CZ031',
    'Prague': 'CZ010',
    'Jihomoravsky': 'CZ064',
    'Stredocesky': 'CZ020',
    'Olomoucky': 'CZ071',
    'Alsace': 'FRF1',
    'Aquitaine': 'FRI1',
    'Auvergne': 'FRK1',
    'Basse-Normandie': 'FRD1',
    'Bourgogne': 'FRC1',
    'Bretagne': 'FRH0',
    'Centre': 'FRB0',
    'Champagne-Ardenne': 'FRF2',
    'Franche-Comte': 'FRC2',
    'Haute-Normandie': 'FRD2',
    'Ile-de-France': 'FR10',
    'Languedoc-Roussillon': 'FRJ1',
    'Limousin': 'FRI2',
    'Lorraine': 'FRF3',
    'Midi-Pyrenees': 'FRJ2',
    'Nord-Pas-de-Calais': 'FRE1',
    'Pays de la Loire': 'FRG0',
    'Picardie': 'FRE2',
    'Poitou-Charentes': 'FRI3',
    "Provence-Alpes-Cote d'Azur": 'FRL0',
    'Rhone-Alpes': 'FRK2',
    'Stuttgart': 'DE11',
    'Karlsruhe': 'DE12',
    'Freiburg': 'DE13',
    'Tubingen': 'DE14',
    'Oberbayern': 'DE21',
    'Niederbayern': 'DE22',
    'Oberpfalz': 'DE23',
    'Oberfranken': 'DE24',
    'Mittelfranken': 'DE25',
    'Unterfranken': 'DE26',
    'Schwaben': 'DE27',
    'Berlin': 'DE30',
    'Brandenburg': 'DE40',
    'Hamburg': 'DE60',
    'Darmstadt': 'DE71',
    'Giessen': 'DE72',
    'Kassel': 'DE73',
    'Mecklenburg-Vorpommern': 'DE80',
    'Braunschweig': 'DE91',
    'Hannover': 'DE92',
    'Luneburg': 'DE93',
    'Weser-Ems': 'DE94',
    'Dusseldorf': 'DEA1',
    'Koln': 'DEA2',
    'Munster': 'DEA3',
    'Detmold': 'DEA4',
    'Arnsberg': 'DEA5',
    'Koblenz': 'DEB1',
    'Trier': 'DEB2',
    'Rheinhessen-Pfalz': 'DEB3',
    'Saarland': 'DEC0',
    'Dresden': 'DED2',
    'Chemnitz': 'DED4',
    'Leipzig': 'DED5',
    'Sachsen-Anhalt': 'DEE0',
    'Schleswig-Holstein': 'DEF0',
    'Thuringen': 'DEG0',
    'Piemonte': 'ITC1',
    'Lombardia': 'ITC4',
    'Trentino-Alto Adige': 'ITH2',
    'Veneto': 'ITH3',
    'Emilia-Romagna': 'ITH5',
    'Toscana': 'ITI1',
    'Umbria': 'ITI2',
    'Marche': 'ITI3',
    'Lazio': 'ITI4',
    'Luxembourg': 'LU00',
    'Groningen': 'NL11',
    'Friesland': 'NL12',
    'Overijssel': 'NL21',
    'Gelderland': 'NL22',
    'Flevoland': 'NL23',
    'Utrecht': 'NL31',
    'Noord-Holland': 'NL32',
    'Zuid-Holland': 'NL33',
    'Zeeland': 'NL34',
    'Noord-Brabant': 'NL41',
    'Limburg': 'NL42',
    'Greater Poland': 'PL41',
    'Lower Silesian': 'PL51',
    'Warmian-Masurian': 'PL62',
    'Pais Vasco': 'ES21',
    'Comunidad Foral de Navarra': 'ES22',
    'Castilla y Leon': 'ES41',
    'Cataluna': 'ES51',
    'Andalucia': 'ES61',
    'Ostergotland': 'SE123',
    'Jonkoping': 'SE211',
    'Kronoberg': 'SE212',
    'Kalmar': 'SE213',
    'Blekinge': 'SE221',
    'Skane': 'SE224',
    'Halland': 'SE231',
    'Vastra Gotaland': 'SE232',
    'Varmland': 'SE311',
    'Vaud': 'CH011',
    'Valais': 'CH012',
    'Geneve': 'CH013',
    'Bern': 'CH021',
    'Fribourg': 'CH022',
    'Solothurn': 'CH023',
    'Neuchatel': 'CH024',
    'Basel-Stadt': 'CH031',
    'Basel-Landschaft': 'CH032',
    'Aargau': 'CH033',
    'Zurich': 'CH040',
    'Glarus': 'CH051',
    'Schaffhausen': 'CH052',
    'Appenzell Ausserrhoden': 'CH053',
    'Appenzell Innerrhoden': 'CH054',
    'Sankt Gallen': 'CH055',
    'Graubunden': 'CH056',
    'Thurgau': 'CH057',
    'Lucerne': 'CH061',
    'Uri': 'CH062',
    'Schwyz': 'CH063',
    'Obwalden': 'CH064',
    'Nidwalden': 'CH065',
    'Ticino': 'CH070',
    'Zug': 'CH066',
    'Tees Valley and Durham': 'UKC1',
    'Northumberland and Tyne and Wear': 'UKC2',
    'Cumbria': 'UKD1',
    'Greater Manchester': 'UKD3',
    'Lancashire': 'UKD4',
    'Cheshire': 'UKD6',
    'East Yorkshire and Northern Lincolnshire': 'UKE1',
    'North Yorkshire': 'UKE2',
    'West Yorkshire': 'UKE4',
    'Derbyshire and Nottinghamshire': 'UKF1',
    'Leicestershire, Rutland and Northamptonshire': 'UKF2',
    'Lincolnshire': 'UKF3',
    'Herefordshire, Worcestershire and Warwickshire': 'UKG1',
    'Shropshire and Staffordshire': 'UKG2',
    'West Midlands': 'UKG3',
    'East Anglia': 'UKH1',
    'Bedfordshire and Hertfordshire': 'UKH2',
    'Essex': 'UKH3',
    'Outer London — West and North West': 'UKI7',
    'Berkshire, Buckinghamshire and Oxfordshire': 'UKJ1',
    'Surrey, East and West Sussex': 'UKJ2',
    'Hampshire and Isle of Wight': 'UKJ3',
    'Kent': 'UKJ4',
    'Gloucestershire, Wiltshire and Bristol/Bath area': 'UKK1',
    'Dorset and Somerset': 'UKK2',
    'Cornwall and Isles of Scilly': 'UKK3',
    'Devon': 'UKK4',
    'West Wales and The Valleys': 'UKL1',
    'East Wales': 'UKL2',
    'North Eastern Scotland': 'UKM5',
    'Highlands and Islands': 'UKM6',
    'Eastern Scotland': 'UKM7',
    'West Central Scotland': 'UKM8',
    'Southern Scotland': 'UKM9',
    'Northern Ireland': 'UKN0',
    'Estonia': 'EE00',
    'Finland': 'FI1',
    'Hungary': 'HU',
    'Norway': 'NO0',
    'Zealand': 'DK02',
    'Southern Denmark': 'DK03',
    'Central Jutland': 'DK04',
    'Northern and Western': 'IE04',
    'Southern': 'IE05',
    'Eastern and Midland': 'IE06',
    'Algarve': 'PT15'
}

trials['map_id'] = trials['new_region'].map(new_id_dict)
trials = trials[trials['map_id'].notna()]


# The next column specifies the level of NUTS detail for each country:


def set_nuts(s):
    if len(str(s['map_id'])) == 5:
        return 3
    elif len(str(s['map_id'])) == 4:
        return 2
    elif len(str(s['map_id'])) == 3 and str(s['map_id']) != 'nan':
        return 1
    elif len(str(s['map_id'])) == 2:
        return 0
    else:
        return s['map_id']


trials['nuts_level'] = trials.apply(set_nuts, axis=1)


# A column with a country code:

trials['cntr_code'] = trials['map_id'].str[:2]


# EU GEO DATASET **************************************************************
# *****************************************************************************

# In this part, I process the NUTS dataset created from GeoJSON at the beginning.

# Codes and names of all the EU countries we'll put on the map:

country_dict = {
    'AL': 'Albania',
    'AT': 'Austria',
    'BE': 'Belgium',
    'BG': 'Bulgaria',
    'CH': 'Switzerland',
    'CZ': 'Czechia',
    'DE': 'Germany',
    'DK': 'Denmark',
    'EE': 'Estonia',
    'EL': 'Greece',
    'ES': 'Spain',
    'FI': 'Finland',
    'FR': 'France',
    'HR': 'Croatia',
    'HU': 'Hungary',
    'IE': 'Ireland',
    'IT': 'Italy',
    'LI': 'Liechtenstein',
    'LT': 'Lithuania',
    'LU': 'Luxembourg',
    'LV': 'Latvia',
    'ME': 'Montenegro',
    'MK': 'Macedonia',
    'MT': 'Malta',
    'NL': 'Netherlands',
    'NO': 'Norway',
    'PL': 'Poland',
    'PT': 'Portugal',
    'RO': 'Romania',
    'RS': 'Serbia',
    'SE': 'Sweden',
    'SI': 'Slovenia',
    'SK': 'Slovakia',
    'UK': 'United Kingdom'
}

# Lists of country codes to extract coordinates from the dataset:

# for the countries aggregated on the NUTS-1 level:
countries_1 = trials[trials['nuts_level'] == 1]['cntr_code'].unique().tolist(
)
# for the countries aggregated on the NUTS-2 level:
countries_2 = trials[trials['nuts_level'] == 2]['cntr_code'].unique().tolist(
) 
# for the countries aggregated on the NUTS-3 level:
countries_3 = trials[trials['nuts_level'] == 3]['cntr_code'].unique().tolist(
) 
# for the countries aggregated on the NUTS-0 (country) level and the countries
# without the data:
present_countries = trials['cntr_code'].unique().tolist(
)  
zero_countries = [
    x for x in list(country_dict.keys()) if x not in present_countries
] 
zero_countries.append('HU')

# Extracting the coordinates & some data:

df_map_0 = nuts[(nuts['CNTR_CODE'].isin(zero_countries))
                & (nuts['LEVL_CODE'] == 0)][[
                    'id', 'CNTR_CODE', 'LEVL_CODE', 'NAME_LATN', 'geometry'
                ]]
df_map_1 = nuts[(nuts['CNTR_CODE'].isin(countries_1))
                & (nuts['LEVL_CODE'] == 1)][[
                    'id', 'CNTR_CODE', 'LEVL_CODE', 'NAME_LATN', 'geometry'
                ]]
df_map_2 = nuts[(nuts['CNTR_CODE'].isin(countries_2))
                & (nuts['LEVL_CODE'] == 2)][[
                    'id', 'CNTR_CODE', 'LEVL_CODE', 'NAME_LATN', 'geometry'
                ]]
df_map_3 = nuts[(nuts['CNTR_CODE'].isin(countries_3))
                & (nuts['LEVL_CODE'] == 3)][[
                    'id', 'CNTR_CODE', 'LEVL_CODE', 'NAME_LATN', 'geometry'
                ]]

df_map = pd.concat([df_map_0, df_map_1, df_map_2,
                    df_map_3])

# Extracting latitude and longitute from the geometry column:

lon = []
lat = []

for i in df_map['geometry']:
    lon.append(i.x)
    lat.append(i.y)

df_map['lon'] = lon
df_map['lat'] = lat


# JOINING THE DATASETS ********************************************************
# *****************************************************************************

# Witch trials dataset + EU geo dataset:

df_map_dec = df_map[[
    'id', 'CNTR_CODE', 'LEVL_CODE', 'NAME_LATN', 'lon', 'lat'
]].set_index('id').join(trials[[
    'map_id', 'decade', 'tried', 'executed'
]].groupby(['map_id', 'decade'
            ]).agg('sum').reset_index().set_index('map_id')).reset_index()


# SOME MORE DATA FOR THE MAP **************************************************
# *****************************************************************************

# Tooltips-1 | the first and last decade of witch trials for each place:

df_map_dec['min_decade'] = df_map_dec.groupby('index')['decade'].transform(
    'min')
df_map_dec['max_decade'] = df_map_dec.groupby('index')['decade'].transform(
    'max')

df_map_dec[['tried', 'executed', 'min_decade', 'max_decade'
            ]] = df_map_dec[['tried', 'executed', 'min_decade',
                             'max_decade']].fillna(0)

# Trials summation + getting rid of the decade column:

df_scatter_total = df_map_dec.groupby([
    'index', 'CNTR_CODE', 'NAME_LATN', 'lon', 'lat', 'min_decade', 'max_decade'
]).agg('sum')[['tried', 'executed']].reset_index()

df_scatter_total[['min_decade', 'max_decade', 'tried',
                  'executed']] = df_scatter_total[[
                      'min_decade', 'max_decade', 'tried', 'executed'
                  ]].astype('int')

# Tooltips-2 | the percentage of executed among the tried:

df_scatter_total[
    'mortality'] = df_scatter_total['executed'] / df_scatter_total['tried']

# Tooltips-3 | country names:

df_scatter_total['country'] = df_scatter_total['CNTR_CODE'].map(country_dict)


# Circles' sizes: to compare their areas, not radiuses, divide by pi


def size1(s):
    if s['tried'] == 0 or s['tried'] == np.nan:
        return 0
    else:
        return np.sqrt(s['tried'] / np.pi) * 1.5


# Circles' centers sizes:


def size2(s):
    if s['tried'] == 0 or s['tried'] == np.nan:
        return 0
    else:
        return 3


df_scatter_total['size1'] = df_scatter_total.apply(size1, axis=1)
df_scatter_total['size2'] = df_scatter_total.apply(size2, axis=1)


# TRANSFORMING THE GEOJSON FILES **********************************************
# *****************************************************************************

# What we want to get on the map: 
# Level-1: Europe continent only, without Africa + surrounding islands;
# Level-2: European countries' borders;
# Level-3: Coastlines;
# Level-4: Scatter map.

# I'll start with the coastlines. The problem is that the Eurostat coastline file 
# creates a solid polygon of Eurasia and Africa. We need only the European part
# and surrounding islands. 

# Transforming one of the coast GeoJSONs from a polygon into a line type:

for p in json_coast_l['features']:
    p['geometry']['type'] = 'LineString'
    p['geometry']['coordinates'] = p['geometry']['coordinates'][0]

# Filtering out all the elements that don't fall into our area of interest 
# (approximately -28:30 by longitude and 32:74 by latitude):

lon_dict = dict()  # longitudes of all the elements in the area of interest
lat_dict = dict()  # latitudes of all the elements in the area of interest
indexes = []  # their ids in the GeoJSON file

for i in range(len(json_coast_l['features'])):
    coord = pd.DataFrame(
        json_coast_l['features'][i]['geometry']['coordinates'])
    idx = json_coast_l['features'][i]['id']
    if coord[0].max() > -28 and coord[0].min() < 30 and coord[1].max(
    ) > 32 and coord[1].min() < 74:
        lon_dict[idx] = coord[0]
        lat_dict[idx] = coord[1]
        indexes.append(idx) # --> GeoJSON IDs to filter

# Filtering the second (polygon) coast GeoJSON by the created IDs list:

new_features = []
for i in range(len(json_coast_p['features'])):
    if json_coast_p['features'][i]['id'] in indexes:
        new_features.append(json_coast_p['features'][i])

json_coast_p['features'] = new_features


# Now we have a line file and a polygon file with only the elements that 
# fall into our area of interest. One of these elements is Eurasia-Africa. 
# We need to leave only the European part.

# I'll cut the polygon by creating an index for each coordinate point and
# then filtering out unnecessary points by this index. 

main_df = pd.DataFrame(json_coast_l['features'][0]['geometry']['coordinates'])
main_df.columns = ['lon', 'lat']
main_df['index'] = list(range(len(main_df['lon'])))

# After checking the map, I manually selected the point range to display
# (the line will start near Turkey and end after the Finnish-Russian border):

main_df_eu = main_df[(main_df['index'] > 5231) & (main_df['index'] < 8051)]

# Replacing the Eurasia-Africa coordinates with truncated coordinates --> lines:

lon_dict[1] = main_df_eu['lon'].tolist()
lat_dict[1] = main_df_eu['lat'].tolist()

# Replacing the Eurasia-Africa coordinates with truncated coordinates --> polygons:

coordinates_0 = []

for lon, lat in zip(main_df_eu['lon'].tolist(), main_df_eu['lat'].tolist()):
    coordinates_0.append([lon, lat])

json_coast_p['features'][0]['geometry']['coordinates'] = [coordinates_0]


# The EU file misses the data on Ukraine's, Belarus's, and Russia's borders, so
# let's extract them from another GeoJSON and append:

add_features = []

for i in range(len(geojson_add['features'])):
    geojson_add['features'][i]['id'] = geojson_add['features'][i][
        'properties']['ISO2']
    if geojson_add['features'][i]['id'] in ['BY', 'RU', 'UA']:
        add_features.append(geojson_add['features'][i])

country_dict['RU'] = 'Russia'
country_dict['BY'] = 'Belarus'
country_dict['UA'] = 'Ukraine'

geojson['features'].extend(add_features)


# + I'll delete one Norwegian island that ruins the view:

geojson['features'][1984]['geometry']['coordinates'] = geojson['features'][
    1984]['geometry']['coordinates'][:-1]


# DRAWING THE MAP *************************************************************
# *****************************************************************************

fig = go.Figure()

# IDs of elements that I want to exclude from the view:
indexes_to_exclude = [360, 527, 1789, 1241] 


# Layer 1 | Polygons | Europe's and islands' lands

fig.add_choropleth(
    geojson=json_coast_p,
    locations=[idx for idx in indexes if idx not in indexes_to_exclude],
    z=[1] * len(indexes),
    text=[idx for idx in indexes if idx not in indexes_to_exclude],
    colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(64, 64, 64, 0.5)']],
    showscale=False,
    marker=dict(line_color='rgba(0,0,0,0)'),
    hoverinfo='none')

# Layer 2 | Polygons | Country boundaries

fig.add_choropleth(geojson=geojson,
                   locations=list(country_dict.keys()),
                   z=[1] * len(list(country_dict.keys())),
                   colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
                   showscale=False,
                   marker=dict(line_width=0.5,
                               line_color='rgba(64, 64, 64, 0.7)'),
                   hoverinfo='none')

# Layer 3 | Lines | Europe's and islands' coastlines

widths = [3.1, 2.5, 2.5, 1.5, 1.5, 0.5]
colors = ['rgba(64, 64, 64, 0.4)', 'rgba(1, 1, 1, 1.0)', 'rgba(64, 64, 64, 0.6)',
          'rgba(1, 1, 1, 1.0)', 'rgba(64, 64, 64, 0.8)', 'rgba(64, 64, 64, 1)']

for i in [h for h in indexes if h not in indexes_to_exclude]:
    for width, color in zip(widths, colors): # this loop is just for better design
        fig.add_scattergeo(lat=lat_dict[i],
                           lon=lon_dict[i],
                           mode='lines',
                           line=dict(width=width, color=color),
                           hoverinfo='none')

# Layer 4 | Points | Scatter map - circles

fig.add_scattergeo(lat=df_scatter_total['lat'],
                   lon=df_scatter_total['lon'],
                   mode='markers',
                   marker=dict(size=df_scatter_total['size1'] * 2,
                               color='rgba(155,1,3,0.3)',
                               showscale=False,
                               line_width=0,
                               line_color='rgba(0,0,0,0)',
                               gradient=dict(
                                   color='rgba(255,178,0,0.9)',
                                   type="radial",
                               )),
                   hoverinfo='none')

# Layer 5 | Points | Scatter map - circles' centers

fig.add_scattergeo(lat=df_scatter_total['lat'],
                   lon=df_scatter_total['lon'],
                   mode='markers',
                   marker=dict(size=df_scatter_total['size2'],
                               color='rgba(255,234,187,0.8)',
                               showscale=False,
                               line_width=0,
                               line_color='rgba(0,0,0,0)'),
                   hoverinfo='none')

# Layer 6 | Points (Invisible) | Tooltips

fig.add_scattergeo(
    lat=df_scatter_total[df_scatter_total['tried'] > 0]['lat'],
    lon=df_scatter_total[df_scatter_total['tried'] > 0]['lon'],
    mode='markers',
    marker=dict(size=df_scatter_total[df_scatter_total['tried'] > 0]['size1'] * 2,
                color='rgba(0,0,0,0)',
                showscale=False,
                line_width=0,
                line_color='rgba(0,0,0,0)'),
    customdata=np.stack(
        (df_scatter_total[df_scatter_total['tried'] > 0]['NAME_LATN'], 
         df_scatter_total[df_scatter_total['tried'] > 0]['country'],
         df_scatter_total[df_scatter_total['tried'] > 0]['min_decade'],
         df_scatter_total[df_scatter_total['tried'] > 0]['max_decade'],
         df_scatter_total[df_scatter_total['tried'] > 0]['tried'], 
         df_scatter_total[df_scatter_total['tried'] > 0]['executed'],
         df_scatter_total[df_scatter_total['tried'] > 0]['mortality']),
        axis=-1),
    hovertemplate=
    '<extra></extra><b>%{customdata[0]} | %{customdata[1]}\
    <br><br><span style="color:#c66a0e;font-size:27">%{customdata[2]}-%{customdata[3]}</span>\
    <br><br><span style="color:#c66a0e;font-size:27">%{customdata[4]:,.0f}</span>\
    people were tried for witchcraft\
    <br><span style="color:#c66a0e;font-size:27">%{customdata[5]:,.0f} (%{customdata[6]:,.0%})</span>\
    of them were killed</b>'
)


# Legend | Title

fig.add_annotation(xref="x domain",
                   yref="y domain",
                   text="<b>Number of people tried for witchcraft:</b>",
                   showarrow=False,
                   x=0.065,
                   y=0.82,
                   font=dict(color='rgba(255,234,187,0.8)',
                             family='Almendra Display',
                             size=21),
                   align='left')

# Legend | Circles

fig.add_scatter(x=[0.07, 0.17, 0.27, 0.37],
                y=[0.755, 0.755, 0.755, 0.755],
                mode='markers',
                marker=dict(size=[
                    np.sqrt(10 / np.pi) * 3,
                    np.sqrt(100 / np.pi) * 3,
                    np.sqrt(1000 / np.pi) * 3,
                    np.sqrt(3000 / np.pi) * 3
                ],
                            color='rgba(155,1,3,0.3)',
                            showscale=False,
                            line_width=0,
                            line_color='rgba(0,0,0,0)',
                            gradient=dict(
                                color='rgba(255,178,0,0.9)',
                                type="radial",
                            )),
                hoverinfo='none')

# Legend | Circles' centers

fig.add_scatter(
    x=[0.07, 0.17, 0.27, 0.37],
    y=[0.755, 0.755, 0.755, 0.755],
    mode='markers+text',
    marker=dict(size=[3, 3, 3, 3],
                color='rgba(255,234,187,0.8)',
                showscale=False,
                line_width=0,
                line_color='rgba(0,0,0,0)'),
    text=['<b> 10</b>', '<b> 100</b>', '<b> 1,000</b>', '<b> 3,000</b>'],
    textfont=dict(color='rgba(255,234,187,0.8)',
                  family='Almendra Display',
                  size=21),
    textposition='middle right',
    hoverinfo='none')


# Footer

fig.add_annotation(
    xref="paper",
    yref="paper",
    text=
    "<b>Created by Tanya Lomskaya\
    <br>Datasource: Leeson, P. T. and Russ, J. W.. Witch Trials. 2018 - The Economic Journal | Github.com/JakeRuss/witch-trials<br></b>",
    showarrow=False,
    x=0.5,
    y=0.0035,
    font=dict(color='rgba(255,234,187,0.8)',
              family='Almendra Display',
              size=18),
    align='center')


# Layout 

fig.update_xaxes(range=[0, 1],
                 showticklabels=False,
                 showgrid=False,
                 zeroline=False)

fig.update_yaxes(range=[0, 1],
                 showticklabels=False,
                 showgrid=False,
                 zeroline=False)

fig.update_geos(bgcolor='rgba(0,0,0,0)',
                showcountries=False,
                landcolor='rgba(0,0,0,0)',
                framecolor='rgba(0,0,0,0)',
                projection=dict(type='miller'),
                showlakes=False,
                scope='europe',
                lonaxis=dict(range=[-13, 30]),
                lataxis=dict(range=[37, 73.75]))

fig.update_layout(title='<b>Witch Trials in Europe<br>1300-1850</b>',
                  title_x=0.5,
                  title_y=0.92,
                  titlefont=dict(family='Almendra Display',
                                 size=37.5,
                                 color='rgba(255,234,187,0.8)'),
                  paper_bgcolor='#010103',
                  plot_bgcolor='#010103',
                  margin=dict(r=0, l=0, t=0, b=30),
                  width=1050,
                  height=1395,
                  showlegend=False,
                  hoverlabel=dict(bgcolor="#010103",
                                  font=dict(family='Almendra Display',
                                            size=22.5,
                                            color='rgba(255,234,187,1)')))


pio.write_image(fig, 'proportional_symbols.png', width=1050, height=1395)

fig.show()