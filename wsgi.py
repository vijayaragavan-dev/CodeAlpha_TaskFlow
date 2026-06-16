from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    from config import PORT, FLASK_ENV
    debug = FLASK_ENV == 'development'
    socketio.run(app, host='0.0.0.0', port=PORT, debug=debug)
