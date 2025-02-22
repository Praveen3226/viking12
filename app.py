from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, json, session
import pymysql
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from mysql.connector import Error
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management
app.permanent_session_lifetime = timedelta(minutes=30)  # Auto logout after 30 minutes of inactivity

# Database Connection Function
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Money2035",
        database="leads",
        cursorclass=pymysql.cursors.DictCursor  # Ensures dictionary output

    )

# User Authentication Data
users = {
    'admin': {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
    'emp': {'username': 'emp', 'password': 'emp123', 'role': 'emp'},
}

# 🔹 Decorator for Login Protection
def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session:
            flash("⚠️ You must log in first!", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# 🔹 Role-Based Access Control Decorator
def role_required(role):
    def decorator(f):
        def wrap(*args, **kwargs):
            if session.get('role') != role:
                flash("⛔ Unauthorized access!", "error")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        wrap.__name__ = f.__name__
        return wrap
    return decorator

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            connection = get_db_connection()
            cursor = connection.cursor(pymysql.cursors.DictCursor)

            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if user:
                stored_password = user['password']

                # Check hashed password
                if check_password_hash(stored_password, password):
                    session.permanent = True
                    session['user_id'] = user['id']
                    session['username'] = user['username']

                    flash('Login successful!', 'success')

                    if 'role' in user and user['role'] == 'Admin':
                        return redirect(url_for('admindash'))
                    return redirect(url_for('empdash'))

                else:
                    flash('Invalid username or password', 'error')
            else:
                flash('Invalid username or password', 'error')

        except Exception as e:
            flash('An error occurred while logging in', 'error')
            print(f"Error: {e}")

        finally:
            cursor.close()
            connection.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear session data
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))




@app.route('/reportFCL')
@login_required
def reportFCL():
    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Fetch relevant data from the `form` table
        cursor.execute("SELECT CertificateNumber, date, applicant_name, container_number ,status FROM form")
        form = cursor.fetchall()

        conn.close()

        # Pass the data to the report.html template
        return render_template('reportFCL.html', form=form)
    except Error as e:
        print(f"Error: {e}")
        flash('An error occurred while fetching the reports. Please try again.', 'error')
        return redirect(url_for('reportFCL'))


@app.route('/reportFCL1/<int:CertificateNumber>')
@login_required
def reportFCL1(CertificateNumber):
    conn = None
    cursor = None
    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the report from the `form` table
        cursor.execute("SELECT * FROM form WHERE CertificateNumber = %s", (CertificateNumber,))
        form = cursor.fetchone()  # Fetch a single row

        # Handle case where no data is found
        if not form:
            flash('No report found for the given Certificate Number.', 'error')
            return redirect(url_for('reportFCL'))

        # Parse the `consignment_details` JSON string into a Python object
        if 'consignment_details' in form and form['consignment_details']:
            try:
                form['consignment_details'] = json.loads(form['consignment_details'])
            except json.JSONDecodeError:
                form['consignment_details'] = []  # Default to an empty list if JSON is invalid
        else:
            form['consignment_details'] = []

        # Render the template with the fetched data
        return render_template('reportFCL1.html', form=form)

    except pymysql.Error as e:
        print(f"Database Error: {e}")
        flash('An error occurred while fetching the reports. Please try again.', 'error')
        return redirect(url_for('reportFCL'))

    finally:
        # Close cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    
@app.route('/reportCER')
@login_required
def reportCER():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Fetch all reports
        cursor.execute("SELECT CertificateNumber, date, applicant_name, shipper, consignee, total_pkgs ,status FROM cer")
        cer_data = cursor.fetchall()

        conn.close()

        return render_template('reportCER.html', cer_data=cer_data)
    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while fetching the reports.', 'error')
        return redirect(url_for('reportCER'))

