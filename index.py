from flask import Flask, request, flash, jsonify, send_from_directory, make_response, send_file
import sqlite3
import json
import os
import datetime
from werkzeug.utils import secure_filename
import jwt
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import shutil

app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
BASE_URL = 'http://192.168.43.227:5000'
app.config['SECRET_KEY'] = 'madman'
cors = CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

conn = sqlite3.connect('./ec.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS authentication (id INTEGER PRIMARY KEY, username TEXT, password TEXT, rank TEXT)''')
conn.commit()
c.execute('''CREATE TABLE IF NOT EXISTS thistory (id INTEGER PRIMARY KEY, username TEXT, transactions TEXT)''')
conn.commit()
conn.close()

@app.route('/changerank', methods=["POST"])
def changerank():
    try:
        userid = request.form.get('userid')
        rankchange = request.form.get('rankchange')
        if not userid or not rankchange:
            return jsonify({"message": "User ID or rank change value missing", "status": 400})

        conn = sqlite3.connect('./ec.db')
        c = conn.cursor()
        c.execute('UPDATE authentication SET rank = ? WHERE username = ?', (rankchange, userid))
        conn.commit()
        conn.close()
        return jsonify({"message": "Rank changed successfully", "status": 200})

    except sqlite3.Error as e:
        return jsonify({"message": "Database error: " + str(e), "status": 500})
    
    except Exception as e:
        return jsonify({"message": "An error occurred: " + str(e), "status": 500})

@app.route('/changebalance', methods=["POST"])
def changebalance():
    try:
        userid = request.form.get('userid')
        balance = request.form.get('balance')
        if not userid or not balance:
            return jsonify({"message": "User ID or balance value missing", "status": 400})

        conn = sqlite3.connect('./ec.db')
        c = conn.cursor()
        c.execute('UPDATE users SET balance = ? WHERE username = ?', (balance, userid))
        conn.commit()
        conn.close()
        return jsonify({"message": "Balance changed successfully", "status": 200})

    except sqlite3.Error as e:
        return jsonify({"message": "Database error: " + str(e), "status": 500})
    
    except Exception as e:
        return jsonify({"message": "An error occurred: " + str(e), "status": 500})


@app.route('/getthistory/', methods=['GET', 'POST'])
def getthistory():
    try:
        password = request.form.get('password')
        if password == 'abcinvest123':
            conn = sqlite3.connect('./ec.db')
            c = conn.cursor()
            c.execute('SELECT * FROM thistory')
            cs = c.fetchall()
            cdict = []
            if cs is not None:
                for s in cs:
                    cs_list = {
                        "id": s[0],
                        "username": s[1],
                        "transaction": s[2],
                        "plan": s[3]
                    }
                    cdict.append(cs_list)
                conn.close()
                return jsonify({"dict": cdict, "status": 200})
            else:
                conn.close()
                return jsonify({"message": "No transaction history found", "status": 404})
        else:
            return jsonify({"message": "Unauthorized access", "status": 509})
    except Exception as e:
        return jsonify({"message": str(e), "status": 500})


@app.route('/downloaditems/<password>', methods=['GET', 'POST'])
def downloaditems(password):
    try:
        # Specify the path to the 'items' folder
        items_folder_path = './uploads'
        if password == 'Godwithus22':
        
        # Create a temporary zip file
            zip_file_path = '/tmp/items.zip'
            shutil.make_archive(zip_file_path[:-4], 'zip', items_folder_path)

            # Set up the response headers
            headers = {
                'Content-Disposition': 'attachment; filename=items.zip',
                'Content-Type': 'application/zip',
            }

            # Send the zip file as a response
            response = send_file(zip_file_path, as_attachment=True)
            return response
        else:
            return jsonify({'Message': 'Wrong Password'})
    except Exception as e:
        return jsonify({'message': 'Error while downloading the items folder', 'status': 500, 'Exception': str(e)})


