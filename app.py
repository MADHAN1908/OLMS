from flask import Flask,render_template,send_file,request, redirect, url_for,session,g
import subprocess
import base64,os
from io import BytesIO
from datetime import datetime, timedelta
import matplotlib
import matplotlib.pyplot as plt
import sqlite3

app=Flask(__name__)
matplotlib.use('agg')
DATABASE = 'StudySync.db1'  
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def getlog(l_id):
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from user_log where log_id = ? ',(l_id,))
    log=cur.fetchone()
    print(log)
    # cur.close()
    return log

def get_next_module_no(course_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT MAX(module_no) FROM course_module WHERE course_id = ?;
    ''', (course_id,))
    max_module_no = cursor.fetchone()[0]
    return (max_module_no + 1) if max_module_no is not None else 1

def get_next_question_no(course_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT MAX(question_no) FROM quiz WHERE course_id = ?;', (course_id,))
    max_question_no = cursor.fetchone()[0]
    return (max_question_no + 1) if max_question_no is not None else 1

def get_next_module_question_no(course_id,module_no):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT MAX(question_no) FROM module_quiz WHERE course_id = ? and module_no= ?;', (course_id,module_no))
    max_question_no = cursor.fetchone()[0]
    return (max_question_no + 1) if max_question_no is not None else 1

app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/UPLOAD_FOLDER/'

@app.route('/cmc')
def cmc():
    try:
        db= get_db()
        cur = db.cursor()
        cur.execute("SELECT 1")
        # cur.close()
        return "sqlite3 connection is established."
    except Exception as e:
        return f"Error connecting to Sqlite3: {e}"

@app.route('/')
def home():
    confirm=request.args.get('confirm')
    return render_template('home.html',confirm=confirm)
@app.route('/user_message' ,methods=['POST'])
def user_message():
    name=request.form['name']
    email=request.form['email']
    message=request.form['message']
    r_mail="Admin"
    subject="Mail from Home Page"
    dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db= get_db()
    cur = db.cursor()
    cur.execute('select student_id from student where email_id = ? and student_name = ?',(email,name))
    student=cur.fetchone()
    cur.execute('select * from instructor where email_id = ? and instructor_name = ?',(email,name))
    instructor=cur.fetchone()
    if student or instructor:
        cur.execute('insert into message (sender_email,receiver_email,subject,body,date_time) values(?,?,?,?,?)',(email,r_mail,subject,message,dt))
        db.commit()
        confirm="Message Send Successfully"
        # cur.close()
    else:
         confirm="Invalid UserName or Email ID , Please use the registered UserName and Email ID . "   
    return redirect(url_for('home', _anchor='contact',confirm=confirm))
@app.route('/studentlogin')
def  studentlogin():
    return render_template('studentlogin.html')

@app.route('/adminlogin')
def  admin():
    return render_template('adminlogin.html')

@app.route('/studentdashboard',methods=['POST'])
def  studentdashboard():
    email=request.form.get('email')
    password=request.form.get('password')
    db= get_db()
    cur = db.cursor()
    cur.execute('select student_id,student_name from student where email_id = ? and password = ?',(email,password))
    student=cur.fetchone()
    date =datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if student :
        cur.execute('INSERT INTO student_log (student_id,student_name,login_date) VALUES (?,?,?)', (student[0],student[1],date))
        db.commit()
        cur.execute('select * from student_log where student_id = ? order by login_date DESC ',(student[0],))
        log_id=cur.fetchone()[0]
        print(log_id)
        # session['log_id']=log_id
        # session['student_id']=student[0]
        # session['user_type']="student"
        return redirect(url_for('sd_profile',l_id=log_id,s_id=student[0]))
    else :
         cur.execute('select * from instructor where email_id = ? and password = ?',(email,password))
         instructor=cur.fetchone()
         if instructor :
            if instructor[4]=="Deactivated":
                error = 'Access is Deactivated.'
                return render_template('studentlogin.html', error=error)
            else :
                u_id=instructor[0]
                u_type="Instructor"
                u_name=instructor[1]
                cur.execute('INSERT INTO user_log (user_type,user_id,user_name,login_date) VALUES (?,?,?,?)', (u_type,u_id,u_name,date))
                db.commit()
                cur.execute('select * from user_log where user_id = ? order by login_date DESC ',(instructor[0],))
                log_id=cur.fetchone()[0]
                # cur.close()
                return redirect(url_for('id',l_id=log_id,u_id=u_id,u_type=u_type,u_name=u_name))
         
         else :
            # cur.close()
            error = 'Invalid username or password. Please try again.'
            return render_template('studentlogin.html', error=error)




@app.route('/logout')
def  logout():
    l_id=request.args.get('l_id')
    s_id=request.args.get('s_id')
    print(l_id,s_id)
    db= get_db()
    cur = db.cursor()
    date =datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if  s_id :
        cur.execute('UPDATE student_log SET logout_date= ? where log_id = ? ',(date,l_id))
        db.commit()
            
    else :
        cur.execute('UPDATE student_log SET logout_date= ? where log_id = ? ',(date,l_id))
        db.commit()
    # cur.close()    
    return redirect('/studentlogin')

@app.route('/logout_user')
def  logout_user():
    l_id=request.args.get('l_id')
    log= getlog(l_id)
    print(l_id,log)
    db= get_db()
    cur = db.cursor()
    date =datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute('UPDATE user_log SET logout_date=? where log_id = ? ',(date,l_id))
    db.commit()
    cur.close()
    if log[1]=="Administrator":
        return redirect('/adminlogin')
    else:    
        return redirect('/studentlogin')

@app.route('/studentregister',methods=['POST'])
def  studentregister():
    name=request.form.get('name')
    email=request.form.get('email')
    password=request.form.get('password')
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db= get_db()
    cur = db.cursor()
    cur.execute('select student_id,student_name from student where email_id = ?',(email,))
    student=cur.fetchone()
    # cur.close()
    if student :
        error=" Already you have an account account for this Email id"
        return render_template('studentlogin.html',error=error)
    else :
        cur.execute('INSERT INTO student (student_name, email_id, password,sign_up_date) VALUES (?,?,?,?)', (name, email, password,date))
        db.commit()
        # cur.close()
        
        message = "Registration successful. You can now log in."
        return render_template('studentlogin.html', success=message)   
@app.route('/instructor_register',methods=['POST'])
def  instructor_register():
    name=request.form.get('name')
    email=request.form.get('email')
    password=request.form.get('password')
    db= get_db()
    cur = db.cursor()
    cur.execute('select student_id,student_name from student where email_id = ?',(email,))
    student=cur.fetchone()
    cur.execute('select * from instructor where email_id = ?',(email,))
    instructor=cur.fetchone()
    # cur.close()
    if student or instructor :
        error=" Already you have an account account for this Email id"
        return render_template('studentlogin.html',error=error)
    else :
        status="Deactivated"
        cur.execute('INSERT INTO instructor (instructor_name, email_id, password,status) VALUES (?,?,?,?)', (name, email, password,status))
        db.commit()
        # cur.close()
        
        message = "Registration successful. You can now log in."
        return render_template('studentlogin.html', success=message)
@app.route('/sd_profile')
def  sd_profile():
    l_id = request.args.get('l_id')
    s_id = request.args.get('s_id')
    sub="profile"
    return render_template('studentdashboard.html',sub=sub,l_id=l_id,s_id=s_id)
@app.route('/profile')
def  profile():
    s_id = request.args.get('s_id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from student where student_id = ?',(s_id,))
    student=cur.fetchone()
    m_no=0
    cur.execute('select course_id,course_name,logo from course WHERE course_id IN (SELECT course_id FROM enroll_course WHERE student_id = ? AND module_no = ? )',(s_id,m_no))
    courses=cur.fetchall()
    courses_with_encoded_images = []
    for course in courses:
        course_list = list(course)  # Convert tuple to list
        image_data = course_list[2]
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        course_list[2] = encoded_image  # Modify the list
        courses_with_encoded_images.append(tuple(course_list))
    cur.execute('select c.course_id,c.course_name,c.logo,a.assessment_id,a.student_name,a.course_name,DATE(a.datetime) from course c JOIN assessment a ON c.course_id = a.course_id WHERE a.student_id = ?',(s_id,))
    completed_courses=cur.fetchall()
    completed_courses_with_encoded_images = []
    for course in completed_courses:
        course_list = list(course)  # Convert tuple to list
        image_data = course_list[2]
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        course_list[2] = encoded_image  # Modify the list
        completed_courses_with_encoded_images.append(tuple(course_list))
    # cur.close()
    return render_template('profile.html',courses=courses_with_encoded_images,completed_courses=completed_courses_with_encoded_images,s_id=student[0], student_name=student[1], email=student[2])

@app.route('/sd_course')
def  sd_course():
    l_id = request.args.get('l_id')
    s_id = request.args.get('s_id')
    sub="course"
    return render_template('studentdashboard.html',sub=sub,l_id=l_id,s_id=s_id)
@app.route('/course')
def  course():
    l_id = request.args.get('l_id')
    s_id = request.args.get('s_id')
    status="Activated"
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_id,course_name,logo from course where status =?',(status,))
    courses=cur.fetchall()
    courses_with_encoded_images = []
    for course in courses:
        course_list = list(course)  # Convert tuple to list
        image_data = course_list[2]
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        course_list[2] = encoded_image  # Modify the list
        courses_with_encoded_images.append(tuple(course_list))
    return render_template('course.html',courses=courses_with_encoded_images,s_id=s_id,l_id=l_id)

@app.route('/enroll')
def  enroll():
    l_id = request.args.get('l_id')
    c_id=request.args.get('c_id')
    s_id = request.args.get('s_id')
    m_no=0
    db= get_db()
    cur = db.cursor()
    cur.execute('select status from enroll_course where course_id= ? and student_id = ? and module_no = ?',(c_id,s_id,m_no))
    status=cur.fetchone()
    cur.execute('select * from course where course_id=?',(c_id,))
    course=cur.fetchone()
    # cur.close()
    encoded_image = base64.b64encode(course[4]).decode('utf-8')
    if status :
        return render_template('enrollcourse.html',course=course,s_id=s_id,img=encoded_image,status=status[0],l_id=l_id)
    else:
        status=''
        return render_template('enrollcourse.html',course=course,s_id=s_id,img=encoded_image,status=status,l_id=l_id)

@app.route('/enrollcourse')
def  enrollcourse():
    l_id = request.args.get('l_id')
    c_id=request.args.get('c_id')
    s_id = request.args.get('s_id')
    m_no=0
    status='ENROLLED'
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db= get_db()
    cur = db.cursor()
    print(c_id,s_id,m_no,status)
    cur.execute('INSERT INTO enroll_course(student_id,course_id,module_no,status,enroll_date) values(?,?,?,?,?)',(s_id[0],c_id,m_no,status,date))
    db.commit()
    return redirect(url_for('enroll',s_id=s_id,c_id=c_id,l_id=l_id))

@app.route('/courseinfo')
def  courseinfo():
    l_id = request.args.get('l_id')
    c_id=request.args.get('c_id')
    s_id = request.args.get('s_id')
    db= get_db()
    cur = db.cursor()
    
    
    cur.execute('select course_id,course_name,course_description from course where course_id=?',(c_id,))
    course=cur.fetchone()
    cur.execute('''SELECT c.module_no, c.title, e.status FROM course_module c
        LEFT JOIN (SELECT course_id, module_no,status FROM enroll_course
        WHERE student_id = ? GROUP BY course_id, module_no) e 
        ON c.course_id = e.course_id AND c.module_no = e.module_no
        WHERE c.course_id = ?''', (s_id, c_id))
    modules=cur.fetchall()
    f_module=cur.fetchone()
    cur.execute('''SELECT c.module_no, c.title, e.status FROM course_module c
        LEFT JOIN (SELECT course_id, module_no,status FROM enroll_course
        WHERE student_id = ? GROUP BY course_id, module_no) e 
        ON c.course_id = e.course_id AND c.module_no = e.module_no
        WHERE c.course_id = ? ORDER BY c.module_no DESC LIMIT 1''', (s_id, c_id))
    last_module=cur.fetchone()
    cur.execute('SELECT * from assessment where student_id = ? and course_id = ?', (s_id, c_id))
    c_course=cur.fetchone()
    print(c_course)
    print(last_module)
    # cur.close()
    return render_template('courseinfo.html',s_id=s_id,c_course=c_course,course=course,modules=modules,f_module=f_module,last_module=last_module,l_id=l_id)

@app.route('/module_status')
def  module_status():
    l_id = request.args.get('l_id')
    c_id=request.args.get('c_id')
    s_id = request.args.get('s_id')
    m_no=request.args.get('m_no')
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db= get_db()
    cur = db.cursor()
 
    cur.execute('select status from enroll_course where course_id= ? and student_id = ? and module_no = ?',(c_id,s_id,m_no))
    status=cur.fetchone()
    if status :
        return redirect(url_for('view_module',s_id=s_id,c_id=c_id,m_no=m_no))            
    else:    
        if m_no=="1" :
            status="In Progress"
            cur.execute('INSERT INTO enroll_course(student_id,course_id,module_no,status,enroll_date) values(?,?,?,?,?)',(s_id[0],c_id,m_no,status,date))
            db.commit()
            return redirect(url_for('courseinfo',s_id=s_id,c_id=c_id))
        else:
            pre_m_no=str(int(m_no)-1)
            cur.execute('select status from enroll_course where course_id= ? and student_id = ? and module_no = ?',(c_id,s_id,pre_m_no))
            enroll_status=cur.fetchone()
            if enroll_status and enroll_status[0]=="Completed":
                status="In Progress"
                cur.execute('INSERT INTO enroll_course(student_id,course_id,module_no,status,enroll_date) values(?,?,?,?,?)',(s_id[0],c_id,m_no,status,date))
                db.commit()
                return redirect(url_for('view_module',s_id=s_id,c_id=c_id,m_no=m_no))
            else:
                sub="courseinfo"
                return render_template('studentdashboard.html',sub=sub,l_id=l_id,c_id=c_id,s_id=s_id)
            
@app.route('/update_module_status')
def  update_module_status():
    c_id=request.args.get('c_id')
    s_id = request.args.get('s_id')
    m_no=request.args.get('m_no')
    m_status="Completed"
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db= get_db()
    cur = db.cursor()
    cur.execute('update enroll_course set status = ? and completed_date=? where course_id= ? and student_id = ? and module_no = ?',(m_status,date,c_id,s_id,m_no))
    db.commit()
    next_m_no=str(int(m_no)+1)
    cur.execute('select status from enroll_course where course_id= ? and student_id = ? and module_no = ?',(c_id,s_id,next_m_no))
    status=cur.fetchone()
    if status:
        return redirect(url_for('view_module',s_id=s_id,c_id=c_id,m_no=next_m_no))            
    else:
        cur.execute('select * from course_module where course_id= ? and module_no = ?',(c_id,next_m_no))
        module=cur.fetchone()
        if module :
           status="In Progress"
           cur.execute('INSERT INTO enroll_course(student_id,course_id,module_no,status,enroll_date) values(?,?,?,?,?)',(s_id[0],c_id,next_m_no,status,date))
           db.commit()
           return redirect(url_for('view_module',s_id=s_id,c_id=c_id,m_no=next_m_no))
        else:
           return redirect(url_for('courseinfo',s_id=s_id,c_id=c_id))            
            
@app.route('/view_module')
def  view_module():
    s_id=request.args.get('s_id')
    c_id=request.args.get('c_id')
    m_no=request.args.get('m_no')
    db= get_db()
    cur = db.cursor()
    cur.execute('select file_path,file_name from course_module where course_id= ? and module_no = ? ',(c_id,m_no))
    pdf=cur.fetchone()
    # cur.close()
    file_path, file_name = pdf
    # pdf_path = os.path.join(file_path, file_name)
    return render_template('module_view.html',pdf_path=file_path,s_id=s_id,c_id=c_id,m_no=m_no) 
@app.route('/module_quiz')
def  module_quiz():
    s_id=request.args.get('s_id')
    c_id=request.args.get('c_id')
    m_no=request.args.get('m_no')
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from module_quiz where course_id=? and module_no =?',(c_id,m_no))
    questions=cur.fetchall()
    print(questions)
    return render_template('module_quiz.html',s_id=s_id,c_id=c_id,m_no=m_no,questions=questions) 

@app.route('/final_quiz')
def  final_quiz():
    l_id = request.args.get('l_id')
    s_id=request.args.get('s_id')
    c_id=request.args.get('c_id')
    print(l_id)
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from quiz where course_id=?',(c_id,))
    questions=cur.fetchall()
    return render_template('final_quiz.html',s_id=s_id,c_id=c_id,l_id=l_id,questions=questions) 

@app.route('/final_result',methods=['POST'])
def  final_result():
    l_id = request.args.get('l_id')
    s_id = request.args.get('s_id')
    c_id=request.args.get('c_id')
    score=int(request.form.get('score'))
    total=int(request.form.get('total'))
    m_no=0
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(s_id,c_id,score,total)
    percentage=(score /total)*100
    print(s_id,c_id,score,total,percentage)
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from student where student_id = ?',(s_id,))
    student=cur.fetchone()
    cur.execute('select * from course where course_id = ?',(c_id,))
    course=cur.fetchone()
    cur.execute('insert into assessment (student_id,course_id,student_name,course_name,score_obtained,total_score,percentage,datetime) values(?,?,?,?,?,?,?,?)',(student[0],course[0],student[1],course[1],score,total,percentage,date))
    db.commit()
    cur.execute('update enroll_course set  completed_date=? where course_id= ? and student_id = ? and module_no = ?',(date,c_id,s_id,m_no))
    db.commit()
    # cur.close()
    return redirect(url_for('sd_profile',s_id=s_id,l_id=l_id)) 

@app.route('/capture_image')
def capture_image():
    ass_id =request.args.get('ass_id')
    s_name =request.args.get('s_name')
    c_name =request.args.get('c_name')
    dt =request.args.get('dt')
    
    WKHTMLTOIMAGE_PATH = r'"C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe" '
    rendered_html = render_template('certificate.html',ass_id=ass_id,s_name=s_name,c_name=c_name,dt=dt)
    command = f'{WKHTMLTOIMAGE_PATH} --encoding utf-8 --quality 90 --width 800 --load-error-handling ignore - -'  # Command to convert HTML to image (stdin to stdout)
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    screenshot, _ = process.communicate(input=rendered_html.encode())
    screenshot_io = BytesIO(screenshot)
    image_name= "SS-C240"+ass_id+".png"
    return send_file(screenshot_io, mimetype='image/png', as_attachment=True, download_name=image_name)         


@app.route('/sd_mylearning')
def  sd_mylearning():
    l_id = request.args.get('l_id')
    s_id = request.args.get('s_id')
    sub="mylearning"
    return render_template('studentdashboard.html',sub=sub,l_id=l_id,s_id=s_id)
@app.route('/mylearning')
def  mylearning():
    l_id=request.args.get('l_id')
    s_id = request.args.get('s_id')
    m_no=0
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_id,course_name,logo,status from course WHERE course_id IN (SELECT course_id FROM enroll_course WHERE student_id = ? AND module_no = ? )',(s_id,m_no))
    courses=cur.fetchall()
    courses_with_encoded_images = []
    for course in courses:
        course_list = list(course)  # Convert tuple to list
        image_data = course_list[2]
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        course_list[2] = encoded_image  # Modify the list
        courses_with_encoded_images.append(tuple(course_list))
    return render_template('mylearning.html',courses=courses_with_encoded_images,s_id=s_id,l_id=l_id)



@app.route('/sd_enquiries')
def  sd_enquiries():
    l_id = request.args.get('l_id')
    s_id = request.args.get('s_id')
    sub="enquiries"
    return render_template('studentdashboard.html',sub=sub,l_id=l_id,s_id=s_id)
@app.route('/enquiries')
def  enquiries():
    s_id = request.args.get('s_id')
    m_no=0
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_id,course_name from course WHERE course_id IN (SELECT course_id FROM enroll_course WHERE student_id = ? AND module_no = ? )',(s_id,m_no))
    courses=cur.fetchall()
    # cur.close()
    return render_template('enquiries.html',s_id=s_id,courses=courses)
@app.route('/send_message',methods=["POST"])
def  send_message():
    s_id = request.args.get('s_id')
    r_id = request.form.get('receiver-name')
    subject = request.form.get('subject')
    body = request.form.get('body')
    date_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(s_id,r_id,subject,body,date_time)
    db= get_db()
    cur = db.cursor()
    cur.execute('select student_id,student_name,email_id from student WHERE student_id =?',(s_id,))
    student=cur.fetchone()
    print(r_id)
    if r_id=="Admin":
        cur.execute('insert into message (sender_email,receiver_email,subject,body,date_time) values(?,?,?,?,?)',(student[2],r_id,subject,body,date_time))
        db.commit()
    else:
        cur.execute('select course_id,course_name from course WHERE course_id =?',(r_id,))
        course=cur.fetchone()
        cur.execute('insert into message (sender_email,receiver_email,subject,body,date_time) values(?,?,?,?,?)',(student[2],course[0],subject,body,date_time))
        db.commit()
    cur.close()
    return redirect(url_for('enquiries',s_id=s_id))

@app.route('/sd_messages')
def  sd_messages():
    l_id = request.args.get('l_id')
    s_id = request.args.get('s_id')
    sub="messages"
    return render_template('studentdashboard.html',sub=sub,l_id=l_id,s_id=s_id)
@app.route('/messages')
def  messages():
    s_id = request.args.get('s_id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select student_id,student_name,email_id from student WHERE student_id =?',(s_id,))  
    student=cur.fetchone()
    cur.execute('select * from message WHERE sender_email = ?',(student[2],))  
    cur.execute('SELECT m.*, c.course_name FROM message m LEFT JOIN course c ON m.receiver_email = c.course_id WHERE m.sender_email = ?', (student[2],))
    s_messages=cur.fetchall()
    cur.execute('SELECT m.*, c.course_name FROM message m LEFT JOIN course c ON m.sender_email = c.course_id WHERE m.receiver_email = ?', (student[2],))
    r_messages=cur.fetchall()
    return render_template('messages.html',s_id=s_id,s_messages=s_messages,r_messages=r_messages)

@app.route('/sd_score')
def  sd_score():
    l_id = request.args.get('l_id')
    s_id = request.args.get('s_id')
    sub="score"
    return render_template('studentdashboard.html',sub=sub,l_id=l_id,s_id=s_id)
@app.route('/score')
def  score():
    s_id = request.args.get('s_id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from assessment WHERE student_id =?',(s_id,))  
    scores=cur.fetchall()
    return render_template('score_details.html',s_id=s_id,scores=scores)

@app.route('/id')
def  id():
    l_id=request.args.get('l_id')
    sub="studentlist"
    return render_template('instructordashboard.html',sub=sub,l_id=l_id)

@app.route('/id_courselist')
def  id_courselist():
    l_id=request.args.get('l_id')
    sub="courselist"
    return render_template('instructordashboard.html',sub=sub,l_id=l_id)

@app.route('/id_coursemodulelist')
def  id_coursemodulelist():
    l_id=request.args.get('l_id')
    sub="coursemodule"
    return render_template('instructordashboard.html',sub=sub,l_id=l_id)

@app.route('/id_messages')
def  id_messages():
    l_id=request.args.get('l_id')
    sub="id_message"
    return render_template('instructordashboard.html',sub=sub,l_id=l_id)

@app.route('/id_message')
def  id_message():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    db= get_db()
    cur = db.cursor()
    cur.execute('SELECT student_id,student_name,email_id FROM student')
    students=cur.fetchall()
    cur.execute('SELECT * from instructor where instructor_id= ?',(log[2],))
    i_id=cur.fetchone()
    
    cur.execute('SELECT * FROM message WHERE sender_email = ?',(i_id[2],))
    s_messages=cur.fetchall()
    cur.execute('''
    SELECT m.*, c.course_name FROM message m
    LEFT JOIN course c ON m.receiver_email = c.course_id
    WHERE m.receiver_email = ? or m.receiver_email = c.course_id''', (i_id[2],))
    r_messages = cur.fetchall()

    return render_template('id_messages.html',s_messages=s_messages,r_messages=r_messages,students=students,l_id=l_id)

@app.route('/id_send_message',methods=["POST"])
def  id_send_message():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    db= get_db()
    cur = db.cursor()
    cur.execute('SELECT * from instructor where instructor_id= ?',(log[2],))
    i_id=cur.fetchone()
    sender_id=i_id[2]
    r_id = request.form.get('receiver-name')
    subject = request.form.get('subject')
    body = request.form.get('body')
    date_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute('insert into message (sender_email,receiver_email,subject,body,date_time) values(?,?,?,?,?)',(sender_id,r_id,subject,body,date_time))
    db.commit()
    # cur.close()
    return redirect(url_for('id_message',l_id=l_id))

@app.route('/id_score_details')
def  id_score_details():
    l_id=request.args.get('l_id')
    sub="score_details"
    return render_template('instructordashboard.html',sub=sub,l_id=l_id)


@app.route('/admin_login',methods=['POST'])
def  admin_login():
    name=request.form.get('name')
    password=request.form.get('password')
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from admin where user_name = ? and password = ?',(name,password))
    admin=cur.fetchone()
    
    print(admin)
    if admin :
        if admin[4]== "0":
            # cur.close()
            error = 'Access deny for the  user. '
            return render_template('adminlogin.html', error=error)
        else:
           date =datetime.now().strftime('%Y-%m-%d %H:%M:%S')
           u_id=admin[0]
           u_type="Administrator"
           u_name=admin[2]
           access=admin[4]
           cur.execute('INSERT INTO user_log (user_type,user_id,user_name,login_date) VALUES (?,?,?,?)', (u_type,u_id,u_name,date))
           db.commit()
           cur.execute('select * from user_log where user_id = ? and user_type= ? order by login_date DESC ',(u_id,u_type))
           log_id=cur.fetchone()[0]
        #    cur.close()
           print(log_id)
           return redirect(url_for('admindashboard',l_id=log_id,access=access))
    else :
        # cur.close()
        error = 'Invalid username or password. Please try again.'
        return render_template('adminlogin.html', error=error)



@app.route('/admindashboard')
def  admindashboard():
    l_id=request.args.get('l_id')
    access=request.args.get('access')
    sub='admindashboard1'
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/admindashboard1')
def  admindashboard1():
    db= get_db()
    cur = db.cursor()
    current_date = datetime.now().date()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    student_counts_per_day = [0] * 7

    for day_offset in range(7):
            day = start_of_week + timedelta(days=day_offset)
            cur.execute('SELECT COUNT(DISTINCT student_id) FROM student_log WHERE DATE(login_date) = ?', (day,))
            count = cur.fetchone()[0]
            student_counts_per_day[day_offset] = count
    days = ['Mon', 'Tues', 'Wednes', 'Thurs', 'Fri', 'Satur', 'Sun']
    plt.clf()
    plt.bar(days, student_counts_per_day)
    plt.yticks(student_counts_per_day)
    plt.xlabel('Day of the Week')
    plt.ylabel('Number of Students Logged In')
    for i, count in enumerate(student_counts_per_day):
     plt.text(i, count , str(count), ha='center', va='bottom')
    plt.title('Number of Students Logged In Throughout the Week')
    plt.grid(False)
    # Save the plot as a BytesIO object
    img = BytesIO()
    plt.savefig(img,transparent="true")
    img.seek(0)
    plt.close()
    # Encode the image as base64
    img_base64 = base64.b64encode(img.getvalue()).decode()
    cur.execute('SELECT COUNT(*) FROM student')
    student_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM instructor')
    instructor_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM course')
    course_count = cur.fetchone()[0]
    # cur.close()
    return render_template('dashboard1.html', plot_data=img_base64,student_count=student_count,instructor_count=instructor_count,course_count=course_count)
    
@app.route('/ad_studentlist')
def  ad_studentlist():
    l_id=request.args.get('l_id')
    access=request.args.get('access')
    sub="studentlist"
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/studentlist')
def  studentlist():
    l_id=request.args.get('l_id')
    c_id=0
    db= get_db()
    cur = db.cursor()
    cur.execute('select student_id,student_name,email_id,sign_up_date from student')
    students=cur.fetchall()
    cur.execute('select course_id,course_name from course')
    courses=cur.fetchall()
    # cur.close()
    return render_template('studentlist.html',students=students,courses=courses,c_id=c_id,l_id=l_id)

@app.route('/course_student')
def  course_student():
    l_id=request.args.get('l_id')
    c_id=request.args.get('course')
    m_no=0
    print(c_id)
    db= get_db()
    cur = db.cursor()
    if c_id=="0" :
        cur.execute('select student_id,student_name,email_id,sign_up_date  from student')
        students=cur.fetchall()
        course_id="0"
    else:   
        cur.execute('select student_id,student_name,email_id,sign_up_date  from student WHERE student_id IN (SELECT student_id FROM enroll_course WHERE course_id = ? AND module_no = ? )',(c_id,m_no))
        students=cur.fetchall()
        cur.execute('select course_id from course where course_id= ?',(c_id,))
        course_id=cur.fetchone()
    cur.execute('select course_id,course_name from course')
    courses=cur.fetchall()
    # cur.close()
    return render_template('studentlist.html',students=students,courses=courses,c_id=course_id,l_id=l_id)

@app.route('/deletestudents',methods=['POST'])
def  deletestudents():
    l_id=request.args.get('l_id')
    c_id=0
    log=getlog(l_id)
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    selected_ids=request.form.getlist('selector')
    db= get_db()
    cur = db.cursor()
    for student_id in selected_ids :
        cur.execute('select student_name from student where student_id=?',(student_id,))
        name=cur.fetchone()[0]
        cur.execute('delete from student where student_id = ?',(student_id,))
        db.commit()
        action=f"Deleted student name is  {name}."
        cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
        db.commit()
    cur.execute('select student_id,student_name,email_id from student')
    students=cur.fetchall()
    # cur.close()
    return redirect(url_for('studentlist',l_id=log[0]))


@app.route('/ad_instructorlist')
def  ad_instructorlist():
    l_id=request.args.get('l_id')
    access=request.args.get('access')
    sub="instructorlist"
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/instructorlist')
def  instructorlist():
    l_id=request.args.get('l_id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from instructor')
    instructors=cur.fetchall()
    # cur.close()
    return render_template('instructorlist.html',instructors=instructors,l_id=l_id)
@app.route('/activate')
def  activate():
    l_id=request.args.get('l_id')
    print(l_id)
    log=getlog(l_id)
    print(log)
    id = request.args.get('id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select instructor_name from instructor where instructor_id=?',(id,))
    name=cur.fetchone()[0]
    activated='Activated'
    cur.execute('update instructor set status = ? where instructor_id = ?',(activated,id))
    db.commit()
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action=f" Instructor {name} Activated"
    cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
    db.commit()
    # cur.close()
    return redirect(url_for('instructorlist',l_id=log[0]))
@app.route('/deactivate')
def  deactivate():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.args.get('id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select instructor_name from instructor where instructor_id= ?',(id,))
    name=cur.fetchone()[0]
    deactivated='Deactivated'
    cur.execute('update instructor set status = ? where instructor_id = ?',(deactivated,id))
    db.commit()
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action=f" Instructor {name} Deactivated"
    cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
    db.commit()
    # cur.close()
    return redirect(url_for('instructorlist',l_id=log[0]))

@app.route('/ad_adminusers')
def  ad_adminusers():
    l_id=request.args.get('l_id')
    access=request.args.get('access')
    sub="adminusers"
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/adminusers')
def  adminusers():
    l_id=request.args.get('l_id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select user_id,name,user_name,privilege from admin ')
    users=cur.fetchall()
    # cur.close()
    return render_template('adminusers.html',users=users,l_id=l_id)
@app.route('/addadminuser',methods=["POST"])
def  addadminuser():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    name=request.form.get('name')
    user_name=request.form.get('user_name')
    pwd=request.form.get('password')
    access_level=request.form.get('access_level')
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from admin where name =? or user_name = ? ',(name,user_name))
    user= cur.fetchone()
    if user is None :
      cur.execute('INSERT INTO admin (name,user_name,password,privilege) VALUES (?,?,?,?)', (name,user_name,pwd,access_level))
      db.commit()
      date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      action=f" Added {user_name} admin with level {access_level}"
      cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
      db.commit()
    # cur.close()
    return redirect(url_for('adminusers',l_id=log[0]))
@app.route('/editadminuser')
def  editadminuser():
    l_id=request.args.get('l_id')
    id= request.args.get('id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select user_id,name,user_name,privilege from admin where user_id = ? ',(id,))
    user=cur.fetchone()
    # cur.close()
    return render_template('editadminuser.html',user=user,l_id=l_id)
@app.route('/updateadminuser',methods=["POST"])
def  updateadminuser():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    user_id=request.form.get('id')
    name=request.form.get('name')
    user_name=request.form.get('user_name')
    pwd=request.form.get('password')
    access_level=request.form.get('access_level')
    print(user_id,access_level)
    db= get_db()
    cur = db.cursor()
    cur.execute('UPDATE admin SET privilege= ? where user_id= ?', (access_level,user_id))
    db.commit()
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action=f" Updated {user_name} admin by level {access_level}"
    cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
    db.commit()
    # cur.close()
    return redirect(url_for('adminusers',l_id=log[0]))
@app.route('/ad_courselist')
def  ad_courselist():
    l_id=request.args.get('l_id')
    access=request.args.get('access')
    sub="courselist"
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/courselist')
def  courselist():
    l_id=request.args.get('l_id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_id,course_name,no_of_modules,status from course')
    courses=cur.fetchall()
    # cur.close()
    return render_template('courselist.html',courses=courses,l_id=l_id)

@app.route('/activate_course')
def  activate_course():
    l_id=request.args.get('l_id')
    print(l_id)
    log=getlog(l_id)
    print(log)
    id = request.args.get('id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_name from course where course_id=?',(id,))
    c_name=cur.fetchone()[0]
    activated='Activated'
    cur.execute('update course set status = ? where course_id = ?',(activated,id))
    db.commit()
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action=f" {c_name} course is Activated"
    cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
    db.commit()
    # cur.close()
    return redirect(url_for('courselist',l_id=log[0]))

@app.route('/deactivate_course')
def  deactivate_course():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.args.get('id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_name from course where course_id= ?',(id,))
    c_name=cur.fetchone()[0]
    deactivated='Deactivated'
    cur.execute('update course set status = ? where course_id = ?',(deactivated,id))
    db.commit()
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action=f"{c_name} course is  Deactivated"
    cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
    db.commit()
    # cur.close()
    return redirect(url_for('courselist',l_id=log[0]))

@app.route('/addcourse',methods=['POST'])
def  addcourse():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    title=request.form.get('title')
    description=request.form.get('description')
    file = request.files['file']
    img = file.read()
    db= get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO course (course_name,course_description,logo) VALUES (?,?,?)', (title,description,img))
    db.commit()
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action=f" Added course {title}"
    cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
    db.commit()
    cur.execute('select course_id,course_name,no_of_modules from course')
    courses=cur.fetchall()
    # cur.close()
    return render_template('courselist.html',courses=courses,l_id=log[0])

@app.route('/editcourse')
def  editcourse():
    l_id=request.args.get('l_id')
    id = request.args.get('id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_id,course_name,course_description from course where course_id = ? ',(id,))
    course=cur.fetchone()
    # cur.close()
    return render_template('editcourse.html',course=course,l_id=l_id)

@app.route('/uptatecourse',methods=["POST"])
def  updatecourse():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.args.get('id')
    title=request.form.get('title')
    description=request.form.get('description')
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_name from course where course_id =?',(id,))
    c_name=cur.fetchone()[0]
    cur.execute('UPDATE course SET course_name = ?,course_description= ? WHERE course_id= ? ', (title,description,id))
    db.commit()
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action=f" Updated {c_name} course content "
    cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
    db.commit()
    # cur.close()
    return redirect(url_for('courselist',l_id=l_id))

@app.route('/uptatecourse_logo',methods=["POST"])
def  updatecourse_logo():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.args.get('id')
    file = request.files['file']
    img = file.read()
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_name from course where course_id =?',(id,))
    c_name=cur.fetchone()[0]
    cur.execute('UPDATE course SET logo= ? WHERE course_id= ? ', (img,id))
    db.commit()
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action=f" Updated  {c_name} course logo"
    cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
    db.commit()
    # cur.close()
    return redirect(url_for('courselist',l_id=l_id))

@app.route('/coursequestion')
def  coursequestion():
    l_id=request.args.get('l_id')
    id = request.args.get('id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select question_no,question,answer from quiz where course_id = ?',(id,))
    questions=cur.fetchall()
    return render_template('addcoursequestion.html',questions=questions,id=id,l_id=l_id)
@app.route('/addcoursequestion',methods=['POST'])
def  addcoursequestion():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.args.get('id')
    question_no=get_next_question_no(id)
    question=request.form.get('question')
    opt1=request.form.get('opt1')
    opt2=request.form.get('opt2')
    opt3=request.form.get('opt3')
    opt4=request.form.get('opt4')
    answer=request.form.get('answer')
    ans_description=request.form.get('ans_description')
    db= get_db()
    cur = db.cursor()
    if question :
        cur.execute('INSERT INTO quiz (course_id,question_no,question,option1,option2,option3,option4,answer,answer_description) VALUES (?,?,?,?,?,?,?,?,?)', (id,question_no,question,opt1,opt2,opt3,opt4,answer,ans_description))
        db.commit()
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        action=f" Added course question "
        cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
        db.commit()    
    # cur.close()
    return redirect(url_for('coursequestion',id=id,l_id=log[0]))

@app.route('/backcoursequestion')
def  backcoursequestion():
    l_id=request.args.get('l_id')
    id = request.args.get('id')
    return redirect(url_for('coursequestion',id=id,l_id=l_id))
@app.route('/editcoursequestion')
def  editcoursequestion():
    l_id=request.args.get('l_id')
    id = request.args.get('id')
    q_no = request.args.get('q_no')
    db= get_db()
    cur = db.cursor()
    cur.execute('select question_no,question,option1,option2,option3,option4,answer,answer_description from quiz where course_id = ? and question_no = ?',(id,q_no))
    question=cur.fetchone()
    # cur.close()
    return render_template('editcoursequestion.html',id=id,question=question,l_id=l_id)

@app.route('/uptatecoursequestion',methods=["POST"])
def  updatecoursequestion():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.args.get('id')
    q_no = request.args.get('q_no')
    question=request.form.get('question')
    opt1=request.form.get('opt1')
    opt2=request.form.get('opt2')
    opt3=request.form.get('opt3')
    opt4=request.form.get('opt4')
    answer=request.form.get('answer')
    ans_description=request.form.get('ans_description')
    db= get_db()
    cur = db.cursor()
    cur.execute('UPDATE quiz SET question= ?,option1= ?,option2= ?,option3= ?,option4= ?,answer= ?,answer_description= ? WHERE course_id= ? and question_no= ?', (question,opt1,opt2,opt3,opt4,answer,ans_description,id,q_no))
    db.commit()
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action=f" Updated course question number {q_no} "
    cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
    db.commit()
    # cur.close()
    return redirect(url_for('coursequestion',id=id,l_id=log[0]))

@app.route('/ad_coursemodulelist')
def  ad_coursemodulelist():
    l_id=request.args.get('l_id')
    access=request.args.get('access')
    sub="coursemodule"
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/coursemodule')
def  coursemodule():
    l_id=request.args.get('l_id')
    print(l_id)
    id = request.args.get('id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_id from course where course_id= ?',(id,))
    course_id=cur.fetchone()
    cur.execute('select course_id ,course_name from course')
    courses=cur.fetchall()
    cur.execute('select course_id ,module_no,title,file_name from course_module where course_id= ?',(id,))
    modules=cur.fetchall()
    # cur.close()
    return render_template('coursemodule.html',modules=modules,courses=courses,id=course_id,l_id=l_id)

@app.route('/selectcourse',methods=["POST"])
def  selectcourse():
    l_id=request.args.get('l_id')
    id=request.form.get('course')
    return redirect(url_for('coursemodule',id=id,l_id=l_id))

@app.route('/addcoursemodule',methods=['POST'])
def  addcoursemodule():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.args.get('id')
    module_no= get_next_module_no(id)
    title=request.form.get('title')
    file = request.files['file']
    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from course_module where file_name= ?',(filename,))
    pdf=cur.fetchone()
    if pdf==None :
    #    folder_path = app.config['UPLOAD_FOLDER'] 
       cur.execute('INSERT INTO course_module (course_id,module_no,title,file_name,file_path) VALUES (?,?,?,?,?)', (id,module_no,title,filename,file_path))
       db.commit()
       date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
       action=f" Added course module for course id {id} "
       cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
       db.commit()
       message= "add successfully"
    else :
        message= "insert has been stoped because of pdf name has been already exits"
    # cur.close()
    return redirect(url_for('coursemodule',id=id,l_id=l_id))

@app.route('/editcoursemodule')
def  editcoursemodule():
    l_id=request.args.get('l_id')
    id = request.args.get('id')
    m_no = request.args.get('m_no')
    message = request.args.get('message')
    db= get_db()
    cur = db.cursor()
    cur.execute('select course_id ,module_no,title,file_name from course_module where course_id=? and module_no = ?',(id,m_no))
    module=cur.fetchone()
    # cur.close()
    return render_template('editcoursemodule.html',module=module,message=message,l_id=l_id)
@app.route('/updatecoursemodule',methods=['POST'])
def  updatecoursemodule():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.form.get('id')
    m_no = request.form.get('m_no')
    title=request.form.get('title')
    db= get_db()
    cur = db.cursor()
    cur.execute('update course_module set title=?  where course_id=? and module_no=?', (title,id,m_no))
    db.commit()
    date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    action=f" Updated course module for course id {id} and module {m_no} "
    cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
    db.commit()
    #    cur.close()
    return redirect(url_for('coursemodule',id=id,l_id=l_id))
    
@app.route('/updatecoursemodule_PDF',methods=['POST'])
def  updatecoursemodule_PDF():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.args.get('id')
    m_no = request.args.get('m_no')
    file = request.files['file']
    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    db= get_db()
    cur = db.cursor()
    cur.execute('select file_path from course_module where course_id= ?  and module_no =?',(id,m_no))
    old_file_path=cur.fetchone()
    cur.execute('select * from course_module where file_name=?',(filename,))
    pdf=cur.fetchone()
    if pdf==None :
       cur.execute('update course_module set file_name=?,file_path=? where course_id=? and module_no=?', (filename,file_path,id,m_no))
       db.commit()
       date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
       action=f" Updated course module for course id {id} and module {m_no} "
       cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
       db.commit()
       if os.path.exists(old_file_path[0]):
            os.remove(old_file_path[0])
       message= "add successfully"
    #    cur.close()
       return redirect(url_for('coursemodule',id=id,l_id=l_id))
    else :
        message= "insert has been stoped because of pdf name has been already exits"
        # cur.close()
        return redirect(url_for('editcoursemodule',id=id,m_no=m_no,message=message,l_id=l_id))
       
@app.route('/coursemodulequestion')
def  coursemodulequestion():
    l_id=request.args.get('l_id')
    id = request.args.get('id')
    m_no = request.args.get('m_no')
    db= get_db()
    cur = db.cursor()
    cur.execute('select question_no,question,answer from module_quiz where course_id = ? and module_no= ?',(id,m_no))
    questions=cur.fetchall()
    # cur.close()
    return render_template('coursemodulequestion.html',questions=questions,id=id,m_no=m_no,l_id=l_id)
@app.route('/addcoursemodulequestion',methods=["POST"])
def  addcoursemodulequestion():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.args.get('id')
    m_no = request.args.get('m_no')
    question_no=get_next_module_question_no(id,m_no)
    question=request.form.get('question')
    opt1=request.form.get('opt1')
    opt2=request.form.get('opt2')
    opt3=request.form.get('opt3')
    opt4=request.form.get('opt4')
    answer=request.form.get('answer')
    ans_description=request.form.get('ans_description')
    db= get_db()
    cur = db.cursor()
    if question :
        cur.execute('INSERT INTO module_quiz (course_id,module_no,question_no,question,option1,option2,option3,option4,answer,answer_description) VALUES (?,?,?,?,?,?,?,?,?,?)', (id,m_no,question_no,question,opt1,opt2,opt3,opt4,answer,ans_description))
        db.commit()
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        action=f" Added course module question for course id {id} and module {m_no} "
        cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
        db.commit()
    # cur.close()
    return redirect(url_for('coursemodulequestion',id=id,m_no=m_no,l_id=l_id))
@app.route('/editcoursemodulequestion')
def  editcoursemodulequestion():
    l_id=request.args.get('l_id')
    id = request.args.get('id')
    m_no = request.args.get('m_no')
    q_no = request.args.get('q_no')
    db= get_db()
    cur = db.cursor()
    cur.execute('select question_no,question,option1,option2,option3,option4,answer,answer_description from module_quiz where course_id = ? and module_no= ? and question_no = ?',(id,m_no,q_no))
    question=cur.fetchone()
    # cur.close()
    return render_template('editcoursemodulequestion.html',id=id,m_no=m_no,question=question,l_id=l_id)

@app.route('/uptatecoursemodulequestion',methods=["POST"])
def  updatecoursemodulequestion():
    l_id=request.args.get('l_id')
    log=getlog(l_id)
    id = request.args.get('id')
    m_no = request.args.get('m_no')
    q_no = request.args.get('q_no')
    question=request.form.get('question')
    opt1=request.form.get('opt1')
    opt2=request.form.get('opt2')
    opt3=request.form.get('opt3')
    opt4=request.form.get('opt4')
    answer=request.form.get('answer')
    ans_description=request.form.get('ans_description')
    print(question,opt1,opt2,opt3,opt4,answer,ans_description,id,m_no,q_no)
    try:
     db= get_db()
     cur = db.cursor()
     cur.execute('UPDATE module_quiz SET question= ?,option1= ?,option2= ?,option3= ?,option4= ?,answer= ?,answer_description= ? WHERE course_id=  ? and module_no= ? and question_no= ?', (question,opt1,opt2,opt3,opt4,answer,ans_description,id,m_no,q_no))
     db.commit()
     date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
     action=f" Updated course module question for course id {id}' , module '{m_no}' and  question '{q_no}' "
     cur.execute('insert into activity_log (user_type,user_id,user_name,date ,action) values(?,?,?,?,?)',(log[1],log[2],log[3],date,action))
     db.commit()
    #  cur.close()
     return redirect(url_for('coursemodulequestion',id=id,m_no=m_no,l_id=log[0]))
    except Exception as e:
        print("Error updating question:", e)
        return "Error updating question"
    
@app.route('/ad_student_log')
def  ad_student_log():
    l_id=request.args.get('l_id')
    access=request.args.get('access')
    sub="student_log"
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/student_log')
def  student_log():
    l_id=request.args.get('l_id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from student_log order by log_id DESC')
    student_log=cur.fetchall()
    # cur.close()
    return render_template('student_log.html',student_log=student_log,l_id=l_id)

@app.route('/ad_activity_log')
def  ad_activity_log():
    l_id=request.args.get('l_id')
    access=request.args.get('access')
    sub="activity_log"
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/activity_log')
def  activity_log():
    l_id=request.args.get('l_id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from activity_log order by log_id DESC')
    activity_log=cur.fetchall()
    # cur.close()
    return render_template('activity_log.html',activity_log=activity_log,l_id=l_id)

@app.route('/ad_user_log')
def  ad_user_log():
    l_id=request.args.get('l_id')
    access=request.args.get('access')
    sub="user_log"
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/user_log')
def  user_log():
    l_id=request.args.get('l_id')
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from user_log order by log_id DESC')
    user_log=cur.fetchall()
    # cur.close()
    return render_template('User_log.html',user_log=user_log,l_id=l_id)

@app.route('/ad_message')
def  ad_message():
    l_id=request.args.get('l_id')
    access=request.args.get('access')
    sub="view_message"
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/view_message')
def  view_message():
    l_id=request.args.get('l_id')
    admin="Admin"
    db= get_db()
    cur = db.cursor()
    cur.execute('SELECT student_id,student_name,email_id FROM student')
    students=cur.fetchall()
    cur.execute('SELECT instructor_id,instructor_name,email_id FROM instructor')
    instructors=cur.fetchall()
    cur.execute('SELECT * FROM message WHERE sender_email = ?', (admin,))
    s_messages=cur.fetchall()
    cur.execute('SELECT * FROM message WHERE receiver_email = ?', (admin,))
    r_messages=cur.fetchall()
    return render_template('ad_messages.html',s_messages=s_messages,r_messages=r_messages,students=students,instructors=instructors,l_id=l_id)

@app.route('/ad_send_message',methods=["POST"])
def  ad_send_message():
    l_id=request.args.get('l_id')
    sender_id="Admin"
    r_id = request.form.get('receiver-name')
    subject = request.form.get('subject')
    body = request.form.get('body')
    date_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db= get_db()
    cur = db.cursor()
    cur.execute('insert into message (sender_email,receiver_email,subject,body,date_time) values(?,?,?,?,?)',(sender_id,r_id,subject,body,date_time))
    db.commit()
    # cur.close()
    return redirect(url_for('view_message',l_id=l_id))

@app.route('/ad_score_details')
def  ad_score_details():
    l_id = request.args.get('l_id')
    access = request.args.get('access')
    sub="score_details"
    return render_template('admindashboard.html',sub=sub,l_id=l_id,access=access)
@app.route('/score_details')
def  score_details():
    l_id = request.args.get('l_id')
    c_id=0
    db= get_db()
    cur = db.cursor()
    cur.execute('select * from assessment')  
    scores=cur.fetchall()
    cur.execute('select * from course')  
    courses=cur.fetchall()
    return render_template('ad_score_details.html',l_id=l_id,c_id=c_id,scores=scores,courses=courses)

@app.route('/course_completed')
def  course_completed():
    l_id=request.args.get('l_id')
    c_id=request.args.get('course')
    m_no=0
    print(c_id)
    db= get_db()
    cur = db.cursor()
    if c_id=="0" :
        cur.execute('select * from assessment')  
        scores=cur.fetchall()
        course_id="0"
    else:   
        cur.execute('select * from assessment where course_id = ? ',(c_id,))  
        scores=cur.fetchall()
        cur.execute('select course_id from course where course_id=?',(c_id,))
        course_id=cur.fetchone()
    cur.execute('select course_id,course_name from course')
    courses=cur.fetchall()
    # cur.close()
    return render_template('ad_score_details.html',scores=scores,courses=courses,c_id=course_id,l_id=l_id)

if __name__=="__main__":
    app.run (debug=True)    
