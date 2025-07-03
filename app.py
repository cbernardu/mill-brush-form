from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import datetime
import pyodbc
from auth import authenticate_user, get_user_by_id, update_last_login

app = Flask(__name__)
app.secret_key = "super_secret_key"  # required for flash messages

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


# Database connection string
# Make sure to replace the connection string with your actual database details
# CONN_STR = (
#     "DRIVER={ODBC Driver 18 for SQL Server};"
#     "SERVER=localhost,1433;"
#     "DATABASE=MyInternDB;"
#     "UID=sa;PWD=Travel1969@;"
#     "TrustServerCertificate=yes;"
# )

CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=kalvwprdsql01;'
    'DATABASE=TRI_ProcessOptimisation;'
    'UID=tri_pro_opt;'
    'PWD=Tiger@2k25;'
)

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return get_user_by_id(user_id)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Authenticate user using our auth module
        user = authenticate_user(username, password)
        
        if user:
            login_user(user, remember=True)
            # update_last_login(user.id)  # Update last login timestamp
            flash('Logged in successfully!', 'success')
            
            # Redirect to next page or main form
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('register'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# if attribute is duplicate within the same month, change old one's latest_upload to 0
def check_reupload(attribute):
    conn = pyodbc.connect(CONN_STR)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE [TRI_ProcessOptimisation].[dbo].[sen_reliability_master]
        SET latest_upload = 0
        WHERE attribute = ?
          AND MONTH(upload_date) = MONTH(GETDATE())
          AND YEAR(upload_date) = YEAR(GETDATE())
          AND latest_upload = 1
    """, (attribute,))
    updated = cursor.rowcount
    conn.commit()
    conn.close()

# Function to insert data into the database
def insert_registration(inspection_date, attribute, size, latest_upload):
    conn = pyodbc.connect(CONN_STR)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO [TRI_ProcessOptimisation].[dbo].[sen_reliability_master] (date, [user], attribute, type, value, upload_date, 
                   latest_upload, project)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (inspection_date, current_user.username, attribute, "Manual Input", size, datetime.datetime.now(), 
          latest_upload, "Mill Brush Measurement"))
    conn.commit()
    conn.close()

# Route for the registration form
@app.route("/", methods=["GET", "POST"])
@login_required

# Fetch the registration form and handle submissions
def register():
    if request.method == "POST":

        # Example for getting brush values in your route
        for i in range(1, 33):
            size = float(request.form.get(f'size{i}', 0))
            replaced = request.form.get(f'check{i}')  # Will be 'on' if checked, None if not
            millName = request.form.get("presetOption")

            date_obj = request.form.get("inspection_date")
            inspection_date = datetime.datetime.strptime(date_obj, "%Y-%m-%d")
            #inspection_date = datetime.strftime("%Y-%m-%d", date_obj)

            if replaced is None:
                replaced = 0
                attribute = f"{millName} - Brush {i} - Length (mm)"
                check_reupload(attribute)
                insert_registration(inspection_date, attribute, size, 1)
            else:
                replaced = 1
                attribute = f"{millName} - Brush {i} - Change out"
                check_reupload(attribute)
                insert_registration(inspection_date, attribute, replaced, 1)
                attribute = f"{millName} - Brush {i} - Length (mm)"
                check_reupload(attribute)
                insert_registration(inspection_date, attribute, size, 1)

        top_brush_val = request.form.get("top_brush")
        bottom_brush_val = request.form.get("bottom_brush")

        if top_brush_val not in (None, "", " "):
            top_brush = float(top_brush_val)
            attribute = f"{millName} - Top Brush - Length (mm)"
            insert_registration(inspection_date, attribute, top_brush, 1)

        if bottom_brush_val not in (None, "", " "):
            bottom_brush = float(bottom_brush_val)
            attribute2 = f"{millName} - Bottom Brush - Length (mm)"
            insert_registration(inspection_date, attribute2, bottom_brush, 1)

        flash("Submitted successful!")
        return redirect(url_for("register"))

    return render_template("index.html")

# Add a route to redirect root to login if not authenticated
@app.route("/home")
@login_required
def index():
    return redirect(url_for("register"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
