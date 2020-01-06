import random
import requests
from bs4 import BeautifulSoup
import json
import time
import os


def get_ip_list(url, headers):
    web_data = requests.get(url, headers=headers)
    soup = BeautifulSoup(web_data.text, 'lxml')
    ips = soup.find_all('tr')
    ip_list = []
    for i in range(1, len(ips)):
        ip_info = ips[i]
        tds = ip_info.find_all('td')
        ip_list.append(tds[1].text + ':' + tds[2].text)
    return ip_list


def get_random_ip(ip_list):
    proxy_list = []
    for ip in ip_list:
        proxy_list.append('http://' + ip)
    proxy_ip = random.choice(proxy_list)
    proxies = {'http': proxy_ip}
    return proxies


def get_headers():
    user_agent_list = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/45.0.2454.85 Safari/537.36 115Browser/6.0.3',
        'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
        'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
        'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0',
        'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
    ]
    user_agent = random.choice(user_agent_list)
    return {'Connection': 'close', 'User-Agent': user_agent}


server = 'https://www.transfermarkt.com'

def get_data_by_country(part_data,country_url_list, land_id, ip_list):
    all_countries = part_data

    for country in country_url_list.keys():
        #判断是否已有该国家数据
        index = -1
        for i in range(len(all_countries)):
            if all_countries[i]['Country']==country:
                index = i
                break
        if index>=0:
            continue

        country_url = server + '/' + country_url_list[country]
        print('country:',country)

        cou = {}
        cou['Country'] = country

        #league info
        while 1:
            try:
                start_page = requests.get(country_url, headers=get_headers(), proxies=get_random_ip(ip_list))
                break
            except:
                print('connection failed,try again...')
                time.sleep(1 + random.random())
                continue

        print('getting league info...')
        cou['LeagueInfo'] = {}
        start_page_bs = BeautifulSoup(start_page.text, 'html.parser')
        cou['LeagueInfo']['LeagueName'] = start_page_bs.find('h1', class_='spielername-profil').string
        profil_tables = start_page_bs.find_all('table', class_='profilheader')
        profil_table1_bs = BeautifulSoup(str(profil_tables[0]), 'html.parser')
        cou['LeagueInfo']['Players'] = profil_table1_bs.find_all('td')[2].string.strip()
        cou['LeagueInfo']['Foreigners'] = profil_table1_bs.find_all('a')[-1].string.split('\xa0')[0]
        cou['LeagueInfo']['ForeignersPercent'] = profil_table1_bs.find_all('span')[-1].string.replace(',', '.')
        cou['LeagueInfo']['AverageMarketValue'] = profil_table1_bs.find_all('td')[-1].string.strip().replace('€', '')
        cou['LeagueInfo']['AverageAge'] = BeautifulSoup(str(profil_tables[1]), 'html.parser').find_all('td')[2].contents[0].strip().replace(',','.')
        total_div = start_page_bs.find('div',class_='marktwert')
        total_a = BeautifulSoup(str(total_div), 'html.parser').find('a')
        cou['LeagueInfo']['TotalMarketValue'] = total_a.contents[1]+total_a.contents[2].string

        print('getting foreigners and natives...')
        for season in range(2009, 2019):
            season_url = country_url + '/saison_id/' + str(season)
            print('season:', season)

            while 1:
                try:
                    reg = requests.get(season_url, headers=get_headers(), proxies=get_random_ip(ip_list))
                    break
                except:
                    print('connection failed,try again...')
                    time.sleep(1 + random.random())
                    continue

            html_bs = BeautifulSoup(reg.text, 'html.parser')

            if 'Foreigners' not in cou.keys():
                cou['Foreigners'] = {}

            foreigners_table = html_bs.find('table', class_='items')
            if foreigners_table is None:
                continue

            foreigners_table_bs = BeautifulSoup(str(foreigners_table), 'html.parser')
            foreigners_trs = foreigners_table_bs.find_all('tr', class_='odd') + foreigners_table_bs.find_all('tr',class_='even')

            cou['Foreigners'][season] = []

            for foreigners_tr in foreigners_trs:
                foreigners_tr_bs = BeautifulSoup(str(foreigners_tr), 'html.parser')
                tds = foreigners_tr_bs.find_all('td')

                temp = {}
                temp['Country'] = foreigners_tr_bs.find('img').get('alt')
                number_a = foreigners_tr_bs.find_all('a')[1]
                temp['Number'] = number_a.string
                detail_link = server + number_a.get('href')
                temp['Share'] = tds[2].string.replace(',', '.')
                temp['Players'] = []

                #natives
                if 'Natives' not in cou.keys():
                    cou['Natives'] = {}
                if season not in cou['Natives'].keys():
                    native_link = '='.join(detail_link.split('=')[:-1])+'='+str(land_id[country])

                    while 1:
                        try:
                            natives_page = requests.get(native_link, headers=get_headers(),proxies=get_random_ip(ip_list))
                            break
                        except:
                            print('connection failed,try again...')
                            time.sleep(1 + random.random())
                            continue

                    native_page_bs = BeautifulSoup(natives_page.text, 'html.parser')
                    native_table = native_page_bs.find('table',class_='items')
                    if native_table is None:
                        cou['Natives'][season] = 0
                    else:
                        native_pager = native_page_bs.find('div',class_='pager')
                        if native_pager is None:
                            native_table_bs = BeautifulSoup(str(native_table), 'html.parser')
                            natives = native_table_bs.find_all('tr',class_='odd')+native_table_bs.find_all('tr',class_='even')
                            cou['Natives'][season] = len(natives)
                        else:
                            last_page_link = server+BeautifulSoup(str(native_pager), 'html.parser').find_all('a')[-1].get('href')
                            pages = int(last_page_link.split('/')[-1])
                            while 1:
                                try:
                                    last_page = requests.get(last_page_link, headers=get_headers(),proxies=get_random_ip(ip_list))
                                    break
                                except:
                                    print('connection failed,try again...')
                                    time.sleep(1 + random.random())
                                    continue
                            last_page_bs = BeautifulSoup(last_page.text, 'html.parser')
                            last_page_table = last_page_bs.find('table',class_='items')
                            last_page_table_bs = BeautifulSoup(str(last_page_table), 'html.parser')
                            last_num = len(last_page_table_bs.find_all('tr',class_='odd')+last_page_table_bs.find_all('tr',class_='even'))
                            cou['Natives'][season] = (pages-1)*25+last_num

                while 1:
                    try:
                        players_page = requests.get(detail_link, headers=get_headers(), proxies=get_random_ip(ip_list))
                        break
                    except:
                        print('connection failed,try again...')
                        time.sleep(1 + random.random())
                        continue

                players_page_bs = BeautifulSoup(players_page.text, 'html.parser')
                players_table = players_page_bs.find('table', class_='items')
                players_table_bs = BeautifulSoup(str(players_table), 'html.parser')
                players_trs = players_table_bs.find_all('tr', class_='odd') + players_table_bs.find_all('tr',class_='even')

                for player_tr in players_trs:
                    player_tr_bs = BeautifulSoup(str(player_tr), 'html.parser')
                    player_as = player_tr_bs.find_all('a')

                    player = {}
                    player['PlayerName'] = player_tr_bs.find('img').get('alt')
                    player['Position'] = player_tr_bs.find_all('td')[3].string  # strum???
                    #profil_link = server + player_as[0].get('href')
                    player['Club'] = player_tr_bs.find_all('img')[1].get('alt') if len(
                        player_tr_bs.find_all('img')) >= 2 else player_tr_bs.find('td', class_='zentriert').string
                    player['Debut'] = player_as[-3].string
                    player['Appearances'] = player_as[-2].string
                    player['Goals'] = player_as[-1].string

                    temp['Players'].append(player)

                cou['Foreigners'][season].append(temp)

        all_countries.append(cou)

        #保存数据
        print('one country finished,saving data...')
        json_data = json.dumps(all_countries)
        json_file = open('data_by_country.json', 'w')
        json_file.write(json_data)
        json_file.close()

    return all_countries

