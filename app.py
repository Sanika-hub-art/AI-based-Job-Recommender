from flask import *
from flask import Flask
from flask import render_template, request, redirect, session, url_for
import sqlite3
import string
import csv
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from operator import itemgetter
from functools import wraps
import shutil
import tempfile

# con= sqlite3.connect('user_data.db')
#
# con.execute("create table if not exists 'applicant_info'('email'TEXT, 'password'TEXT);")
# cursor = con.cursor()
count = 0
applicant_login= False
company_login= False
useremail = ""
userid=0
app = Flask( __name__, template_folder='templates')


app.secret_key= b'0p]*:;_zd}=@hu'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return render_template('login.html', msg="You will need to login first!")
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=["GET", "POST"])
def home():
    if (request.method == "POST"):
        if (request.form["jobtitle"] != "" and request.form["locselect"] != ""):
            jobtitle = request.form['jobtitle']
            location = request.form['locselect']
            jobs = searchjob(location, jobtitle)
            con = sqlite3.connect("user_data.db")
            c = con.cursor()
            c.execute("Select count(*) from applicant_info;")
            result = c.fetchone()
            data_can = result[0]
            c.execute("Select count(*) from company_info;")
            result = c.fetchone()
            data_com = result[0]
            with open('Profile_data.csv', 'r', encoding='utf-8') as file1:
                csv_can = csv.reader(file1)
                csv_can = list(csv_can)
                file1.close()
            with open('Job_roles.csv', 'r', encoding='utf-8') as file1:
                csv_com = csv.reader(file1)
                csv_com = list(csv_com)
                file1.close()
            # print(data_can, data_com, csv_can, csv_com)
            # return render_template('index.html')

            return render_template('index.html', jobs=jobs, len=len(jobs), data_can_count=data_can, data_com_count=data_com,
                                   linkedin_count=len(csv_can), indeed_count=len(csv_com))
    con = sqlite3.connect("user_data.db")
    c = con.cursor()
    c.execute("Select count(*) from applicant_info;")
    result = c.fetchone()
    data_can = result[0]
    c.execute("Select count(*) from company_info;")
    result = c.fetchone()
    data_com = result[0]
    with open('Profile_data.csv', 'r', encoding='utf-8') as file1:
        csv_can = csv.reader(file1)
        csv_can= list(csv_can)
        file1.close()
    with open('Job_roles.csv', 'r', encoding='utf-8') as file1:
        csv_com = csv.reader(file1)
        csv_com= list(csv_com)
        file1.close()
    # print(data_can, data_com, csv_can, csv_com)
    return render_template('index.html',data_can_count=data_can, data_com_count=data_com,linkedin_count=len(csv_can) , indeed_count=len(csv_com))


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/nextpage')
def listpage():
    global count
    count = count + 1
    return render_template('job-listings.html', count=count)


# @app.route('/signup', methods=["GET", "POST"])
# def signup():
#     if(request.method == "POST"):
#          if(request.form["email"]!= "" and request.form["passw"]!=""):
#             email = request.form["email"]
#             password = request.form["passw"]
#             con = sqlite3.connect("user_data.db")
#             c= con.cursor()
#             con.execute("create table if not exists 'applicant_info'('email'TEXT, 'password'TEXT);")
#             query="INSERT INTO applicant_info VALUES ();"
# c.execute("INSERT INTO applicant_info VALUES ('"+email+"','"+password+"')")
# con.commit()
# con.close()

@app.route('/login', methods=["GET", "POST"])
def login():
    if (request.method == "POST"):
        global useremail
        global userid
        global company_login
        global applicant_login
        email = request.form["username"]
        password = request.form["pass"]
        con = sqlite3.connect("user_data.db")
        c = con.cursor()
        c.execute(
            "SELECT * FROM company_info WHERE username='" + email + "' and password='" + password + "' ")
        recruiter = c.fetchall()
        c.execute(
            "SELECT * FROM applicant_info WHERE username='" + email + "' and password='" + password + "' ")
        applicant = c.fetchall()
        print(applicant)
        for i in recruiter:
            if (email == i[11] and password == i[12]):
                useremail = email
                userid=i[0]
                company_login= True
                session['username'] = email
                session['role'] = 'company'
                can = candidatelist()
                can= sorted(can, key=lambda d: d['URL'][:2])
                pass_dict = {'companyname': i[1], 'jobtitle': i[2], 'location': i[3],'jobtype': i[4],'description': i[5].replace('`', '\n'), 'website': i[6], 'email': i[7],'salary': i[10], 'facebook': i[8], 'twitter': i[9]}
                  # print(can)
                return render_template('candidatelisting.html', len=len(can), candidates=can, profile=pass_dict)
        for j in applicant:
            if (email == j[8] and password == j[9]):
                useremail = email
                userid=j[0]
                applicant_login= True
                session['username'] = email
                session['role'] = 'applicant'
                jobs = joblistings()
                jobs = sorted(jobs, key=lambda d: d['URL'][:2])
                pass_dict = {'Name': j[1], 'email': j[2], 'location': j[3], 'education': j[4],'skills': j[5], 'contact': j[6], 'linkedin': j[7], 'tagline': j[10]}
                return render_template('job-listings.html', len=len(jobs), candidates=jobs, profile=pass_dict)
        con.close()
        return render_template('login.html', msg="Invalid username or password! Try again....")
    return render_template('login.html')

    # con.commit()
    # con.close()


