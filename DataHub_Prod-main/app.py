import os
from flask import Flask, render_template, request, redirect, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)

#db_config host, username, password and all have been removed by us. 
db_config = {
    'host': '',
    'user': '',
    'password': '',
    'database': '',
    'port': 
}

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
except mysql.connector.Error as err:
    print(f"Error: {err}")

def get_db_connection():
    return mysql.connector.connect(**db_config)

def get_connection():
    return mysql.connector.connect(**db_config)

def get_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()

    # Get all course details for each department
    for dept in departments:
        cursor.execute("SELECT CourseNo, Title, Year, Did FROM courses WHERE Did = %s", (dept['Did'],))
        dept['courses'] = cursor.fetchall()

    cursor.close()
    conn.close()
    return departments

def validate_department_data(data):
    required_fields = ["Did", "Dname", "ContactNo", "HOD", "Cid"]
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing or invalid required field: {field}"
    return True, ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route("/student_get")
def student_get():
    return render_template('student.html')  # Frontend for students

@app.route("/add-student")
def student_add():
    return render_template("add-student.html")

@app.route('/course_details')
def course_details():
    departments = get_data()
    return render_template('course_details.html', departments=departments)

@app.route('/college')
def college():
    return render_template('college.html')

@app.route("/department")
def department():
    return render_template("department-details.html")

@app.route('/faculty-details')
def faculty_details():
    return render_template('faculty-details.html')



@app.route('/update-courses')
def update_courses():
    return render_template('update_courses.html')

@app.route('/add-course', methods=['POST'])
def add_course():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (CourseNo, Title, Year, Did) VALUES (%s, %s, %s, %s)", (
        request.form['CourseNo'],
        request.form['Title'],
        request.form['Year'],
        request.form['Did']
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/update-courses')

@app.route('/edit-course', methods=['POST'])
def edit_course():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE courses
        SET Title = %s, Year = %s, Did = %s
        WHERE CourseNo = %s
    """, (
        request.form['Title'],
        request.form['Year'],
        request.form['Did'],
        request.form['CourseNo']
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/update-courses')

@app.route('/delete-course', methods=['POST'])
def delete_course():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE CourseNo = %s", (request.form['CourseNo'],))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/update-courses')


@app.route('/all', methods=['GET'])
def get_all_colleges():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT c.Cid AS college_id, c.Name AS name, c.Address AS address, cc.ContactNo AS contact
        FROM colleges c
        LEFT JOIN collegecontact cc ON c.Cid = cc.Cid
    """
    cursor.execute(query)
    colleges = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(colleges)

