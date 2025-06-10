from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client')  # 'agency' or 'client'
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    company = db.relationship('Company', backref='users', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'company_id': self.company_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    plan = db.Column(db.String(50), nullable=False, default='starter')  # 'starter', 'aceleracao', 'crescimento'
    monthly_budget = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'plan': self.plan,
            'monthly_budget': self.monthly_budget,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # 'google', 'facebook', 'instagram'
    status = db.Column(db.String(20), default='active')  # 'active', 'paused', 'completed'
    budget = db.Column(db.Float, default=0.0)
    spent = db.Column(db.Float, default=0.0)
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    revenue = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    company = db.relationship('Company', backref='campaigns', lazy=True)
    
    def to_dict(self):
        ctr = (self.clicks / self.impressions * 100) if self.impressions > 0 else 0
        cpc = (self.spent / self.clicks) if self.clicks > 0 else 0
        roas = (self.revenue / self.spent) if self.spent > 0 else 0
        
        return {
            'id': self.id,
            'company_id': self.company_id,
            'name': self.name,
            'platform': self.platform,
            'status': self.status,
            'budget': self.budget,
            'spent': self.spent,
            'impressions': self.impressions,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'revenue': self.revenue,
            'ctr': round(ctr, 2),
            'cpc': round(cpc, 2),
            'roas': round(roas, 2),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