@app.route('/post', methods=["GET", "POST"])
def post():
    if (request.method == "POST"):
        # print("x")
        # print(request.form["companyemail"], request.form["jobtitle"])
        if (request.form["companyemail"] != "" and request.form["jobtitle"] != "" and request.form["joblocation"] != "" and request.form["jobtype"] != "" and request.form["companyname"] != "" and request.form["companywebsite"] != "" and request.form["description"] != "" and request.form["email"] != "" and request.form['passw'] != "" and request.form["retype"] != ""):
            # print("x")
            paj_email = request.form["companyemail"]
            jobtitle = request.form["jobtitle"]
            joblocation = request.form["joblocation"]
            # jobregion= request.form["jobregion"]
            jobtype = request.form["jobtype"]
            # editor1 = request.form["editor1"]
            companyname = request.form["companyname"]
            # companytagline= request.form["companytagline"]
            # editor2= request.form["editor2"]
            # if request.form["companywebsite"]!="":
            companywebsite = request.form["companywebsite"]
            # else:
            #     companywebsite = " "
            if request.form["companywebsitefb"] != "":
                companywebsitefb = request.form["companywebsitefb"]
            else:
                companywebsitefb = " "
            if request.form["companywebsitetw"] != "":
                companywebsitetw = request.form["companywebsitetw"]
            else:
                companywebsitetw = " "
            if request.form["salary"] != "":
                salary = request.form["salary"]
            else:
                salary = " "
            desc = request.form["description"]
            desc= desc.replace('\n','`')
            email = request.form["email"]
            print(salary)
            password = request.form["passw"]
            con = sqlite3.connect("user_data.db")

            # con.execute("create table if not exists 'applicant_info'('email'TEXT, 'password'TEXT);")
            c = con.cursor()
            c.execute("Select count(*) from company_info where companyname='"+companyname+"' and jobtitle='"+jobtitle+"' and joblocation='"+joblocation+"' and username='"+email+"'")
            duplic = c.fetchone()
            if duplic[0]==0:
                query1 = "INSERT INTO company_info(companyname,jobtitle,joblocation,jobtype,description,companywebsite,email,companywebsitefb,companywebsitetw,salary,username,password) VALUES (?,?,?,?,?,?,?,?,?,?,?,?);"
                c.execute(query1, (companyname, jobtitle, joblocation, jobtype, desc, companywebsite, paj_email, companywebsitefb,companywebsitetw, salary, email, password))
                con.commit()
                con.close()
                write_dict = {'Job Title': jobtitle, 'Company': companyname, 'Location': joblocation, 'Salary': salary,
                              'Description': desc, 'URL': "database"}
                head = ['Job Title', 'Company', 'Location', 'Salary', 'Description', 'URL']
                with open('Job_roles.csv', 'a', newline='', encoding='utf-8') as file1:
                    writor = csv.DictWriter(file1, head)
                    writor.writerow(write_dict)
                    file1.close()
                return render_template('login.html')
            else:
                con.close()
                flash("Job Profile with the mentioned details already exist!\nTry changing some of the fields.....")
        elif (request.form["companyemail"] == "" or request.form["jobtitle"] == "" or request.form["joblocation"] == "" or request.form["jobtype"] == "" or request.form["companyname"] == "" or request.form["companywebsite"] == "" or request.form["description"] == "" or request.form["email"] == "" ):
            flash("Please fill all the required fields!")
        elif (request.form['passw'] != request.form["retype"]):
            flash("Password and retyped password don't match!")

    return render_template('post-job.html')


# @app.route('/jobsingle')
# def jobsingle():
#     return render_template('job-single.html')