@app.route('/reportCER1/<int:CertificateNumber>')
@login_required
def reportCER1(CertificateNumber):  # This must match url_for('reportCER1')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Fetch the certificate details
        cursor.execute("SELECT * FROM cer WHERE CertificateNumber = %s", (CertificateNumber,))
        cer_details = cursor.fetchone()

        conn.close()

        if not cer_details:
            flash("No record found for the given Certificate Number.", "error")
            return redirect(url_for("reportCER"))

        # Convert survey_data from JSON (if available)
        survey_data = []
        if cer_details.get('survey_data'):  
            try:
                survey_data = json.loads(cer_details['survey_data'])
            except json.JSONDecodeError:
                flash("Error processing survey data.", "error")

        return render_template('reportCER1.html', cer=cer_details, survey_data=survey_data)

    except Exception as e:
        print(f"Error fetching report: {e}")
        flash("An error occurred while fetching the report.", "error")
        return redirect(url_for("reportCER"))

@app.route('/reportContainer')
@login_required
def reportContainer():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Fetch all container records
        cursor.execute("SELECT CertificateNumber, date, applicant_for_survey, date_of_inspection, container_no ,status FROM container")
        container_data = cursor.fetchall()

        conn.close()

        return render_template('reportContainer.html', container_data=container_data)
    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while fetching the container records.', 'error')
        return redirect(url_for('reportContainer'))
    

@app.route('/reportContainer1/<int:CertificateNumber>')
@login_required
def reportContainer1(CertificateNumber):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Fetch the container details based on CertificateNumber
        cursor.execute("""
            SELECT * FROM container WHERE CertificateNumber = %s
        """, (CertificateNumber,))
        container_details = cursor.fetchone()

        # Debug: print the fetched data
        print(container_details)  # This will print all fields of container_details

        conn.close()

        if not container_details:
            flash("No record found for the given Certificate Number.", "error")
            return redirect(url_for("reportContainer"))

        # Optionally handle any survey data or survey checkboxes if needed
        survey_data = {}
        if container_details.get('survey_checkboxes'):
            try:
                survey_data = json.loads(container_details['survey_checkboxes'])
            except json.JSONDecodeError:
                flash("Error processing survey checkboxes.", "error")

        return render_template('reportContainer1.html', container=container_details, survey_data=survey_data)

    except Exception as e:
        print(f"Error fetching container report: {e}")
        flash("An error occurred while fetching the container report.", "error")
        return redirect(url_for("reportContainer"))

    
@app.route('/admindash')
@login_required
def admindash():
    if session.get('role') != 'Admin':
        flash("Unauthorized access!", "error")
        
    return render_template('admindash.html')

@app.route('/cont')
@login_required
def cont():
    if session.get('role') != 'admin':
        flash("Unauthorized access!", "error")
    return render_template('cont.html')

@app.route('/contrpt')
@login_required
def contrpt():
    return render_template('contrpt.html')


@app.route('/empcertificate')
@login_required
def empcertificate():
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:

                # Fetch the latest certificate
                cursor.execute("SELECT * FROM cer ORDER BY id DESC LIMIT 1")
                certificate_data = cursor.fetchone()

                # If no certificate exists, set a default placeholder
                if not certificate_data:
                    certificate_data = {"CertificateNumber": "N/A", "status": "Unknown"}

        return render_template('empcertificate.html', certificate=certificate_data)

    except Exception as e:
        print(f"Error fetching certificate: {e}")
        return "Error fetching certificate", 500

@app.route('/empforms')
@login_required
def empforms():
    return render_template('empforms.html')
    

@app.route('/empdash')
@login_required
def empdash():
    return render_template('empdash.html')


@app.route('/empemp')
@login_required
def empemp():
    form_data = None  # Ensure form_data is defined

    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Fetch the latest CertificateNumber and status from 'form' table
                cursor.execute("SELECT CertificateNumber, status FROM form ORDER BY id DESC LIMIT 1")
                form_data = cursor.fetchone()

        if not form_data:  # If no record exists, return default values
            form_data = {"CertificateNumber": "N/A", "status": "Unknown"}

    except Exception as e:
        print(f"Error fetching form data: {e}")
        form_data = {"CertificateNumber": "Error", "status": "Error"}

    print("Fetched Form Data:", form_data)  # ✅ Debugging log

    return render_template('empemp.html', form=form_data)



