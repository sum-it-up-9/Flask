from flask import Flask, redirect, url_for, request,session
from flask import render_template,flash
from flaskext.mysql import MySQL
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import pickle
import re
import os
import pandas as pd
from urllib.parse import urlparse
from datetime import date,timedelta
from flask_mail import Mail, Message

app=Flask("mn")

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'url_detection'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

conn = mysql.connect()
cursor =conn.cursor()

cursor.execute("select * from user")
data = cursor.fetchone()
print(data)

app.config['SECRET_KEY'] = 'thisisfirstflaskapp'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'samv9668@gmail.com'
app.config['MAIL_PASSWORD'] = 'eqguytwzoncvojrf'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

mail = Mail(app)
app.config['STRIPE_PUBLIC_KEY']=''
app.config['STRIPE_SECRET_KEY']=''
app.secret_key = '123456'


UPLOAD_FOLDER = 'static/files'
app.config['UPLOAD_FOLDER'] =UPLOAD_FOLDER

#Load the model
model=pickle.load(open("model.pkl","rb"))

@app.route('/complaintmail',methods=['GET','POST'])
def complaintmail():
    if request.method == 'POST':
        message = request.form['message']
        msg = Message('User sent you a Message', recipients=['imxpath@gmail.com'], sender='Cyborg')
        msg.body = message
        mail.send(msg)
        flash("Message sent successfully")
        return render_template("introductionPage.html")



