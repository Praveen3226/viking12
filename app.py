from flask import Flask, render_template, request, redirect, url_for ,flash,jsonify,json
import pymysql
from mysql.connector import Error
from datetime import datetime
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages

# Function to get database connection
def get_db_connection():
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="Money2035",
        database="leads"
    )
    return connection

# User authentication data (as before)
users = {
    'admin': {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
    'emp': {'username': 'emp', 'password': 'emp123', 'role': 'emp'},
}





@app.route('/')
def index():
    return render_template('index.html')



@app.route('/reportFCL')
def reportFCL():
    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Fetch relevant data from the `form` table
        cursor.execute("SELECT CertificateNumber, date, applicant_name, container_number FROM form")
        form = cursor.fetchall()

        conn.close()

        # Pass the data to the report.html template
        return render_template('reportFCL.html', form=form)
    except Error as e:
        print(f"Error: {e}")
        flash('An error occurred while fetching the reports. Please try again.', 'error')
        return redirect(url_for('reportFCL'))
    
@app.route('/reportFCL1/<int:CertificateNumber>')
def report(CertificateNumber):
    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Fetch all reports from the `form` table
        cursor.execute("SELECT * FROM form WHERE CertificateNumber = %s", (CertificateNumber,))
        form = cursor.fetchall()

        conn.close()
        
        # Pass the fetched data to the report.html template
        return render_template('reportFCL1.html', form=form)
    except Error as e:
        print(f"Error: {e}")
        flash('An error occurred while fetching the reports. Please try again.', 'error')
        return redirect(url_for('reportFCL'))
    
@app.route('/reportCER')
def reportCER():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Fetch all reports
        cursor.execute("SELECT CertificateNumber, date, applicant_name, shipper, consignee, total_pkgs FROM cer")
        cer_data = cursor.fetchall()

        conn.close()

        return render_template('reportCER.html', cer_data=cer_data)
    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while fetching the reports.', 'error')
        return redirect(url_for('reportCER'))

@app.route('/reportCER1/<int:CertificateNumber>')
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
def reportContainer():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Fetch all container records
        cursor.execute("SELECT CertificateNumber, date, applicant_for_survey, date_of_inspection, container_no FROM container")
        container_data = cursor.fetchall()

        conn.close()

        return render_template('reportContainer.html', container_data=container_data)
    except Exception as e:
        print(f"Error: {e}")
        flash('An error occurred while fetching the container records.', 'error')
        return redirect(url_for('reportContainer'))
    

@app.route('/reportContainer1/<int:CertificateNumber>')
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
def admindash():
    return render_template('admindash.html')

@app.route('/cont')
def cont():
    return render_template('cont.html')

@app.route('/contrpt')
def contrpt():
    return render_template('contrpt.html')


    

@app.route('/empdash')
def empdash():
    return render_template('empdash.html')

@app.route('/certificate')
def certificate():
    return render_template('certificate.html')

@app.route('/container')
def container():
    return render_template('container.html')

@app.route('/add_survey', methods=['POST'])
def add_survey():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

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

        # Check for empty required fields
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
                return redirect(url_for('forms'))

        # Check for duplicate CertificateNumber
        cursor.execute("SELECT COUNT(*) FROM container WHERE CertificateNumber = %s", (CertificateNumber,))
        if cursor.fetchone()['COUNT(*)'] > 0:
            flash(f"Certificate Number {CertificateNumber} already exists!", "error")
            return redirect(url_for('forms'))

        # Insert data into the database
        insert_query = """
            INSERT INTO container (
                CertificateNumber, date, applicant_for_survey, date_of_inspection, container_no, place_of_inspection,
                type, size, tare_weight, csc_no, payload_capacity, year_of_manufacture, max_gross_weight,
                remarks, surveyor
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            CertificateNumber, date, applicant_for_survey, date_of_inspection, container_no, place_of_inspection,
            container_type, size, tare_weight, csc_no, payload_capacity, year_of_manufacture, max_gross_weight,
            remarks, surveyor
        )

        cursor.execute(insert_query, values)
        conn.commit()

        flash('Survey added successfully!', 'success')
        return redirect(url_for('forms'))

    except Exception as e:
        print(f"❌ Error: {type(e).__name__} - {e}")
        flash(f'Error: {e}', 'error')
        return redirect(url_for('forms'))

    finally:
        cursor.close()
        conn.close()
 # Redirect to show error flash message







@app.route('/emp')
def emp():
    return render_template('emp.html')

@app.route('/employee')
def employee():
    return render_template('employee.html')

@app.route('/empadd')
def empadd():
    return render_template('empadd.html')

@app.route('/forms')
def forms():
    return render_template('forms.html')

@app.route('/certificatert')
def certificatert():
    return render_template('certificatert.html')

@app.route('/certificaterpt')
def certificaterpt():
    return render_template('certificaterpt.html')

@app.route('/containerrpt')
def containerrpt():
    return render_template('containerrpt.html')

# Fetch the latest certificate number
@app.route('/get_number')
def get_number():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT CertificateNumber FROM form ORDER BY id DESC LIMIT 1")
        last_record = cursor.fetchone()

        if last_record:
            last_number = int(last_record[0][6:])  # Access the first element (CertificateNumber)
            next_number = last_number + 1
        else:
            next_number = 1  # Start if no record exists

        current_year_month = datetime.now().strftime("%Y%m")
        new_certificate_number = f"{current_year_month}{str(next_number).zfill(6)}"

        return jsonify({"certificateNumber": new_certificate_number})

    except Exception as e:
        print(f"Error fetching certificate number: {e}")
        return jsonify({"error": str(e)})

    finally:
        cursor.close()
        conn.close()


@app.route('/get_containers')
def get_containers():
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="Money2035",
            database="leads"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT container_no, applicant_for_survey, size, tare_weight, payload_capacity, max_gross_weight FROM container")
        containers = cursor.fetchall()
        conn.close()

        # Format the data to be returned as JSON
        container_data = []
        for row in containers:
            container_data.append({
                "container_no": row[0],
                "applicant_for_survey": row[1],
                "size": row[2],
                "tare_weight": row[3],
                "payload_capacity": row[4],
                "max_gross_weight": row[5],
            })
        return jsonify(container_data)
    
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Unable to fetch container details"}), 500

@app.route('/get_consignment_details')
def get_consignment_details():
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="Money2035",
            database="leads"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT shipper, consignee, commodity, sb_number, total_pkgs,total_volume FROM cer")
        consignments = cursor.fetchall()
        conn.close()

        # Format the data to be returned as JSON
        consignment_data = []
        for row in consignments:
            consignment_data.append({
                "shipper": row[0],
                "consignee": row[1],
                "commodity": row[2],
                "sb_number": row[3],
                "total_pkgs":row[4],
                "total_volume": row[5]
            })
        return jsonify(consignment_data)

    except pymysql.MySQLError as e:
        print(f"Database error: {e}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500



@app.route('/submit', methods=['POST'])
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

        stuffing_comm_date_time = request.form.get('stuffingCommDateTime', None)
        stuffing_comp_date_time = request.form.get('stuffingCompDateTime', None)
        seal_number = request.form.get('sealNumber', '')
        port_of_discharge = request.form.get('portOfDischarge', '')
        place_of_stuffing = request.form.get('placeOfStuffing', '')
        cbm = request.form.get('cbm', '')
        loading_condition = request.form.get('loadingCondition', '')
        lashing = request.form.get('lashing', '')
        others = request.form.get('others', '')
        weather_condition = request.form.get('weatherCondition', '')
        surveyor_name = request.form.get('surveyorName', '')
        signature = request.form.get('signature', '')

        # Convert JSON string to actual JSON object
        consignment_details = request.form.get('consignmentDetails', None)
        if consignment_details:
            try:
                consignment_details = json.loads(consignment_details)  # Ensure valid JSON
            except json.JSONDecodeError:
                flash("Invalid consignment details format.", "error")
                return redirect(url_for("forms"))
        else:
            consignment_details = None

        # Convert empty values and date-time fields
        date = date if date else None
        stuffing_comm_date_time = stuffing_comm_date_time if stuffing_comm_date_time else None
        stuffing_comp_date_time = stuffing_comp_date_time if stuffing_comp_date_time else None

        # Debugging: Print formatted values
        values = [
            CertificateNumber, date, applicant_name, container_number, size_type, tare_weight, 
            payload_capacity, declared_total_weight, stuffing_comm_date_time, stuffing_comp_date_time, 
            seal_number, port_of_discharge, place_of_stuffing, cbm, loading_condition, 
            lashing, others, weather_condition, surveyor_name, signature, 
            json.dumps(consignment_details) if consignment_details else None  # Convert JSON to string
        ]

        print("Formatted Values:", values)  # Debugging print

        # Prepare the query to insert data into the form table
        insert_query = """
            INSERT INTO form (
                CertificateNumber, date, applicant_name, container_number, size_type, tare_weight, 
                payload_capacity, declared_total_weight, stuffing_comm_date_time, stuffing_comp_date_time, 
                seal_number, port_of_discharge, place_of_stuffing, cbm, loading_condition, 
                lashing, others, weather_condition, surveyor_name, signature, consignment_details
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Execute the query
        cursor.execute(insert_query, tuple(values))

        conn.commit()
        flash("Form submitted successfully!", "success")
        return redirect(url_for("forms"))

    except Exception as e:
        print(f"Error submitting form: {e}")
        flash(f"Error: {e}", "error")
        return redirect(url_for("forms"))

    finally:
        cursor.close()
        conn.close()

def get_last_certificate_number():
    try:
        # Establish a connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query to get the last certificate number
        cursor.execute("SELECT CertificateNumber FROM cer ORDER BY id DESC LIMIT 1")
        last_record = cursor.fetchone()

        if last_record:
            return last_record[0]
        else:
            return None  # No records found

    except Exception as e:
        print(f"Error fetching last certificate number: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def generate_certificate_number():
    last_certificate_number = get_last_certificate_number()

    if last_certificate_number:
        # Extract the numeric part and increment it
        last_number = int(last_certificate_number[6:])  # Assuming last 6 digits are the number
        next_number = last_number + 1
    else:
        # Start from the first certificate number if no records exist
        next_number = 1

    # Format the new certificate number (e.g., 202502000001 for February 2025)
    current_year_month = datetime.now().strftime("%Y%m")
    new_certificate_number = f"{current_year_month}{str(next_number).zfill(6)}"

    return new_certificate_number

@app.route('/get_last_certificate_number', methods=['GET'])
def get_last_certificate_number_api():
    try:
        certificate_number = generate_certificate_number()
        return {'certificateNumber': certificate_number}, 200
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/submit_cer', methods=['POST'])
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
                return float(value)
            except ValueError:
                return 0.0

        quantity = safe_float(request.form['quantity'])
        gross_weight = safe_float(request.form['gross_weight'])
        
        cf_agent = request.form['cf_agent']
        container_number = request.form['container_number']

        # Process checkbox values (survey measure data)
        survey_data = []
        rows = len(request.form.getlist('marksNos[]'))  # Getting the number of rows submitted
        for i in range(rows):
            marks_no = request.form.getlist('marksNos[]')[i]
            no_of_pkgs = int(request.form.getlist('noOfPkgs[]')[i]) if request.form.getlist('noOfPkgs[]')[i] else 0
            length = safe_float(request.form.getlist('length[]')[i])
            breadth = safe_float(request.form.getlist('breadth[]')[i])
            height = safe_float(request.form.getlist('height[]')[i])
            volume_unit = safe_float(request.form.getlist('volumeUnit[]')[i])
            
            # Calculate volume and volume in cubic meters
            volume = length * breadth * height
            volume_cum = volume_unit * volume

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
        total_volume = sum([row['volume'] for row in survey_data])
        total_pkgs = sum([row['no_of_pkgs'] for row in survey_data])

        # Database insertion logic
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert data into the cer table
        insert_query = """
            INSERT INTO cer (
                CertificateNumber, date, applicant_name, shipper, consignee, commodity, 
                port_of_discharge, sb_number, quantity, gross_weight, cf_agent, container_number,
                total_volume, total_pkgs, survey_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Serialize survey data as a string for storage in a single column
        import json
        survey_data_json = json.dumps(survey_data)

        # Execute the insert query
        cursor.execute(insert_query, (
            certificate_number, date, applicant_name, shipper, consignee, commodity, 
            port_of_discharge, sb_number, quantity, gross_weight, cf_agent, container_number,
            total_volume, total_pkgs, survey_data_json
        ))

        conn.commit()  # Commit the transaction
        cursor.close()
        conn.close()

        flash('Form submitted successfully!', 'success')
        return redirect(url_for('forms'))  # Redirect to the forms page after successful submission

    except Exception as e:
        print(f"Error: {e}")
        flash(f'An error occurred while submitting the form. Error: {e}', 'error')
        return redirect(url_for('forms'))  # Redirect to show error flash message



        
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if user exists and password matches
        if username in users and users[username]['password'] == password:
            # Redirect to appropriate dashboard based on role
            if users[username]['role'] == 'admin':
                return redirect(url_for('admindash'))
            elif users[username]['role'] == 'emp':
                return redirect(url_for('empdash'))
        
        # If user authentication fails, reload login page with error message
        flash('Invalid username or password. Please try again.', 'error')

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
