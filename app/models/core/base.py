"""
Core database models for the Personal Health Record Manager.
This module contains base database setup and core models.
"""

from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# User-Family relationship table
user_family = db.Table(
    "user_family",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column(
        "family_member_id",
        db.Integer,
        db.ForeignKey("family_members.id"),
        primary_key=True,
    ),
)
