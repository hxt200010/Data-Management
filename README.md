# 🏢 Insurance CRM - Customer Data Management

A modern Customer Relationship Management (CRM) system built for insurance companies, demonstrating **Python**, **Flask**, **SQLite**, and full **CRUD operations** with data validation.

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-green?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue?logo=sqlite)

---

## ✨ Features

| Feature                | Description                                                |
| ---------------------- | ---------------------------------------------------------- |
| 🔄 **CRUD Operations** | Create, Read, Update, Delete for customers and policies    |
| ✅ **Data Validation** | Server-side validation with regex patterns for email/phone |
| 🔍 **Search & Filter** | Real-time search across customer fields                    |
| 📄 **Pagination**      | Configurable page sizes (5, 10, 25, 50 records)            |
| 📊 **Dashboard**       | Live statistics with policy expiration alerts              |
| 📥 **CSV Export**      | Export customers and policies data                         |
| 🎨 **Modern UI**       | Dark theme with glassmorphism design                       |

---

## 🛠️ Tech Stack

```
┌─────────────────────────────────────────────────────┐
│                    Frontend                         │
│  HTML5 • CSS3 • Vanilla JavaScript • Fetch API     │
├─────────────────────────────────────────────────────┤
│                    Backend                          │
│  Python 3 • Flask (Web Framework)                  │
├─────────────────────────────────────────────────────┤
│                    Database                         │
│  SQLite (File-based, Zero Configuration)           │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Database Schema

### Entity Relationship Diagram

```
┌─────────────────────┐         ┌─────────────────────────┐
│     customers       │         │       policies          │
├─────────────────────┤         ├─────────────────────────┤
│ id (PK)            │◄────────┤ customer_id (FK)        │
│ name               │    1:N  │ id (PK)                 │
│ email (UNIQUE)     │         │ policy_type             │
│ phone              │         │ policy_number (UNIQUE)  │
│ address            │         │ premium                 │
│ created_at         │         │ start_date              │
└─────────────────────┘         │ end_date                │
                                │ status                  │
                                │ created_at              │
                                └─────────────────────────┘
```

### SQL Schema

```sql
-- Customers Table
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Policies Table
CREATE TABLE policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    policy_type TEXT NOT NULL,           -- 'auto', 'home', 'life', 'health'
    policy_number TEXT UNIQUE NOT NULL,
    premium REAL NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT DEFAULT 'active',        -- 'active', 'expired', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
);
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version       | Check Command      |
| ----------- | ------------- | ------------------ |
| Python      | 3.8 or higher | `python --version` |
| pip         | Latest        | `pip --version`    |
| Git         | Any           | `git --version`    |

---

### 📥 Step 1: Clone the Repository

```bash
# Clone via HTTPS
git clone https://github.com/YOUR_USERNAME/Data-Management.git

# Or clone via SSH (if you have SSH keys configured)
git clone git@github.com:YOUR_USERNAME/Data-Management.git

# Navigate into the project folder
cd Data-Management
```

> 💡 **Tip**: Replace `YOUR_USERNAME` with your actual GitHub username after pushing to your repository.

---

### 🔧 Step 2: Create Virtual Environment

A virtual environment keeps your project dependencies isolated.

**Windows (PowerShell or CMD):**

```powershell
python -m venv venv
```

**macOS / Linux:**

```bash
python3 -m venv venv
```

---

### ⚡ Step 3: Activate Virtual Environment

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

> ⚠️ **PowerShell Execution Policy Error?** Run this first:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**Windows (Command Prompt):**

```cmd
venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

✅ You'll know it's activated when you see `(venv)` at the beginning of your terminal prompt.

---

### 📦 Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

- **Flask** - Python web framework

---

### 🚀 Step 5: Run the Application

```bash
python app.py
```

You should see output like:

```
==================================================
  Insurance CRM System
  Open: http://127.0.0.1:5000
==================================================

Database initialized successfully!
 * Running on http://127.0.0.1:5000
