# Vernika - Multi-User Management System

A professional multi-user desktop application built with **Python** and **Flet**, featuring Admin and Employee roles with secure authentication and database management.

## 🏗️ Architecture

```
Vernika/
├── database/
│   ├── __init__.py          # Database module init
│   ├── connection.py        # Database connection management
│   ├── models.py            # SQLAlchemy models (User, Role, Employee, AuditLog)
│   └── operations.py        # CRUD operations
├── auth/
│   ├── __init__.py          # Auth module init
│   ├── login.py             # Login/authentication logic
│   ├── session.py           # Session management
│   └── role_check.py        # Role-based access control
├── screens/
│   ├── __init__.py          # Screens module init
│   ├── base_screen.py       # Base screen class
│   ├── login_screen.py      # Login window
│   ├── admin_screen.py      # Admin dashboard
│   └── employee_screen.py   # Employee dashboard
├── utils/
│   ├── __init__.py          # Utils module init
│   ├── constants.py         # Application constants
│   └── helpers.py           # Utility functions
├── config.py                # Configuration file
├── main.py                  # Application entry point
└── requirements.txt         # Dependencies
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

### Database
- 🗄️ SQLite database (easily changeable to PostgreSQL/MySQL)
- 📋 User management (CRUD operations)
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

3. **Run the application**
   ```bash
   python main.py
   ```

### Default Credentials
After running the application, use these demo credentials:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Employee | employee | employee123 |

## 🎯 Framework Comparison: Flet vs Kivy

| Feature | Flet ✅ | Kivy |
|---------|---------|------|
| **UI Design** | Modern, native-like | Custom widgets |
| **Learning Curve** | Easy (Python only) | Steeper (Kv language) |
| **Database** | Excellent async support | Good but complex |
| **Multi-user** | Easy to implement | Possible but complex |
| **Desktop Feel** | Professional | More mobile-like |
| **Performance** | Good (Flutter-based) | Good |

**Verdict**: Flet is recommended for this project because:
- Easier to create professional desktop UIs
- Better async support for database operations
- Modern navigation system
- Simpler state management

## 📁 Database Schema

### Users Table
- id, username, email, hashed_password, role_id, is_active, created_at, updated_at

### Roles Table
- id, name (Admin/Employee), description

### Employees Table
- id, user_id, first_name, last_name, department, position, phone, address

### AuditLogs Table
- id, user_id, action, details, ip_address, created_at

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Database
DATABASE_PATH = "vernika.db"

# Window Settings
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800

# Theme
PRIMARY_COLOR = "#2E86AB"
```

## 📝 Adding New Screens

1. Create a new screen file in `screens/`
2. Inherit from `BaseScreen` or `Column`
3. Add route in `main.py` route handler
4. Update `auth/role_check.py` if role restriction needed

## 🔒 Security Features

- Password hashing with bcrypt
- Session-based authentication
- Role-based access control (RBAC)
- Audit logging for all actions
- SQL injection prevention via SQLAlchemy

## 🎨 Customization

### Changing Colors
Edit `config.py`:
```python
PRIMARY_COLOR = "#2E86AB"
SECONDARY_COLOR = "#A23B72"
```

### Adding New Roles
1. Add role in database `roles` table
2. Update `auth/role_check.py` with role permissions
3. Add route handling in `main.py`

## 📦 Dependencies

- **flet**: Desktop UI framework
- **sqlalchemy**: ORM for database
- **bcrypt**: Password hashing
- **python-jose**: JWT token handling
- **python-dotenv**: Environment variables

## 🐛 Troubleshooting

### Database Errors
Delete `vernika.db` and restart the app to reinitialize.

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

# Vernika
