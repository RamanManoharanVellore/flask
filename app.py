from flask import Flask, render_template, url_for, redirect, request, flash, abort, session, jsonify
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config["SECRET_KEY"] = "abc123"

# MySQL Configuration
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "crud"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

# Flask-Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)


# User Model
class User(UserMixin):
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email

# Login Manager Loader
@login_manager.user_loader
def load_user(user_id):
    try:
        con = mysql.connection.cursor()
        con.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = con.fetchone()
        con.close()
        if not user_data:
            return None
        return User(user_data['id'], user_data['NAME'], user_data['email'])
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

# Forms
class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    city = StringField('City', validators=[DataRequired(), Length(min=2, max=50)])
    age = IntegerField('Age', validators=[DataRequired()])
    submit = SubmitField('Submit')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

# Routes
@app.route("/")

def home():
    try:
        con = mysql.connection.cursor()
        sql="SELECT * FROM users"
        con.execute(sql)
        res=con.fetchall()
        return render_template("home.html", users=res)
    except Exception as e:
        flash(f"Error fetching users: {e}", 'error')
        return redirect(url_for('home'))

@app.route("/addUsers", methods=['GET', 'POST'])

def addUsers():
    if request.method=='POST':
        name=request.form['name']
        city=request.form['city']
        age=request.form['age']
        con=mysql.connection.cursor()
        sql="insert into users(NAME,CITY,AGE) value (%s,%s,%s)"
        con.execute(sql,[name,city,age])
        mysql.connection.commit()
        con.close()
        flash('User Details Added')        
        return redirect(url_for("home"))
    return render_template("addUsers.html")


@app.route("/editUser/<int:id>", methods=['GET', 'POST'])

def editUser(id):
    try:
        con = mysql.connection.cursor()
        con.execute("SELECT * FROM users WHERE id = %s", (id,))
        user = con.fetchone()
        con.close()
        
        form = UserForm(obj=user)
        if form.validate_on_submit():
            name = form.name.data
            city = form.city.data
            age = form.age.data
            con = mysql.connection.cursor()
            con.execute("UPDATE users SET NAME = %s, CITY = %s, AGE = %s WHERE id = %s", (name, city, age, id))
            mysql.connection.commit()
            con.close()
            flash('User Detail Updated')
            return redirect(url_for("home"))
        
        return render_template("editUser.html", form=form)
    except Exception as e:
        flash(f"Error editing user: {e}", 'error')
        return redirect(url_for("home"))

@app.route("/deleteUser/<int:id>", methods=['POST'])

def deleteUser(id):
    try:
        con = mysql.connection.cursor()
        con.execute("DELETE FROM users WHERE id = %s", (id,))
        mysql.connection.commit()
        con.close()
        flash('User Details Deleted')
        return redirect(url_for("home"))
    except Exception as e:
        flash(f"Error deleting user: {e}", 'error')
        return redirect(url_for("home"))

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        try:
            # Check if the email is already registered
            con = mysql.connection.cursor()
            con.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = con.fetchone()
            
            if existing_user:
                flash('Email is already registered. Please use a different email.', 'error')
                return redirect(url_for('register'))
            
            # Insert the new user into the database
            con.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (username, email, password))
            mysql.connection.commit()
            con.close()
            
            flash('Registration successful. Please log in.')
            return redirect(url_for('login'))
        
        except Exception as e:
            flash(f"Registration error: {e}", 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    user_id = session.get('user_id')
    if user_id is not None:
        return redirect(url_for('home'))
    else:
        form = LoginForm()
        if form.validate_on_submit():
            try:
                email = form.email.data
                password = form.password.data
                
                con = mysql.connection.cursor()
                con.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = con.fetchone()
                con.close()
                
                if user and password == user['password']:  # Add proper password validation
                    user_obj = User(user['id'], user['NAME'], user['email'])
                    login_user(user_obj)
                    session['user_id'] = user['id']
                    session['user_name'] = user['NAME']
                    print(f"User authenticated: {user['NAME']}")

                    flash('Logged in successfully.')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid email or password.', 'error')
                    return redirect(url_for('login'))
            except Exception as e:
                flash(f"Login error: {e}", 'error')
                return redirect(url_for('login'))
        
        return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('login'))