def candidatelist():
    global useremail
    global userid
    vectorizer = TfidfVectorizer()
    stop_words = set(stopwords.words('english'))
    con = sqlite3.connect("user_data.db")
    c = con.cursor()
    c.execute("Select * from company_info where username='" + useremail + "' and companyid="+str( userid))
    result = c.fetchone()
    c.execute("")
    con.close()
    loc1 = result[2]
    skill1 = result[4]
    recommend2 = []
    loc_similar_rows = []
    default_recommend = []
    recommend = []
    temp_dict = {}
    with open('Profile_data.csv', 'r', encoding='utf-8') as file1:
        data = csv.DictReader(file1,fieldnames=['Name', 'Job Title', 'Company', 'College', 'Location', 'Skills', 'URL'])
        # data1 = list(data)
        for one_row in data:
            # row_no = data1.index(one_row)
            # print(row_no)
            # Location similarity
            if one_row['Name'] == 'Name':
                continue
            temp_dict = one_row
            # temp_dict.update('Job':"location_similarity")
            # print(temp_dict)
            locat2 = one_row['Location']
            loc1 = loc1.lower()
            loca2 = locat2.lower()
            loc1 = loc1.translate(str.maketrans(" ", " ", string.punctuation))
            loc2 = loca2.translate(str.maketrans(" ", " ", string.punctuation))
            lo1 = word_tokenize(loc1)
            lo2 = word_tokenize(loc2)
            loc1_nostop = [w for w in lo1 if not w.lower() in stop_words]
            loc2_nostop = [w for w in lo2 if not w.lower() in stop_words]
            corpus_location = [' '.join(loc1_nostop), ' '.join(loc2_nostop)]
            matrix_location = vectorizer.fit_transform(corpus_location)
            cosine_sim_loc = cosine_similarity(matrix_location, matrix_location)
            loc_similarity = cosine_sim_loc[0][1]

            # Skill similarity
            skill2 = one_row['Skills']
            skill2.replace('`', ' ')
            skill1 = skill1.lower()
            skill2 = skill2.lower()
            location2 = locat2.lower()
            skill1 = skill1.translate(str.maketrans(" ", " ", string.punctuation))
            skill2 = skill2.translate(str.maketrans(" ", " ", string.punctuation))
            skill_1 = word_tokenize(skill1)
            skill_2 = word_tokenize(skill2)
            Doc1_nostop = [w for w in skill_1 if not w.lower() in stop_words]
            Doc2_nostop = [w for w in skill_2 if not w.lower() in stop_words]
            corpus_skills = [' '.join(Doc1_nostop), ' '.join(Doc2_nostop)]
            matrix_skill = vectorizer.fit_transform(corpus_skills)
            cosine_sim_skill = cosine_similarity(matrix_skill, matrix_skill)
            # skill_similarity = cosine_sim_skill[0][1]
            if one_row['URL']=='database':
                con = sqlite3.connect("user_data.db")
                c = con.cursor()
                c.execute("Select applicantid,tagline from applicant_info where name='" + one_row['Name'] + "' and email='"+ one_row['Company']+"'")
                result = c.fetchone()
                print(result[0])
                temp_dict.update({'applicantid': result[0]})
                temp_dict.update({'tagline': result[1]})
                con.close()
            temp_dict.update({'Location_similarity': cosine_sim_loc[0][1]})
            temp_dict.update({'Skill_similarity': cosine_sim_skill[0][1]})
            if cosine_sim_loc[0][1] > 0.3:
                if cosine_sim_skill[0][1] >= 0.01:
                    # temp_dict.update({'Skill_similarity' : cosine_sim_skill[0][1]})
                    recommend.append(one_row)
                elif cosine_sim_loc[0][1] >= 0:
                    # temp_dict.update({'Skill_similarity' : cosine_sim_skill[0][1]})
                    loc_similar_rows.append(one_row)
                else:
                    default_recommend.append(one_row)
            else:
                recommend2.append(one_row)
        # print(sorted(recommend, key=itemgetter('Skill_similarity'), reverse=True))
        if recommend != []:
            jobs = sorted(recommend, key=itemgetter('Skill_similarity'), reverse=True)
        elif loc_similar_rows != []:
            jobs = sorted(loc_similar_rows, key=itemgetter('Skill_similarity'), reverse=True)
        elif default_recommend != []:
            jobs = sorted(default_recommend, key=itemgetter('Skill_similarity'), reverse=True)
        else:
            jobs = sorted(recommend2, key=itemgetter('Skill_similarity'), reverse=True)

        # lastlist = sorted(jobs, key=lambda s: (not s['Company'], s['Company']), reverse=True)
        file1.close()
    # print(jobs)
    return (jobs)
        # print(cosine_sim_skill[0][1])
        # print(one_row)


