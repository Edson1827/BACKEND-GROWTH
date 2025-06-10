from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Company, Campaign
from sqlalchemy import func

client_bp = Blueprint('client', __name__)

@client_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_client_dashboard():
    """Dashboard específico do cliente"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'client' or not user.company_id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        company = Company.query.get(user.company_id)
        if not company:
            return jsonify({'error': 'Empresa não encontrada'}), 404
        
        # Campanhas da empresa
        campaigns = Campaign.query.filter_by(company_id=company.id).all()
        
        # KPIs específicos da empresa
        total_spent = sum(c.spent for c in campaigns)
        total_revenue = sum(c.revenue for c in campaigns)
        total_conversions = sum(c.conversions for c in campaigns)
        total_clicks = sum(c.clicks for c in campaigns)
        total_impressions = sum(c.impressions for c in campaigns)
        
        # Cálculos
        roi = ((total_revenue - total_spent) / total_spent * 100) if total_spent > 0 else 0
        cac = (total_spent / total_conversions) if total_conversions > 0 else 0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        ltv_cac = 3.5  # Mock LTV/CAC ratio
        
        # Performance por plataforma
        platform_performance = {}
        for campaign in campaigns:
            platform = campaign.platform
            if platform not in platform_performance:
                platform_performance[platform] = {
                    'spent': 0,
                    'revenue': 0,
                    'conversions': 0,
                    'clicks': 0,
                    'impressions': 0
                }
            
            platform_performance[platform]['spent'] += campaign.spent
            platform_performance[platform]['revenue'] += campaign.revenue
            platform_performance[platform]['conversions'] += campaign.conversions
            platform_performance[platform]['clicks'] += campaign.clicks
            platform_performance[platform]['impressions'] += campaign.impressions
        
        # Calcular ROAS por plataforma
        for platform in platform_performance:
            data = platform_performance[platform]
            data['roas'] = round(data['revenue'] / data['spent'], 2) if data['spent'] > 0 else 0
            data['ctr'] = round(data['clicks'] / data['impressions'] * 100, 2) if data['impressions'] > 0 else 0
            data['cpc'] = round(data['spent'] / data['clicks'], 2) if data['clicks'] > 0 else 0
        
        return jsonify({
            'company': company.to_dict(),
            'kpis': {
                'roi': round(roi, 2),
                'cac': round(cac, 2),
                'ltv_cac': ltv_cac,
                'conversion_rate': round(conversion_rate, 2),
                'revenue_attributed': round(total_revenue, 2),
                'total_spent': round(total_spent, 2),
                'total_conversions': total_conversions,
                'total_clicks': total_clicks,
                'total_impressions': total_impressions
            },
            'campaigns': [c.to_dict() for c in campaigns],
            'platform_performance': platform_performance
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/campaigns', methods=['GET'])
@jwt_required()
def get_client_campaigns():
    """Lista campanhas específicas do cliente"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'client' or not user.company_id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        campaigns = Campaign.query.filter_by(company_id=user.company_id).all()
        
        return jsonify({
            'campaigns': [c.to_dict() for c in campaigns]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/company', methods=['GET'])
@jwt_required()
def get_client_company():
    """Informações da empresa do cliente"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'client' or not user.company_id:
            return jsonify({'error': 'Acesso negado'}), 403
        
        company = Company.query.get(user.company_id)
        if not company:
            return jsonify({'error': 'Empresa não encontrada'}), 404
        
        return jsonify({'company': company.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