@app.route('/empcontainer')
@login_required
def empcontainer():
    container_data = None  # Ensure container_data is defined
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT * FROM container ORDER BY id DESC LIMIT 1")
                container_data = cursor.fetchone()

        if not container_data:  # If no container exists, define an empty dictionary
            container_data = {"CertificateNumber": "N/A", "status": "Unknown"}

    except Exception as e:
        print(f"Error fetching container data: {e}")
        container_data = {"CertificateNumber": "Error", "status": "Error"}

    return render_template('empcontainer.html', container=container_data)

@app.route('/certificate')
@login_required
def certificate():
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:

                # Fetch the latest certificate
                cursor.execute("SELECT * FROM cer ORDER BY id DESC LIMIT 1")
                certificate_data = cursor.fetchone()

                # If no certificate exists, set a default placeholder
                if not certificate_data:
                    certificate_data = {"CertificateNumber": "N/A", "status": "Unknown"}

        return render_template('certificate.html', certificate=certificate_data)

    except Exception as e:
        print(f"Error fetching certificate: {e}")
        return "Error fetching certificate", 500



@app.route('/container')
@login_required
def container():
    container_data = None  # Ensure container_data is defined
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT * FROM container ORDER BY id DESC LIMIT 1")
                container_data = cursor.fetchone()

        if not container_data:  # If no container exists, define an empty dictionary
            container_data = {"CertificateNumber": "N/A", "status": "Unknown"}

    except Exception as e:
        print(f"Error fetching container data: {e}")
        container_data = {"CertificateNumber": "Error", "status": "Error"}

    return render_template('container.html', container=container_data)



@app.route('/get_numbers')
@login_required
def get_numbers():
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                
                # 1️⃣ Check if an existing "Open" certificate number exists
                cursor.execute("SELECT CertificateNumber FROM container WHERE status = 'Open' ORDER BY id DESC LIMIT 1")
                last_record = cursor.fetchone()

                print("Fetched existing open certificate:", last_record)  # Debug log

                if last_record and last_record["CertificateNumber"]:
                    new_certificate_number = last_record["CertificateNumber"]  # ✅ Reuse existing number
                else:
                    # 2️⃣ Fetch the last issued certificate number
                    cursor.execute("SELECT CertificateNumber FROM container ORDER BY id DESC LIMIT 1")
                    last_record = cursor.fetchone()

                    if last_record and last_record["CertificateNumber"] and last_record["CertificateNumber"].isdigit():
                        next_number = int(last_record["CertificateNumber"]) + 1
                    else:
                        next_number = 1  # Start fresh if no records exist

                    # 3️⃣ Generate new Certificate Number
                    new_certificate_number = str(next_number)

                    # Insert new certificate number with status "Open"
                    insert_query = "INSERT INTO container (CertificateNumber, status) VALUES (%s, %s)"
                    cursor.execute(insert_query, (new_certificate_number, "Open"))
                    conn.commit()

                print("Returning Certificate Number:", new_certificate_number)  # Debugging log
                return jsonify({"certificateNumber": new_certificate_number, "status": "Open"})

    except Exception as e:
        print(f"Error fetching certificate number: {e}")  # Log error details
        return jsonify({"error": str(e)}), 500  # Return HTTP 500 for errors





