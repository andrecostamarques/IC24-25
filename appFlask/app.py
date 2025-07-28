from flask import Flask
from routes.main_routes import main_bp
from routes.api_routes import api_bp
import os

def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__)
    
    # Configurações
    app.config['DEBUG'] = True
    app.config['CSV_FOLDER'] = 'data'
    
    # Criar diretório de dados se não existir
    os.makedirs(app.config['CSV_FOLDER'], exist_ok=True)
    
    # Registrar blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)