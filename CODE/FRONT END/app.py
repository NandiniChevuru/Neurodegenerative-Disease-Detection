from flask import Flask,render_template,redirect,request,url_for, send_file,session,flash
import mysql.connector, os,joblib
import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.layers import LSTM, Reshape
import cv2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from flask_mail import Mail, Message
import base64
from io import BytesIO
from PIL import Image
import mysql.connector
from tensorflow.keras.applications import MobileNet

from tensorflow.keras.applications.mobilenet import preprocess_input

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key="hii"


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3306",
    database='db'
)

mycursor = mydb.cursor()

def executionquery(query,values):
    mycursor.execute(query,values)
    mydb.commit()
    return

def retrivequery1(query,values):
    mycursor.execute(query,values)
    data = mycursor.fetchall()
    return data

def retrivequery2(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    return data


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']
        phone = request.form['phone']
        
        if password == c_password:
            query = "SELECT UPPER(email) FROM users"
            email_data = retrivequery2(query)
            email_data_list = [i[0] for i in email_data]

            
            if email.upper() not in email_data_list:
                query = "INSERT INTO users (name, email, password, phone) VALUES (%s, %s, %s, %s)"
                values = (name, email, password, phone)
                executionquery(query, values)
                return render_template('login.html', message="Successfully Registered!")
            return render_template('register.html', message="This email ID already exists!")
        
        return render_template('register.html', message="Confirm password does not match!")
    
    return render_template('register.html')



@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        query = "SELECT UPPER(email) FROM users"
        email_data = retrivequery2(query)
        email_data_list = []
        for i in email_data:
            email_data_list.append(i[0])

        if email.upper() in email_data_list:
            query = "SELECT UPPER(password) FROM users WHERE email = %s"
            values = (email,)
            password__data = retrivequery1(query, values)
            if password.upper() == password__data[0][0]:
                global user_email
                # user_email = email
                session['user_name'] =name
                session['user_email'] =email
                return redirect("/home")
            return render_template('login.html', message= "Invalid Password!!")
        return render_template('login.html', message= "This email ID does not exist!")
    return render_template('login.html')


# ####################################################################
@app.route('/adlogin', methods=["GET", "POST"])
def adlogin():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        if email == "admin@gmail.com":
            if password == "admin":
                # return redirect("/admin",)
                return render_template('admin.html', message= "  welcome to  Admin!!")
            return render_template('adlogin.html', message= "Invalid Password for Admin!!")
        return render_template('adlogin.html', message= "This email ID does not exist!")
    return render_template('adlogin.html')



######################################################################
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')



@app.route('/view_data')
def view_data():
    email = session.get('user_email')
    name = session.get('user_name')
    print(11111111, email)
    print(22222222222, name)
    # disease = session.get('result')
    query = "SELECT name, email, disease FROM prediction WHERE email = %s"
    values = (email, ) 
    predictions_data = retrivequery1(query, values)
    print()
    print(predictions_data)
    return render_template('view_data.html', data = predictions_data)








# Set image dimensions for MobileNet
img_height, img_width = 224, 224

# Load the MobileNet model for feature extraction
mobilenet = MobileNet(weights='imagenet', include_top=False, input_shape=(img_height, img_width, 3))

# Load the pre-trained SVM model
svm_classifier = joblib.load("svm_mobilenet_model.pkl")

# Label mapping (adjust as needed based on your model's training)
label_map = {0: "Patient has Alzheimer Disease", 
             1: "Patient is Normal", 
             2: "Patient has Parkinson Disease"}

# Precautions and reasons based on the prediction
precautions_reasons = {
    "Patient has Alzheimer Disease": {
        "Precautions": [
            "Engage in mental stimulation activities like puzzles and reading.",
            "Maintain a healthy diet and exercise regularly.",
            "Regularly consult a healthcare professional for monitoring."
        ],
        "Reasons": [
            "Alzheimer’s disease affects cognitive functions such as memory and thinking.",
            "It is essential to manage the symptoms to improve quality of life.",
            "Early intervention and care can slow the progression of the disease."
        ]
    },
    "Patient is Normal": {
        "Precautions": [
            "Maintain a balanced lifestyle with healthy food and regular exercise.",
            "Engage in cognitive and physical activities to keep your brain and body healthy."
        ],
        "Reasons": [
            "No symptoms of neurodegenerative diseases are detected.",
            "Continued lifestyle habits can help prevent potential health issues."
        ]
    },
    "Patient has Parkinson Disease": {
        "Precautions": [
            "Take prescribed medication regularly to manage symptoms.",
            "Consider physical therapy to improve mobility and balance.",
            "Maintain a healthy diet and stay hydrated."
        ],
        "Reasons": [
            "Parkinson’s disease affects movement and can cause tremors and stiffness.",
            "Managing the disease requires a comprehensive treatment plan."
        ]
    }
}

# Function to preprocess and extract features from the image
def preprocess_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        flash("Error: Image not loaded correctly", "danger")
        return None
    img = cv2.resize(img, (img_width, img_height))  # Resize the image to fit MobileNet input size
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    img = preprocess_input(img)  # Preprocess image for MobileNet
    feature = mobilenet.predict(img)  # Extract features using MobileNet
    feature = feature.flatten()  # Flatten the feature map
    return feature

# Function to predict the class of an image and return precautions and reasons
def predict_image(image_path):
    # Preprocess the uploaded image
    feature = preprocess_image(image_path)
    if feature is None:
        return None, None, None  # Return None if the feature extraction fails
    
    # Make prediction using the trained SVM classifier
    prediction = svm_classifier.predict([feature])
    
    # Map the predicted class label to a human-readable label
    predicted_label = label_map.get(prediction[0], "Unknown Class")
    
    # Fetch the precautions and reasons based on the predicted label
    if predicted_label != "Unknown Class":
        precautions = precautions_reasons.get(predicted_label, {}).get("Precautions", [])
        reasons = precautions_reasons.get(predicted_label, {}).get("Reasons", [])
    else:
        precautions = reasons = []
    name = session['user_name']  # Get the name from session
    email = session['user_email']
    session['result'] = predicted_label
    print(name)
    print(email)
    query = "INSERT INTO prediction (name, email, disease) VALUES (%s, %s, %s)"
    values = (name, email, predicted_label)
    executionquery(query, values)

    return predicted_label, precautions, reasons

# Function to check allowed file extensions (add more as necessary)
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure the Upload_images directory exists
UPLOAD_FOLDER = 'static/Upload_images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Route to handle file upload and prediction
@app.route("/upload", methods=["POST", "GET"])
def upload():
    if request.method == 'POST':
        # Check if 'file' is in the request
        if 'file' not in request.files:
            flash("No file part", "danger")
            return render_template('upload.html')

        myfile = request.files['file']

        # Validate file name and extension
        if myfile.filename == '' or not allowed_file(myfile.filename):
            flash("Only image formats are accepted", "danger")
            return render_template('upload.html')

        # Save the file securely
        fn = secure_filename(myfile.filename)
        mypath = os.path.join(UPLOAD_FOLDER, fn)
        myfile.save(mypath)

        # Predict using the model
        predicted_label_text, precautions, reasons = predict_image(mypath)

        # Check if prediction was made
        if predicted_label_text is None:
            flash("Prediction failed. Please try again.", "danger")
            return render_template("upload.html", mypath=mypath, fn=fn)

        # Render the upload page with the prediction, precautions, reasons, and image path
        return render_template("upload.html", mypath=mypath, prediction=predicted_label_text, precautions=precautions, reasons=reasons, fn=fn)

    # Render the form for GET request
    return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug = True)