# Route to search for a college by ID, name, or contact
@app.route('/search', methods=['POST'])
def search_college():
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT c.Cid AS college_id, c.Name AS name, c.Address AS address, cc.ContactNo AS contact
        FROM colleges c
        LEFT JOIN collegecontact cc ON c.Cid = cc.Cid
        WHERE c.Cid = %s OR c.Name = %s OR cc.ContactNo = %s
        LIMIT 1
    """
    cursor.execute(query, (keyword, keyword, keyword))
    college = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(college if college else {})

# Route to add or update a college
@app.route('/add_or_update', methods=['POST'])
def add_or_update_college():
    data = request.get_json()
    college_id = data.get('id')
    name = data.get('name')
    address = data.get('address')
    contact = data.get('contact')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the college exists
    cursor.execute("SELECT COUNT(*) FROM colleges WHERE Cid = %s", (college_id,))
    exists = cursor.fetchone()[0]

    if exists:
        # Update existing college
        cursor.execute("UPDATE colleges SET Name = %s, Address = %s WHERE Cid = %s", (name, address, college_id))
        cursor.execute("DELETE FROM collegecontact WHERE Cid = %s", (college_id,))
        cursor.execute("INSERT INTO collegecontact (Cid, ContactNo) VALUES (%s, %s)", (college_id, contact))
    else:
        # Insert new college
        cursor.execute("INSERT INTO colleges (Cid, Name, Address) VALUES (%s, %s, %s)", (college_id, name, address))
        cursor.execute("INSERT INTO collegecontact (Cid, ContactNo) VALUES (%s, %s)", (college_id, contact))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Success'})

# Route to delete a college
@app.route('/delete', methods=['POST'])
def delete_college():
    data = request.get_json()
    college_id = data.get('id')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM collegecontact WHERE Cid = %s", (college_id,))
    cursor.execute("DELETE FROM colleges WHERE Cid = %s", (college_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Deleted'})

@app.route("/departments", methods=["GET"])
def get_departments():
    try:
        cursor.execute("SELECT * FROM departments")
        result = cursor.fetchall()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Route to add a new department
@app.route("/departments", methods=["POST"])
def add_department():
    try:
        data = request.get_json()
        
        # Validate data
        is_valid, error_msg = validate_department_data(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400  # Bad Request
        
        query = """
        INSERT INTO departments (Did, Dname, ContactNo, HOD, Cid)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["Did"],
            data["Dname"],
            data["ContactNo"],
            data["HOD"],
            data["Cid"]
        ))
        conn.commit()
        return jsonify({"message": "Department added", "id": cursor.lastrowid}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Route to update an existing department by Did
@app.route("/departments/<Did>", methods=["PUT"])
def update_department(Did):
    try:
        data = request.get_json()
        
        # Validate data
        is_valid, error_msg = validate_department_data(data)
        if not is_valid:
            return jsonify({"error": error_msg}), 400  # Bad Request
        
        query = """
        UPDATE departments 
        SET Dname = %s, ContactNo = %s, HOD = %s, Cid = %s 
        WHERE Did = %s
        """
        cursor.execute(query, (data["Dname"], data["ContactNo"], data["HOD"], data["Cid"], Did))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Department not found"}), 404  # Not Found
        return jsonify({"message": "Department updated"})
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# Route to delete a department by Did
@app.route("/departments/<Did>", methods=["DELETE"])
def delete_department(Did):
    try:
        cursor.execute("DELETE FROM departments WHERE Did = %s", (Did,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Department not found"}), 404  # Not Found
        
        return jsonify({"message": "Department deleted"})
    except mysql.connector.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/faculties', methods=['GET'])
def get_faculties():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM faculties')
    faculties = cursor.fetchall()
    conn.close()
    return jsonify(faculties)

# Fetch a faculty by ID
@app.route('/faculties/<fid>', methods=['GET'])
def get_faculty(fid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM faculties WHERE Fid = %s', (fid,))
    faculty = cursor.fetchone()
    conn.close()
    if faculty:
        return jsonify(faculty)
    else:
        return jsonify({"error": "Faculty not found"}), 404

# Add a new faculty
@app.route('/faculties', methods=['POST'])
def add_faculty():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO faculties (Fid, Did, Name, Designation, Qualification, Address, ContactNo, Cid)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (data['Fid'], data['Did'], data['Name'], data['Designation'], data['Qualification'], data['Address'], data['ContactNo'], data['Cid']))

    conn.commit()
    conn.close()
    return jsonify({"message": "Faculty added successfully"}), 201

# Update a faculty's details
@app.route('/faculties/<fid>', methods=['PUT'])
def update_faculty(fid):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE faculties
        SET Did = %s, Name = %s, Designation = %s, Qualification = %s, Address = %s, ContactNo = %s, Cid = %s
        WHERE Fid = %s
    ''', (data['Did'], data['Name'], data['Designation'], data['Qualification'], data['Address'], data['ContactNo'], data['Cid'], fid))

    conn.commit()
    conn.close()
    return jsonify({"message": "Faculty updated successfully"})

# Delete a faculty by ID
@app.route('/faculties/<fid>', methods=['DELETE'])
def delete_faculty(fid):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM faculties WHERE Fid = %s', (fid,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Faculty deleted successfully"})

@app.route("/students", methods=["GET"])
def get_students():
    """Fetch all students from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(students)
    except Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500

@app.route("/students/<Sid>", methods=["GET"])
def get_student(Sid):
    """Fetch a single student by Sid."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE Sid = %s", (Sid,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()
        if student:
            return jsonify(student)
        return jsonify({"message": "Student not found."}), 404
    except Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500

@app.route("/students", methods=["POST"])
def add_student():
    """Add a new student to the database."""
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (Sid, Name, Year, ContactNo, Address, CourseNo)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data["Sid"], data["Name"], int(data["Year"]),
            data["ContactNo"], data["Address"], data["CourseNo"]
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Student added successfully."}), 201
    except Error as err:
        return jsonify({"message": f"Error while adding student: {err}"}), 500

@app.route("/students/<Sid>", methods=["PUT"])
def update_student(Sid):
    """Update an existing student in the database."""
    data = request.get_json()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE students
            SET Name=%s, Year=%s, ContactNo=%s, Address=%s, CourseNo=%s
            WHERE Sid=%s
        """, (
            data["Name"], data["Year"], data["ContactNo"],
            data["Address"], data["CourseNo"], Sid
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Student updated successfully."})
    except Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500

@app.route("/students/<Sid>", methods=["DELETE"])
def delete_student(Sid):
    """Delete a student from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE Sid = %s", (Sid,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Student deleted successfully."})
    except Error as err:
        return jsonify({"error": f"Database error: {err}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv("PORT", 5000), debug=True)

