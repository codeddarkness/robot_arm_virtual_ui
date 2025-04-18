# Development route for Robot Arm Virtual UI v0.3.1-1

from flask import render_template

def add_dev_route(app):
    """Add development version route to the Flask app"""
    @app.route('/dev')
    def dev_index():
        return render_template('dev/index.html')
