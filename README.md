# POS Management System (Django)

A **full-featured Point of Sale (POS) software** built with **Django**, designed for small to medium businesses to manage inventory, sales, purchases, customers, vendors, and reports efficiently.

This system supports **barcode-based sales**, **stock & expiry tracking**, **customer due management**, and **role-based user access**.

---

## 🚀 Key Features

### 📦 Product & Inventory
- Create and manage products
- Stock in / stock out management
- Automatic stock update on purchase & sale
- Expiry date tracking for products
- Low stock & expired product visibility

---

### 🛒 Purchase Management
- Create purchase orders
- Receive purchased products
- Vendor-wise purchase tracking
- Purchase product return system
- Vendor payment management
- Purchase history & reports

---

### 💰 Sales System (POS)
- Barcode-based sales
- Real-time stock deduction
- Sale product return
- Daily sales report
- Sales history & invoice generation

---

### 👥 Customer Management
- Customer-wise sales tracking
- Due purchase system
- Customer payment & due adjustment
- Customer due reports

---

### 🧾 Reports
- Daily sales report
- Purchase reports
- Customer due reports
- Vendor payment reports
- Stock & expiry reports

---

### 🔐 User & Access Control
- User authentication system
- User-wise access & permissions
- Admin and staff role separation
- Secure session handling

---

## 🛠 Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, Bootstrap 5, JS
- **Database:** MySQL
- **Authentication:** Django Auth
- **Reporting:** Django ORM, ReportLab
- **Version Control:** Git & GitHub

---

## 📂 Project Structure
shop_man/
├── core/
│ ├── models.py
│ ├── views.py
│ ├── urls.py
│ ├── middleware.py
│ └── templates/
├── shop_man/
│ ├── settings.py
│ ├── urls.py
│ └── wsgi.py
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/ayshaakter231194-netizen/your-repo-name.git
cd your-repo-name
2️⃣ Create Virtual Environment
python -m venv env
env\Scripts\activate   # Windows
3️⃣ Install Dependencies
pip install -r requirements.txt
4️⃣ Environment Configuration

Create a .env file in the same folder as manage.py:

SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=shop_management
DB_USER=shop_user
DB_PASSWORD=strong_password
DB_HOST=localhost
DB_PORT=3306
5️⃣ Database Migration
python manage.py makemigrations
python manage.py migrate

6️⃣ Create Superuser
python manage.py createsuperuser

7️⃣ Run the Server
python manage.py runserver
Open:

http://127.0.0.1:8000/
