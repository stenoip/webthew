from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# --- Configuration ---
app = Flask(__name__)

# CONFIGURE DATABASE FOR RENDER
# Uses the DATABASE_URL environment variable on Render (PostgreSQL)
# Falls back to local SQLite if the variable is not found (for Chromebook testing)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///wordtile.db').replace("postgres://", "postgresql://", 1)
    
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# NEW: Initialize the database tables immediately upon application startup.
# This ensures tables are created on Render's Free Tier where the shell isn't available.
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
                return "There was an issue creating your post.", 500
        else:
            return redirect(url_for('index'))

    # Handle viewing posts
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)

# --- Initializer (For Local Chromebook/Linux Run ONLY) ---
if __name__ == '__main__':
    # When run locally, the 'db.create_all()' above already runs, 
    # but this block executes the local development server.
    app.run(debug=True, host='0.0.0.0')

# For Render deployment, Gunicorn runs 'wordtile.app:app' and executes the code outside of this block.
