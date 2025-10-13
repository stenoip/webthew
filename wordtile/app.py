# app.py

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os # Import os for environment variables

# --- Configuration ---
app = Flask(__name__)

# CONFIGURE DATABASE FOR RENDER
# It checks for a DATABASE_URL environment variable (set by Render)
# If not found (for local testing), it uses a placeholder or local SQLite.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1) \
    if os.environ.get('DATABASE_URL') else 'sqlite:///wordtile.db'
    
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Model (NO CHANGE NEEDED) ---
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Post {self.id}>'

# --- Application Routes (NO CHANGE NEEDED) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        post_content = request.form['content'].strip()
        
        if post_content:
            new_post = Post(content=post_content)
            try:
                db.session.add(new_post)
                db.session.commit()
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                print(f"Error saving post: {e}")
                return "There was an issue creating your post.", 500
        else:
            return redirect(url_for('index'))

    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', posts=posts)

# --- Initializer ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # CHANGE: Use Gunicorn or similar for production
    app.run(debug=True, host='0.0.0.0')

# This is the line Render uses to run your app with gunicorn
# The variable name MUST be 'app'
# Use this for deployment:
# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run()
