from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

# Function to fetch filtered data from the database
def fetch_filtered_data(group_number, search_query=None):
    # Establish the database connection
    connection = mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="",  # Replace with your MySQL password
        database="project_management"  # Replace with your database name
    )

    # Create a cursor object to interact with the database
    cursor = connection.cursor()

    # Base query to fetch data from the projects table
    query = "SELECT * FROM projects WHERE group_number = %s"
    params = [group_number]

    # If a search query exists, add it to the query to filter by project name or member-related fields
    if search_query:
        query += " AND (project_name LIKE %s OR frontend LIKE %s OR backend LIKE %s)"
        params += ['%' + search_query + '%'] * 3

    # Execute query for projects
    cursor.execute(query, tuple(params))
    projects = cursor.fetchall()

    # Fetch data from the members table, filtering by the group number and search query if provided
    member_query = "SELECT * FROM members WHERE project_id IN (SELECT id FROM projects WHERE group_number = %s)"
    if search_query:
        member_query += " AND (name LIKE %s OR roll_no LIKE %s)"
        params_member = ['%' + search_query + '%'] * 2
        cursor.execute(member_query, [group_number] + params_member)
    else:
        cursor.execute(member_query, [group_number])

    members = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    connection.close()

    return projects, members
@app.route('/')
def home():
    return render_template('group_data.html')

@app.route('/group/<group_number>', methods=['GET', 'POST'])
def group_data(group_number):
    # Get search query from the form
    search_query = request.form.get('search_query', '')  # Default to empty if no search term

    # Fetch filtered data based on the search query
    projects, members = fetch_filtered_data(group_number, search_query)

    # Render the results in the HTML template
    return render_template('group_data.html', group_number=group_number, projects=projects, members=members, search_query=search_query)

if __name__ == '__main__':
    app.run(debug=True)
