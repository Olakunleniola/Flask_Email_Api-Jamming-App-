from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import emails
import json
import os

# Create a Flask application
app = Flask(__name__)

# Get Environment variable information
sender = os.environ.get("EMAIL_SENDER", "")
password = os.environ.get("SMTP_PASSWORD", "")
url = os.environ.get("SITE_URL", "http://example.com")
ALLOWED_HOST = os.environ.get('HOSTS', "localhost, 127.0.0.1").split(",")

CORS(app, origins=ALLOWED_HOST)

# create user and notify developer endpoint 
@app.route('/spotify/mail', methods=['POST'])
def send_mail():
    # extract the data fr the request body
    data = request.json
    if data is None or 'name' not in data or 'email' not in data:
        abort(400) # return if request body is empty or does not contain required data
    # Get username and email from the data
    user_email = data['email']
    user_name = data['name']
    # Email Message body that will be sent to the user
    user_body = """
        <h1>REGISTRATION REQUEST</h1>
        <p>Dear <strong>{0}</strong>,</p>
        <p>
            Thank you for choosing the Jamming App.<br>
            Your registration request has been submitted successfully.<br>
            <br>You will be notified when your request has been granted.    
        </p>
        <p>Keep Jamming!!!<br>Lakunle-CEO</p>
    """.format(user_name)
    
    # Email Message body that will be sent to the developer 
    client_body = """
        <h1>Register User</h1>
        <p><b>Name:</b> {0}</p>
        <p><b>Email:</b> {1}</p>

        <form action="{2}/spotify/register?username={0}&email={1}" method="POST">
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
    
    try:
        # SENd the eamil to the user and developer 
        emails.send_html_mail(sender, sender,"REQUEST TO REGISTER USER TO SPOTIFY", client_body, password)
        emails.send_html_mail(sender, user_email,"JAMMING APP REGISTRATION", user_body, password)
        
        # Register add new user to the data base
        with open ('users.json', "r") as users_json:
            user_data = json.load(users_json)
            new_user = {'name':user_name, 'email':user_email, 'registered': False, 'pending': True}
            user_data.append(new_user)
        with open ('users.json', "w") as users_json:
            json.dump(user_data, users_json)
        # Return the new user if successful
        return jsonify(new_user), 201  
    # Handle Database Error
    except FileExistsError:
        abort(500)
    # Handle all  Errors
    except Exception as e:
        print(e)
        abort(500)
        

# get user endpoint
@app.route('/spotify/user/<name>', methods=["GET"])
def get_user(name):
    try:
        # Get user in the data base  
        with open('users.json', "r") as json_file:
            data = json.load(json_file)
            user = [user for user in data if user['name'].lower() == name.lower()]
            # user = next((user for user in data if user['name'].lower() == name.lower()), None) # Alternative
            #if user exist return user
            if user:
                return jsonify(user[0]), 200
            # else return error message
            else:
                return jsonify({"error":"user does not exist"}), 401
    #Hnadle error            
    except:
        abort(500)
    

# register user endpoint 
@app.route('/spotify/register', methods=['POST'])
def alter_user():
    username = str(request.args.get('username'))
    user_email = str(request.args.get('email'))
    try:
        # cjheck the user in the database
        with open('users.json', "r") as user_json:
            users = json.load(user_json)
            user = next((user for user in users if user['name'].lower() == username.lower()), None)
            # if user exist, Alter the registered and pending status of user and also send email to the user
            if user:
                user_index = users.index(user)
                users[user_index]["registered"] = True
                users[user_index]["pending"] = False
                #update the database
                with open('users.json', "w") as users_js:
                    json.dump(users, users_js)
                    
                # send an email to the user and notify changes made 
                body = """
                    <h1>RE: REGISTRATION REQUEST</h1>
                    <p>Dear <b>{0}</b>,</p>
                    <p>
                        This is to inform you that your request to use the jamming app have granted<br> 
                        click <a href={1}>here</a> to visit the webpage<br><br>
                        Thank you for choosing the jamming app
                    </p>
                    <p>
                        Lakunle<br>
                        Keep Jamming!!!!!
                    </p> 
                """.format(username, url)
                emails.send_html_mail(sender, user_email, "RE:JAMMIMG APP REGISTRATION REQUEST", body, password)
            # else user not exist return error message 
            else:
                return jsonify({"error": "user nor found"}), 404 
        #return success if successful
        return jsonify({"msg":"Success"}), 201
    #Handle database errors
    except FileExistsError:
        abort(500)
    #handle all errors
    except Exception as e:
        print(e)
        abort(404)
        

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
    app.run()