def searchjob(loc1, skill1):
    vectorizer = TfidfVectorizer()
    stop_words = set(stopwords.words('english'))

    # con = sqlite3.connect("user_data.db")
    # c = con.cursor()
    # c.execute("Select * from applicant_info where username='" + useremail + "'")
    # result = c.fetchone()
    # con.close()
    # loc1 = result[2]
    # skill1 = result[4]
    recommend2=[]
    loc_similar_rows = []
    default_recommend=[]
    recommend = []
    temp_dict = {}
    with open('Job_roles.csv', 'r', encoding='utf-8') as file1:
        data = csv.DictReader(file1, fieldnames=['Job Title', 'Company', 'Location', 'Salary', 'Description', 'URL'])
        # data1 = list(data)
        for one_row in data:
            # row_no = data1.index(one_row)
            # print(row_no)

            # Location similarity
            if one_row['Job Title'] == 'Job Title':
                continue
            temp_dict = one_row
            # temp_dict.update('Job':"location_similarity")
            # print(temp_dict)
            locat2 = one_row['Location']
            loc1 = loc1.lower()
            loca2 = locat2.lower()
            loc1 = loc1.translate(str.maketrans(" ", " ", string.punctuation))
            loc2 = loca2.translate(str.maketrans(" ", " ", string.punctuation))
            lo1 = word_tokenize(loc1)
            lo2 = word_tokenize(loc2)
            loc1_nostop = [w for w in lo1 if not w.lower() in stop_words]
            loc2_nostop = [w for w in lo2 if not w.lower() in stop_words]
            corpus_location = [' '.join(loc1_nostop), ' '.join(loc2_nostop)]
            matrix_location = vectorizer.fit_transform(corpus_location)
            cosine_sim_loc = cosine_similarity(matrix_location, matrix_location)
            loc_similarity = cosine_sim_loc[0][1]

            # Skill similarity
            skill2 = one_row['Job Title']
            # skill2.replace('`', ' ')
            skill1 = skill1.lower()
            skill2 = skill2.lower()
            location2 = locat2.lower()
            skill1 = skill1.translate(str.maketrans(" ", " ", string.punctuation))
            skill2 = skill2.translate(str.maketrans(" ", " ", string.punctuation))
            skill_1 = word_tokenize(skill1)
            skill_2 = word_tokenize(skill2)
            Doc1_nostop = [w for w in skill_1 if not w.lower() in stop_words]
            Doc2_nostop = [w for w in skill_2 if not w.lower() in stop_words]
            corpus_skills = [' '.join(Doc1_nostop), ' '.join(Doc2_nostop)]
            matrix_skill = vectorizer.fit_transform(corpus_skills)
            cosine_sim_skill = cosine_similarity(matrix_skill, matrix_skill)
            # skill_similarity = cosine_sim_skill[0][1]
            temp_dict.update({'Location_similarity': cosine_sim_loc[0][1]})
            temp_dict.update({'Skill_similarity': cosine_sim_skill[0][1]})
            if cosine_sim_loc[0][1] > 0.3:
                if cosine_sim_skill[0][1] >= 0.01:
                # temp_dict.update({'Skill_similarity' : cosine_sim_skill[0][1]})
                    recommend.append(one_row)
                elif cosine_sim_loc[0][1] >= 0:
                        # temp_dict.update({'Skill_similarity' : cosine_sim_skill[0][1]})
                       loc_similar_rows.append(one_row)
                else:
                    default_recommend.append(one_row)
            else:
                recommend2.append(one_row)
        # print(sorted(recommend, key=itemgetter('Skill_similarity'), reverse=True))
        if recommend!=[]:
            jobs = sorted(recommend, key=itemgetter('Skill_similarity'), reverse=True)
        elif loc_similar_rows!=[]:
            jobs = sorted(loc_similar_rows, key=itemgetter('Skill_similarity'), reverse=True)
        elif default_recommend!=[]:
            jobs = sorted(default_recommend, key=itemgetter('Skill_similarity'), reverse=True)
        else:
            jobs = sorted(recommend2, key=itemgetter('Skill_similarity'), reverse=True)
        # lastlist = sorted(jobs, key=lambda s: (not s['Salary'], s['Salary']))
        # print(cosine_sim_skill[0][1])
        # print(one_row)
        file1.close()
    return (jobs)


