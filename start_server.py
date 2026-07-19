import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web_app import app

if __name__ == '__main__':
    print("Starting Flask app on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
