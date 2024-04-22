from flask import Flask ,g
import sqlite3
DATABASE = 'StudySync.db'  
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


def create_table():
    # conn = sqlite3.connect(DATABASE)
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name VARCHAR(45) NOT NULL,
            email_id VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(45) NOT NULL,
            img_location VARCHAR(100),
            phone_no INTEGER UNIQUE,
            city VARCHAR(45), sign_up_date DATETIME
        );
    ''')
    db.commit()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name VARCHAR(100) NOT NULL UNIQUE,
            no_of_modules INTEGER DEFAULT 0,
            course_description VARCHAR(255) NOT NULL,
            logo BLOB, status VARCHAR(100)
        );
    ''')
    db.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz (
            course_id INTEGER NOT NULL,
            question_no INTEGER NOT NULL,
            question VARCHAR(100) NOT NULL,
            option1 VARCHAR(45) NOT NULL,
            option2 VARCHAR(45) NOT NULL,
            option3 VARCHAR(45) NOT NULL,
            option4 VARCHAR(45) NOT NULL,
            answer VARCHAR(45) NOT NULL,
            answer_description VARCHAR(100),
            PRIMARY KEY (course_id, question_no)
        );
    ''')
    db.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessment (
            assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            student_name VARCHAR(45) NOT NULL,
            course_name VARCHAR(45) NOT NULL,
            score_obtained INTEGER NOT NULL,
            total_score INTEGER NOT NULL,
            percentage FLOAT NOT NULL,
            datetime DATETIME NOT NULL
        );
    ''')

    db.commit()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS course_module (
        course_id INTEGER NOT NULL,
        module_no INTEGER NOT NULL,
        title VARCHAR(100) NOT NULL,
        file_name VARCHAR(100) NOT NULL,
        file_path VARCHAR(100) NOT NULL,
        PRIMARY KEY (course_id, module_no)
        );
    ''')
    db.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS module_quiz (
            course_id INTEGER NOT NULL,
            module_no INTEGER NOT NULL,
            question_no INTEGER NOT NULL,
            question VARCHAR(100) NOT NULL,
            option1 VARCHAR(45) NOT NULL,
            option2 VARCHAR(45) NOT NULL,
            option3 VARCHAR(45) NOT NULL,
            option4 VARCHAR(45) NOT NULL,
            answer VARCHAR(45) NOT NULL,
            answer_description VARCHAR(100),
            PRIMARY KEY (course_id, module_no, question_no)
        );
    ''')
    db.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_email VARCHAR(45) NOT NULL,
            receiver_email VARCHAR(45) NOT NULL,
            subject VARCHAR(100) NOT NULL,
            body VARCHAR(255) NOT NULL,
            date_time DATETIME NOT NULL,
            reply_id INTEGER
        );
    ''')

    db.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(45) NOT NULL,
            user_name VARCHAR(45) NOT NULL,
            password VARCHAR(45) NOT NULL,
            privilege VARCHAR(45)
        );
    ''')

    db.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instructor (
            instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            instructor_name VARCHAR(45) NOT NULL,
            email_id VARCHAR(45) NOT NULL,
            password VARCHAR(45) NOT NULL,
            status VARCHAR(45)
        );
    ''')
    db.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enroll_course (
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            module_no INTEGER NOT NULL,
            status VARCHAR(45), enroll_date DATETIME, completed_date DATETIME,
            PRIMARY KEY (student_id, course_id, module_no)
        );
    ''')

    db.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            log_id INTEGER PRIMARY KEY,
            user_type VARCHAR(45) NOT NULL,
            user_id INTEGER NOT NULL,
            user_name VARCHAR(45) NOT NULL,
            date DATETIME NOT NULL,
            action VARCHAR(100)
        );
    ''')
    db.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            student_name VARCHAR(45) NOT NULL,
            login_date DATETIME,
            logout_date DATETIME
        );
    ''')
    db.commit()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_type VARCHAR(45) NOT NULL,
            user_id INTEGER NOT NULL,
            user_name VARCHAR(45) NOT NULL,
            login_date DATETIME,
            logout_date DATETIME
        );
    ''')
    db.commit()



def add_module_count_trigger():
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
    CREATE TRIGGER IF NOT EXISTS add_module_count
    AFTER INSERT ON course_module
    FOR EACH ROW
    BEGIN
        UPDATE course SET no_of_modules = no_of_modules + 1 WHERE course_id = NEW.course_id;
    END;
    ''')
    db.commit()
    # db.close()