def joblistings():
    global useremail
    global userid
    vectorizer = TfidfVectorizer()
    stop_words = set(stopwords.words('english'))
    con = sqlite3.connect("user_data.db")
    c = con.cursor()
    c.execute("Select * from applicant_info where username='" + useremail + "' and applicantid="+str(userid))
    result = c.fetchone()
    con.close()
    loc1 = result[2]
    skill1 = result[4]
    recommend2 = []
    loc_similar_rows = []
    default_recommend = []
    recommend = []
    temp_dict = {}
    with open('Job_roles.csv', 'r', encoding='utf-8') as file1:
        data = csv.DictReader(file1, fieldnames=['Job Title', 'Company', 'Location', 'Salary', 'Description', 'URL'])
        # data1 = list(data)
        for one_row in data:
            # row_no = data1.index(one_row)
            # print(row_no)
            # Location similarity
            if one_row['Job Title'] == 'Job Title':
                continue
            temp_dict = one_row
            # temp_dict.update('Job':"location_similarity")
            # print(temp_dict)
            locat2 = one_row['Location']
            loc1 = loc1.lower()
            loca2 = locat2.lower()
            loc1 = loc1.translate(str.maketrans(" ", " ", string.punctuation))
            loc2 = loca2.translate(str.maketrans(" ", " ", string.punctuation))
            lo1 = word_tokenize(loc1)
            lo2 = word_tokenize(loc2)
            loc1_nostop = [w for w in lo1 if not w.lower() in stop_words]
            loc2_nostop = [w for w in lo2 if not w.lower() in stop_words]
            corpus_location = [' '.join(loc1_nostop), ' '.join(loc2_nostop)]
            matrix_location = vectorizer.fit_transform(corpus_location)
            cosine_sim_loc = cosine_similarity(matrix_location, matrix_location)
            loc_similarity = cosine_sim_loc[0][1]

            # Skill similarity
            skill2 = one_row['Description']
            skill2.replace('`', ' ')
            skill1 = skill1.lower()
            skill2 = skill2.lower()
            location2 = locat2.lower()
            skill1 = skill1.translate(str.maketrans(" ", " ", string.punctuation))
            skill2 = skill2.translate(str.maketrans(" ", " ", string.punctuation))
            skill_1 = word_tokenize(skill1)
            skill_2 = word_tokenize(skill2)
            Doc1_nostop = [w for w in skill_1 if not w.lower() in stop_words]
            Doc2_nostop = [w for w in skill_2 if not w.lower() in stop_words]
            corpus_skills = [' '.join(Doc1_nostop), ' '.join(Doc2_nostop)]
            matrix_skill = vectorizer.fit_transform(corpus_skills)
            cosine_sim_skill = cosine_similarity(matrix_skill, matrix_skill)
            # skill_similarity = cosine_sim_skill[0][1]
            if one_row['URL']=='database':
                con = sqlite3.connect("user_data.db")
                c = con.cursor()
                c.execute("Select companyid,companywebsite,email from company_info where companyname='" + one_row['Company'] + "' and jobtitle='"+ one_row['Job Title']+"'")
                result = c.fetchone()
                websit= result[1]
                maile= result[2]
                temp_dict.update({'companyid': result[0]})
                temp_dict.update({'website': websit})
                temp_dict.update({'email': maile})
                con.close()
            temp_dict.update({'Location_similarity': cosine_sim_loc[0][1]})
            temp_dict.update({'Skill_similarity': cosine_sim_skill[0][1]})
            if cosine_sim_loc[0][1] > 0.3:
                if cosine_sim_skill[0][1] >= 0.01:
                    # temp_dict.update({'Skill_similarity' : cosine_sim_skill[0][1]})
                    recommend.append(one_row)
                elif cosine_sim_loc[0][1] >= 0:
                    # temp_dict.update({'Skill_similarity' : cosine_sim_skill[0][1]})
                    loc_similar_rows.append(one_row)
                else:
                    default_recommend.append(one_row)
            else:
                recommend2.append(one_row)
        print(sorted(recommend, key=itemgetter('Skill_similarity'), reverse=True))
        print(sorted(loc_similar_rows, key=itemgetter('Skill_similarity'), reverse=True))
        print(sorted(default_recommend, key=itemgetter('Skill_similarity'), reverse=True))
        print(sorted(recommend2, key=itemgetter('Skill_similarity'), reverse=True))
        if recommend != []:
            jobs = sorted(recommend, key=itemgetter('Skill_similarity'), reverse=True)
        elif loc_similar_rows != []:
            jobs = sorted(loc_similar_rows, key=itemgetter('Skill_similarity'), reverse=True)
        elif default_recommend != []:
            jobs = sorted(default_recommend, key=itemgetter('Skill_similarity'), reverse=True)
        else:
            jobs = sorted(recommend2, key=itemgetter('Skill_similarity'), reverse=True)
        # lastlist = sorted(jobs, key=lambda s: (not s['Salary'], s['Salary']))
        # print(cosine_sim_skill[0][1])
        # print(one_row)
        file1.close()
    return (jobs)


