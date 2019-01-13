from datetime import timedelta
from pprint import pprint
import json
import pickle
import unittest

from bs4 import BeautifulSoup as soup
from matplotlib.patches import Polygon
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.basemap import Basemap
from tqdm import tqdm
import geopy.distance
import requests, requests_cache

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


requests_cache.install_cache('web_cache', expire_after=timedelta(days=300))

# we are screem scraping for good instead of evil, so lets pretend we are a real browser
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
states=['alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado', 'connecticut', 
        'florida', 'georgia', 'idaho', 'illinois', 'hawaii', 'indiana', 'iowa', 'kansas', 
        'kentucky', 'louisiana', 'maine', 'maryland', 'massachusetts', 'michigan', 'minnesota', 
        'mississippi', 'missouri', 'montana', 'nebraska', 'nevada', 'new-hampshire', 'new-jersey', 
        'new-mexico', 'new-york', 'north-carolina', 'north-dakota', 'ohio', 'oklahoma', 'oregon', 
        'pennsylvania', 'rhode-island', 'south-carolina', 'south-dakota', 'tennessee', 'texas', 'utah', 
        'vermont', 'virginia', 'washington', 'west-virginia', 'wisconsin', 'wyoming' ]


def getLaQuintaLocations():
    locationlist = []
    print 'fetching master LaQuinta list'

    url = 'https://www.lq.com/en'
    r = requests.get(url, headers=headers)
    page_soup = soup(r.text, "html.parser") 
    item = page_soup.find_all("a")
    print 'getting inn ids'
    for scripttags in page_soup.find_all("script"):
        if 'hotelUrls' in scripttags.text:
            jkl = scripttags.text.split("\n")
            jsonstring = jkl[3].replace ('hotelUrls:', '').replace("\\'", '')[:-1]
            print 'getting geo info for inns'
            for id, uri in tqdm(json.loads(jsonstring).items(), unit='inn'):
                if uri.split('/')[1] in states:
                    r2 = requests.get('https://www.lq.com/bin/lq/hotel-summary.%s.en.json' % id, headers=headers)
                    data = r2.json()
                    locationlist.append({'address': data['address'], 
                                         'stateProvince': data['address']['stateProvince'],
                                         'latitude': data['latitude'],
                                         'longitude': data['longitude'],
                                         })

    print "\nfound", len(locationlist), 'LaQuinta locations'
    return locationlist

def getDennysLocations():
    locationlist = []
    # get top level list
    print 'fetching master Denny\'s list'
    url = 'https://locations.dennys.com/index.html'
    r = requests.get(url, headers=headers)

    page_soup = soup(r.text, "html.parser") 
    directoryitems = page_soup.find_all("a", {'class': 'c-directory-list-content-item-link'})
    print 'fetching Denny\'s state pages'
    for a in tqdm(directoryitems):
        # iterate over each state's page
        print a['href'],
        url = 'https://locations.dennys.com/%s' % a['href']
        r = requests.get(url, headers=headers)
        page_soup = soup(r.text, "html.parser") 
        
        mapitem = page_soup.find("script", {'class': 'js-map-config'})
        j = json.loads(mapitem.contents[0])
        for loc in j['locs']:
            loc['address'] = loc['altTagText'].replace('Location at ', '')
            ''' add a state field from the address in the alt text, always ends with abreviated state '''
            loc['stateProvince'] = loc['altTagText'][-2:]
        locationlist.extend(j['locs'])
    print "\nfound", len(locationlist), 'Denny\'s locations'
    return locationlist

def calculate_proximity():
    print 'finding nearest Denny\'s for each LaQuinta Inn'
    try:
        df = pickle.load( open( "laquintadennyscache.p", "rb" ) )
    except:
        df = pd.DataFrame(columns=['dennys_address', 'la_quinta_address', 'distance'])
        data = {'dennys': getDennysLocations(),
                'la_quinta': getLaQuintaLocations()}
        for la_quinta in tqdm(data['la_quinta'], unit='inn'):
            coords_la_quinta = (la_quinta['latitude'], la_quinta['longitude'])
            closest_dennys = None
            closest_dennys_distance = None
            for dennys in data['dennys']:
                distance  = geopy.distance.vincenty((la_quinta['latitude'], la_quinta['longitude']), 
                                                    (dennys['latitude'], dennys['longitude'])).mi
                if closest_dennys_distance is None or distance < closest_dennys_distance:
                    closest_dennys_distance = distance
                    closest_dennys = dennys
            row = {
                   'la_quinta_address': "%s %s, %s" % (la_quinta['address']['street'],
                                                       la_quinta['address']['city'],
                                                       la_quinta['address']['stateProvince'],
                                                       ),
                   'la_quinta_state': la_quinta['address']['stateProvince'],
                   'latitude': la_quinta['latitude'],
                   'longitude': la_quinta['longitude'],
                   'distance': closest_dennys_distance,
                   'dennys_address': closest_dennys['address'],
                   'dennys_state': closest_dennys['stateProvince'],
                   }
    
            df = df.append(row, ignore_index=True)
        data['df'] = df
        pickle.dump( df, open( "laquintadennyscache.p", "wb" ) )
    return df

def histogram(df):
    print df['longitude']
    ''' histogram of distances to Denny's '''
    print 'creating histogram'
    print 'all LaQuintas', df.shape
    print 'all LaQuintas with a Denny\'s less than a mile away', df[df['distance'] < 1].shape
    print 'all LaQuintas with a Denny\'s less than 2/10th mile away', df[df['distance'] < .2].shape

    pd.set_option('display.width', None)

    print df.columns
    print df[df['la_quinta_state'] != df['dennys_state']].groupby(['la_quinta_state']).count()
    print  df.loc[df['distance'].idxmax()]
    return
#     all LaQuinta locations
    ax = df['distance'].hist(bins=15)
    ax.grid(False)
    plt.xlabel("Denny's distance to a La Quinta (mi)",fontsize=15)
    plt.show()


def create_map(df):
    # create the map
    print 'creating map'
    map = Basemap(llcrnrlon=-119,llcrnrlat=22,urcrnrlon=-64,urcrnrlat=49,
            projection='lcc',lat_1=33,lat_2=45,lon_0=-95)
    map.readshapefile('st99_d00', name='states', drawbounds=True)

    lat = df['latitude'].values
    lon = df['longitude'].values
    
    population = []
    for jkl in df['distance'].values:
        population.append(df['distance'].max()-jkl)

    #https://jakevdp.github.io/PythonDataScienceHandbook/04.13-geographic-data-with-basemap.html
    map.scatter(lon, lat, latlon=True, c=df['distance'].values, cmap='RdBu', alpha=0.5)

    cb = plt.colorbar(orientation='vertical', shrink = 1.0)
#     c_ax.yaxis.set_ticks_position('left')
    plt.show()
    return df


class Test(unittest.TestCase):

    def testLaQuinta(self):
        locationlist = getLaQuintaLocations()
        self.assertGreaterEqual(len(locationlist), 912)  # as of Jan 2019, there were 912 LaQuinta locations listed

    def testDennys(self):
        locationlist = getDennysLocations()
        self.assertGreaterEqual(len(locationlist), 1157)  # as of Jan 2019, there were 1157 Denny's locations listed

    def testCreateMap(self):
        df = calculate_proximity()
        histogram(df)
#         create_map(df)

if __name__ == "__main__":
    df = create_map()
    histogram(df)