@app.route('/uploads/<path:filename>')
def serve_video(filename):
    video_path = 'uploads'  # Replace with the actual path to your video files directory
    full_path = os.path.join(video_path, filename)

    # Check if the file exists
    if not os.path.isfile(full_path):
        return "Video not found", 404

    # Determine the content type based on the file extension
    if filename.endswith('.mp4'):
        content_type = 'video/mp4'
    else:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        return send_from_directory(os.path.join(root_dir, 'uploads'), filename)

    # Set the Content-Disposition header to display the file inline
    response = make_response(send_from_directory(video_path, filename, mimetype=content_type))
    response.headers['Content-Disposition'] = f'inline; filename="{filename}"'

    return response

@app.route('/paymentvalidation', methods=["POST", "GET"])
def paymentvalidation():
    try:
        screenshot = request.files.get('screenshot')
        username = request.form.get('username')
        plan = request.form.get('plan')
        
        if screenshot is not None:
            filename = secure_filename(screenshot.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)  # Construct the file path
            
            # Create the upload folder if it doesn't exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            screenshot.save(filepath)  # Save the uploaded file to the specified path
            
            # Construct the URL to the saved file
            file_url = os.path.join(BASE_URL, filename).replace(os.path.sep, '/')
            
            conn = sqlite3.connect('./ec.db')
            c = conn.cursor()
            c.execute('INSERT INTO thistory (username, transactions, plan) VALUES (?, ?, ?)', (username, file_url, plan))
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Transaction Completed', 'status': 200})
        else:
            return jsonify({'status': 400, 'message': 'No screenshot provided'})

    except Exception as e:
        return jsonify({'status': 509, 'message': str(e)})


@app.route('/signup', methods=['POST'])
def signup():
    print('here')
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            conn = sqlite3.connect('./ec.db')
            c = conn.cursor()
            c.execute('SELECT * FROM authentication WHERE username = ?', (username,))
            cs = c.fetchone()
            rank = 'FREE'
            conn.close()
            if cs is not None:
                return jsonify({'message': 'User already exists', 'status': 409})
            else:
                print(password)
                conn = sqlite3.connect('./ec.db')
                c = conn.cursor()
                c.execute('INSERT INTO authentication (username, password, rank, balance) VALUES (?, ?, ?, ?)', (username, password, rank, 0))
                conn.commit()
                conn.close()
                balance = '0'
                payload = {
                        'username': username,
                        'password': password,
                        "rank": rank,
                        "balance": balance
                }
                jwt_token = jwt.encode(payload, app.secret_key, algorithm='HS256')
                

                return jsonify({'message': 'Signup Successful', 'status': 200, 'token': jwt_token})
        except Exception as e:
            return jsonify({'message': 'Error. Db may be busy', 'exception': str(e)})

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')

            if username is not None:
                conn = sqlite3.connect('./ec.db')
                c = conn.cursor()
                c.execute('SELECT * FROM authentication WHERE username = ? AND password = ?', (username, password))
                cs = c.fetchone()

                if cs is not None:
                    rank = cs[3]
                    balance = cs[4]
                    payload = {
                        'username': username,
                        'password': password,
                        "rank": rank,
                        "balance": balance
                    }
                    jwt_token = jwt.encode(payload, app.secret_key, algorithm='HS256')
                    return jsonify({'message': 'Login Successful', 'status': 200, 'token': jwt_token})
                else:
                    return jsonify({'message': 'Incorrect username or password', 'status': 404})
            else:
                return jsonify({'message': 'Not a valid username', 'status': 400})

        except sqlite3.Error as e:
            return jsonify({'message': 'Database error. Please try again later.', 'status': 500})
        except Exception as e:
            return jsonify({'message': 'An error occurred. Please try again later.', 'status': 500})
    else:
        return jsonify({'message': 'Method not allowed', 'status': 405})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, use_reloader=True)
