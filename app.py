from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate
from flask_cors import CORS
import emails
import os


# Get Environment variable information
sender = os.environ.get("EMAIL_SENDER", os.environ.get('SENDER'))
password = os.environ.get("SMTP_PASSWORD", os.environ.get('PASS'))
url = os.environ.get("SITE_URL", "http://example.com")
ALLOWED_HOST = os.environ.get('HOSTS', "localhost, 127.0.0.1").split(",")
DEBUG = bool(int(os.environ.get('DEBUG', 1))) 
# Create a Flask application
app = Flask(__name__)

# database Configuration for devlopment and production
if DEBUG:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('LOCAL_DATABASE_URL', "")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', "")
   
db = SQLAlchemy(app)

# created a model/table
class SpotifyUser(db.Model):
    _email = db.Column('email', db.String(120), primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    registered = db.Column(db.Boolean, default=False ,nullable=False)
    pending = db.Column(db.Boolean, default=True ,nullable=False)
    
    # ensure the email column is stored in lower case
    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if value is not None:
            self._email = value.lower()

    def __repr__(self):
        return '<User %r>' % self.name

# Allow connection from all host
CORS(app) 

# Allow migration
migrate = Migrate(app, db)

# create user and notify developer endpoint 
@app.route('/spotify/mail', methods=['POST'])
def send_mail():
    # extract the data from the request body
    data = request.json
    if data is None or 'name' not in data or 'email' not in data:
        abort(400) # return if request body is empty or does not contain required data
    # Get username and email from the data
    user_email = data['email']
    user_name = data['name']
    # Email Message body that will be sent to the user
    user_body = """
        <h1 style="color: #db1ddb;">REGISTRATION REQUEST</h1>
        <p style="font-size:20px">Dear <strong>{0}</strong>,</p>
        <p style="font-size:20px;">
            Thank you for choosing the Jamming App.<br>
            Your registration request has been submitted successfully.<br>
            <br>You will be notified when your request has been granted.    
        </p>
        <p style="font-size:20px;">Keep Jamming!!!<br>Lakunle-CEO</p>
    """.format(user_name)
    # Email Message body that will be sent to the developer 
    client_body = """
        <h1 style="color: #db1ddb;">Register User</h1>
        <p><b>Name:</b> {0}</p>
        <p><b>Email:</b> {1}</p>

        <form action="{2}/spotify/register?email={1}&name={0}" method="POST">
            <button type="submit" style="
                background-color: #4CAF50; /* Green */
                border: none;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;">Register User</button>
        </form>
    """.format(user_name, user_email, url)
    new_user = SpotifyUser(name=user_name, email=user_email)
    try:
        # Register add new user to the data base
        db.session.add(new_user)
        db.session.commit()
        # SENd the eamil to the user and developer 
        emails.send_html_mail(sender, sender,"REQUEST TO REGISTER USER TO SPOTIFY", client_body, password)
        emails.send_html_mail(sender, user_email,"JAMMING APP REGISTRATION", user_body, password)
        # Return the new user if successful
        return  jsonify({'name':user_name, 'email':user_email, 'registered': False, 'pending': True}), 201
    #Handle database errors
    except IntegrityError as e:
        return jsonify({"error": "user with the email already exist"}), 401
    # # Handle all Other Errors
    except Exception as e:
        print(e)
        abort(500)

# get user endpoint
@app.route('/spotify/user/<email>', methods=["GET"])
def get_user(email):
    try:
        # Get user in the data base
        user = SpotifyUser.query.get(email.lower())
        
        if user: #check if user exist
            # if user return a json user object
            user = {"name":user.name, "email":user.email, "registered":user.registered, "pending":user.pending}
            return jsonify(user), 200
        
        # else return error message
        else:
            return jsonify({"error":"user does not exist"}), 401
    
    #Handle error            
    except Exception as e:
        print(e)
        abort(500)

# register user endpoint 
@app.route('/spotify/register', methods=['POST'])
def alter_user():
    username = request.args.get('name')
    user_email = request.args.get('email')
    
    # Check if email is part of the request
    if user_email is None or username is None:
        abort(400)
    
    # get the user
    user = SpotifyUser.query.get(user_email.lower())
    
    # user not exist return error message 
    if not user:
        return jsonify({"error":"user does not exist"}), 401
    
    # if user exist, Alter the registered and pending status of user and also send email to the user
    user.registered = True
    user.pending = False
    
    #update the database
    try:
        db.session.add(user)
        db.session.commit()
    
        # send an email to the user and notify changes made 
        body = """
            <h1 style="color: #db1ddb;">RE: REGISTRATION REQUEST</h1>
            <p style="font-size:20px;">Dear <b>{0}</b>,</p>
            <p style="font-size:20px;">
                This is to inform you that your request to use the jamming app have granted<br> 
                click <a href={1}>here</a> to visit the webpage<br><br>
                Thank you for choosing the jamming app
            </p>
            <p style="font-size:20px;">
                Lakunle<br>
                Keep Jamming!!!!!
            </p> 
        """.format(username, url)
        emails.send_html_mail(sender, user_email, "RE:JAMMIMG APP REGISTRATION REQUEST", body, password)
    
        # return a success message
        return jsonify({"msg":"Success"}), 201
    
    #handle all errors
    except Exception as e:
        print(e) 
        abort(500)

# Accept message from my portfolio website
@app.route("/olakunle_email", methods=["POST"])
def recieve_email():
    name = request.form['name']
    email = request.form['email']
    msg = request.form['message']
    
    body = """
            <h1 style="color: #db1ddb;">MESSAGE FROM {0}</h1>
            <p style="font-size:16px;">
                {2}
            </p>
            <p style="font-size:12px;">
                Sender Email: {1}
            </p>
        """.format(name, email, msg)
    
    try:    
        emails.send_html_mail(sender, sender, "MESSAGE FROM MY WEBSITE", body, password)
        return jsonify({"msg": "message sent"})
    except:
        abort(500)

# Handle Page not found errors  
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

#Hnandle missing data errors
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request'}), 400

#Handle Server Errors
@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal Server Error'}), 500

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=DEBUG)