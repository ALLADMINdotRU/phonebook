from app import create_app
from app.scheduler import init_scheduler  # Импортируем новый планировщик

app = create_app()

if __name__ == '__main__':
    # use_reloader=False чтобы избежать двойного запуска планировщика при разработке
    # app.run(debug=True, use_reloader=False, host='0.0.0.0')
    app.run(host='0.0.0.0', port=5050)
