from flask import Flask, render_template, url_for, request, redirect, Response, jsonify
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask_pymongo import PyMongo
from pymongo import MongoClient
import random, json, base64
from difflib import SequenceMatcher
from news_crawler import get_articles
from intent_classifier import classify_intent
from nltk import sent_tokenize, word_tokenize
from cryptography.fernet import Fernet
from datetime import date, datetime, timedelta
from stat_report import get_list
import string, random, smtplib

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'phrmsst2018'
app.config["MONGO_URI"] = "mongodb://phast1:a1b2c3d4@ds119662.mlab.com:19662/phrmsst2018"
mongo = PyMongo(app)
ph_ci_dbase = mongo.db.commonillnesses
ph_u_dbase = mongo.db.users
ph_r_dbase = mongo.db.responses
ph_m_dbase = mongo.db.medications
ph_i_dbase = mongo.db.intents
ph_ac_dbase = mongo.db.accountqueues

fname = "User"
lname = ""
studNo = "0"
age = "0"
gender = ""
email = ""
codeSent = False
loginCount = 0
disAccount = ""
illnessList = []
medicineList = []
otherSymptoms = []
symptomCount = 0
symptomCountTotal = 0
currSympList = []
verSympList = []
currIndex = 0
currIllness = ""
hasYN = False
hasSO = False
tryAgain = False
answerYN = ""
category = ""
news = ""
final_illnessList = [] #all illness found
final_illnessSymptomCount = [] #per count - all illness
final_illnessSymptomCountAnswer = [] #per count - all illness - user "yes"
final_userSymptomList = [] #per illness - pag nag yes and provided by user
final_randomSymptomList = [] #to be asked - skip already typed
final_indexCount = 0

# Email
app.config.update(
MAIL_SERVER="smtp.gmail.com",
MAIL_USERNAME="apppharmassist18@gmail.com",
MAIL_PASSWORD="PharmApp2018",
MAIL_PORT = 465,
MAIL_USE_SSL = True,
MAIL_USE_TLS =False)

mail = Mail(app)
s = URLSafeTimedSerializer('secret-key')