def get_confederation(data,all_country_url,ip_list):
    print('get confederation and points...')
    for season in range(2009,2019):
        print('season:',season)
        count = 0
        for page in range(1,10):
            url = all_country_url[season] + '/page/'+str(page)

            while 1:
                try:
                    reg = requests.get(url, headers=get_headers(), proxies=get_random_ip(ip_list))
                    break
                except:
                    print('connection failed,try again...')
                    time.sleep(1 + random.random())
                    continue

            html_bs = BeautifulSoup(reg.text,'html.parser')
            table = html_bs.find('table',class_='items')
            table_bs = BeautifulSoup(str(table), 'html.parser')
            trs = table_bs.find_all('tr',class_='odd')+table_bs.find_all('tr',class_='even')

            for tr in trs:
                tr_bs = BeautifulSoup(str(tr),'html.parser')
                tds = tr_bs.find_all('td')
                country = tr_bs.find('img').get('alt')
                if country == 'Bosnia':
                    country = 'Bosnia-Herzegovina'

                index = -1
                for i in range(len(data)):
                    if data[i]['Country'] == country:
                        index = i
                        break
                if index==-1:
                    continue
                count += 1

                if 'Confederation' not in data[index].keys():
                    data[index]['Confederation'] = tds[-2].string
                
                if 'Points' not in data[index].keys():
                    data[index]['Points'] = {}

                data[index]['Points'][season] = tds[-1].string
                print(data[index])

                if count >= 66:
                    break
            if count >= 66:
                break

        if count<66:
            print('以下国家该赛季不在表单中：')
            for t in data:
                if 'Confederation' not in t.keys():
                    print(t['Country'])

    return data


