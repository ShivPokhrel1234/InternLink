# from flask import Flask, render_template, request, abort, redirect, url_for
# import mysql.connector

# # Connect to MySQL
# connection = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="Sagarmatha1$",
#     database="internlink"
# )

# app = Flask(__name__)

# @app.route("/", methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         user_name = request.form['username']
#         pwd = request.form['password']

#         cursor = connection.cursor()
#         cursor.execute("SELECT username, password_hash FROM users WHERE username = %s", (user_name,))
#         result = cursor.fetchone()

#         if result and 1 == 1:
#             return redirect(url_for('welcome'))
#         else:
#             return "Invalid credentials", 401

#     return render_template('login.html')

# @app.route("/welcome")
# def welcome():
#     return render_template('welcome.html')

# if __name__ == '__main__':
#     app.run(debug=True)



from flask import Flask, render_template, request, abort, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
import bcrypt
from flask import flash
from flask import session
import myModule


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Sagarmatha1$",
            database="internlink1"
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
    
@app.route("/")
def home():
    return render_template('home.html')




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Extract and validate form data
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get("role")
        university = request.form.get("university")
        course = request.form.get("course")
        resume_path = request.form.get("resume_path")
        full_name = request.form.get("full_name")
        email = request.form.get("email")  
        profile_image = request.form.get("profile_image")
        status = request.form.get("status", "Y")  # Default to 'Y' if not provided

        

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Save to database
        print(f"Registering user: {username} with role: {role} and hashed password: {hashed_password}")
        connection = get_db_connection()
        if not connection:
            return "Database connection error", 500
        
        cursor = connection.cursor()
        print( cursor.execute("INSERT INTO users (username,full_name,email, password_hash,profile_image, role,status) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                    (username,full_name,email, hashed_password,profile_image, role,status)))
        connection.commit() 
        cursor = connection.cursor()
        cursor.execute(
                "SELECT MAX(user_id) as UserId FROM users "
            )
        result = cursor.fetchone()
        user_id= result[0]
        cursor.execute("INSERT INTO student (user_id, university, course,resume_path) VALUES (%s, %s, %s, %s)", 
                    (user_id, university, course, resume_path))
        connection.commit() 


        connection.close() 
        
        flash("Registration successful! Please log in.", "success")
 
    return render_template("home.html")



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')

        if not username or not password_input:
            return "Username and password are required", 400

        connection = get_db_connection()
        if not connection:
            return "Database connection error", 500

        result = None
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT username, password_hash, role, s.student_id FROM users u LEFT JOIN student s ON s.user_id=u.user_id WHERE username = %s", 
                (username,)
            )
            result = cursor.fetchone()

            if result:
                stored_hash = result[1].encode('utf-8')
                if bcrypt.checkpw(password_input.encode('utf-8'), stored_hash):
                    session['username'] = username
                    session['role'] = result[2]
                    session['student_id'] = result[3]
                    return redirect(url_for('welcome'))

            return "Invalid credentials", 401

        except Error as e:
            print(f"Database error: {e}")
            return "Database error", 500
        finally:
            if connection.is_connected():
                connection.close()


    return render_template('login.html')


@app.route("/student/<int:student_id>/<int:internship_id>")
def apply_to_internship(student_id, internship_id):
    # Optional: verify user session matches student_id
    if 'student_id' not in session or session['student_id'] != student_id:
        return "Unauthorized", 403

    connection = get_db_connection()
    cursor = connection.cursor()

    # You might have a table like 'applications' to store this
    cursor.execute(
        "INSERT INTO applications (student_id, internship_id) VALUES (%s, %s)",
        (student_id, internship_id)
    )
    connection.commit()
    connection.close()

    flash("Application submitted successfully!", "success")
    return redirect(url_for("student"))

@app.route("/student/<int:student_id>/profile", methods=["GET"])
def view_profile(student_id):
    if 'student_id' not in session or session['student_id'] != student_id:
        return "Unauthorized", 403

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT  university, course FROM student WHERE student_id = %s", (student_id,))
    profile = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template("profile.html", profile=profile)
@app.route("/student/<int:student_id>/profile", methods=["POST"])
def edit_profile(student_id):
    if 'student_id' not in session or session['student_id'] != student_id:
        return "Unauthorized", 403
    
    university = request.form["university"]
    course = request.form["course"]

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE student
        SET  university = %s, course = %s 
        WHERE student_id = %s
    """, ( university, course, student_id))
    connection.commit()
    cursor.close()
    connection.close()
    flash("Profile updated successfully!", "success")
    return redirect(url_for("view_profile", student_id=student_id))
    
@app.route("/student/<int:student_id>")
def view_my_internship(student_id):
    # Optional: verify user session matches student_id
    if 'student_id' not in session or session['student_id'] != student_id:
        return "Unauthorized", 403

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)  # For field-based access in Jinja

    # Make sure to pass the student_id as a tuple
    cursor.execute(
        "SELECT * FROM applications WHERE student_id = %s", 
        (student_id,)
    )
    
    result = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('student.html', applications=result)

  

@app.route("/student", methods=['GET', 'POST'])
def student():
    
        connection = get_db_connection()
        if not connection:
            return "Database connection error", 500

        result = None
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM internships", 
                
            )
            result = cursor.fetchall()


        except Error as e:
            print(f"Database error: {e}")
            return "Database error", 500
        finally:
            if connection.is_connected():
                connection.close()


        return render_template('student.html', internships=result)


@app.route("/welcome")
def welcome():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('welcome.html', username=session['username'], user_type=session['role'])

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
