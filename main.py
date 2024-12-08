from flask import Flask, render_template, request, redirect, flash,session
from flask import Flask, make_response, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from flask import url_for
import pandas as pd
import json
import io
from fpdf import FPDF
from flask import send_file
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flash messages



# Function to establish a DB connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="project_management"
        )
        if connection.is_connected():
            return connection
    except Error as e:
        app.logger.error(f"Database connection failed: {e}")
        return None

# Route to render the login page
@app.route('/')
def home():
    return render_template('login.html')

# Route to handle login form submission
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    # Check if the email exists and the password matches
    if email == "keyur@admin.com" and password == "keyur@password":
        session['user'] = email  # Store user in session
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid email or password. Please try again.', 'danger')
        return redirect(url_for('home'))




# Route for a protected dashboard page
@app.route('/dashboard')
def dashboard():
    connection = None
    try:
        connection = get_db_connection()
        if not connection:
            app.logger.error("Database connection failed!")
            return render_template('error.html', error_message="Unable to connect to the database. Please try again later.")

        cursor = connection.cursor(dictionary=True)

        # Fetch data from the projects table
        cursor.execute("SELECT * FROM projects")
        projects = cursor.fetchall()

        # Fetch members for each project
        cursor.execute("SELECT * FROM members")
        members = cursor.fetchall()

        # Group members by group_number
        grouped_members = {}
        for member in members:
            group = member.get('group_number')
            if group not in grouped_members:
                grouped_members[group] = []
            grouped_members[group].append(member)

        return render_template('data_table.html', projects=projects, grouped_members=grouped_members)
    except Error as e:
        app.logger.error(f"Error fetching project data: {e}")
        return render_template('error.html', error_message="An error occurred while fetching project data."),url_for('logout')
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()



# Route to logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))





    