@app.route('/createprofile', methods=["GET", "POST"])
def createprofile():
    # print("x")
    if (request.method == "POST"):
        # print("x")
        if (request.form["name"] != "" and request.form["profileemail"] != "" and request.form["location"] != "" and
                request.form["education"] != "" and request.form["skills"] != "" and request.form["contact"] != "" and
                request.form["email"] != "" and request.form['passw'] != "" and request.form["retype"] != ""):
            # print("x")
            can_name = request.form["name"]

            can_mail = request.form["profileemail"]
            location = request.form["location"]
            # jobregion= request.form["jobregion"]
            edu = request.form["education"]
            # editor1 = request.form["editor1"]
            skills = request.form["skills"]
            # companytagline= request.form["companytagline"]
            # editor2= request.form["editor2"]
            # if request.form["companywebsite"]!="":
            can_contact = request.form["contact"]
            # else:
            #     companywebsite = " "
            if request.form["linkedin"] != "":
                can_linkedin = request.form["linkedin"]
            else:
                can_linkedin = " "
            if request.form["subtitle"] != "":
                can_tag = request.form["subtitle"]
            else:
                can_tag = " "
            email = request.form["email"]
            password = request.form["passw"]
            con = sqlite3.connect("user_data.db")

            # con.execute("create table if not exists 'applicant_info'('email'TEXT, 'password'TEXT);")
            c = con.cursor()
            c.execute("Select count(*) from applicant_info where name='"+can_name+"' and email='"+can_mail+"' and username='"+email+"'")
            duplic=c.fetchone()
            if duplic[0]==0:
                query = "INSERT INTO applicant_info(name,email,location,education,skills,contact,linkedin,username,password,tagline) VALUES (?,?,?,?,?,?,?,?,?,?)"
                # print(query)
                c.execute(query, (can_name, can_mail, location, edu, skills, can_contact, can_linkedin, email, password, can_tag))
                con.commit()
                con.close()
                write_dict = {'Name': can_name, 'Job Title': can_contact, 'Company': can_mail, 'College': edu, 'Location': location,
                              'Skills': skills, 'URL': "database"}
                head = ['Name', 'Job Title', 'Company', 'College', 'Location', 'Skills', 'URL']
                with open('Profile_data.csv', 'a', newline='', encoding='utf-8') as file1:
                    writor = csv.DictWriter(file1, head)
                    writor.writerow(write_dict)
                return render_template('login.html')
            else:
                con.close()
                flash("Applicant with the mentioned details already exist!\nTry changing some of the fields.....")
        elif (request.form["name"] == "" or request.form["profileemail"] == "" or request.form[
            "location"] == "" or request.form["education"] == "" or request.form["skills"] == "" or request.form[
                  "contact"] == "" or request.form["email"] == "" or request.form["passw"] == ""):
            flash("Please fill all the required fields!")
        elif (request.form['passw'] != request.form["retype"]):
            flash("Password and retyped password don't match!")
    return render_template('create-profile.html')

@app.route('/<int:passedid>', methods=["Get", "post"])
@login_required
def viewprofile(passedid):
    global company_login, userid,useremail
    # print(applicant_login, userid, useremail)
    def check_role():
        if 'role' not in session:
            return None
        elif session['role'] == 'company':
            return 'company'
        else:
            return 'applicant'
    role = check_role()
    if role is None:
         return render_template('login.html', msg="You are not authorized to visit the page! Please log in to continue...")
    elif role == 'company':
        con = sqlite3.connect("user_data.db")
        c = con.cursor()
        c.execute("Select * from applicant_info where applicantid=?",(passedid,))
        result = c.fetchone()
        pass_dict={'Name': result[1],'email':result[2],'location':result[3],'education':result[4],'skills':result[5], 'contact': result[6],'linkedin':result[7], 'tagline':result[10]}
        con.close()
        return render_template('profile-single.html', candi=pass_dict)
    else:
        con = sqlite3.connect("user_data.db")
        c = con.cursor()
        c.execute("Select * from company_info where companyid=?",(passedid,))
        result = c.fetchone()
        pass_dict = {'companyname': result[1], 'jobtitle': result[2], 'location': result[3], 'jobtype': result[4],'description': result[5].replace('`','\n'), 'website': result[6], 'email': result[7], 'salary': result[10], 'facebook':result[8], 'twitter':result[9]}
        con.close()
        return render_template('job-single.html', jobd=pass_dict)


