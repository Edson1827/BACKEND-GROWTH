from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.user import db, User, Company
import random

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Credenciais inválidas'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        role = data.get('role', 'client')
        company_name = data.get('company_name')
        plan = data.get('plan', 'starter')
        
        if not all([email, password, name]):
            return jsonify({'error': 'Email, senha e nome são obrigatórios'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email já cadastrado'}), 400
        
        # Create company if role is client
        company_id = None
        if role == 'client' and company_name:
            company = Company(name=company_name, plan=plan)
            db.session.add(company)
            db.session.flush()  # Get the ID
            company_id = company.id
        
        # Create user
        user = User(
            email=email,
            name=name,
            role=role,
            company_id=company_id
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/demo-data', methods=['POST'])
def create_demo_data():
    """Criar dados de demonstração para o protótipo"""
    try:
        # Create agency user
        agency_user = User(
            email='admin@ai.growth',
            name='Admin AI.GROWTH',
            role='agency'
        )
        agency_user.set_password('admin123')
        db.session.add(agency_user)
        
        # Create demo companies and users
        companies_data = [
            {'name': 'TechSolve Ltda', 'plan': 'aceleracao', 'budget': 15000},
            {'name': 'Marketing Pro', 'plan': 'crescimento', 'budget': 25000},
            {'name': 'StartupX', 'plan': 'starter', 'budget': 5000},
            {'name': 'E-commerce Plus', 'plan': 'aceleracao', 'budget': 18000},
            {'name': 'Consultoria Digital', 'plan': 'crescimento', 'budget': 30000}
        ]
        
        for comp_data in companies_data:
            # Create company
            company = Company(
                name=comp_data['name'],
                plan=comp_data['plan'],
                monthly_budget=comp_data['budget']
            )
            db.session.add(company)
            db.session.flush()
            
            # Create client user for company
            client_user = User(
                email=f"cliente@{comp_data['name'].lower().replace(' ', '').replace('ltda', '')}.com",
                name=f"Gestor {comp_data['name']}",
                role='client',
                company_id=company.id
            )
            client_user.set_password('cliente123')
            db.session.add(client_user)
            
            # Create demo campaigns
            platforms = ['google', 'facebook', 'instagram']
            for i, platform in enumerate(platforms):
                if comp_data['plan'] == 'starter' and i > 0:
                    break  # Starter only gets 1 campaign
                if comp_data['plan'] == 'aceleracao' and i > 1:
                    break  # Aceleracao gets 2 campaigns
                
                campaign_budget = comp_data['budget'] / (3 if comp_data['plan'] == 'crescimento' else 2 if comp_data['plan'] == 'aceleracao' else 1)
                spent = campaign_budget * random.uniform(0.6, 0.9)
                impressions = int(spent * random.uniform(50, 150))
                clicks = int(impressions * random.uniform(0.02, 0.08))
                conversions = int(clicks * random.uniform(0.05, 0.15))
                revenue = spent * random.uniform(2.5, 5.0)
                
                from src.models.user import Campaign
                campaign = Campaign(
                    company_id=company.id,
                    name=f'Campanha {platform.title()} - {comp_data["name"]}',
                    platform=platform,
                    budget=campaign_budget,
                    spent=spent,
                    impressions=impressions,
                    clicks=clicks,
                    conversions=conversions,
                    revenue=revenue
                )
                db.session.add(campaign)
        
        db.session.commit()
        return jsonify({'message': 'Dados de demonstração criados com sucesso'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