@app.route('/add_survey', methods=['POST'])
@login_required
def add_survey():
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                
                # Extract form data
                CertificateNumber = request.form.get('CertificateNumber', '').strip()
                date = request.form.get('date', '').strip()
                applicant_for_survey = request.form.get('applicant_for_survey', '').strip()
                date_of_inspection = request.form.get('date_of_inspection', '').strip()
                container_no = request.form.get('container_no', '').strip()
                place_of_inspection = request.form.get('place_of_inspection', '').strip()
                container_type = request.form.get('type', '').strip()
                size = request.form.get('size', '').strip()
                tare_weight = request.form.get('tare_weight', '').strip()
                csc_no = request.form.get('csc_no', '').strip()
                payload_capacity = request.form.get('payload_capacity', '').strip()
                year_of_manufacture = request.form.get('year_of_manufacture', '').strip()
                max_gross_weight = request.form.get('max_gross_weight', '').strip()
                remarks = request.form.get('remarks', '').strip()
                surveyor = request.form.get('surveyor', '').strip()

                # ✅ Validate required fields
                required_fields = {
                    "CertificateNumber": CertificateNumber,
                    "date": date,
                    "applicant_for_survey": applicant_for_survey,
                    "date_of_inspection": date_of_inspection,
                    "container_no": container_no,
                    "place_of_inspection": place_of_inspection,
                    "surveyor": surveyor,
                }

                for field, value in required_fields.items():
                    if not value:
                        flash(f"Error: {field.replace('_', ' ').title()} is required!", "error")
                        return redirect(url_for('container'))  # Redirect if a field is missing

                # ✅ Check if CertificateNumber exists
                cursor.execute("SELECT COUNT(*) AS count FROM container WHERE CertificateNumber = %s", (CertificateNumber,))
                result = cursor.fetchone()

                if result and result["count"] == 0:
                    flash(f"Error: Certificate Number {CertificateNumber} not found!", "error")
                    return redirect(url_for('forms'))  # Redirect if record does not exist

                # ✅ Update existing survey record
                update_query = """
                    UPDATE container
                    SET 
                        date = %s, applicant_for_survey = %s, date_of_inspection = %s, container_no = %s,
                        place_of_inspection = %s, type = %s, size = %s, tare_weight = %s, csc_no = %s,
                        payload_capacity = %s, year_of_manufacture = %s, max_gross_weight = %s, 
                        remarks = %s, surveyor = %s, status = 'In Progress'
                    WHERE CertificateNumber = %s
                """
                values = (
                    date, applicant_for_survey, date_of_inspection, container_no, place_of_inspection,
                    container_type, size, tare_weight, csc_no, payload_capacity, year_of_manufacture,
                    max_gross_weight, remarks, surveyor, CertificateNumber
                )

                cursor.execute(update_query, values)
                conn.commit()

                flash('Survey updated successfully!', 'success')
                return redirect(url_for('forms'))  # ✅ Redirect on success

    except Exception as e:
        print(f"Error: {e}")
        flash(f'An error occurred: {e}', 'error')
        return redirect(url_for('container'))



@app.route('/emp')
@login_required
def emp():
    form_data = None  # Ensure form_data is defined

    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Fetch the latest CertificateNumber and status from 'form' table
                cursor.execute("SELECT CertificateNumber, status FROM form ORDER BY id DESC LIMIT 1")
                form_data = cursor.fetchone()

        if not form_data:  # If no record exists, return default values
            form_data = {"CertificateNumber": "N/A", "status": "Unknown"}

    except Exception as e:
        print(f"Error fetching form data: {e}")
        form_data = {"CertificateNumber": "Error", "status": "Error"}

    print("Fetched Form Data:", form_data)  # ✅ Debugging log

    return render_template('emp.html', form=form_data)



@app.route('/employee')
@login_required
def employee():
    return render_template('employee.html')


@app.route('/forms')
@login_required
def forms():
    return render_template('forms.html')

@app.route('/certificatert')
@login_required
def certificatert():
    return render_template('certificatert.html')

@app.route('/certificaterpt')
@login_required
def certificaterpt():
    return render_template('certificaterpt.html')

@app.route('/containerrpt')
@login_required
def containerrpt():
    return render_template('containerrpt.html')

# Fetch the latest certificate number


