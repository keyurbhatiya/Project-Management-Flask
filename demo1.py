# from flask import Flask, render_template, request
# import mysql.connector

# app = Flask(__name__)

# # Function to fetch filtered data from the database
# def fetch_filtered_data(group_number, search_query=None):
#     # Establish the database connection
#     connection = mysql.connector.connect(
#         host="localhost",
#         user="root",  # Replace with your MySQL username
#         password="",  # Replace with your MySQL password
#         database="project_management"  # Replace with your database name
#     )

#     # Create a cursor object to interact with the database
#     cursor = connection.cursor()

#     # Base query to fetch data from the projects table
#     query = "SELECT * FROM projects WHERE group_number = %s"
#     params = [group_number]

#     # If a search query exists, add it to the query to filter by project name or member-related fields
#     if search_query:
#         query += " AND (project_name LIKE %s OR frontend LIKE %s OR backend LIKE %s)"
#         params += ['%' + search_query + '%'] * 3

#     # Execute query for projects
#     cursor.execute(query, tuple(params))
#     projects = cursor.fetchall()

#     # Fetch data from the members table, filtering by the group number and search query if provided
#     member_query = "SELECT * FROM members WHERE project_id IN (SELECT id FROM projects WHERE group_number = %s)"
#     if search_query:
#         member_query += " AND (name LIKE %s OR roll_no LIKE %s)"
#         params_member = ['%' + search_query + '%'] * 2
#         cursor.execute(member_query, [group_number] + params_member)
#     else:
#         cursor.execute(member_query, [group_number])

#     members = cursor.fetchall()

#     # Close the cursor and connection
#     cursor.close()
#     connection.close()

#     return projects, members
# @app.route('/')
# def home():
#     return render_template('group_data.html')

# @app.route('/group/<group_number>', methods=['GET', 'POST'])
# def group_data(group_number):
#     # Get search query from the form
#     search_query = request.form.get('search_query', '')  # Default to empty if no search term

#     # Fetch filtered data based on the search query
#     projects, members = fetch_filtered_data(group_number, search_query)

#     # Render the results in the HTML template
#     return render_template('group_data.html', group_number=group_number, projects=projects, members=members, search_query=search_query)

# if __name__ == '__main__':
#     app.run(debug=True)


'''

@app.route('/dashboard')
def dashboard():
    
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

'''



''' using database to login '''
# def login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']

#         connection = get_db_connection()
#         if connection:
#             cursor = connection.cursor()
#             cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
#             user = cursor.fetchone()

#             # Debugging: Print the stored hash and entered password
#             print(f"Stored hash: {user[3]}")  # The password hash
#             print(f"Entered password: {password}")  # The password entered by the user

#             if user and check_password_hash(user[3], password):  # Compare hashed password with entered password
#                 session['user'] = user[1]  # Store user in session (user[1] might be the username)
#                 flash('Login successful!', 'success')
#                 return redirect(url_for('dashboard'))
#             else:
#                 flash('Invalid email or password. Please try again.', 'danger')
#         else:
#             flash('Database connection failed!', 'danger')

#     return render_template('login.html')