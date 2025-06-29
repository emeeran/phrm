🔑 PHRM LOGIN CREDENTIALS REFERENCE
==========================================

🛡️  ADMIN LOGIN
--------------
URL: http://localhost:5010/auth/admin/login
Email: emeeranjp@gmail.com
Password: admin123

👤 USER LOGIN  
--------------
URL: http://localhost:5010/auth/login
Email: emeeran@hotmail.com
Password: user123

📝 NOTES:
---------
- Admin login requires EMAIL ADDRESS, not username
- The username "Admin" won't work in the email field
- Use the full email: emeeranjp@gmail.com
- Both login forms are separate and use different routes

🛡️  ADMIN CAPABILITIES:
------------------------
✅ User Management:
   • View all users in the system
   • Add new users
   • Edit user details (username, email, name, password)
   • Activate/deactivate user accounts
   • Delete users (with confirmation)

✅ Family Member Management:
   • View all family members across all users
   • Add family members to any user account
   • Edit family member details for any user
   • Delete family members from any user account
   • View family member medical information

✅ Medical Records Access:
   • View all medical records in the system
   • Access records from any family member
   • View record details and attachments
   • See comprehensive medical histories

✅ Medication Management:
   • View all medications across all users
   • See medication schedules for all family members
   • Access drug interaction information
   • Monitor system-wide medication data

✅ System Administration:
   • Access admin dashboard with system statistics
   • View user activity and system usage
   • Manage system-wide settings
   • Security event monitoring

👤 USER CAPABILITIES:
---------------------
✅ Personal Profile:
   • View and edit own profile information
   • Change own password
   • Manage notification preferences
   • Account settings

✅ Family Management:
   • Add/edit/delete own family members only
   • View family member profiles
   • Manage family medical information
   • Emergency contact management

✅ Medical Records:
   • Create medical records for family members
   • Upload and attach documents
   • View medical history and summaries
   • AI-powered medical chat

✅ Medication Tracking:
   • Track current medications for family
   • Set medication schedules
   • Check drug interactions within family
   • Medication reminders and notes

🚫 USER RESTRICTIONS:
   • Cannot view other users' data
   • Cannot access admin areas
   • Cannot manage other user accounts
   • Limited to own family data only

✅ VERIFICATION:
- Admin has 0 family members (as expected)
- User has 2 family members with 15 medications
- Admin and user systems are properly separated