@app.route('/get_number')
@login_required
def get_number():
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                
                # Check if an existing "Open" certificate number exists
                cursor.execute("SELECT CertificateNumber FROM form WHERE status = 'Open' ORDER BY id DESC LIMIT 1")
                last_record = cursor.fetchone()

                print("Fetched existing open certificate:", last_record)  # Debugging log

                if last_record:
                    new_certificate_number = last_record["CertificateNumber"]  # ✅ Return the same number
                else:
                    # Fetch the last used certificate number
                    cursor.execute("SELECT CertificateNumber FROM form ORDER BY id DESC LIMIT 1")
                    last_record = cursor.fetchone()

                    if last_record and last_record["CertificateNumber"].isdigit():
                        next_number = int(last_record["CertificateNumber"]) + 1
                    else:
                        next_number = 1  # Start from 1 if no record exists

                    new_certificate_number = str(next_number)

                    # Insert new certificate number with status "Open"
                    insert_query = "INSERT INTO form (CertificateNumber, status) VALUES (%s, %s)"
                    cursor.execute(insert_query, (new_certificate_number, "Open"))
                    conn.commit()

                print("Returning Certificate Number:", new_certificate_number)  # Debugging log
                return jsonify({"certificateNumber": new_certificate_number, "status": "Open"})

    except Exception as e:
        print(f"Error fetching certificate number: {e}")
        return jsonify({"error": str(e)}), 500  # Return HTTP 500 for errors



@app.route('/get_consignment_details')
@login_required
def get_consignment_details():
    conn = None  # Initialize connection variable
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="Money2035",
            database="leads"
        )
        cursor = conn.cursor()

        # ✅ Only fetch consignments where status is 'In Progress'
        cursor.execute("""
            SELECT id, shipper, consignee, commodity, sb_number, total_pkgs, gross_weight, total_volume, status
            FROM cer
            WHERE status = 'In Progress'
        """)

        consignments = cursor.fetchall()
        
        consignment_data = [
            {
                "id": row[0],  
                "shipper": row[1],
                "consignee": row[2],
                "commodity": row[3],
                "sb_number": row[4],
                "total_pkgs": row[5],
                "gross_weight": row[6],
                "total_volume": row[7],
                "status": row[8]
            }
            for row in consignments
        ]

        print("Filtered Consignment Data:", consignment_data)  # ✅ Debugging
        return jsonify(consignment_data)

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Unable to fetch consignment details"}), 500

    finally:
        if conn:
            conn.close()  # ✅ Ensure connection closes




@app.route('/get_containers')
@login_required
def get_containers():
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="Money2035",
            database="leads"
        )
        cursor = conn.cursor()

        # ✅ Only fetch containers where status is 'In Progress'
        cursor.execute("""
            SELECT container_no, applicant_for_survey, size, tare_weight, 
                   payload_capacity, max_gross_weight, status 
            FROM container
            WHERE status = 'In Progress'
        """)

        containers = cursor.fetchall()
        conn.close()

        container_data = []
        for row in containers:
            container_data.append({
                "container_no": row[0],
                "applicant_for_survey": row[1],
                "size": row[2],
                "tare_weight": row[3],
                "payload_capacity": row[4],
                "max_gross_weight": row[5],
                "status": row[6]
            })

        print("Filtered Container Data:", container_data)  # ✅ Debugging
        return jsonify(container_data)

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Unable to fetch container details"}), 500




