# PI-Installer - Architektur & Design

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                          │
│                  (React Frontend)                       │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/WebSocket
                     │ Port 3000/80
                     │
┌────────────────────▼────────────────────────────────────┐
│              Nginx Reverse Proxy                        │
│          (API Gateway & Load Balancer)                  │
│                   Port 80/443                          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP REST API
                     │ Port 8000
                     │
┌────────────────────▼────────────────────────────────────┐
│             FastAPI Backend Server                      │
│           (Core Logic & Orchestration)                  │
├─────────────────────────────────────────────────────────┤
│ ┌──────────────┬──────────────┬──────────────────────┐ │
│ │  Security    │   Users      │   DevEnv Module     │ │
│ │  Module      │   Module     │                      │ │
│ └──────────────┴──────────────┴──────────────────────┘ │
│ ┌──────────────┬──────────────┬──────────────────────┐ │
│ │  WebServer   │   Mail       │   System Utils       │ │
│ │  Module      │   Module     │                      │ │
│ └──────────────┴──────────────┴──────────────────────┘ │
└────────────┬───────────────────────────────────────────┘
             │ Shell Commands & System Calls
             │ /usr/bin/bash, sudo, apt-get, systemctl
             │
┌────────────▼───────────────────────────────────────────┐
│         Raspberry Pi OS (Debian-based)                  │
│              System Layer                              │
├─────────────────────────────────────────────────────────┤
│ • Package Manager (apt)                                │
│ • Systemd Service Manager                              │
│ • Network Stack                                        │
│ • File System                                          │
│ • Hardware Access                                      │
└─────────────────────────────────────────────────────────┘
```

## 📦 Component Breakdown

### Frontend Layer (React + TypeScript)

```
frontend/
├── src/
│   ├── components/
│   │   ├── Sidebar.tsx       # Navigation
│   │   └── [Other shared components]
│   ├── pages/
│   │   ├── Dashboard.tsx      # Main overview
│   │   ├── SecuritySetup.tsx  # Security config
│   │   ├── UserManagement.tsx # User admin
│   │   ├── DevelopmentEnv.tsx # Dev tools
│   │   ├── WebServerSetup.tsx # Web config
│   │   ├── MailServerSetup.tsx# Mail config
│   │   └── InstallationWizard.tsx # Step-by-step
│   ├── App.tsx               # Main app component
│   ├── App.css               # Styling & animations
│   └── index.css             # Global styles
├── vite.config.ts            # Vite configuration
├── tailwind.config.js        # Tailwind CSS
├── postcss.config.js         # PostCSS
└── package.json              # Dependencies
```

**Tech Stack:**
- React 18 - UI Framework
- TypeScript - Type Safety
- Vite - Build Tool
- Tailwind CSS - Styling
- Lucide React - Icons
- Axios - HTTP Client
- React Hot Toast - Notifications
- Zustand - State Management

### Backend Layer (Python + FastAPI)

```
backend/
├── app.py                    # Main FastAPI application
├── requirements.txt          # Python dependencies
└── modules/
    ├── __init__.py
    ├── security.py           # Security & hardening
    │   ├── scan_system()
    │   ├── configure()
    │   ├── _harden_ssh()
    │   ├── _configure_firewall()
    │   ├── _install_fail2ban()
    │   └── _enable_audit_logging()
    │
    ├── users.py              # User management
    │   ├── create_user()
    │   ├── delete_user()
    │   ├── reset_password()
    │   ├── change_role()
    │   └── _create_ssh_key()
    │
    ├── devenv.py             # Development environment
    │   ├── configure()
    │   ├── install_language()
    │   ├── install_database()
    │   ├── install_tool()
    │   ├── _init_postgres()
    │   ├── _init_mysql()
    │   └── _init_mongodb()
    │
    ├── webserver.py          # Web server setup
    │   ├── configure()
    │   ├── _install_nginx()
    │   ├── _install_apache()
    │   ├── _configure_ssl()
    │   ├── _install_php()
    │   ├── _install_webadmin()
    │   └── _install_cms()
    │
    ├── mail.py               # Mail server setup
    │   ├── configure()
    │   ├── _install_postfix()
    │   ├── _install_dovecot()
    │   └── _install_spamassassin()
    │
    └── utils.py              # System utilities
        ├── get_system_info()
        ├── run_command()
        ├── check_service()
        ├── install_package()
        └── create_backup()
```

**Tech Stack:**
- FastAPI - Web Framework
- Pydantic - Data Validation
- Uvicorn - ASGI Server
- asyncio - Async Support
- subprocess - System Calls
- psutil - System Info

## 🔄 Data Flow

### Installation Process

```
User Input (GUI)
    │
    ▼
Frontend State (React)
    │
    ▼
API Request (POST /api/install/start)
    │
    ▼
Backend Processing
    │
    ├─→ Security Configuration
    │   ├─→ Enable Firewall (UFW)
    │   ├─→ SSH Hardening
    │   ├─→ Fail2Ban Setup
    │   └─→ Auto-Updates
    │
    ├─→ User Creation
    │   ├─→ Create Users
    │   ├─→ Set Permissions
    │   └─→ SSH Keys
    │
    ├─→ Development Environment
    │   ├─→ Install Languages
    │   ├─→ Install Databases
    │   └─→ Setup Tools
    │
    ├─→ Web Server
    │   ├─→ Install Server
    │   ├─→ Configure SSL
    │   └─→ Install CMS
    │
    └─→ Mail Server (Optional)
        ├─→ Postfix SMTP
        ├─→ Dovecot IMAP/POP3
        └─→ Spam Filter
    │
    ▼