@app.route("/dashboard")
@login_required
def dashboard():
    if 'user_name' in session:
        username = session['user_name']
        return f'Hello, {username}! You are in Dashboard.'
    # If 'user_name' is not in the session, redirect to the login page
    return redirect(url_for('login'))
    
# api code
# API Endpoints

# Create User
@app.route("/api/users", methods=['POST'])
def create_user():
    try:
        # Ensure request has JSON content type
        if request.headers.get('Content-Type') != 'application/json':
            return jsonify({'error': 'Unsupported Media Type. Content-Type must be application/json.'}), 415
        
        # Extract user data from JSON payload
        data = request.json
        name = data.get('name')
        city = data.get('city')
        age = data.get('age')
        email = data.get('email')
        password = data.get('password')
        
        # Validate required fields
        if not name or not city or not age or not email or not password:
            return jsonify({'error': 'Missing required fields. All fields (name, city, age, email, password) are required.'}), 400
        
        # Insert user into database
        con = mysql.connection.cursor()
        sql = "INSERT INTO users (NAME, CITY, AGE, email, password) VALUES (%s, %s, %s, %s, %s)"
        con.execute(sql, (name, city, age, email, password))
        mysql.connection.commit()
        con.close()
        
        return jsonify({'message': 'User created successfully'}), 201
    
    except Exception as e:
        return jsonify({'error': f"Failed to create user: {e}"}), 500

# Read Users
@app.route("/api/users", methods=['GET'])
def get_all_users():
    try:
        con = mysql.connection.cursor()
        con.execute("SELECT * FROM users")
        users = con.fetchall()
        con.close()
        
        return jsonify(users), 200
    
    except Exception as e:
        return jsonify({'error': f"Failed to fetch users: {e}"}), 500

# Read Single User
@app.route("/api/users/<int:id>", methods=['GET'])
def get_user(id):
    try:
        con = mysql.connection.cursor()
        con.execute("SELECT * FROM users WHERE id = %s", (id,))
        user = con.fetchone()
        con.close()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify(user), 200
    
    except Exception as e:
        return jsonify({'error': f"Failed to fetch user: {e}"}), 500

# Update User
@app.route("/api/users/<int:id>", methods=['PUT'])
def update_user(id):
    try:
        # Ensure request has JSON content type
        if request.headers.get('Content-Type') != 'application/json':
            return jsonify({'error': 'Unsupported Media Type. Content-Type must be application/json.'}), 415
        
        # Extract user data from JSON payload
        data = request.json
        name = data.get('NAME')  # Retrieve 'NAME' from JSON payload
        city = data.get('CITY')  # Retrieve 'CITY' from JSON payload
        age = data.get('AGE')    # Retrieve 'AGE' from JSON payload

        # Validate required fields
        if not name or not city or not age:
            return jsonify({'error': 'Missing required fields. All fields (NAME, CITY, AGE) are required.'}), 400

        # Update user in database
        con = mysql.connection.cursor()
        sql = "UPDATE users SET NAME = %s, CITY = %s, AGE = %s WHERE id = %s"
        con.execute(sql, (name, city, age, id))
        mysql.connection.commit()
        con.close()
        
        return jsonify({'message': 'User updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': f"Failed to update user: {e}"}), 500
# Delete User
@app.route("/api/users/<int:id>", methods=['DELETE'])
def delete_user(id):
    try:
        con = mysql.connection.cursor()
        con.execute("DELETE FROM users WHERE id = %s", (id,))
        mysql.connection.commit()
        con.close()
        
        return jsonify({'message': 'User deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': f"Failed to delete user: {e}"}), 500
    
# Custom 404 Page
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)