@app.route('/submit', methods=['POST'])
@login_required
def submit():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get form data
        CertificateNumber = request.form.get('CertificateNumber', '')  
        date = request.form.get('date', None)
        applicant_name = request.form.get('applicantName', '')
        container_number = request.form.get('containerNumber', '')
        size_type = request.form.get('sizeType', '')
        tare_weight = request.form.get('tareWeight', '')
        payload_capacity = request.form.get('payloadCapacity', '')
        declared_total_weight = request.form.get('declaredTotalWeight', '')
        stuffing_comm_date_time = request.form.get('stuffingCommDateTime')
        stuffing_comp_date_time = request.form.get('stuffingCompDateTime')
        seal_number = request.form.get('sealNumber', '')
        port_of_discharge = request.form.get('portOfDischarge', '')
        place_of_stuffing = request.form.get('placeOfStuffing', '')
        cbm = request.form.get('volume', '')
        loading_condition = request.form.get('loadingCondition', '')
        lashing = request.form.get('lashing', '')
        others = request.form.get('others', '')
        weather_condition = request.form.get('weatherCondition', '')
        surveyor_name = request.form.get('surveyorName', '')
        signature = request.form.get('signature', '')
        totalPackages = request.form.get('totalPackages', '')
        gross_weight = request.form.get('grossWeight', '')

        # Retrieve and validate consignment_details JSON
        consignment_details = request.form.get('consignmentDetails', '[]')
        try:
            consignment_details = json.loads(consignment_details)  
            print("Parsed Consignment Details:", consignment_details)
        except json.JSONDecodeError:
            flash("Invalid consignment details format.", "error")
            return redirect(url_for("forms"))

        # ✅ Update the form entry status
        update_form_query = """
            UPDATE form
            SET date = %s, applicant_name = %s, container_number = %s, size_type = %s, tare_weight = %s, 
                payload_capacity = %s, declared_total_weight = %s, stuffing_comm_date_time = %s, 
                stuffing_comp_date_time = %s, seal_number = %s, port_of_discharge = %s, place_of_stuffing = %s, 
                cbm = %s, total_gross_weight = %s, loading_condition = %s, lashing = %s, others = %s, 
                weather_condition = %s, surveyor_name = %s, signature = %s, totalPackages = %s, 
                consignment_details = %s, status = 'Completed'
            WHERE CertificateNumber = %s
        """

        values = [
            date, applicant_name, container_number, size_type, tare_weight, 
            payload_capacity, declared_total_weight, stuffing_comm_date_time, stuffing_comp_date_time,
            seal_number, port_of_discharge, place_of_stuffing, cbm, gross_weight, loading_condition, 
            lashing, others, weather_condition, surveyor_name, signature, 
            totalPackages, json.dumps(consignment_details), CertificateNumber
        ]

        cursor.execute(update_form_query, tuple(values))

        # ✅ Update the container status to 'Completed'
        update_container_query = """
            UPDATE container
            SET status = 'Completed'
            WHERE container_no = %s AND status = 'In Progress'
        """
        cursor.execute(update_container_query, (container_number,))

        # ✅ Update related consignments in `cer` table using `id`
        consignment_ids = [item["id"] for item in consignment_details]  # Extract IDs
        print("Consignment IDs to update:", consignment_ids)  # Debugging

        if consignment_ids:
            format_strings = ','.join(['%s'] * len(consignment_ids))
            update_consignment_query = f"""
                UPDATE cer
                SET status = 'Completed'
                WHERE id IN ({format_strings})
            """
            cursor.execute(update_consignment_query, tuple(consignment_ids))

        # ✅ Commit changes after updating consignments
        conn.commit()

        flash(f"Form submitted successfully! Certificate Number {CertificateNumber} is now Completed.", "success")
        return redirect(url_for("forms"))

    except Exception as e:
        print(f"Error submitting form: {e}")
        flash(f"Error: {e}", "error")
        return redirect(url_for("forms"))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()




