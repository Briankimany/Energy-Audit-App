from server.blueprints.auth_bp import bp as auth_bp
from server.blueprints.buildings_bp import bp as buildings_bp
from server.blueprints.energy_bp import bp as energy_bp
from server.blueprints.institution_bp import bp as institution_bp
from server.blueprints.users_bp import bp as users_bp

blueprints = [auth_bp, institution_bp, users_bp, buildings_bp, energy_bp]

__all__ = ["blueprints"]
