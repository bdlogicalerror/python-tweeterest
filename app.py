import sys
from routes import app

if len(sys.argv) > 1:
    mode = sys.argv[1]
    if mode == "production":
        import bjoern

        host = '0.0.0.0'
        port = 5000
        print("Server is running in production mode")
        from flask_cors import CORS

        CORS(app)
        bjoern.run(app, host, port)
    elif mode == "testing":
        from flask_cors import CORS

        CORS(app)
        print("Server is running in testing mode, switch to production when needed")
        app.run(debug=True)
    else:
        print("Invalid mode argument, exiting")
        exit()

else:
    print("No arguments")
    exit()



