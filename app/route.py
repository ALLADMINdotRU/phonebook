from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint('main', __name__)       #подключаем как bluerprint


@main_bp.route('/')
def index():
    return redirect(url_for('phonebook.phonebook_index'))