"""
In loving memory of Tariq Al Fayad (Oct-03 1997 - Mar-18 2020)
A beloved son whose spirit lives on in every line of code,
every patient helped, and every life touched by this system.
His memory inspires us to build technology that heals and serves humanity.

"Those we love never truly leave us - they live on in our hearts,
our work, and the difference we make in the world."

Rest in peace, dear Tariq. Your legacy continues through this dedication
to improving healthcare and helping others.
"""

# Script to promote a user to admin in the PHRM system
# Usage: python scripts/make_admin.py user@example.com

import sys
from app import create_app, db
from app.models.core.user import User

if len(sys.argv) != 2:
    print("Usage: python scripts/make_admin.py user@example.com")
    sys.exit(1)

email = sys.argv[1]

app = create_app()
with app.app_context():
    user = User.query.filter_by(email=email).first()
    if not user:
        print(f"User with email {email} not found.")
        sys.exit(1)
    user.is_admin = True
    db.session.commit()
    print(f"User {email} is now an admin.")