@app.route("/", methods=["POST", "GET"])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USER WHERE USERNAME = %s OR email = %s', (username, email))
        account = cursor.fetchone()

        if account:
            flash('Account with same email OR username already exists!')
            return render_template("home.html")

        else:
            cursor.execute('INSERT INTO USER(name,username,password,email) VALUES ( %s, %s, %s, %s)',
                           (name, username, password, email,))
            conn.commit()
            msg = Message(
            'Cyborg Registration',
            sender='Cyborg',
            recipients=[email]
            )
            msg.body = 'Hello ' + username + ',\n\nWelcome to Cyborg! We hope you will have a great experience. Get started by logging into your new account!'
            mail.send(msg)
            flash('You have successfully registered! Please Log in to continue!')
            return render_template("home.html")

    return render_template("home.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        username = request.form['username1']
        password = request.form['password1']

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USER WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        print(account)

        if account:
            # Createing session data

            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['name'] = account[2]
            session['email'] = account[3]
            print(type(session))

            msg = 'Logged in successfully!'
            return render_template("introductionPage.html", msg=msg)

        else:
            flash('Please Check credentials!')
            return render_template("home.html")

    return render_template("home.html")


@app.route('/changepass/<user>',methods=['GET','POST'])
#@app.route('/changepass',methods=['GET','POST'])
def changepass(user):
#def changepass():

    if request.method == 'POST':
        #print("under post")
        user_id=user[1]
        #print(user)
        #print(type(user))
        #print(user_id)
        password = request.form['password']
        #print(password)
        cursor = conn.cursor()
        cursor.execute("UPDATE user SET password = %s WHERE user_id = %s",
                       (password,user_id))
        conn.commit()
        flash("Password changed! Please login!")
        return render_template("home.html")

    return render_template("change_password.html")

def get_token(user,expires_sec):
    serial=Serializer(app.config['SECRET_KEY'], expires_in=expires_sec)
    return serial.dumps({'user_id':user[0]}).decode('utf-8')

def verify_token(token):
    serial=Serializer(app.config['SECRET_KEY'])
    try:
        user_id=serial.loads(token)['user_id']
    except:
        return None
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user WHERE user_id =%s', (user_id,))
    user = cursor.fetchone()
    print(user)
    return user




@app.route('/reset_password/<token>',methods=['GET','POST'])
def reset_token(token):
    user=verify_token(token)
    print("received from verify token")
    print(user)

    if user is None:
        flash('That is invalid token or expired. Please try again.')
        return render_template("reset.html")

    return render_template("change_password.html",user=user)




def send_mail(user):
    token = get_token(user, 3600)
    email = user[3]
    msg = Message('Password Reset Request', recipients=[email], sender='Cyborg')
    msg.body = f''' To reset your password. Please follow the link below.

    {url_for('reset_token', token=token, _external=True)}

    If you didn't send a password reset request. Please ignore this message.

    '''
    mail.send(msg)

@app.route('/reset_password',methods=['GET','POST'])
def reset():
    if request.method == 'POST':
        email = request.form['email']
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user WHERE email =%s', (email,))
        user = cursor.fetchone()
        print(user)
        if user:
            send_mail(user)
            flash('Reset request sent. Check your mail!')
            return render_template("reset.html")
        else:
            flash('This email id does not exist!')
            return render_template("reset.html")


    return render_template("reset.html")


@app.route('/df')
def dataframe():
    if session.get('loggedin') == True:
        print("true")
        return render_template("dataframe.html")

    #print("false")
    return render_template("notallowed.html")

def parseCSV(filePath):
    # CVS Column Names
    col_names = ['url']
    # Use Pandas to parse the CSV file
    csvData = pd.read_csv(filePath,names=col_names, header=None)
    csvData.head()
    # Loop through the Rows
    #for i, row in csvData.iterrows():
        #sql = "INSERT INTO addresses (first_name, last_name, address, street, state, zip) VALUES (%s, %s, %s, %s, %s, %s)"
        #value = (row['first_name'], row['last_name'], row['address'], row['street'], row['state'], str(row['zip']))
        #mycursor.execute(sql, value, if_exists='append')
        #mydb.commit()
        #print(i, row['first_name'], row['last_name'], row['address'], row['street'], row['state'], row['zip'])


def isValidURL(str):
    # Regex to check valid URL
    regex = ("((http|https)://)(www.)?" +
             "[a-zA-Z0-9@:%._\\+~#?&//=]" +
             "{2,256}\\.[a-z]" +
             "{2,6}\\b([-a-zA-Z0-9@:%" +
             "._\\+~#?&//=]*)")

    # Compile the ReGex
    p = re.compile(regex)

    # If the string is empty
    # return false
    if (str == None):
        return 'False'

    # Return if the string
    # matched the ReGex
    if (re.search(p, str)):
        return 'True'
    else:
        return 'False'


def urlresult(num):
    if(num==0):
        return 'Safe'
    else:
        return 'Malicious'

def predictforcsv(file_path):
    col_names = ['url']
    df = pd.read_csv(file_path, names=col_names, header=None)
    print(df)

    df['isURLValid'] = df['url'].apply(isValidURL)
    if ("False" in set(df['isURLValid'])) == True:
        print('back')
        flash("Data should contain urls only!")
        return render_template("mali-Url.html")
    else:
        #print(url)
        #print(df.dtypes)
        df['url_length'] = df['url'].apply(lambda i: len(str(i)))
        df['hostname_length'] = df['url'].apply(lambda i: len(urlparse(i).netloc))
        df['path_length'] = df['url'].apply(lambda i: len(urlparse(i).path))
        df['count-'] = df['url'].apply(lambda i: i.count('-'))
        df['count@'] = df['url'].apply(lambda i: i.count('@'))
        df['count?'] = df['url'].apply(lambda i: i.count('?'))
        df['count%'] = df['url'].apply(lambda i: i.count('%'))
        df['count.'] = df['url'].apply(lambda i: i.count('.'))
        df['count='] = df['url'].apply(lambda i: i.count('='))
        df['count-http'] = df['url'].apply(lambda i: i.count('http'))
        df['count-https'] = df['url'].apply(lambda i: i.count('https'))
        df['count-www'] = df['url'].apply(lambda i: i.count('www'))

        def fd_length(url):
            urlpath = urlparse(url).path
            try:
                return len(urlpath.split('/')[1])
            except:
                return 0

        df['fd_length'] = df['url'].apply(lambda i: fd_length(i))

        def digit_count(url):
            digits = 0
            for i in url:
                if i.isnumeric():
                    digits = digits + 1
            return digits

        df['count-digits'] = df['url'].apply(lambda i: digit_count(i))

        def letter_count(url):
            letters = 0
            for i in url:
                if i.isalpha():
                    letters = letters + 1
            return letters

        df['count-letters'] = df['url'].apply(lambda i: letter_count(i))

        def no_of_dir(url):
            urldir = urlparse(url).path
            return urldir.count('/')

        df['count_dir'] = df['url'].apply(lambda i: no_of_dir(i))

        import re
        # Use of IP or not in domain
        def having_ip_address(url):
            match = re.search(
                '(([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.'
                '([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\/)|'  # IPv4
                '((0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\/)'  # IPv4 in hexadecimal
                '(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}', url)  # Ipv6
            if match:
                # print match.group()
                return -1
            else:
                # print 'No matching pattern found'
                return 1

        df['use_of_ip'] = df['url'].apply(lambda i: having_ip_address(i))

        def shortening_service(url):
            match = re.search('bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|'
                              'yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|'
                              'short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|'
                              'doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|'
                              'db\.tt|qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|'
                              'q\.gs|is\.gd|po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|'
                              'x\.co|prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|'
                              'tr\.im|link\.zip\.net',
                              url)
            if match:
                return -1
            else:
                return 1

        df['short_url'] = df['url'].apply(lambda i: shortening_service(i))
        x = df[['hostname_length',
                     'path_length', 'fd_length', 'count-', 'count@', 'count?',
                     'count%', 'count.', 'count=', 'count-http', 'count-https', 'count-www', 'count-digits',
                     'count-letters', 'count_dir', 'use_of_ip']]

        prediction=model.predict(x)

        df2 = pd.DataFrame(prediction,columns=['result'])
        #print(df2.dtypes)
        #print(df2)
        df=df.drop(['hostname_length','url_length','short_url','isURLValid',
                     'path_length', 'fd_length', 'count-', 'count@', 'count?',
                     'count%', 'count.', 'count=', 'count-http', 'count-https', 'count-www', 'count-digits',
                     'count-letters', 'count_dir', 'use_of_ip'], axis=1)
        df['Result'] = df2['result'].apply(urlresult)
        #print(prediction)
        #print(df)
        cursor = conn.cursor()
        USER_ID = session['id']
        for i, row in df.iterrows():
            cursor.execute('INSERT INTO checked_url(url,result,user_id) VALUES ( %s, %s, %s)',
                           (row['url'], row['Result'], USER_ID))
            conn.commit()


        return df






@app.route('/upload',methods=["POST", "GET"])
def uploadFiles():
    if session.get('loggedin') == True:

        ID = session['id']
        cursor = conn.cursor()
        cursor.execute('SELECT SUBSCRIPTION_DATE,SUB_END_DATE FROM ORDERS WHERE user_id =%s', (ID,))
        USER = cursor.fetchone()
        print(USER)
        if(USER):
            print("ok user found")

        else:
            print("done")
            flash('To use this feature, you need to buy a subscription!')
            return render_template("mali-Url.html")

        SUB_DATE=USER[0]
        end_date=USER[1]
        diff=end_date-SUB_DATE
        dataa = [diff]
        tempdf = pd.DataFrame(dataa, columns=['diff'])
        tempdf["diff"] = (tempdf["diff"]).dt.days
        num=tempdf.iloc[0,0]
        #print(dff.dtypes)
        #print(type(num))
        #print(num)
        if(num>30):
            print("done")
            flash('To use this feature, you need to buy a subscription!')
            return render_template("mali-Url.html")


        # get the uploaded file


        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            # set the file path
            uploaded_file.save(file_path)
            check_df = pd.read_csv(file_path)
            noofcolumns=check_df.shape[1]
            print(noofcolumns)
            if(noofcolumns>1 or noofcolumns<1):
                print("greater")
                flash('File should contain only one column and should be in .csv format!')
                return render_template("mali-Url.html")

            col_names = ['url']
            df = pd.read_csv(file_path, names=col_names, header=None)
            print(df)

            df['isURLValid'] = df['url'].apply(isValidURL)
            if ("False" in set(df['isURLValid'])) == True:
                print('back')
                flash("Data should contain urls only!")
                return render_template("mali-Url.html")

            df=predictforcsv(file_path)
            row_data = list(df.values.tolist())
            print(row_data)
            print(type(row_data))
            return render_template("dataframe.html", column_names=df.columns.values, row_data=list(df.values.tolist()),
                  zip=zip)

    else:
        return render_template("notallowed.html")



@app.route('/show',methods=["POST", "GET"])
def show():
    if session.get('loggedin') == True:
        ID = session['id']
        cursor = conn.cursor()
        cursor.execute('SELECT url,result FROM CHECKED_URL WHERE user_id =%s', (ID,))
        USER = cursor.fetchall()
        print(type(USER))
        print(USER)
        columns=['URL','RESULT']
        return render_template("showhistory.html", column_names=columns, row_data=USER,
                               zip=zip)
    else:
        return render_template("notallowed.html")




@app.route('/predict',methods=["POST", "GET"])
def predict():
    if request.method == 'POST':

        url = request.form['url']
        print(type(url))
        ans=isValidURL(url)
        if(ans=='False'):
            print('back')
            flash("Note: The URL must start with either http or https and then followed by :// and www. respectively for eg, https://www.google.com")
            return render_template("mali-Url.html")

        df = pd.DataFrame(columns=['url'])
        new_row = {'url': url}
        df = df.append(new_row, ignore_index=True)
        print(df)

        df['url_length'] = df['url'].apply(lambda i: len(str(i)))
        df['hostname_length'] = df['url'].apply(lambda i: len(urlparse(i).netloc))
        df['path_length'] = df['url'].apply(lambda i: len(urlparse(i).path))
        df['count-'] = df['url'].apply(lambda i: i.count('-'))
        df['count@'] = df['url'].apply(lambda i: i.count('@'))
        df['count?'] = df['url'].apply(lambda i: i.count('?'))
        df['count%'] = df['url'].apply(lambda i: i.count('%'))
        df['count.'] = df['url'].apply(lambda i: i.count('.'))
        df['count='] = df['url'].apply(lambda i: i.count('='))
        df['count-http'] = df['url'].apply(lambda i: i.count('http'))
        df['count-https'] = df['url'].apply(lambda i: i.count('https'))
        df['count-www'] = df['url'].apply(lambda i: i.count('www'))

        def fd_length(url):
            urlpath = urlparse(url).path
            try:
                return len(urlpath.split('/')[1])
            except:
                return 0

        df['fd_length'] = df['url'].apply(lambda i: fd_length(i))

        def digit_count(url):
            digits = 0
            for i in url:
                if i.isnumeric():
                    digits = digits + 1
            return digits

        df['count-digits'] = df['url'].apply(lambda i: digit_count(i))

        def letter_count(url):
            letters = 0
            for i in url:
                if i.isalpha():
                    letters = letters + 1
            return letters

        df['count-letters'] = df['url'].apply(lambda i: letter_count(i))

        def no_of_dir(url):
            urldir = urlparse(url).path
            return urldir.count('/')

        df['count_dir'] = df['url'].apply(lambda i: no_of_dir(i))

        import re
        # Use of IP or not in domain
        def having_ip_address(url):
            match = re.search(
                '(([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.'
                '([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\/)|'  # IPv4
                '((0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\.(0x[0-9a-fA-F]{1,2})\\/)'  # IPv4 in hexadecimal
                '(?:[a-fA-F0-9]{1,4}:){7}[a-fA-F0-9]{1,4}', url)  # Ipv6
            if match:
                # print match.group()
                return -1
            else:
                # print 'No matching pattern found'
                return 1

        df['use_of_ip'] = df['url'].apply(lambda i: having_ip_address(i))

        def shortening_service(url):
            match = re.search('bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|'
                              'yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|'
                              'short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|'
                              'doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|'
                              'db\.tt|qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|'
                              'q\.gs|is\.gd|po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|'
                              'x\.co|prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|'
                              'tr\.im|link\.zip\.net',
                              url)
            if match:
                return -1
            else:
                return 1

        df['short_url'] = df['url'].apply(lambda i: shortening_service(i))
        x = df[['hostname_length',
                     'path_length', 'fd_length', 'count-', 'count@', 'count?',
                     'count%', 'count.', 'count=', 'count-http', 'count-https', 'count-www', 'count-digits',
                     'count-letters', 'count_dir', 'use_of_ip']]

        prediction=model.predict(x)
        print(prediction)
        num=prediction[0]
        result=urlresult(num)

        #print(type(url))


        cursor = conn.cursor()
        USER_ID = session['id']
        
        cursor.execute('INSERT INTO CHECKED_URL(url,result,user_id) VALUES ( %s, %s, %s)',
                       (url,result, USER_ID))
        conn.commit()

        if(prediction==0):
            print("benign-safe")
            return render_template("result.html")
        else:
            print("malicious")
            return render_template("wrong-url.html")









@app.route('/re')
def base():
    return render_template("base.html")

@app.route('/wrongurl')
def wrongurl():
    if session.get('loggedin') == True:
        return render_template("wrong-url.html")
    else:
        return render_template("notallowed.html")

@app.route('/result')
def result():
    if session.get('loggedin') == True:
        return render_template("result.html")
    else:
        return render_template("notallowed.html")



@app.route('/subs')
def subs():
    if session.get('loggedin') == True:
        return render_template("subscription.html")
    else:
        return render_template("notallowed.html")







@app.route('/success',methods=["POST", "GET"])
def success():

   cursor = conn.cursor()
   USER_ID = session['id']
   cursor.execute('SELECT user_id FROM orders WHERE user_id =%s', (USER_ID,))
   account = cursor.fetchone()
   if account:
       print("subscription exists")
       flash("Payment declined,You alredy have an active subscription!")
       return render_template("subscription.html")
   today = date.today()
   sub_end_date = date.today() + timedelta(days=30)
   email=session['email']

   username=session['username']
   cursor.execute('INSERT INTO ORDERS(user_id,username,email,subscription_date,sub_end_date) VALUES ( %s, %s, %s, %s, %s)',
                  (USER_ID, username,  email, today, sub_end_date,))
   conn.commit()
   flash('Congratulation,you are now subscribed!')
   return render_template("subscription.html")


@app.route('/mali')
def mali():
    if session.get('loggedin') == True:
        return render_template("mali-Url.html")

    else:
        print(session.get("key"))
        return render_template("notallowed.html")


@app.route('/profile')
def profile():
    if session.get('loggedin') == True:
        username=session['username']
        ID = session['id']
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USER WHERE user_id =%s',(ID,) )
        USER=cursor.fetchone()
        return render_template("profile.html",USER=USER)
    else:
        return render_template("notallowed.html")



@app.route('/update',methods=["POST", "GET"])
def update():
    if request.method == 'POST':
        cursor = conn.cursor()
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        if not username:
            username=session['username']

        if not name:
            name=session['name']

        if not email:
            email = session['email']
        id = session['id']

        # sql = "UPDATE USER SET name = %s,username = %s,email = %s WHERE USER_ID = %s",(name, username, email)
        # val = (name, username, email)
        cursor.execute("UPDATE USER SET name = %s, username = %s, email = %s WHERE USER_ID = %s",
                       (name, username, email, id,))
        conn.commit()
        session['username']=username
        session['name']=name
        session['email']=email

        return redirect(url_for('profile'))



@app.route('/logout')
def logout():
    if session.get('loggedin') == True:
       session.pop('loggedin', None)
       session.pop('id', None)
       session.pop('username', None)
       session.pop('name', None)
       session.pop('email', None)
       return redirect(url_for('login'))

    else:
        return render_template("notallowed.html")




@app.route('/introduction')
def intro():
    if session.get('loggedin') == True:
        return render_template("introductionPage.html")
    else:
        return render_template("notallowed.html")



@app.route('/singleurl',methods=["POST", "GET"])
def singleurl():
    cursor = conn.cursor()
    USER_ID = session['id']
    URL=request.form['url']
    cursor.execute('INSERT INTO CHECKED_URL(URL,user_id) VALUES ( %s, %s)',
                   (URL,USER_ID))
    conn.commit()
    msg = 'Congratulation,Payment successful!'

    return render_template("success.html")


app.run()
