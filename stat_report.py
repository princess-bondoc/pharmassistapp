from flask import Flask
from flask_pymongo import PyMongo
#from pymongo import MongoClient

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'phrmsst2018'
app.config["MONGO_URI"] = "mongodb://phast1:a1b2c3d4@ds119662.mlab.com:19662/phrmsst2018"
mongo = PyMongo(app)
ph_i_dbase = mongo.db.intents
ph_m_dbase = mongo.db.medications
ph_ci_dbase = mongo.db.commonillnesses

# def list_values(dbase, key):
#     values = [i.get(key) for i in dbase.find()]
#     return values

# def get_frequency(intent, type):
#     freq_cnt = {}
#     category = list_values(ph_i_dbase, 'category')
#     date = list_values(ph_i_dbase, 'date')
#     for i,val in enumerate(intent):
#         if(category[i]==type):
#             freq_cnt[val] = [intent.count(val), date]

#     return(sorted(freq_cnt, key=freq_cnt.get, reverse=True))

def get_dbvalues(dbase, key):
    values = [i.get(key) for i in dbase.find()]
    return values

def getlist_day_frequency(intent, type, dt):
    freq_cnt = {}
    day_intents = []
    category = get_dbvalues(ph_i_dbase, 'category')
    date = get_dbvalues(ph_i_dbase, 'date')

    for i,val in enumerate(intent):
        if(category[i]==type and date[i]==dt):
            day_intents.append(val)

    for i, val in enumerate(day_intents):
        freq_cnt[val] = day_intents.count(val)

    sorted_results = sorted(freq_cnt, key=freq_cnt.get, reverse=True)
    return sorted_results

def getlist_general_frequency(intent, type):
    freq_cnt = {}
    category = get_dbvalues(ph_i_dbase, 'category')

    for i,val in enumerate(intent):
        if(category[i]==type):
            freq_cnt[val] = intent.count(val)

    sorted_results = sorted(freq_cnt, key=freq_cnt.get, reverse=True)
    return sorted_results


#=================================================

def get_list(cat, dt):
    intents = get_dbvalues(ph_i_dbase, 'intent')
    # inte = get_frequency(intents, 'definition')
    # med = get_frequency(intents, 'medicine inquiry')

    date = dt
    print(date)

    if cat == 'all_ci':
        genDef = getlist_general_frequency(intents, 'definition')
    elif cat == 'all_med':
        genDef = getlist_general_frequency(intents, 'medicine inquiry')
    elif cat == 'sort_ci' and date != 0:
        genDef = getlist_day_frequency(intents, 'definition', date)
    elif cat == 'sort_med' and date != 0:
        genDef = getlist_day_frequency(intents, 'medicine inquiry', date)
    else:
        date = dt

    strInfo = ""
    for i in genDef:
        strInfo += i + "-/-" #+ "Illness" + "-/-" + "20400001" + "-/-" + "2018" + "-/-"
    return strInfo




