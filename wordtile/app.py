from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# --- Configuration ---
app = Flask(__name__)

# 1. CONFIGURE DATABASE URI: 
# Reads the DATABASE_URL environment variable (set by Render for PostgreSQL)
# Falls back to local 'sqlite:///wordtile.db' for Chromebook testing.
DB_URL = os.environ.get('DATABASE_URL', 'sqlite:///wordtile.db')

# 2. ENSURE CORRECT DIALECT: 
# Replaces 'postgres://' (sometimes used) with the required 'postgresql://' dialect prefix.
if DB_URL.startswith('postgres://'):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)
    
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 3. DATABASE INITIALIZATION FOR RENDER FREE TIER:
# Automatically creates the database tables when the application is loaded by Gunicorn.
# This replaces the need for manual shell access.
with app.app_context():
    db.create_all()

# --- Database Model ---
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.id}>'

# --- Application Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        post_content = request.form['content'].strip()
        
        if post_content:
            new_post = Post(content=post_content)
            try:
                db.session.add(new_post)
                db.session.commit()
                # Redirect to GET request to prevent resubmission
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                print(f"Error saving post: {e}")
                # For debugging on Render, print the full error to the logs
                import traceback
                traceback.print_exc()
                return "There was an issue creating your post. Check the server logs for details.", 500
        else:
            return redirect(url_for('index'))

    # Handle viewing posts
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)

# --- Initializer (For Local Chromebook/Linux Run ONLY) ---
if __name__ == '__main__':
    # The db.create_all() call above handles initialization.
    # This block only starts the local development server.
    app.run(debug=True, host='0.0.0.0')

# For Render, the Gunicorn process executes the code outside of this block.