url = 'http://www.xicidaili.com/nn/'
ip_list = get_ip_list(url, headers=get_headers())

country_url_list = {'Albania': 'kategoria-superiore/gastarbeiter/wettbewerb/ALB1',
                    'Algeria': 'ligue-professionnelle-1/gastarbeiter/wettbewerb/ALG1',
                    'Argentina': 'superliga/gastarbeiter/wettbewerb/AR1N',
                    'Australia': 'a-league/gastarbeiter/wettbewerb/AUS1',
                    'Austria': 'bundesliga/gastarbeiter/wettbewerb/A1',
                    'Azerbaijan': 'premyer-liqasi/gastarbeiter/wettbewerb/AZ1',
                    'Belarus': 'vysheyshaya-liga/gastarbeiter/wettbewerb/WER1',
                    'Belgium': 'jupiler-pro-league/gastarbeiter/wettbewerb/BE1',
                    'Bosnia-Herzegovina': 'premijer-liga/gastarbeiter/wettbewerb/BOS1',
                    'Brazil': 'campeonato-brasileiro-serie-a/gastarbeiter/wettbewerb/BRA1',
                    'Bulgaria': 'efbet-liga/gastarbeiter/wettbewerb/BU1',
                    'Canada': 'canadian-premier-league-spring-season/gastarbeiter/wettbewerb/CAN1',
                    'Chile': 'campeonato-plan-vital-primera-division/gastarbeiter/wettbewerb/CLPD',
                    'China': 'chinese-super-league/gastarbeiter/wettbewerb/CSL',
                    # 'Colombia':'',
                    'Costa Rica': 'primera-division-apertura-finale/gastarbeiter/wettbewerb/CIF',
                    'Croatia': '1-hnl/gastarbeiter/wettbewerb/KR1',
                    'Cyprus': 'first-division/gastarbeiter/wettbewerb/ZYP1',
                    'Czech Republic': 'fortuna-liga/gastarbeiter/wettbewerb/TS1',
                    'Denmark': 'superligaen/gastarbeiter/wettbewerb/DK1',
                    'Ecuador': 'ligapro-serie-a/gastarbeiter/wettbewerb/EC1N',
                    'Egypt': 'egyptian-premier-league/gastarbeiter/wettbewerb/EGY1',
                    'England': 'premier-league/gastarbeiter/wettbewerb/GB1',
                    'Estonia': 'premium-liiga/gastarbeiter/wettbewerb/EST1',
                    'Finland': 'veikkausliiga/gastarbeiter/wettbewerb/FI1',
                    'France': 'ligue-1/gastarbeiter/wettbewerb/FR1',
                    'Georgia': 'crystalbet-erovnuli-liga/gastarbeiter/wettbewerb/GE1N',
                    'Germany': 'bundesliga/gastarbeiter/wettbewerb/L1',
                    'Ghana': 'premier-league/gastarbeiter/wettbewerb/GHPL',
                    'Greece': 'super-league-1/gastarbeiter/wettbewerb/GR1',
                    'Hungary': 'nemzeti-bajnoksag/gastarbeiter/wettbewerb/UNG1',
                    'Iceland': 'pepsi-max-deild/gastarbeiter/wettbewerb/IS1',
                    'India': 'indian-super-league/gastarbeiter/wettbewerb/IND1',
                    'Iran': 'persian-gulf-pro-league/gastarbeiter/wettbewerb/IRN1',
                    'Israel': 'ligat-haal/gastarbeiter/wettbewerb/ISR1',
                    'Italy': 'serie-a/gastarbeiter/wettbewerb/IT1',
                    'Japan': 'j1-league/gastarbeiter/wettbewerb/JAP1',
                    'Kazakhstan': 'premier-liga/gastarbeiter/wettbewerb/KAS1',
                    'South Korea': 'k-league-1/gastarbeiter/wettbewerb/RSK1',
                    # 'Lebanon':'',
                    'Luxembourg': 'bgl-ligue/gastarbeiter/wettbewerb/LUX1',
                    # 'Macedonia':'',
                    'Mexico': 'liga-mx-apertura/gastarbeiter/wettbewerb/MEXA',
                    'Moldova': 'divizia-nationala/gastarbeiter/wettbewerb/MO1N',
                    'Montenegro': 'telekom-1-cfl/gastarbeiter/wettbewerb/MNE1',
                    'Morocco': 'botola-pro/gastarbeiter/wettbewerb/MAR1',
                    'Netherlands': 'eredivisie/gastarbeiter/wettbewerb/NL1',
                    'New Zealand': 'new-zealand-premiership/gastarbeiter/wettbewerb/NZL1',
                    'Norway': 'eliteserien/gastarbeiter/wettbewerb/NO1',
                    # 'Peru':'',
                    'Poland': 'pko-ekstraklasa/gastarbeiter/wettbewerb/PL1',
                    'Portugal': 'liga-nos/gastarbeiter/wettbewerb/PO1',
                    'Qatar': 'qatar-stars-league/gastarbeiter/wettbewerb/QSL',
                    'Romania': 'liga-1/gastarbeiter/wettbewerb/RO1',
                    'Russia': 'premier-liga/gastarbeiter/wettbewerb/RU1',
                    'Saudi Arabia': 'saudi-professional-league/gastarbeiter/wettbewerb/SA1',
                    'Scotland': 'scottish-premiership/gastarbeiter/wettbewerb/SC1',
                    'Serbia': 'super-liga-srbije/gastarbeiter/wettbewerb/SER1',
                    'Slovakia': 'fortuna-liga/gastarbeiter/wettbewerb/SLO1',
                    'Slovenia': 'prva-liga/gastarbeiter/wettbewerb/SL1',
                    'South Africa': 'absa-premiership/gastarbeiter/wettbewerb/SFA1',
                    'Spain': 'laliga/gastarbeiter/wettbewerb/ES1',
                    'Sweden': 'allsvenskan/gastarbeiter/wettbewerb/SE1',
                    'Switzerland': 'super-league/gastarbeiter/wettbewerb/C1',
                    'Tunisia': 'ligue-professionnelle-1/gastarbeiter/wettbewerb/TUN1',
                    'Turkey': 'super-lig/gastarbeiter/wettbewerb/TR1',
                    'Ukraine': 'premier-liga/gastarbeiter/wettbewerb/UKR1',
                    'United States': 'major-league-soccer/gastarbeiter/wettbewerb/MLS1',
                    'Uruguay': 'primera-division-apertura/gastarbeiter/wettbewerb/URU1',
                    'Wales': 'cymru-premier/gastarbeiter/wettbewerb/WAL1'
                    }