# @app.route('/profile-single', methods=["Get", "post"])
# def profilesingle():
#     return render_template('profile-single.html')
#
#
# @app.route('/<id>', methods=["Get", "post"])
# def viewjob(id):
#     global applicant_login, userid, useremail
#     print(applicant_login,userid,useremail)
#     if useremail!="" and userid!=0 and applicant_login!= False:
#         return render_template('job-single.html')
#     return render_template('index.html')


@app.route('/updateprofile', methods=['POST', 'GET'])
@login_required
def update():
    user= session['username']
    def chec_role():
        if 'role' not in session:
            return None
        elif session['role'] == 'company':
            return 'company'
        else:
            return 'applicant'
    role = chec_role()
    if role is None:
         return render_template('login.html', msg="You are not authorized to visit the page! Please log in to continue...")
    elif role=='company':
        if (request.method == "POST"):
            paj_email = request.form["companyemail"]
            jobtitle = request.form["jobtitle"]
            joblocation = request.form["joblocation"]
            # jobregion= request.form["jobregion"]
            jobtype = request.form["jobtype"]
            # editor1 = request.form["editor1"]
            companyname = request.form["companyname"]
            companywebsite = request.form["companywebsite"]
            if request.form["companywebsitefb"] != "":
                companywebsitefb = request.form["companywebsitefb"]
            else:
                companywebsitefb = " "
            if request.form["companywebsitetw"] != "":
                companywebsitetw = request.form["companywebsitetw"]
            else:
                companywebsitetw = " "
            if request.form["salary"] != "":
                salary = request.form["salary"]
            else:
                salary = " "
            desc = request.form["description"]
            desc = desc.replace('\n', '`')
            # email = request.form["email"]
            # print(salary)
            # password = request.form["passw"]
            conn = sqlite3.connect('user_data.db')
            c = conn.cursor()
            c.execute("Select * from company_info where username=?" ,(user,))
            result_list = c.fetchone()
            c.execute("UPDATE company_info SET companyname=?, jobtitle=?,joblocation=?,jobtype=?, description=?, companywebsite=?, email=?, companywebsitefb=?, companywebsitetw=?, salary=? WHERE username=?", ( companyname,jobtitle,joblocation, jobtype, desc.replace('\n','`'), companywebsite, paj_email, companywebsitefb, companywebsitetw, salary, user))
            # Commit the changes and close the connection
            conn.commit()
            new_values={'Job Title': result_list[2], 'Company': result_list[1],'Location': joblocation,'Salary': salary,'Description': desc, 'URL':'database'}
            print(new_values)
            with open('Job_roles.csv', mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                rows = []
                for row in csv_reader:
                    rows.append(row)
                file.close()
            for index, row in enumerate(rows):
                if row['Job Title'] == result_list[2] and row['Company']==result_list[1]:
                    rows[index].update(new_values)

            with open('Job_roles.csv', mode='w', newline='', encoding='utf-8') as file:
                head = ['Job Title', 'Company', 'Location', 'Salary', 'Description', 'URL']
                csv_writer = csv.DictWriter(file, fieldnames=head)
                csv_writer.writeheader()
                for row in rows:
                    csv_writer.writerow(row)
                file.close()
            conn.close()
            return render_template('login.html', msg="Profile updated successfully! Please login again...")
        else:
            con = sqlite3.connect("user_data.db")
            c = con.cursor()
            c.execute("Select * from company_info where username=?", ( user,))
            result = c.fetchone()
            pass_dict = {'companyname': result[1], 'jobtitle': result[2], 'location': result[3], 'jobtype': result[4],
                         'description': result[5].replace('`', '\n'), 'website': result[6], 'email': result[7],
                         'salary': result[10], 'facebook': result[8], 'twitter': result[9]}
            print(pass_dict)
            con.close()
            return render_template('update.html', role=role, profile=pass_dict)
    elif role == 'applicant':
        if (request.method == "POST"):
            can_name = request.form["name"]
            can_mail = request.form["profileemail"]
            location = request.form["location"]
            edu = request.form["education"]
            skills = request.form["skills"]
            can_contact = request.form["contact"]
            if request.form["linkedin"] != "":
                can_linkedin = request.form["linkedin"]
            else:
                can_linkedin = " "
            if request.form["subtitle"] != "":
                can_tag = request.form["subtitle"]
            else:
                can_tag = " "
            # email = request.form["email"]
            # password = request.form["passw"]
            conn = sqlite3.connect('user_data.db')
            c = conn.cursor()
            c.execute("Select * from company_info where username=" + user)
            result_list = c.fetchone()
            c.execute("UPDATE applicant_info SET name=?, email=?, location=?, education=?, skills=?, contact=?, linkedin=?, tagline=? WHERE username=?", (can_name,can_mail, location, edu, skills, can_contact, can_linkedin,can_tag,user))
            conn.commit()
            new_values = {'Name': result_list[1], 'Job Title': can_contact, 'Company': can_mail, 'College':edu,'Location': location,
                          'Skills': skills, 'URL': 'database'}
            with open('Profile_data.csv', mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                rows = []
                for row in csv_reader:
                    rows.append(row)
                file.close()
            for index, row in enumerate(rows):
                if row['Name'] == result_list[1] and row['Company'] == result_list[2] and row['College']==result_list[4]:
                    rows[index].update(new_values)

            with open('Profile_data.csv', mode='w', newline='', encoding='utf-8') as file:
                head = ['Name', 'Job Title', 'Company', 'College', 'Location', 'Skills', 'URL']
                csv_writer = csv.DictWriter(file, fieldnames=head)
                csv_writer.writeheader()
                for row in rows:
                    csv_writer.writerow(row)
                file.close()

            conn.close()
            return render_template('login.html', msg="Profile updated successfully! Please login again...")
        else:
            con = sqlite3.connect("user_data.db")
            c = con.cursor()
            c.execute("Select * from applicant_info where applicantid=" + str(userid))
            result = c.fetchone()
            pass_dict = {'name': result[1], 'email': result[2], 'location': result[3], 'education': result[4],
                         'skills': result[5], 'contact': result[6], 'linkedin': result[7], 'tagline': result[10]}
            con.close()
            return render_template('update.html', role=role, profile=pass_dict)



@app.route('/logout')
def logout():
    global applicant_login, userid, useremail, company_login
    applicant_login = False
    company_login = False
    useremail = ""
    userid = 0
    session.clear()
    return render_template('login.html')

@app.route('/dropaccount', methods=['POST'])
@login_required
def dropaccount():
    user= session['username']
    def check_role():
        if 'role' not in session:
            return None
        elif session['role'] == 'company':
            return 'company'
        else:
            return 'applicant'
    role = check_role()
    if request.method == "POST" and role=='company':
        passw= request.form['del_password']
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute("Select * from company_info where username=?",(  user,))
        result_list = c.fetchone()
        if passw==result_list[12]:
            c.execute("UPDATE company_info SET password='' WHERE username=?",(user,))
            conn.commit()
            with open('Job_roles.csv', mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                rows = []
                for row in csv_reader:
                    rows.append(row)
                file.close()
            for index, row in enumerate(rows):
                if row['Job Title'] == result_list[2] and row['Company']==result_list[1]:
                    del rows[index]

            with open('Job_roles.csv', mode='w', newline='', encoding='utf-8') as file:
                head = ['Job Title', 'Company', 'Location', 'Salary', 'Description', 'URL']
                csv_writer = csv.DictWriter(file, fieldnames=head)
                csv_writer.writeheader()
                for row in rows:
                    csv_writer.writerow(row)
                file.close()
            conn.close()
            return render_template('login.html', msg="Profile deleted successfully!")

    elif request.method == "POST" and role=='applicant':
        passw= request.form['del_password2']
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute("Select * from applicant_info where username=?",(  user,))
        result_list = c.fetchone()
        if passw == result_list[9]:
            c.execute("UPDATE applicant_info SET password='' WHERE username=?", (user,))
            conn.commit()
            with open('Profile_data.csv', mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                rows = []
                for row in csv_reader:
                    rows.append(row)
                file.close()
            for index, row in enumerate(rows):
                if row['Name'] == result_list[1] and row['Company'] == result_list[2] and row['College']==result_list[4]:
                    del rows[index]

            with open('Profile_data.csv', mode='w', newline='', encoding='utf-8') as file:
                head = ['Name', 'Job Title', 'Company', 'College', 'Location', 'Skills', 'URL']
                csv_writer = csv.DictWriter(file, fieldnames=head)
                csv_writer.writeheader()
                for row in rows:
                    csv_writer.writerow(row)
                file.close()

            conn.close()
            return render_template('login.html', msg="Profile Deleted Successfully!")

if __name__ == '__main__':
    app.run(debug=True, port=5004)