# Custom filter to format datetime
@app.template_filter('format_datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    if isinstance(value, datetime):
        return value.strftime(format)  # Format if it's already a datetime object
    elif isinstance(value, str):
        try:
            # Try to parse the string into a datetime object
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return value.strftime(format)
        except ValueError:
            return 'Invalid Date'  # If parsing fails, return an error message
    return 'N/A'  # Return 'N/A' if the value is None or not in a valid format



# Route for inserting a new member
@app.route('/insert_member', methods=['POST'])
def insert_member():
    try:
        # Fetch form data
        group_number = request.form.get('groupNumber')
        name = request.form.get('name')
        roll_no = request.form.get('rollNo')
        contact = request.form.get('contact')

        if not group_number or not name or not roll_no or not contact:
            flash('Invalid member data. Please check your inputs.', 'danger')
            return redirect('/')

        connection = get_db_connection()
        if not connection:
            flash('Database connection failed!', 'danger')
            return redirect('/')

        cursor = connection.cursor()
        # Insert data into the members table
        cursor.execute(
            "INSERT INTO members (group_number, name, roll_no, contact) VALUES (%s, %s, %s, %s)",
            (group_number, name, roll_no, contact)
        )
        connection.commit()
        flash('Member added successfully!', 'success')
    except Error as e:
        app.logger.error(f"Error inserting member: {e}")
        if connection.is_connected():
            connection.rollback()
        flash('An error occurred while adding the member.', 'danger')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    return redirect('/dashboard')



# Route to insert project data
@app.route('/insert_project', methods=['POST'])
def insert_project():
    try:
        # Fetch form data
        group_number = request.form.get('groupNumber')
        project_name = request.form.get('projectName')
        member_count = int(request.form.get('memberCount', 0))
        frontend = request.form.get('frontend')
        backend = request.form.get('backend')
        
        # Handle deliverables (checkbox values)
        deliverables = []
        if request.form.get('ppt'):
            deliverables.append('PPT')
        if request.form.get('wordfile'):
            deliverables.append('Word File')
        if request.form.get('database'):
            deliverables.append('Database')
        deliverables = ', '.join(deliverables)  # Convert list to a comma-separated string
        
        status = request.form.get('status')
        notes = request.form.get('msg')
        submission_datetime = request.form.get('datetime')

        # Print the collected data for debugging purposes
        print(f"Group Number: {group_number}, Project Name: {project_name}, Deliverables: {deliverables}, Notes: {notes}, Submission Date/Time: {submission_datetime}")
        
        # Validate project data
        if not group_number or not project_name or member_count <= 0:
            flash('Invalid project data. Please check your inputs.', 'danger')
            return redirect('/dashboard')

        connection = get_db_connection()
        if not connection:
            flash('Database connection failed!', 'danger')
            return redirect('/')

        cursor = connection.cursor()

        # Insert data into the projects table
        cursor.execute(
            """
            INSERT INTO projects 
            (group_number, project_name, member_count, frontend, backend, deliverables, status, notes, submission_datetime)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (group_number, project_name, member_count, frontend, backend, deliverables, status, notes, submission_datetime)
        )

        # Insert data into the members table
        for i in range(1, member_count + 1):
            name = request.form.get(f'member_name_{i}')
            roll_no = request.form.get(f'rollno_{i}')
            contact = request.form.get(f'contact_{i}')
            
            if name and roll_no and contact:  # Validate member data
                cursor.execute(
                    """
                    INSERT INTO members (group_number, name, roll_no, contact)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (group_number, name, roll_no, contact)
                )
            print(f"Member {i} inserted: Name: {name}, Roll No: {roll_no}, Contact: {contact}")
        connection.commit()
        flash('Project and members added successfully!', 'success')
    except Error as e:
        app.logger.error(f"Error inserting project: {e}")
        if connection.is_connected():
            connection.rollback()
        flash('An error occurred while adding the project.', 'danger')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    return redirect('/dashboard')



# Route to edit project data
@app.route('/edit_project/<int:group_number>', methods=['GET', 'POST'])
def edit_project(group_number):
    try:
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed!', 'danger')
            return redirect('/')

        cursor = connection.cursor(dictionary=True)

        if request.method == 'POST':
            # Handle form submission for editing
            project_name = request.form.get('projectName')
            member_count = int(request.form.get('memberCount', 0))
            frontend = request.form.get('frontend')
            backend = request.form.get('backend')
            status = request.form.get('status')
            notes = request.form.get('msg')
            submission_datetime = request.form.get('datetime')

            # Handle deliverables
            deliverables = []
            if request.form.get('ppt'):
                deliverables.append('PPT')
            if request.form.get('wordfile'):
                deliverables.append('Word File')
            if request.form.get('database'):
                deliverables.append('Database')
            deliverables = ', '.join(deliverables)

            # Update the project
            cursor.execute(
                """
                UPDATE projects 
                SET project_name = %s, member_count = %s, frontend = %s, backend = %s,
                    deliverables = %s, status = %s, notes = %s, submission_datetime = %s
                WHERE group_number = %s
                """,
                (project_name, member_count, frontend, backend, deliverables, status, notes, submission_datetime, group_number)
            )

            # Update members
            cursor.execute("DELETE FROM members WHERE group_number = %s", (group_number,))
            for i in range(1, member_count + 1):
                name = request.form.get(f'member_name_{i}')
                roll_no = request.form.get(f'rollno_{i}')
                contact = request.form.get(f'contact_{i}')

                if name and roll_no and contact:
                    cursor.execute(
                        """
                        INSERT INTO members (group_number, name, roll_no, contact)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (group_number, name, roll_no, contact)
                    )

            connection.commit()
            flash('Project updated successfully!', 'success')
            return redirect('/dashboard')

        # Handle GET request to fetch project data
        cursor.execute("SELECT * FROM projects WHERE group_number = %s", (group_number,))
        project = cursor.fetchone()

        cursor.execute("SELECT * FROM members WHERE group_number = %s", (group_number,))
        members = cursor.fetchall()

        if not project:
            flash('Project not found!', 'danger')
            return redirect('/dashboard')

        # Ensure deliverables is not None
        project['deliverables'] = project['deliverables'] or ''

        return render_template('edit_project.html', project=project, members=members)
    except Error as e:
        app.logger.error(f"Error editing project: {e}")
        if connection.is_connected():
            connection.rollback()
        flash('An error occurred while editing the project.', 'danger')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    return redirect('/dashboard')



# Route to delete a project
@app.route('/delete_project/<int:group_number>', methods=['POST'])
def delete_project(group_number):
    try:
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed!', 'danger')
            return redirect('/')

        cursor = connection.cursor()

        cursor.execute("DELETE FROM projects WHERE group_number = %s", (group_number,))
        cursor.execute("DELETE FROM members WHERE group_number = %s", (group_number,))
        connection.commit()
        flash('Project deleted successfully!', 'success')
    except Error as e:
        app.logger.error(f"Error deleting project: {e}")
        if connection.is_connected():
            connection.rollback()
        flash('An error occurred while deleting the project.', 'danger')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    return redirect('/dashboard')



# # Route to display project data
# @app.route('/view-data')
# def display_data():
    try:
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed!', 'danger')
            return redirect('/')

        cursor = connection.cursor(dictionary=True)

        # Fetch data from the projects table
        cursor.execute("SELECT * FROM projects")
        projects = cursor.fetchall()

        # Fetch members for each project
        cursor.execute("SELECT * FROM members")
        members = cursor.fetchall()

        # Group members by group_number
        grouped_members = {}
        for member in members:
            group = member['group_number']
            if group not in grouped_members:
                grouped_members[group] = []
            grouped_members[group].append(member)

        return render_template('data_table.html', projects=projects, grouped_members=grouped_members)
    except Error as e:
        app.logger.error(f"Error fetching project data: {e}")
        flash('An error occurred while fetching projects.', 'danger')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    return redirect('/')



# Route to view members for a specific project
@app.route('/members/<group_number>')
def view_members(group_number):
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect('/')
    
    try:
        cursor = connection.cursor()
        # Fetch members for a specific project
        cursor.execute("SELECT * FROM members WHERE group_number = %s", (group_number,))
        members = cursor.fetchall()
        return render_template('members_table.html', group_number=group_number, members=members)
    except Error as e:
        app.logger.error(f"Error fetching members: {e}")
        flash('An error occurred while fetching members.', 'danger')
        return redirect('/dashboard')
    finally:
        cursor.close()
        connection.close()



# Route to export project data
@app.route('/export/<format>', methods=['GET'])
def export_data(format):
    connection = None
    cursor = None
    try:
        # Validate format first
        if format not in ['csv', 'json', 'pdf']:
            flash('Invalid export format!', 'danger')
            return redirect(url_for('index'))
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection failed!', 'danger')
            return redirect(url_for('index'))
        
        cursor = connection.cursor(dictionary=True)
        
        # Fetch data
        cursor.execute("SELECT * FROM projects")
        projects = cursor.fetchall()
        
        cursor.execute("SELECT * FROM members")
        members = cursor.fetchall()
        
        # Export data based on format
        if format == 'csv':
            # Convert projects and members to DataFrames
            projects_df = pd.DataFrame(projects)
            members_df = pd.DataFrame(members)
            
            # Create a CSV output
            output = io.StringIO()
            
            # Write both DataFrames to the output with a separator
            output.write("--- Projects ---\n")
            projects_df.to_csv(output, index=False)
            output.write("\n--- Members ---\n")
            members_df.to_csv(output, index=False)
            
            # Get the CSV content
            csv_output = output.getvalue()
            output.close()
            
            # Create response
            response = make_response(csv_output)
            response.headers["Content-Disposition"] = "attachment; filename=project_data.csv"
            response.headers["Content-Type"] = "text/csv"
            return response
        
        elif format == 'json':
            # Use pandas to convert to JSON
            projects_df = pd.DataFrame(projects)
            members_df = pd.DataFrame(members)
            
            # Create a dictionary to hold both DataFrames
            json_data = {
                "projects": projects_df.to_dict(orient='records'),
                "members": members_df.to_dict(orient='records')
            }
            
            # Create response
            response = make_response(json.dumps(json_data, indent=2))
            response.headers["Content-Disposition"] = "attachment; filename=project_data.json"
            response.headers["Content-Type"] = "application/json"
            return response

        elif format == 'pdf':
           # Create a PDF instance
             from itertools import zip_longest  # To handle lists of different lengths

        # Create a PDF instance
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Set up table header
        pdf.set_font("Arial", style="B", size=14)
        pdf.cell(0, 10, txt="Projects and Members Data", ln=True, align='C')
        pdf.ln(5)

        pdf.set_font("Arial", size=12)

        # Define table headers
        headers = ['Name', 'Roll Number', 'Contact', 'Project Name', 'Group Number']
        column_width = pdf.w / len(headers)  # Dynamically calculate column width

        # Add headers to the table
        for header in headers:
            pdf.cell(column_width, 10, header, border=1, align='C')
        pdf.ln()

        # Combine data from projects and members
        table_data = []
        for member, project in zip_longest(members, projects, fillvalue={}):
            row = {
                "name": member.get("name", ""),
                "rollnum": member.get("rollnum", ""),
                "contact": member.get("contact", ""),
                "projectname": project.get("projectname", ""),
                "groupnumber": project.get("groupnumber", "")
            }
            table_data.append(row)

        # Add rows to the table
        for row in table_data:
            pdf.cell(column_width, 10, str(row['name']), border=1, align='C')
            pdf.cell(column_width, 10, str(row['rollnum']), border=1, align='C')
            pdf.cell(column_width, 10, str(row['contact']), border=1, align='C')
            pdf.cell(column_width, 10, str(row['projectname']), border=1, align='C')
            pdf.cell(column_width, 10, str(row['groupnumber']), border=1, align='C')
            pdf.ln()

        # Output PDF to a byte stream
        pdf_output = pdf.output(dest='S').encode('latin1')  # Use 'S' to output to a string

        # Create response
        response = make_response(pdf_output)
        response.headers["Content-Disposition"] = "attachment; filename=projects_and_members_data.pdf"
        response.headers["Content-Type"] = "application/pdf"
        return response

    except Exception as e:
        app.logger.error(f"Error exporting data: {e}")
        flash('An error occurred while exporting the data.', 'danger')
        print(e)
        return redirect('/dashboard')
    
    finally:
        # Ensure proper cleanup
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()





# Function to export all projects and their members
def export_all_projects_pdf():
    """
    Generate a PDF export for all projects and their members
    
    :return: PDF file containing all project details
    """
    try:
        # Establish database connection
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Fetch all projects with their members
        cursor.execute("""
            SELECT p.*, 
                   GROUP_CONCAT(
                       CONCAT(m.name, ' (', m.roll_no, ') - ', m.contact) 
                       SEPARATOR ' | '
                   ) AS member_details
            FROM projects p
            LEFT JOIN members m ON p.group_number = m.group_number
            GROUP BY p.group_number
            ORDER BY p.group_number
        """)
        projects = cursor.fetchall()
        
        # Close database connection
        cursor.close()
        connection.close()
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        
        # Add title with current date
        current_date = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph("Project Details Report", title_style))
        elements.append(Paragraph(f"Generated on: {current_date}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Prepare table data
        table_data = [
            [
                'Group Number', 
                'Project Name', 
                # 'Member Count', 
                # 'Frontend', 
                # 'Backend', 
                'Deliverables', 
                'Status', 
                'Members (Name, Roll No, Contact)',
                'Submission Date'
            ]
        ]
        
        # Add project data to table
        for project in projects:
            table_data.append([
                str(project['group_number']),
                project['project_name'],
                # str(project['member_count']),
                # project['frontend'],
                # project['backend'],
                project['deliverables'],
                project['status'],
                project['member_details'] or 'No members',
                str(project['submission_datetime'])
            ])
        
        # Create table
        table = Table(table_data, repeatRows=1, splitByRow=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('WORDWRAP', (0,0), (-1,-1), 1)
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        
        # Move buffer position to the beginning
        buffer.seek(0)
        
        # Generate filename
        filename = f"All_Projects_Report_{current_date}.pdf"
        
        return send_file(
            buffer, 
            mimetype='application/pdf', 
            as_attachment=True, 
            download_name=filename
        )
    
    except mysql.connector.Error as e:
        app.logger.error(f"Database error in PDF export: {e}")
        flash('Failed to export PDF. Database error occurred.', 'danger')
        return redirect('/dashboard')
    except Exception as e:
        app.logger.error(f"Unexpected error in PDF export: {e}")
        flash('An unexpected error occurred during PDF export.', 'danger')
        return redirect('/dashboard')

# Route to trigger PDF export for all projects
@app.route('/export_all_projects_pdf')
def export_all_projects_route():
    return export_all_projects_pdf()


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
