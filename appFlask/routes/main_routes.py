from flask import Blueprint, render_template, send_file, current_app
from services.app_state import app_state
import os

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    """Página principal da aplicação"""
    return render_template('index.html')

@main_bp.route("/download")
def download():
    """Download do arquivo CSV atual"""
    try:
        csv_filename = app_state.data_manager.get_csv_filename()
        if csv_filename and os.path.exists(csv_filename):
            return send_file(csv_filename, as_attachment=True)
        else:
            return "Arquivo CSV não encontrado", 404
    except Exception as e:
        return f"Erro ao baixar arquivo: {str(e)}", 500