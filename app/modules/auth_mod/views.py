from flask import render_template, redirect, url_for, session, flash, current_app
from .forms import LoginForm
from app.models import User


def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Проверяем через конфиг вместо базы данных
        if (form.username.data == current_app.config['ADMIN_USERNAME'] and 
            form.password.data == current_app.config['ADMIN_PASSWORD']):
            
            session['user_id'] = 1  # фиксированный ID для админа
            session['username'] = form.username.data
            flash('Успешный вход', 'success')
            return redirect(url_for('main.index'))
        
        flash('Неверный логин или пароль', 'danger')
    return render_template('auth/login.html', form=form)


def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('main.index'))