#Generating a login code for PharmAssist
def loginCode(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

#============================================================

@app.route("/")
def index():
	return render_template('home.html')

#============================================================

def SendEmail(name, email, token):
	email_content = """
					<!DOCTYPE html>
					<html>
					<head>
					<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Raleway">
					    <style type="text/css">
					    body {font-family: "Raleway", san-serif; font-weight: lighten}
					    form {border: 3px solid #f1f1f1;}

					    .container {
							color:   #232323;
						    padding: 15px 25px 28px 25px;
						    text-align: left;
							font-size: 13px;
							text-decoration: none;
					    }

						.text-div {
							color:   #232323;
							text-align: left;
							font-size: 13px;
							text-decoration: none;
						}

					    .head {
					        color: white;
							background-color: #fff;
							font-size: 20px;
							font-weight: bold;
					        padding: 15px 20px;
					        text-align: left;
					        border: none;
							display: flex;
							flex-direction: row;
							justify-content: flex-start;
							border-bottom: 5px solid #52BDF6;
				        }

						.ph-txt {
							color: #000;
							font-size: 20px;
						}

						.ast-txt {
							color: #52BDF6;
							font-size: 20px;
						}

						.note-div {
							color: #4c4c4c;
							font-size: 13px;
							font-style: italic;
							text-align: left;
						}

						.code-box {
							color: #fff;
							background-color: #52BDF6;
							font-size: 16px;
							padding: 10px;
							width: 222px;
							margin-top: 15px;
							display: flex;
							justify-content: center;
							align-items: center;
						}
					</style>
					</head>

					<body>
					    <form width: 100%;>
					        <div class="head">
								<div class="ph-txt">
									Pharm
								</div>
								<div class="ast-txt">
									Assist
								</div>
							</div>
					        <div class="container">
								<div class="text-div">
									<br><strong>Hi """+name+"""!</strong></br>
									<br></br>
									<br>Thank you for creating an account on PharmAssist.</br>
									<br>Provided below is the code you will use to fully activate your account.</br>
									<br>Once you confirm, all future activities in your PharmAssist account will be sent to """+email+"""</br>
								</div>
								<div class="code-box">
							    	<strong>Confirmation Code: """+token+"""</strong>
								</div>
								<br></br>
								<div class="note-div">
									Note: If you didn't register for a PharmAssist account using this email address, you can safely ignore this message.
								</div>
					        </div>
					    </form>

					</body>
					</html>
					"""

	MESSAGE = MIMEMultipart('alternative')
	MESSAGE['subject'] = "PharmAssist - Confirm Account Email"
	MESSAGE['To'] = ""+email
	MESSAGE['From'] = "apppharmassist18@gmail.com"
	HTML_BODY = MIMEText(email_content, 'html')
	MESSAGE.attach(HTML_BODY)
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login("apppharmassist18@gmail.com","PharmApp2018")
	server.sendmail("apppharmassist18@gmail.com", [email], MESSAGE.as_string())
	server.quit()

#============================================================

def SendLoginCode(name, email, token):
	email_content = """
					<!DOCTYPE html>
					<html>
					<head>
					<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Raleway">
					    <style type="text/css">
					    body {font-family: "Raleway", san-serif; font-weight: lighten}
					    form {border: 3px solid #f1f1f1;}

					    .container {
							color:   #232323;
						    padding: 15px 25px 28px 25px;
						    text-align: left;
							font-size: 13px;
							text-decoration: none;
					    }

						.text-div {
							color:   #232323;
							text-align: left;
							font-size: 13px;
							text-decoration: none;
						}

					    .head {
					        color: white;
							background-color: #fff;
							font-size: 20px;
							font-weight: bold;
					        padding: 15px 20px;
					        text-align: left;
					        border: none;
							display: flex;
							flex-direction: row;
							justify-content: flex-start;
							border-bottom: 5px solid #52BDF6;
				        }

						.ph-txt {
							color: #000;
							font-size: 20px;
						}

						.ast-txt {
							color: #52BDF6;
							font-size: 20px;
						}

						.note-div {
							color: #4c4c4c;
							font-size: 13px;
							font-style: italic;
							text-align: left;
						}

						.code-box {
							color: #fff;
							background-color: #52BDF6;
							font-size: 16px;
							padding: 10px;
							width: 195px;
							margin-top: 15px;
							display: flex;
							justify-content: center;
							align-items: center;
						}
					</style>
					</head>

					<body>
					    <form width: 100%;>
					        <div class="head">
								<div class="ph-txt">
									Pharm
								</div>
								<div class="ast-txt">
									Assist
								</div>
							</div>
					        <div class="container">
								<div class="text-div">
									<br><strong>Hi """+name+""",</strong></br>
									<br></br>
									<br>You recently tried to access your account in PharmAssist.</br>
									<br>Provided below is the code you will use to fully login to your account in that session.</br>
								</div>
								<div class="code-box">
							    	<strong>Login Code: """+token+"""</strong>
								</div>
								<br></br>
								<div class="note-div">
									Note: Login codes are different per login session.
								</div>
					        </div>
					    </form>

					</body>
					</html>
					"""

	MESSAGE = MIMEMultipart('alternative')
	MESSAGE['subject'] = "PharmAssist - Login Code"
	MESSAGE['To'] = ""+email
	MESSAGE['From'] = "apppharmassist18@gmail.com"
	HTML_BODY = MIMEText(email_content, 'html')
	MESSAGE.attach(HTML_BODY)
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login("apppharmassist18@gmail.com","PharmApp2018")
	server.sendmail("apppharmassist18@gmail.com", [email], MESSAGE.as_string())
	server.quit()

#============================================================

def SendDiagnosis(illness, definition, medicine, administration, warning):
	global fname, lname, email, final_userSymptomList, ph_r_dbase
	name = fname + " " + lname;
	illness = illness.title()
	dtime = str(datetime.now())[0:18]
	symptoms = ", ".join(final_userSymptomList)
	msgList = ""

	for i in ph_r_dbase.find():
		msgArr = i.get("tc").split("-=/=-")
		for o in range(0, len(msgArr)):
			if o % 2 == 0:
				msgList += "PharmAssist: " + msgArr[o] +"<br>"
			else:
				msgList += "You: " + msgArr[o] +"<br>"


	email_content = """
					<!DOCTYPE html>
					<html>
					<head>
					<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Raleway">
					    <style type="text/css">
					    body {font-family: "Raleway", san-serif; font-weight: lighten}
					    form {border: 3px solid #f1f1f1;}

					    .container {
							color:   #232323;
						    padding: 15px 25px 28px 25px;
						    text-align: left;
							font-size: 13px;
							text-decoration: none;
					    }

						.text-div {
							color:   #232323;
							text-align: left;
							font-size: 14px;
							text-decoration: none;
						}

					    .head {
					        color: white;
							background-color: #fff;
							font-size: 20px;
							font-weight: bold;
					        padding: 15px 20px;
					        text-align: left;
					        border: none;
							display: flex;
							flex-direction: row;
							justify-content: flex-start;
							border-bottom: 5px solid #52BDF6;
				        }

						.ph-txt {
							color: #000;
							font-size: 20px;
						}

						.ast-txt {
							color: #52BDF6;
							font-size: 20px;
						}

						.note-div {
							color: #4c4c4c;
							font-size: 13px;
							font-style: italic;
							text-align: left;
						}

						.code-box {
							color: #000;
							background-color: #bfe8ff;
							font-size: 15px;
							padding: 10px 20px;
							width: 70%;
							margin-top: 15px;
							text-align: left;
						}

						.code-box p { font-style: italic; font-size: 14px; }
					</style>
					</head>

					<body>
					    <form width: 100%;>
					        <div class="head">
								<div class="ph-txt">
									Pharm
								</div>
								<div class="ast-txt">
									Assist
								</div>
							</div>
					        <div class="container">
								<div class="text-div">
									<br><strong>Hi """+name+""",</strong></br>
									<br></br>
									<br>Here is the result of your consultation.</br>
								</div>
								<div class="code-box">
							    	<br>You seem to have a/an <strong>"""+illness+"""</strong></br>
									<br></br>
									<br>Symptoms Found: <strong>"""+symptoms+"""</strong></br>
									<br></br>
									<br>"""+definition+"""</br>
									<br></br>
									<br>Medicine you could take is <strong>"""+medicine+"""</strong>.</br>
									<br></br>
									<br>Administration: """+administration+"""</br>
									<br></br>
									<br><p><strong>Warning: </strong>"""+warning+"""</p></br>
									<br><strong>Conversation Transcript: </strong></br>
									<br>"""+msgList+"""</br>
								</div>
								<br></br>
								<div class="note-div">
									Note: All successful diagnosis conducted on your PharmAssist account will be sent to this email address.
								</div>
					        </div>
					    </form>

					</body>
					</html>
					"""

	MESSAGE = MIMEMultipart('alternative')
	MESSAGE['subject'] = "PharmAssist - Transcript ("+ dtime +")"
	MESSAGE['To'] = ""+email
	MESSAGE['From'] = "apppharmassist18@gmail.com"
	HTML_BODY = MIMEText(email_content, 'html')
	MESSAGE.attach(HTML_BODY)
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login("apppharmassist18@gmail.com","PharmApp2018")
	server.sendmail("apppharmassist18@gmail.com", [email], MESSAGE.as_string())
	server.quit()

#============================================================

def load_ci_data():
	global ph_ci_dbase, illnessList
	for i in ph_ci_dbase.find():
		if i.get("class") and (not i.get("class") in illnessList):
			illnessList.append(i.get("class"))

#============================================================

def load_med_data():
	global ph_m_dbase, medicineList
	for i in ph_m_dbase.find():
		if i.get("Generic Name") and (not i.get("Generic Name") in medicineList):
			medicineList.append(i.get("Generic Name"))

#============================================================

def check_date(m, d, y):
	try:
		today = date.today()
		born = datetime.strptime(m+' '+d+' '+y+' 12:00AM', '%b %d %Y %I:%M%p')
		return (today.year - born.year - ((today.month, today.day) < (born.month, born.day)))
	except:
		return 0

#============================================================

def verify_date(m, d, y):
	try:
		date = datetime.strptime(m+' '+d+' '+y+' 12:00AM', '%b %d %Y %I:%M%p')
		frmt_m = format(date.month, '02d')
		frmt_d = format(date.day, '02d')
		frmt_y = format(date.year, '04d')
		return (frmt_y+'-'+frmt_m+'-'+frmt_d)
	except:
		return 0

#============================================================

def reset_data():
	global illnessList, otherSymptoms, symptomCount, symptomCountTotal, currSympList, currIndex, currIllness, hasYN, answerYN, category, hasSO, tryAgain
	global final_illnessList, final_illnessSymptomCount, final_illnessSymptomCountAnswer, final_userSymptomList, final_randomSymptomList, final_indexCount
	illnessList = []
	otherSymptoms = []
	symptomCount = 0
	symptomCountTotal = 0
	currSympList = []
	currIndex = 0
	currIllness = ""
	hasYN = False
	hasSO = False
	tryAgain = False
	answerYN = ""
	category = ""
	final_illnessList = []
	final_illnessSymptomCount = []
	final_illnessSymptomCountAnswer = []
	final_userSymptomList = []
	final_randomSymptomList = []
	final_indexCount = 0

#============================================================

def reset_diagnosis():
	global otherSymptoms, symptomCount, symptomCountTotal, currSympList, currIndex, currIllness, hasYN, answerYN, hasSO, tryAgain
	global final_illnessList, final_illnessSymptomCount, final_illnessSymptomCountAnswer, final_userSymptomList, final_randomSymptomList, final_indexCount
	otherSymptoms = []
	symptomCount = 0
	symptomCountTotal = 0
	currSympList = []
	currIndex = 0
	currIllness = ""
	hasYN = False
	hasSO = False
	tryAgain = False
	final_illnessList = []
	final_illnessSymptomCount = []
	final_illnessSymptomCountAnswer = []
	final_userSymptomList = []
	final_randomSymptomList = []
	final_indexCount = 0

#============================================================

def load_per_data():
	global ph_r_dbase, fname, lname, gender, email, news, studNo

	for i in ph_r_dbase.find():
		user = i.get("user").encode("utf-8")
		stid = i.get("studno").encode("utf-8")
		cryp_stid = i.get("studno")
		key = i.get("ed")
		cipher_suite = Fernet(key)
		decr_fname = cipher_suite.decrypt(user)
		decr_stid = cipher_suite.decrypt(stid)
		fname = decr_fname.decode("utf-8")
		studNo = decr_stid.decode("utf-8")

	lname = ph_u_dbase.find_one({"studno": cryp_stid}).get("lname").encode("utf-8")
	gender = ph_u_dbase.find_one({"studno": cryp_stid}).get("gender").encode("utf-8")
	email = ph_u_dbase.find_one({"studno": cryp_stid}).get("email").encode("utf-8")
	key = ph_u_dbase.find_one({"studno": cryp_stid}).get("ed").encode("utf-8")
	cipher_suite = Fernet(key)
	lname = cipher_suite.decrypt(lname).decode("utf-8")
	gender = cipher_suite.decrypt(gender).decode("utf-8")
	email = cipher_suite.decrypt(email).decode("utf-8")

	if news == "":
		news = get_articles(3)

#============================================================

def compare_words(base, message):
	verifiedList = []
	illnessArray = message.split()
	baseList = base

	s = SequenceMatcher(None)
	limit = 0.60

	for il in baseList:
		s.set_seq2(il)
		for ul in illnessArray:
			s.set_seq1(ul)
			b = s.ratio()>=limit and len(s.get_matching_blocks())==2
			#print (il, ul, s.ratio(), '** MATCH **' if s.ratio() > 0.5 else '')
			if s.ratio() > limit and not(il in verifiedList):
				verifiedList.append(il)

	return verifiedList

#============================================================

def compare_wordList(base, message):
	verifiedList = []
	illnessArray = message.split()
	baseList = base.split()

	s = SequenceMatcher(None)
	limit = 0.60

	for il in baseList:
	    s.set_seq2(il)
	    for ul in illnessArray:
	        s.set_seq1(ul)
	        b = s.ratio()>=limit and len(s.get_matching_blocks())==2
	        # print (il, ul, s.ratio(), '** MATCH **' if s.ratio() > 0.6 else '')
	        if s.ratio() > limit and not(il in verifiedList):
	        	verifiedList.append(il)

#============================================================

def MessageParser(message):
	global ph_ci_dbase, final_illnessList, final_illnessSymptomCount, final_userSymptomList, final_randomSymptomList
	symptomList = []
	message = message.split()

	#single
	for i in range(len(message)):
		result = classify_intent(message[i])
		if result[0][1] > 0.9 and not result[0][0] in final_userSymptomList:
			final_userSymptomList.append(result[0][0])
	#dual
	for i in range(len(message)-1):
		result = classify_intent(message[i] + " " + message[i+1])
		if result[0][1] > 0.9 and not result[0][0] in final_userSymptomList:
			final_userSymptomList.append(result[0][0])
	#triad
	for i in range(len(message)-2):
		result = classify_intent(message[i] + " " + message[i+1]+ " " + message[i+2])
		if result[0][1] > 0.9 and not result[0][0] in final_userSymptomList:
			final_userSymptomList.append(result[0][0])

	#check qualified commonillnesses
	# print(final_userSymptomList)
	for i in ph_ci_dbase.find():
		name = i.get("class")
		symptoms = i.get("symptoms")[0]
		for o in symptoms:
			for e in final_userSymptomList:
				if o == e and not name in final_illnessList:
					final_illnessList.append(name)
					final_illnessSymptomCount.append(0)
					#add symptoms to be asked
					for u in symptoms:
						for m in final_userSymptomList:
							if u != m and not u in final_userSymptomList and not u in final_randomSymptomList:
								final_randomSymptomList.append(u)
					break

	final_randomSymptomList = shuffle_in_place(final_randomSymptomList)
	# print("Final illness List: ", final_illnessList)
	# print("Symptoms: ", final_randomSymptomList)

#============================================================

def shuffle_in_place(array):
	array_len = len(array)
	for index in range(array_len):
		swap = random.randrange(array_len - 1)
		swap += swap >= index
		array[index], array[swap] = array[swap], array[index]

	return array

#============================================================

@app.route("/admin", methods=['GET', 'POST'])
def admin():
	global fname, news
	reset_data()
	load_per_data()

	msgStr = "Hi, " + fname + "! What would you like to do?"

	return render_template('admin.html', msg=msgStr, news=news)

#============================================================

@app.route("/home", methods=['GET', 'POST'])
def home():
	return render_template('home.html')

#============================================================

@app.route("/statreport", methods=['GET', 'POST'])
def statreport():
	strInfo = get_list("all_ci", 0)
	return render_template('statreport.html', info=strInfo)

#============================================================

@app.route("/userlogs", methods=['GET', 'POST'])
def userlogs():
	#strInfo = get_list()
	return render_template('userlogs.html', info=strInfo)

#============================================================

@app.route("/confirm")
def confirm():
    return render_template('confirm.html')

#============================================================

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')

#============================================================

@app.route("/login", methods=['GET', 'POST'])
def login():
	global ph_r_dbase, disAccount
	dtime = str(datetime.now())[14:16]

	for i in ph_r_dbase.find():
		user = i.get("user")
		stno = i.get("studno")
		age = i.get("age")
		ed = i.get("ed")
		disAccount = i.get("ban")
		ph_r_dbase.find_one_and_update({"user": user}, {"$set": {"user": "none", "tc": ""}})
		ph_r_dbase.find_one_and_update({"age": age}, {"$set": {"age": "0"}})
		ph_r_dbase.find_one_and_update({"studno": stno}, {"$set": {"studno": "0"}})
		ph_r_dbase.find_one_and_update({"ed": ed}, {"$set": {"ed": "0"}})
		if i.get("dt") != "":
			dt = i.get("dt")[3:]
			if int(dtime) > int(dt):
				ph_r_dbase.find_one_and_update({"ban": disAccount}, {"$set": {"ban": "", "dt": ""}})
				disAccount = ""

	reset_data()

	return render_template('login.html')

#============================================================

@app.route("/chat", methods=['GET', 'POST'])
def chat():
	global fname, news, ph_r_dbase
	reset_data()
	load_per_data()
	msgStr = "Hi, " + fname + "!\nWhat can I do for you?"

	return render_template('chat.html', msg=msgStr, news=news)

#============================================================

@app.route("/process_message", methods=['POST'])
def process_message():
	global ph_ci_dbase, ph_r_dbase, ph_m_dbase, ph_i_dbase, studNo, illnessList, medicineList, otherSymptoms, symptomCount, symptomCountTotal, currSympList, verSympList, currIllness, hasYN, answerYN, currIndex, category, hasSO, tryAgain
	global final_illnessList, final_illnessSymptomCount, final_illnessSymptomCountAnswer, final_userSymptomList, final_randomSymptomList, final_indexCount, gender, user
	load_ci_data()
	load_med_data()
	load_per_data()
	origMsg = request.form['txtMessage']
	message = request.form['txtMessage'].lower()
	selfMsg = ""

	for i in ph_r_dbase.find():
		newTC = i.get("tc") + "-=/=-" + origMsg

		ph_r_dbase.find_one_and_update({"tc": i.get("tc")}, {"$set": {"tc": newTC}})

	response = "I'm sorry I didn't quite get that. Could you please specify it more clearly?"
	intentList = classify_intent(message)
	intent = intentList[0][0]

	if message == "yes" or message == "no":
		intent = "answer"

	if gender == "male":
		ph_ci_dbase = mongo.db.commonillnessesmale

	#tokenization
	tokens = []
	msgArray = []

	sents = sent_tokenize(message)
	for s in sents:
		tokens.append(word_tokenize(s))
	for x in tokens:
		for y in x:
			msgArray.append(y)

	illnessArray = compare_words(illnessList, message)
	medArray = compare_words(medicineList, message)

	if category == "Definition":
		response = ""
		remedyCheckList = compare_words("remedy", message)
		sympCheckList = compare_words("symptom", message)
		if message == "definition":
			response = "What common illness would you like to ask about?"

		elif remedyCheckList:
			for i in ph_ci_dbase.find():
				for o in illnessArray:
					if str(i.get("class")) == o:
						defStr = ph_ci_dbase.find_one({"class": o})
						defList = defStr["quick-remedies"]
						defList = ', '.join(defList)
						response += "Quick remedies for "+ o +" include:" + "-/-" + defList + "-/-"
						ph_i_dbase.insert_one({"category": category.lower(), "intent": o, "date": str(date.today()), "time": str(datetime.today().time())[0:8]})

		elif sympCheckList:
			for i in ph_ci_dbase.find():
				for o in illnessArray:
					if str(i.get("class")) == o:
						defStr = ph_ci_dbase.find_one({"class": o})
						defList = defStr["symptoms"]
						defList = ', '.join(defList)
						response += "Symptoms of "+ o +" include:" + "-/-" + defList + "-/-"
						ph_i_dbase.insert_one({"category": category.lower(), "intent": o, "date": str(date.today()), "time": str(datetime.today().time())[0:8]})

		else:
			for i in ph_ci_dbase.find():
				for o in illnessArray:
					if i.get("class") == o:
						defStr = ph_ci_dbase.find_one({"class": o})
						source = defStr["sources"]
						defList = defStr["definition"]
						defList = ' '.join(defList)
						response += defList + " - " + defStr["sources"] + "-/-"
						ph_i_dbase.insert_one({"category": category.lower(), "intent": o, "date": str(date.today()), "time": str(datetime.today().time())[0:8]})

	elif category == "Symptom Checker":
		if message != "symptom checker" and message != "yes" and message != "no":
			MessageParser(message)

		if message == "symptom checker":
			response = "Please describe your symptoms."

		elif intent == "answer":
			if message == "yes":
				final_userSymptomList.append(final_randomSymptomList[final_indexCount-1])

			if tryAgain and answerYN == "Yes":
				response = "Please describe your symptoms."
				reset_diagnosis()

			elif tryAgain and answerYN == "No":
				response = "Okay let's try a different category."
				hasSO = True

			elif len(final_randomSymptomList) > final_indexCount:
				response = ""
				question =  random.choice(ph_r_dbase.find_one({"class": "question"}).get("response"))
				response += question + " " + final_randomSymptomList[final_indexCount] +"?-/-"
				hasYN = True
				final_indexCount += 1

			elif len(final_randomSymptomList) == final_indexCount:
				for r in range(len(final_illnessList)):
					for i in ph_ci_dbase.find():
						if final_illnessList[r] == i.get("class"):
							symptoms = i.get("symptoms")[0]
							final_illnessSymptomCountAnswer.append(len(symptoms))
							for o in symptoms:
								for u in final_userSymptomList:
									if o == u:
										final_illnessSymptomCount[r] = final_illnessSymptomCount[r] + 1

				for i in range(len(final_illnessList)):
					final_illnessSymptomCountAnswer[i] = int((final_illnessSymptomCount[i] / final_illnessSymptomCountAnswer[i]) * 100)

				m = max(final_illnessSymptomCountAnswer)
				maxVal = [i for i, j in enumerate(final_illnessSymptomCountAnswer) if j == m]
				if final_illnessSymptomCountAnswer[maxVal[0]] > 65:
					illness = final_illnessList[maxVal[0]]
					response = "You seem to have a/an " + illness + ".-/-"
					defStr = ph_ci_dbase.find_one({"class": illness})
					medicine = defStr["doctor-recommended-medicine"]
					uses = ph_m_dbase.find_one({"Generic Name": medicine}).get("Indications")
					admin = ph_m_dbase.find_one({"Generic Name": medicine}).get("Administration")
					defList = defStr["definition"]
					defList = ''.join(defList)
					response += defList + "-/-"
					response += "Medicine you could take is " + medicine + ".-/-Administration: "+ admin + ".-/-"
					# response += ''.join(uses) + "-/-"
					response += "If your doctor has recommended a different medication from the ones given here, do not change the way that you are taking the medication without consulting your doctor.-/-"
					response += "Would you like to try again?-/-"
					hasYN = True
					tryAgain = True
					SendDiagnosis(illness, defList, medicine, admin, "If your doctor has recommended a different medication from the ones given here, do not change the way that you are taking the medication without consulting your doctor." )

				else:
					response = "I'm sorry I have failed to come up with a diagnosis.-/-If symptoms persists, please consult a doctor immediately.-/-Would you like to try again?-/-"
					hasYN = True
					tryAgain = True


		else:
			try:
				question =  random.choice(ph_r_dbase.find_one({"class": "question"}).get("response"))
				response = "Sorry to hear that.-/-I'm now going to ask you a series of questions to get to the bottom of your condition.-/-"
				response += question + " " + final_randomSymptomList[final_indexCount] +"?-/-"
				hasYN = True
				final_indexCount += 1
			except:
				response = ""

	elif category == "Medicine Inquiry":
		response = ""
		sideEffCheckList = compare_words("side effects", message)
		doseCheckList = compare_words("dosages", message)

		if message == "medicine inquiry":
			response = "What medicine would you like to inquire about?"

		elif sideEffCheckList:
			for i in ph_m_dbase.find():
				for o in medArray:
					if str(i.get("Generic Name")) == o:
						defStr = ph_m_dbase.find_one({"Generic Name": o})
						defList = defStr["side-effects"]
						defList = '-/-'.join(defList)
						response += defList + "-/-"
						ph_i_dbase.insert_one({"category": category.lower(), "intent": o, "date": str(date.today()), "time": str(datetime.today().time())[0:8]})


		elif doseCheckList:
			for i in ph_m_dbase.find():
				for o in medArray:
					if str(i.get("Generic Name")) == o:
						defStr = ph_m_dbase.find_one({"Generic Name": o})
						defList = defStr["Dosage"]
						defList = '-/-'.join(defList)
						response += defList + "-/-"
						ph_i_dbase.insert_one({"category": category.lower(), "intent": o, "date": str(date.today()), "time": str(datetime.today().time())[0:8]})


		else:
			for i in ph_m_dbase.find():
				for o in medArray:
					if str(i.get("Generic Name")) == o:
						defStr = ph_m_dbase.find_one({"Generic Name": o})
						defList = defStr["Indications"]
						defList = ''.join(defList)
						response += 'It can be used for: ' + defList + "-/-"
						ph_i_dbase.insert_one({"category": category.lower(), "intent": o, "date": str(date.today()), "time": str(datetime.today().time())[0:8]})

	if "-/-" in response: # trim excess separator
		response = response[:-3]

	if hasYN: # if ask to answer yes no questions
		response += "YN";

	if hasSO:
		response += "SO"

	if response == "":
		response = "I'm sorry I didn't quite get that. Could you please specify it more clearly?"

	if message: # return if message is not blank
		hasYN = False
		hasSO = False
		answerYN = ""
		for i in ph_r_dbase.find():
			newTC = i.get("tc") + "-=/=-" + response
			ph_r_dbase.find_one_and_update({"tc": i.get("tc")}, {"$set": {"tc": newTC}})

		return jsonify({'message': response})

	return jsonify({'error': 'No data.'})

#=============================================================

@app.route("/process_yn_buttons", methods=['POST'])
def process_yn_buttons():
	global answerYN
	answerYN = request.form['answer']

	return jsonify({'answer': answerYN})

#============================================================

@app.route("/process_login", methods=['POST'])
def process_login():
	global ph_u_dbase, ph_r_dbase, fname, age, codeSent, loginCount, disAccount
	username = request.form['txtUsername']
	password = request.form['txtPassword']
	code = request.form['txtCode']
	verify = "F"
	dtime = str(datetime.now() + timedelta(minutes=2))[11:16]

	if disAccount == username:
		verify = "dis"
	else:
		loginCount += 1
		for i in ph_u_dbase.find():
			key = i.get("ed").encode("utf-8")
			status = i.get("status")
			lcode = i.get("lcode")
			fname = i.get("fname").encode("utf-8")
			pwd = i.get("password").encode("utf-8")
			uname = i.get("username").encode("utf-8")
			email = i.get("email").encode("utf-8")
			acclevel = i.get("acclevel").encode("utf-8")
			cipher_suite = Fernet(key)
			decr_email = cipher_suite.decrypt(email)
			decr_pass = cipher_suite.decrypt(pwd)
			decr_uname = cipher_suite.decrypt(uname)
			decr_fname = cipher_suite.decrypt(fname)
			decr_acclevel = cipher_suite.decrypt(acclevel)
			decr_pass = decr_pass.decode("utf-8")
			decr_uname = decr_uname.decode("utf-8")
			email = decr_email.decode("utf-8")
			fname = decr_fname.decode("utf-8")
			acclevel = decr_acclevel.decode("utf-8")

			if decr_uname != username:
				verify = "U"
			elif decr_uname == username and decr_pass != password:
				verify = "P"
				if loginCount == 5:
					verify = "W"
					ph_r_dbase.find_one_and_update({"ban": ""}, {"$set": {"ban": username, "dt": dtime}})
				break
			elif decr_uname == username and decr_pass == password and lcode == code:
				age = i.get("age")
				msgStr = "Hi, " + fname + "! What can I do for you?"

				if acclevel == "admin":
					verify = "admin"
				elif acclevel == "user":
					verify = "user"

				if status == "X":
					verify = "noverif"

				ph_r_dbase.find_one_and_update({"user": "none"}, {"$set": {"user": i.get("fname")}})
				ph_r_dbase.find_one_and_update({"studno": "0"}, {"$set": {"studno": i.get("studno")}})
				ph_r_dbase.find_one_and_update({"age": "0"}, {"$set": {"age": i.get("age")}})
				ph_r_dbase.find_one_and_update({"ed": "0"}, {"$set": {"ed": i.get("ed")}})
				ph_r_dbase.find_one_and_update({"tc": ""}, {"$set": {"tc": msgStr}})
				ph_r_dbase.find_one_and_update({"ban": ""}, {"$set": {"ban": username, "dt": dtime}})
				break
			elif decr_uname == username and decr_pass == password and lcode != code and code != "":
				verify = "LI"
				break
			else:
				if not codeSent and decr_uname == username and decr_pass == password:
					token = loginCode()
					ph_u_dbase.find_one_and_update({"username": i.get("username")}, {"$set": {"lcode": token}})
					SendLoginCode(fname, email, token)
					codeSent = True
					verify = "EC"
				else:
					verify = "LE"
					if loginCount == 5:
						verify = "W"
				break

	return jsonify({'verify': verify})

#=============================================================

@app.route("/process_confirm", methods=['POST'])
def process_confirm():
	global ph_u_dbase
	username = request.form['txtUsername']
	code = request.form['txtCode']
	verify = "F"

	for i in ph_u_dbase.find():
		key = i.get("ed").encode("utf-8")
		status = i.get("status")
		crypt_uname = i.get("username")
		uname = i.get("username").encode("utf-8")
		cipher_suite = Fernet(key)
		ucode = i.get("code")
		decr_uname = cipher_suite.decrypt(uname)
		decr_uname = decr_uname.decode("utf-8")

		if decr_uname == username and ucode == code:
			verify = "T"
			ph_u_dbase.find_one_and_update({"username": crypt_uname}, {"$set": {"status": "Y"}})
			break
		elif decr_uname == username and status == "Y":
			verify = "V"
			break;
		elif decr_uname != username:
			verify = "A"

	return jsonify({'verify': verify})

#=============================================================

@app.route("/process_resend", methods=['POST'])
def process_resend():
	global ph_u_dbase
	username = request.form['txtUsernameR']
	email = request.form['txtEmail']
	verify = "F"

	for i in ph_u_dbase.find():
		key = i.get("ed").encode("utf-8")
		status = i.get("status")
		cryp_uname = i.get("username")
		fname = i.get("fname").encode("utf-8")
		lname = i.get("lname").encode("utf-8")
		uname = i.get("username").encode("utf-8")
		cipher_suite = Fernet(key)
		decr_uname = cipher_suite.decrypt(uname)
		decr_uname = decr_uname.decode("utf-8")
		decr_fname = cipher_suite.decrypt(fname)
		decr_fname = decr_fname.decode("utf-8")
		decr_lname = cipher_suite.decrypt(lname)
		decr_lname = decr_lname.decode("utf-8")
		cryp_email = cipher_suite.encrypt(email.encode("utf-8"))
		cryp_email = cryp_email.decode("utf-8")
		name = decr_fname + " " + decr_lname

		if decr_uname == username and status == "X":
			verify = "T"
			token = loginCode()
			ph_u_dbase.find_one_and_update({"username": cryp_uname}, {"$set": {"email": cryp_email, "code": token}})
			SendEmail(name, email, token)
			break
		elif decr_uname == username and status == "Y":
			verify = "V"
			break;
		elif decr_uname != username:
			verify = "A"

	return jsonify({'verify': verify})

#=============================================================

@app.route("/process_signup", methods=['POST'])
def process_signup():
	global ph_u_dbase
	fname = request.form['txtFName']
	mname = request.form['txtMName']
	lname = request.form['txtLName']
	studNo = request.form['txtStudNo']
	day = request.form['txtDay']
	month = request.form['txtMonth']
	year = request.form['txtYear']
	gender = request.form['txtGender']
	email = request.form['txtEmail']
	username = request.form['txtUsername']
	password = request.form['txtPassword']
	confpassword = request.form['txtConfPassword']
	check = request.form['check']
	verify = "F"
	age = check_date(month, day, year)
	level = "user"

	for i in ph_u_dbase.find():
		uname = i.get("username").encode("utf-8")
		stid = i.get("studno").encode("utf-8")
		eml = i.get("email").encode("utf-8")
		key = i.get("ed").encode("utf-8")
		cipher_suite = Fernet(key)
		decr_uname = cipher_suite.decrypt(uname)
		decr_uname = decr_uname.decode("utf-8")
		decr_stid = cipher_suite.decrypt(stid)
		decr_stid = decr_stid.decode("utf-8")
		decr_eml = cipher_suite.decrypt(eml)
		decr_eml = decr_eml.decode("utf-8")
		if decr_stid == studNo:
			verify = "ID"
			break
		if decr_eml == email:
			verify = "EM"
			break
		if decr_uname == username:
			verify = "U"
			break

	if not(fname):
		verify = "F"
	elif not(mname):
		verify = "MN"
	elif not(lname):
		verify = "L"
	elif not(studNo.isdigit()):
		verify = "SN"
	elif not(day):
		verify = "D"
	elif not(month):
		verify = "M"
	elif not(year):
		verify = "Y"
	elif age < 13 or age > 65:
		verify = "B"
	elif not(gender):
		verify = "G"
	elif verify == "ID":
		verify = "ID"
	elif verify == "EM":
		verify = "EM"
	elif verify == "U" or not(username):
		verify = "U"
	elif password != confpassword or (password == '' or confpassword == ''):
		verify = "P"
	elif check == "false" or not(check):
		verify = "C"
	else:
		birthdate = month+"-"+day+"-"+year
		key = Fernet.generate_key()
		key = key.decode("utf-8")
		cipher_suite = Fernet(key)
		fname = cipher_suite.encrypt(fname.encode("utf-8"))
		mname = cipher_suite.encrypt(mname.encode("utf-8"))
		lname = cipher_suite.encrypt(lname.encode("utf-8"))
		studNo = cipher_suite.encrypt(str(studNo).encode("utf-8"))
		age = str(age)
		age = cipher_suite.encrypt(age.encode("utf-8"))
		birthdate = cipher_suite.encrypt(birthdate.encode("utf-8"))
		gender = cipher_suite.encrypt(gender.encode("utf-8"))
		email = cipher_suite.encrypt(email.encode("utf-8"))
		username = cipher_suite.encrypt(username.encode("utf-8"))
		password = cipher_suite.encrypt(password.encode("utf-8"))
		level = cipher_suite.encrypt(level.encode("utf-8"))
		fname = fname.decode("utf-8")
		mname = mname.decode("utf-8")
		lname = lname.decode("utf-8")
		studNo = studNo.decode("utf-8")
		age = age.decode("utf-8")
		birthdate = birthdate.decode("utf-8")
		gender = gender.decode("utf-8")
		email = email.decode("utf-8")
		username = username.decode("utf-8")
		password = password.decode("utf-8")
		level = level.decode("utf-8")
		token = loginCode()
		ph_u_dbase.insert_one({"fname" : fname, "mname": mname, "lname": lname, "studno": studNo, "age": age, "birthdate": birthdate, "gender": gender, "email": email, "username": username, "password": password, "acclevel": level, "ed": key, "status": "X", "code": token, "lcode": ""})
		# ph_ac_dbase.insert_one({"username": username, "ed": key, "code": code})

		email = request.form['txtEmail']
		name = request.form['txtFName'] + " " + request.form['txtLName']

		SendEmail(name, email, token)

	return jsonify({'verify': verify})

#=============================================================

@app.route("/process_class_buttons", methods=['POST'])
def process_class_buttons():
	global category
	category = request.form['category']

	return jsonify({'category': category})

#=============================================================

@app.route("/process_startover", methods=['POST'])
def process_startover():
	global illnessList, otherSymptoms, symptomCount, symptomCountTotal, currSympList, currIndex, currIllness, hasYN, answerYN, category
	illnessList = []
	medicineList = []
	otherSymptoms = []
	symptomCount = 0
	symptomCountTotal = 0
	currSympList = []
	currIndex = 0
	currIllness = ""
	hasYN = False
	answerYN = ""
	category = ""
	done = "T"

	return jsonify({'done': done})

#============================================================

@app.route("/process_report", methods=['POST'])
def process_report():
	#studNo = request.form['txtStudNo']
	day = request.form['txtDay']
	month = request.form['txtMonth']
	year = request.form['txtYear']
	category = request.form['txtCategory']
	cat = request.form['category']
	verify = "T"
	date = verify_date(month, day, year)
	# print(studNo, day, month, year, category, cat, date)

	if cat == "all":
		if category == "Medicine":
			verify = get_list("all_med", 0)
		else:
			verify = get_list("all_ci", 0)

	elif cat == "sort":
		if date != 0 and category == "Medicine":
			verify = get_list("sort_med", date)
		else:
			verify = get_list("sort_ci", date)

	return jsonify({'verify': verify})

#============================================================

# FOR UPDATING
#ph_u_dbase.find_one_and_update({"username" : username}, {"$set": {"username": username}})

# intent = classify_illness("text")
# intent = intent['classification']
# elif intent == "greeting":
# 	greet =  ph_r_dbase.find_one({"class": "greeting"}).get("response")
# 	response = random.choice(greet)

if __name__ == '__main__':
	app.run(host='0.0.0.0',debug=True)
