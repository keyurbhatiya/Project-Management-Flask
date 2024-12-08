from werkzeug.security import generate_password_hash, check_password_hash

# Example of how to hash a password before inserting into the database
password = '12345678'
hashed_password = generate_password_hash(password)
# Store hashed_password in the database, instead of plain text
print( "hey",hashed_password)  
