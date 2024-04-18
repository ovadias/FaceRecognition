from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
import os
import csv
from werkzeug.utils import secure_filename
from attendance import take_attendance
import cv2

app = Flask(__name__, static_url_path='/static')

DATA_FOLDER = os.path.join(app.root_path, 'data')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['DATA_FOLDER'] = DATA_FOLDER

os.makedirs(DATA_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_csv(file_path):
    data = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            data.append(row)
    return data

def write_csv(file_path, data, fieldnames):
    with open(file_path, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def get_courses():
    courses = []
    for course_folder in os.listdir(DATA_FOLDER):
        course_path = os.path.join(DATA_FOLDER, course_folder)
        if os.path.isdir(course_path):
            course = {
                'id': course_folder,
                'title': course_folder
            }
            courses.append(course)
    return courses

def get_course(course_id):
    course_path = os.path.join(DATA_FOLDER, course_id)
    if os.path.isdir(course_path):
        return {'id': course_id, 'title': course_id}
    return None

def add_course(course_title, class_list_file):
    course_id = course_title.replace(' ', '_')
    course_path = os.path.join(DATA_FOLDER, course_id)
    os.makedirs(course_path, exist_ok=True)

    class_list_file_path = os.path.join(course_path, 'class_list.csv')
    class_list_file.save(class_list_file_path)

    return course_id

def get_course_students(course_id):
    class_list_file_path = os.path.join(DATA_FOLDER, course_id, 'class_list.csv')
    if not os.path.exists(class_list_file_path):
        return []
    return read_csv(class_list_file_path)

def save_attendance(course_id, selected_date, attendance_data):
    attendance_folder = os.path.join(DATA_FOLDER, course_id, selected_date)
    os.makedirs(attendance_folder, exist_ok=True)

    attendance_file_path = os.path.join(attendance_folder, 'attendance.csv')
    fieldnames = ['name', 'present']
    write_csv(attendance_file_path, attendance_data, fieldnames)

@app.route('/')
def home():
    courses = get_courses()
    return render_template('home.html', courses=courses)

@app.route('/add_course', methods=['POST'])
def add_course_route():
    course_title = request.form['courseTitle']
    class_list_file = request.files['classListFile']
    course_id = add_course(course_title, class_list_file)
    return jsonify({'message': 'Course added successfully', 'course_id': course_id})

@app.route('/course/<course_id>')
def course_page(course_id):
    course = get_course(course_id)
    students = get_course_students(course_id)
    return render_template('course.html', course=course, students=students)

@app.route('/course/<course_id>/take_attendance', methods=['GET', 'POST'])
def take_attendance_page(course_id):
    course = get_course(course_id)
    if request.method == 'POST':
        selected_date = request.form.get('attendanceDate')
        if selected_date:
            return render_template('take_attendance.html', course=course, selected_date=selected_date)
        else:
            return "Please provide a valid date.", 400
    return render_template('take_attendance.html', course=course)

@app.route('/upload', methods=['POST'])
def upload_image():
    file = request.files.get('file')
    course_id = request.form['course_id']
    selected_date = request.form['selected_date']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(DATA_FOLDER, course_id, selected_date)
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        file_url = url_for('uploaded_file', course_id=course_id, selected_date=selected_date, filename=filename)
        return jsonify({'file_url': file_url})
    return jsonify({'error': 'Invalid file format'})

@app.route('/take_attendance', methods=['POST'])
def take_attendance_route():
    file = request.files['file']
    course_id = request.form['course_id']
    selected_date = request.form['selected_date']
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(DATA_FOLDER, course_id, selected_date)
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        embeddings_path = os.path.join(DATA_FOLDER, 'known_faces_50px.pickle')
        class_list_csv = os.path.join(DATA_FOLDER, course_id, 'class_list.csv')
        output_directory = upload_folder

        # Check if the embeddings file exists
        embeddings_path = os.path.join(DATA_FOLDER, 'known_faces_50px.pickle')
        if not os.path.isfile(embeddings_path):
            print(f"Embeddings file not found: {embeddings_path}")
        else:
            print(f"Embeddings file exists: {embeddings_path}")
                
        try:
            processed_image_path, attendance_csv_path = take_attendance(file_path, embeddings_path, class_list_csv, output_directory)
            
            # Read the processed image
            processed_image = cv2.imread(processed_image_path)
            
            # Save the annotated image
            annotated_image_filename = 'annotated_' + filename
            annotated_image_path = os.path.join(upload_folder, annotated_image_filename)
            cv2.imwrite(annotated_image_path, processed_image)
            
            attendance_csv_filename = os.path.basename(attendance_csv_path)
            
            annotated_image_url = url_for('uploaded_file', course_id=course_id, selected_date=selected_date, filename=annotated_image_filename)
            attendance_csv_url = url_for('uploaded_file', course_id=course_id, selected_date=selected_date, filename=attendance_csv_filename)
            
            return jsonify({
                'annotated_image_url': annotated_image_url,
                'attendance_csv_url': attendance_csv_url
            })
        
        except Exception as e:
            print(str(e))  # Print the error message for debugging
            return jsonify({'error': 'An error occurred during attendance processing'})
    
    else:
        return jsonify({'error': 'Invalid file format'})
    
@app.route('/save_attendance', methods=['POST'])
def save_attendance_route():
    course_id = request.form['course_id']
    selected_date = request.form['selected_date']
    csv_data = request.form['csv_data']
    attendance_data = [row.split(',') for row in csv_data.strip().split('\n')]
    save_attendance(course_id, selected_date, attendance_data)
    return jsonify({'message': 'Attendance saved successfully'})

@app.route('/data/<path:course_id>/<path:selected_date>/<path:filename>')
def uploaded_file(course_id, selected_date, filename):
    file_path = os.path.join(DATA_FOLDER, course_id, selected_date, filename)
    return send_from_directory(os.path.dirname(file_path), filename)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)