@app.route('/get_numbercer')
@login_required
def get_numbercer():
    try:
        with get_db_connection() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                
                # Get the current Year-Month (YYYYMM)
                current_year_month = datetime.now().strftime("%Y%m")

                # 1️⃣ Lock row to prevent race conditions
                cursor.execute("SELECT CertificateNumber FROM cer WHERE status = 'Open' ORDER BY id DESC LIMIT 1 FOR UPDATE")
                last_record = cursor.fetchone()

                print("Fetched existing open certificate:", last_record)  # Debug log

                if last_record and last_record["CertificateNumber"]:
                    new_certificate_number = last_record["CertificateNumber"]  # ✅ Reuse existing open certificate
                else:
                    # 2️⃣ Fetch the last issued certificate number
                    cursor.execute("SELECT CertificateNumber FROM cer ORDER BY id DESC LIMIT 1 FOR UPDATE")
                    last_record = cursor.fetchone()

                    if last_record and last_record["CertificateNumber"]:
                        last_certificate = last_record["CertificateNumber"]
                        last_year_month = last_certificate[:6]  # Extract YYYYMM

                        if last_year_month == current_year_month:
                            last_number = int(last_certificate[6:])  # Extract numeric part
                            next_number = last_number + 1
                        else:
                            next_number = 1  # Reset numbering for new month/year
                    else:
                        next_number = 1  # Start fresh if no records exist

                    # 3️⃣ Generate new Certificate Number
                    new_certificate_number = f"{current_year_month}{str(next_number).zfill(6)}"

                    # Insert new certificate number with status "Open"
                    cursor.execute("INSERT INTO cer (CertificateNumber, status) VALUES (%s, %s)", 
                                   (new_certificate_number, "Open"))
                    conn.commit()

                print("Returning Certificate Number:", new_certificate_number)  # Debugging log
                return jsonify({"certificateNumber": new_certificate_number, "status": "Open"})

    except Exception as e:
        conn.rollback()  # Rollback in case of error
        print(f"Error fetching certificate number: {e}")
        return jsonify({"error": str(e)}), 500  # Return HTTP 500 for errors


@app.route('/submit_cer', methods=['POST'])
@login_required
def submit_cer():
    try:
        # Extract form data
        certificate_number = request.form['CertificateNumber']
        date = request.form['date']
        applicant_name = request.form['applicantName']
        shipper = request.form['shipper']
        consignee = request.form['consignee']
        commodity = request.form['commodity']
        port_of_discharge = request.form['portOfDischarge']
        sb_number = request.form['sb_number']

        # Safely parse numerical fields (handle missing or invalid data)
        def safe_float(value):
            try:
                return float(value) if value.strip() else None  # Return None if empty
            except ValueError:
                return None  # Return None if conversion fails

        quantity = safe_float(request.form['quantity'])
        gross_weight = safe_float(request.form['gross_weight'])
        cf_agent = request.form['cf_agent']
        container_number = request.form['container_number']

        # Process checkbox values (survey measure data)
        survey_data = []
        rows = len(request.form.getlist('marksNos[]'))  # Getting the number of rows submitted
        for i in range(rows):
            marks_no = request.form.getlist('marksNos[]')[i].strip() if request.form.getlist('marksNos[]')[i].strip() else None
            no_of_pkgs = int(request.form.getlist('noOfPkgs[]')[i]) if request.form.getlist('noOfPkgs[]')[i].strip() else None
            length = safe_float(request.form.getlist('length[]')[i])
            breadth = safe_float(request.form.getlist('breadth[]')[i])
            height = safe_float(request.form.getlist('height[]')[i])
            volume_unit = safe_float(request.form.getlist('volumeUnit[]')[i])

            # Calculate volume and volume in cubic meters
            volume = length * breadth * height if all([length, breadth, height]) else None
            volume_cum = volume_unit * volume if volume and volume_unit else None

            # Append survey data
            survey_data.append({
                'marks_no': marks_no,
                'no_of_pkgs': no_of_pkgs,
                'length': length,
                'breadth': breadth,
                'height': height,
                'volume': volume,
                'volume_unit': volume_unit,
                'volume_cum': volume_cum
            })

        # Calculate total volume and total packages
        total_volume = sum(row['volume'] for row in survey_data if row['volume'] is not None)
        total_pkgs = sum(row['no_of_pkgs'] for row in survey_data if row['no_of_pkgs'] is not None)

        # Serialize survey data as JSON
        import json
        survey_data_json = json.dumps(survey_data)

        # Connect to the database
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Check if the certificate number already exists
                cursor.execute("SELECT CertificateNumber FROM cer WHERE CertificateNumber = %s", (certificate_number,))
                exists = cursor.fetchone()

                if exists:
                    # Update the existing record
                    update_query = """
                        UPDATE cer SET 
                            date = %s, applicant_name = %s, shipper = %s, consignee = %s, 
                            commodity = %s, port_of_discharge = %s, sb_number = %s, quantity = %s, 
                            gross_weight = %s, cf_agent = %s, container_number = %s, 
                            total_volume = %s, total_pkgs = %s, survey_data = %s, status = 'In Progress'
                        WHERE CertificateNumber = %s
                    """
                    cursor.execute(update_query, (
                        date, applicant_name, shipper, consignee, commodity, port_of_discharge,
                        sb_number, quantity, gross_weight, cf_agent, container_number,
                        total_volume, total_pkgs, survey_data_json, certificate_number
                    ))
                else:
                    flash("Error: Certificate number not found in database.", "error")
                    return redirect(url_for('forms'))

                conn.commit()

        flash('Form submitted successfully!', 'success')
        return redirect(url_for('forms'))

    except Exception as e:
        print(f"Error: {e}")
        flash(f'An error occurred while submitting the form. Error: {e}', 'error')
        return redirect(url_for('forms'))