land_id = {'Albania': 3,
            'Algeria': 4,
            'Argentina': 9,
            'Australia': 12,
            'Austria': 127,
            'Azerbaijan': 13,
            'Belarus': 18,
            'Belgium': 19,
            'Bosnia-Herzegovina': 24,
            'Brazil': 26,
            'Bulgaria': 28,
            'Canada': 80,
            'Chile': 33,
            'China': 34,
            # 'Colombia':'',
            'Costa Rica': 36,
            'Croatia': 37,
            'Cyprus': 188,
            'Czech Republic': 172,
            'Denmark': 39,
            'Ecuador': 44,
            'Egypt': 2,
            'England': 189,
            'Estonia': 47,
            'Finland': 49,
            'France': 50,
            'Georgia': 53,
            'Germany': 40,
            'Ghana': 54,
            'Greece': 56,
            'Hungary': 178,
            'Iceland': 73,
            'India': 67,
            'Iran': 71,
            'Israel': 74,
            'Italy': 75,
            'Japan': 77,
            'Kazakhstan': 81,
            'South Korea': 87,
            # 'Lebanon':'',
            'Luxembourg': 99,
            # 'Macedonia':'',
            'Mexico': 110,
            'Moldova': 112,
            'Montenegro': 216,
            'Morocco': 107,
            'Netherlands': 122,
            'New Zealand': 120,
            'Norway': 125,
            # 'Peru':'',
            'Poland': 135,
            'Portugal': 136,
            'Qatar': 137,
            'Romania': 140,
            'Russia': 141,
            'Saudi Arabia': 146,
            'Scotland': 190,
            'Serbia': 215,
            'Slovakia': 154,
            'Slovenia': 155,
            'South Africa': 159,
            'Spain': 157,
            'Sweden': 147,
            'Switzerland': 148,
            'Tunisia': 173,
            'Turkey': 174,
            'Ukraine': 177,
            'United States': 184,
            'Uruguay': 179,
            'Wales': 191}
all_country_url = {2009:'https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/2009-09-02/plus/0',
                   2010:'https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/2010-09-24/plus/0',
                   2011:'https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/2011-09-21/plus/0',
                   2012:'https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/2012-09-05/plus/0',
                   2013:'https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/2013-09-12/plus/0',
                   2014:'https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/2014-09-18/plus/0',
                   2015:'https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/2015-09-03/plus/0',
                   2016:'https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/2016-09-15/plus/0',
                   2017:'https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/2017-09-14/plus/0',
                   2018:'https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/2018-09-20/plus/0'
                   }

#读取已经爬到的部分数据
if os.path.exists('data_by_country.json'):
    f = open('data_by_country.json', 'r')
    data = json.load(f)
    f.close()
else:
    data = []

data = get_data_by_country(data,country_url_list, land_id, ip_list)
data = get_confederation(data,all_country_url,ip_list)

print('all countries finished,saving data...')
json_data = json.dumps(data)
json_file = open('data_by_country.json', 'w')
json_file.write(json_data)
json_file.close()