System Commands Execution
    │
    ├─→ apt-get install ...
    ├─→ systemctl enable/start ...
    ├─→ ufw allow/deny ...
    ├─→ useradd ...
    └─→ Custom Config Files
    │
    ▼
API Response
    │
    ▼
Frontend Update (Progress Bar)
    │
    ▼
User Notification (Toast)
```

## 🔐 Security Architecture

### Multi-Layer Security Approach

```
Layer 1: Physical Security
├─ SSH Key-based Authentication
├─ Fail2Ban Brute-Force Protection
└─ Port Blocking

Layer 2: Firewall & Network
├─ UFW (Uncomplicated Firewall)
├─ Port Management
└─ Rate Limiting

Layer 3: Application Security
├─ Input Validation (Pydantic)
├─ CORS Configuration
├─ Rate Limiting
└─ Authentication (Future: JWT)

Layer 4: System Hardening
├─ SSH Configuration Hardening
├─ Audit Logging (auditd)
├─ Auto-Updates (unattended-upgrades)
└─ Service Isolation

Layer 5: Encryption
├─ TLS/SSL (Let's Encrypt)
├─ Secure Password Storage
└─ Secrets Management
```

## 📊 Module Interaction Diagram

```
┌─────────────────────────────────────────────────────┐
│              FastAPI Main App                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │           System Utils (Base)                │  │
│  │  • run_command()                             │  │
│  │  • install_package()                         │  │
│  │  • check_service()                           │  │
│  │  • get_system_info()                         │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                   │
│    ┌────────────┼────────────┬────────────┐        │
│    │            │            │            │        │
│    ▼            ▼            ▼            ▼        │
│ ┌──────┐  ┌──────────┐  ┌──────┐  ┌────────┐     │
│ │Sec.  │  │Users     │  │DevEnv│  │WebServ│     │
│ │Mod.  │  │Module    │  │Mod.  │  │Mod.   │     │
│ └──────┘  └──────────┘  └──────┘  └────────┘     │
│    │            │            │            │        │
│    ▼            ▼            ▼            ▼        │
│  UFW     Linux Users    Languages      Nginx/Apache
│ Fail2Ban   SSH Keys    Databases          CMS
│ auditd    sudoers      Docker          Webadmin
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 🚀 Deployment Architecture

### Development Mode
```
Local Machine
├─ Frontend Dev Server (port 3000)
├─ Backend Dev Server (port 8000)
└─ Hot Module Reloading
```

### Production Mode (Docker)
```
Docker Host
├─ Frontend Container (Node.js)
│  └─ port 3000
├─ Backend Container (Python)
│  └─ port 8000
├─ Nginx Container (Reverse Proxy)
│  ├─ port 80
│  └─ port 443
└─ Shared Network
```

### Scaling Architecture (Future)
```
Load Balancer
├─ Backend Cluster
│  ├─ Instance 1
│  ├─ Instance 2
│  └─ Instance 3
├─ Frontend CDN
└─ Database Cluster
```

## 📈 Performance Considerations

### Frontend Optimization
- Code Splitting with Vite
- Component Lazy Loading
- Image Optimization
- CSS Minification
- Production Build (~150KB gzipped)

### Backend Optimization
- Async I/O Operations
- Connection Pooling
- Caching Strategies
- Database Query Optimization
- Background Tasks

### Network Optimization
- Gzip Compression
- CDN Usage
- Connection Keep-Alive
- Request/Response Optimization

## 🔄 API Design Patterns

### RESTful Endpoints
```
GET    /api/status              - System status
GET    /api/system-info         - System information

POST   /api/security/scan       - Run security scan
POST   /api/security/configure  - Configure security
GET    /api/security/status     - Get security status

GET    /api/users               - List users
POST   /api/users/create        - Create user
DELETE /api/users/{username}    - Delete user

POST   /api/devenv/configure    - Setup dev environment
GET    /api/devenv/status       - Dev environment status

POST   /api/webserver/configure - Setup web server
GET    /api/webserver/status    - Web server status

POST   /api/mail/configure      - Setup mail server
GET    /api/mail/status         - Mail server status

POST   /api/install/start       - Start installation
GET    /api/install/progress    - Installation progress
```

## 🛠️ Development Workflow

```
1. Design Phase
   ├─ API Design (OpenAPI/Swagger)
   └─ UI Mockups (Figma)

2. Implementation Phase
   ├─ Backend Development
   │  └─ Module by module
   ├─ Frontend Development
   │  └─ Component by component
   └─ Integration Testing

3. Testing Phase
   ├─ Unit Tests
   ├─ Integration Tests
   ├─ E2E Tests
   └─ Security Audit

4. Deployment Phase
   ├─ Docker Build
   ├─ Registry Push
   ├─ Production Deploy
   └─ Monitoring
```

---

**Version:** 1.0.0  
**Architecture Pattern:** Monolithic with Modular Backend  
**Scalability:** Horizontal Scaling Ready (Future)  
**Maintainability:** High (Clear Separation of Concerns)