```

---

### 🌐 Step 6: Open in Browser

Open your web browser and go to:

```
http://127.0.0.1:5000
```

or

```
http://localhost:5000
```

🎉 **You should now see the Insurance CRM dashboard!**

---

### 🛑 Stopping the Application

Press `Ctrl + C` in the terminal to stop the server.

To deactivate the virtual environment:

```bash
deactivate
```

---

### 🔄 Quick Commands Reference

| Action                             | Command                           |
| ---------------------------------- | --------------------------------- |
| Activate venv (Windows PowerShell) | `.\venv\Scripts\Activate.ps1`     |
| Activate venv (Windows CMD)        | `venv\Scripts\activate.bat`       |
| Activate venv (macOS/Linux)        | `source venv/bin/activate`        |
| Install dependencies               | `pip install -r requirements.txt` |
| Run application                    | `python app.py`                   |
| Stop server                        | `Ctrl + C`                        |
| Deactivate venv                    | `deactivate`                      |

---

### ❓ Troubleshooting

| Issue                   | Solution                                                           |
| ----------------------- | ------------------------------------------------------------------ |
| `python` not found      | Try `python3` instead, or add Python to your PATH                  |
| PowerShell script error | Run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`          |
| Port 5000 in use        | Change port in `app.py`: `app.run(debug=True, port=5001)`          |
| Module not found        | Ensure venv is activated and run `pip install -r requirements.txt` |

---

## 📁 Project Structure

```
Data Management/
├── app.py              # Flask application & REST API routes
├── database.py         # SQLite database operations & CRUD functions
├── requirements.txt    # Python dependencies
├── customers.db        # SQLite database file (auto-generated)
├── templates/
│   └── index.html      # Frontend UI (single-page application)
├── venv/               # Virtual environment (gitignored)
└── README.md           # Project documentation
```

---

## 🔌 API Endpoints

### Customers API

| Method   | Endpoint              | Description                               |
| -------- | --------------------- | ----------------------------------------- |
| `GET`    | `/api/customers`      | List customers (with pagination & search) |
| `POST`   | `/api/customers`      | Create new customer                       |
| `GET`    | `/api/customers/<id>` | Get customer by ID                        |
| `PUT`    | `/api/customers/<id>` | Update customer                           |
| `DELETE` | `/api/customers/<id>` | Delete customer                           |

### Policies API

| Method   | Endpoint             | Description       |
| -------- | -------------------- | ----------------- |
| `GET`    | `/api/policies`      | List all policies |
| `POST`   | `/api/policies`      | Create new policy |
| `GET`    | `/api/policies/<id>` | Get policy by ID  |
| `PUT`    | `/api/policies/<id>` | Update policy     |
| `DELETE` | `/api/policies/<id>` | Delete policy     |

### Dashboard & Export

| Method | Endpoint                | Description             |
| ------ | ----------------------- | ----------------------- |
| `GET`  | `/api/stats`            | Dashboard statistics    |
| `GET`  | `/api/export/customers` | Export customers as CSV |
| `GET`  | `/api/export/policies`  | Export policies as CSV  |

---

## 📝 API Usage Examples

### Create Customer

```bash
curl -X POST http://127.0.0.1:5000/api/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-123-4567",
    "address": "123 Main St"
  }'
```

### Get Paginated Customers

```bash
curl "http://127.0.0.1:5000/api/customers?page=1&per_page=10&search=john"
```

### Create Policy

```bash
curl -X POST http://127.0.0.1:5000/api/policies \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "policy_type": "auto",
    "policy_number": "POL-001",
    "premium": 1200.00,
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "status": "active"
  }'
```

---

## ✅ Validation Rules

### Customer Validation

- **Name**: Required, non-empty
- **Email**: Required, valid email format (regex validated)
- **Phone**: Optional, pattern `[\d\s\-\+\(\)]{7,20}`

### Policy Validation

- **Customer ID**: Required, must exist
- **Policy Type**: Required (`auto`, `home`, `life`, `health`)
- **Policy Number**: Required, unique
- **Premium**: Required, > 0
- **Dates**: Start and end dates required

---

## 🎯 Skills Demonstrated

- **Python**: OOP, modules, exception handling
- **Flask**: Routes, templates, JSON API, request handling
- **SQL**: DDL, DML, JOINs, aggregations, parameterized queries
- **Web Development**: REST API design, SPA architecture
- **Data Validation**: Regex patterns, server-side validation
- **Database Design**: Normalization, foreign keys, constraints

---

## 📄 License

MIT License - Feel free to use this project for learning and development.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
