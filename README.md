# Vernika - Multi-User Business Management System

A professional multi-user desktop application built with **Python** and **Flet**, featuring Admin and Employee roles with secure authentication and database management.

## 🏗️ Architecture

```
Vernika/
├── database/              # Database layer
│   ├── connection.py       # Database connection management
│   ├── models.py           # SQLAlchemy models
│   ├── operations.py       # CRUD operations
│   ├── repositories.py     # Data repositories
│   └── session_manager.py  # Session management
├── auth/                  # Authentication
│   ├── login.py           # Login logic
│   ├── session.py         # Session management
│   ├── role_check.py      # Role-based access control
│   └── models.py          # Auth models
├── screens/               # Application screens
│   ├── login_screen.py    # Login window
│   ├── admin_screen.py    # Admin dashboard
│   ├── employee_screen.py # Employee dashboard
│   ├── employees_screen.py
│   ├── departments_screen.py
│   ├── positions_screen.py
│   ├── chat_screen.py     # Chat functionality
│   ├── leaves_screen.py   # Leave management
│   ├── attendance_screen.py
│   ├── projects_screen.py
│   ├── tasks_screen.py
│   ├── teams_screen.py
│   ├── inventory_screen.py
│   ├── transactions_screen.py
│   ├── crm_screen.py       # CRM Dashboard
│   ├── mail_screen.py
│   └── ...                # Many more screens
├── utils/                 # Utility functions
│   ├── notification_manager.py
│   ├── helpers.py
│   └── ...
├── core/                  # Core functionality
│   ├── navigation.py
│   ├── theme.py
│   └── ...
├── components/            # Reusable UI components
├── scripts/               # Database/utility scripts
├── assets/                # Static assets
├── config.py              # Configuration
├── main.py                # Entry point
└── requirements.txt       # Dependencies
```

## ✨ Features

### Authentication
- 🔐 Secure multi-user login
- 🔑 Password hashing with bcrypt
- 📝 Session management
- 📊 Audit logging

### User Roles
- **Admin**: Full access to users, employees, settings, and audit logs
- **Employee**: Limited access to personal profile and tasks

### Core Modules
- 👥 Employee Management
- 📅 Attendance Tracking
- 📝 Leave Management
- 💬 Real-time Chat
- 📊 Project Management
- 📦 Inventory Management
- 📧 Email Integration
- 📈 Reports & Analytics
- 🤝 CRM (Leads, Contacts, Calendar, Vendors, Warehouses, Assets, Contracts, Invoices)

### Database
- 🗄️ Supabase (PostgreSQL) with RLS
- 📋 User management
- 👥 Employee profiles
- 📜 Audit trail

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd Vernika
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   - Copy `env_template_complete.txt` to `.env`
   - Fill in your Supabase credentials

4. **Run the application**
   ```bash
   python main.py
   ```

## 📦 Dependencies

- **flet**: Desktop UI framework
- **sqlalchemy**: ORM for database
- **bcrypt**: Password hashing
- **python-jose**: JWT token handling
- **python-dotenv**: Environment variables
- **supabase**: Database client
- **pandas**: Data processing
- **openpyxl**: Excel export

## 🔒 Security Features

- Password hashing with bcrypt
- Session-based authentication
- Role-based access control (RBAC)
- Row Level Security (RLS) in Supabase
- Audit logging for all actions
- SQL injection prevention via SQLAlchemy

## 📝 Project Structure

- `auth/` - Authentication and authorization
- `database/` - Database models and operations
- `screens/` - All application screens (30+ screens)
- `components/` - Reusable UI components
- `core/` - Core application logic
- `utils/` - Utility functions
- `scripts/` - Database setup and maintenance scripts
- `assets/` - Static assets (logos, images)
- `supabase/` - Database migrations

## 🐛 Troubleshooting

### Database Errors
Check your Supabase credentials in `.env`

### Import Errors
Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Port Already in Use
Flet uses port 8000 by default. No configuration needed as it auto-assigns.

## 📄 License

This project is open source and available for personal and commercial use.

---

Built with ❤️ using Python and Flet

