from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Company, Campaign
from sqlalchemy import func

agency_bp = Blueprint('agency', __name__)

@agency_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_agency_dashboard():
    """Dashboard consolidado da agência"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'agency':
            return jsonify({'error': 'Acesso negado'}), 403
        
        # KPIs consolidados
        total_companies = Company.query.filter_by(is_active=True).count()
        total_campaigns = Campaign.query.join(Company).filter(Company.is_active == True).count()
        
        # Receita total gerenciada
        total_budget = db.session.query(func.sum(Company.monthly_budget)).filter_by(is_active=True).scalar() or 0
        
        # Gastos e receita das campanhas
        campaign_stats = db.session.query(
            func.sum(Campaign.spent).label('total_spent'),
            func.sum(Campaign.revenue).label('total_revenue'),
            func.sum(Campaign.conversions).label('total_conversions')
        ).join(Company).filter(Company.is_active == True).first()
        
        total_spent = campaign_stats.total_spent or 0
        total_revenue = campaign_stats.total_revenue or 0
        total_conversions = campaign_stats.total_conversions or 0
        
        # Cálculos de KPIs
        roi = ((total_revenue - total_spent) / total_spent * 100) if total_spent > 0 else 0
        avg_cac = (total_spent / total_conversions) if total_conversions > 0 else 0
        
        # Performance por plano
        plans_performance = db.session.query(
            Company.plan,
            func.count(Company.id).label('count'),
            func.sum(Company.monthly_budget).label('budget'),
            func.avg(Campaign.revenue / Campaign.spent).label('avg_roas')
        ).join(Campaign).filter(Company.is_active == True).group_by(Company.plan).all()
        
        # Top performers
        top_companies = db.session.query(
            Company.name,
            Company.plan,
            func.sum(Campaign.revenue).label('revenue'),
            func.sum(Campaign.spent).label('spent'),
            (func.sum(Campaign.revenue) / func.sum(Campaign.spent)).label('roas')
        ).join(Campaign).filter(Company.is_active == True).group_by(Company.id).order_by(
            (func.sum(Campaign.revenue) / func.sum(Campaign.spent)).desc()
        ).limit(5).all()
        
        return jsonify({
            'kpis': {
                'total_companies': total_companies,
                'total_campaigns': total_campaigns,
                'total_budget': round(total_budget, 2),
                'total_spent': round(total_spent, 2),
                'total_revenue': round(total_revenue, 2),
                'roi': round(roi, 2),
                'avg_cac': round(avg_cac, 2),
                'total_conversions': total_conversions
            },
            'plans_performance': [
                {
                    'plan': p.plan,
                    'count': p.count,
                    'budget': round(p.budget or 0, 2),
                    'avg_roas': round(p.avg_roas or 0, 2)
                } for p in plans_performance
            ],
            'top_companies': [
                {
                    'name': c.name,
                    'plan': c.plan,
                    'revenue': round(c.revenue or 0, 2),
                    'spent': round(c.spent or 0, 2),
                    'roas': round(c.roas or 0, 2)
                } for c in top_companies
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agency_bp.route('/companies', methods=['GET'])
@jwt_required()
def get_all_companies():
    """Lista todas as empresas clientes"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'agency':
            return jsonify({'error': 'Acesso negado'}), 403
        
        companies = Company.query.filter_by(is_active=True).all()
        
        companies_data = []
        for company in companies:
            # Calculate company metrics
            campaigns = Campaign.query.filter_by(company_id=company.id).all()
            total_spent = sum(c.spent for c in campaigns)
            total_revenue = sum(c.revenue for c in campaigns)
            total_conversions = sum(c.conversions for c in campaigns)
            
            roi = ((total_revenue - total_spent) / total_spent * 100) if total_spent > 0 else 0
            
            companies_data.append({
                **company.to_dict(),
                'total_spent': round(total_spent, 2),
                'total_revenue': round(total_revenue, 2),
                'total_conversions': total_conversions,
                'roi': round(roi, 2),
                'campaigns_count': len(campaigns)
            })
        
        return jsonify({'companies': companies_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@agency_bp.route('/campaigns', methods=['GET'])
@jwt_required()
def get_all_campaigns():
    """Lista todas as campanhas de todos os clientes"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'agency':
            return jsonify({'error': 'Acesso negado'}), 403
        
        campaigns = db.session.query(Campaign, Company.name.label('company_name')).join(
            Company
        ).filter(Company.is_active == True).all()
        
        campaigns_data = []
        for campaign, company_name in campaigns:
            campaign_dict = campaign.to_dict()
            campaign_dict['company_name'] = company_name
            campaigns_data.append(campaign_dict)
        
        return jsonify({'campaigns': campaigns_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