@app.route('/empadd')
def empadd():
    return render_template('empadd.html')

# Route to fetch all employees
# Fetch all employees
@app.route('/employees', methods=['GET'])
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees')
    employees = cursor.fetchall()
    conn.close()
    
    print("Fetched Employees:", employees)  # Debugging line
    return jsonify(employees)  # Returns JSON data

# Route to add a new employee

@app.route('/add_employee', methods=['POST'])
def add_employee():
    conn = None
    cursor = None

    try:
        print("Form Data Received:", request.form)  # Debugging: Print all form data

        # Extract form data
        empId = request.form.get('empId')
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        role = request.form.get('role')  # Ensure this matches the name attribute in the form
        username = request.form.get('username')
        password = request.form.get('password')

        # Debugging: Print individual form fields
        print("empId:", empId)
        print("name:", name)
        print("phone:", phone)
        print("address:", address)
        print("role:", role)
        print("username:", username)
        print("password:", password)

        # Validate all fields
        if not all([empId, name, phone, address, role, username, password]):
            return jsonify({'error': 'Missing form fields!'}), 400

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()
        conn.begin()

        # Insert into employees table
        cursor.execute('''
            INSERT INTO employees (empId, name, phone, address, role, username, password)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (empId, name, phone, address, role, username, hashed_password))

        # Insert into users table
        cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
        ''', (username, hashed_password, role))

        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'Employee added successfully!'}), 201

    except Exception as e:
        # Rollback in case of error
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Route to edit employees (bulk update)
@app.route('/edit_employee', methods=['POST'])
def edit_employee():
    try:
        data = request.get_json()  # Expecting a list of employees
        conn = get_db_connection()
        cursor = conn.cursor()

        for emp in data:
            empId = emp['empId']
            name = emp['name']
            phone = emp['phone']
            address = emp['address']
            username = emp['username']
            password = emp['password']

            cursor.execute('''
                UPDATE employees
                SET name = %s, phone = %s, address = %s, username = %s, password = %s
                WHERE empId = %s
            ''', (name, phone, address, username, password, empId))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Employees updated successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to delete employees
@app.route('/delete_employees', methods=['POST'])
def delete_employees():
    try:
        data = request.get_json()
        employee_ids = data.get('ids', [])

        if not employee_ids:
            return jsonify({'error': 'No employees selected'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Correct SQL query using tuple formatting
        query = 'DELETE FROM employees WHERE empId IN ({})'.format(','.join(['%s'] * len(employee_ids)))
        cursor.execute(query, tuple(employee_ids))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'message': 'Employees deleted successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
