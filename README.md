# Database Management System

A comprehensive web-based database management and visualization system built for analyzing World Development Indicators (WDI) data across multiple domains. This project is developed as a term project for the course **BLG-317E (Database Systems)**.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [Role-Based Access Control](#role-based-access-control)
- [Data Domains](#data-domains)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This Database Management System provides an interactive platform for exploring, analyzing, and managing multi-domain indicator data from the World Development Indicators dataset. The system enables users to:

- Browse and filter country-level and regional data
- Visualize trends through interactive charts and maps
- Perform cross-country comparisons
- Analyze time-series data with trend calculations
- Manage data through role-based CRUD operations
- Track data modifications via audit logging

## ✨ Features

### Core Functionality

- **Multi-Domain Data Management**: Support for 6 data domains (Countries, Health, GHG Emissions, Energy, Freshwater, Sustainability)
- **Interactive Dashboards**: Overview dashboards with key metrics and visualizations
- **Advanced Filtering**: Filter data by country, region, year, and indicator
- **Trend Analysis**: Automatic calculation of percentage changes and trends over time
- **Data Visualization**: 
  - Interactive line charts for time-series data
  - Global trend visualizations
  - Regional comparisons
  - Sparkline indicators
- **Geographic Visualization**: Interactive world map with country-level data
- **Data Export**: CSV export functionality for filtered datasets

### User Experience

- **Responsive Design**: Works seamlessly on desktop and tablet devices
- **Smooth Animations**: Subtle UI animations for enhanced user experience
- **Tooltips & Helpers**: Contextual information throughout the interface
- **Search Functionality**: Quick search across countries and indicators
- **Pagination**: Efficient handling of large datasets

### Security & Access Control

- **Role-Based Access Control (RBAC)**: Three distinct user roles
  - **Viewer**: Read-only access to all data
  - **Editor**: Can add and edit records
  - **Admin**: Full CRUD access including delete operations
- **Audit Logging**: Track data modifications with user attribution
- **Session Management**: Secure authentication and session handling

## 🛠 Technology Stack

### Backend
- **Python 3.11+**
- **Flask**: Web framework
- **MySQL**: Relational database management system
- **mysql-connector-python**: MySQL database connector
- **Pandas**: Data manipulation and analysis

### Frontend
- **HTML5/CSS3**: Structure and styling
- **JavaScript (ES6+)**: Interactive functionality
- **Bootstrap 5.3**: Responsive UI framework
- **Chart.js 4.4**: Interactive chart rendering
- **Font Awesome 6.5**: Icon library

### Development Tools
- **Python Virtual Environment**: Dependency isolation
- **Git**: Version control

## 📁 Project Structure

```
Database-Management-System/
├── App/
│   ├── routes/           # Flask route handlers
│   │   ├── dashboard.py  # Dashboard overview
│   │   ├── countries.py  # Country management
│   │   ├── ghg.py        # GHG emissions domain
│   │   ├── health.py     # Health indicators domain
│   │   ├── energy.py     # Energy data domain
│   │   ├── freshwater.py # Freshwater resources domain
│   │   ├── sustainability.py # Sustainability metrics
│   │   ├── login.py      # Authentication
│   │   └── about.py      # About page
│   ├── db.py             # Database connection utilities
│   └── models.py         # Data models
├── Data/                 # CSV data files
│   ├── countries.csv
│   ├── greenhouse_emissions.csv
│   ├── health_system.csv
│   └── ...
├── SQL/                  # SQL scripts
│   ├── database.sql      # Database schema
│   └── load_*.sql        # Data loading scripts
├── frontend/
│   ├── css/
│   │   ├── style.css     # Global styles
│   │   └── templates/    # Jinja2 templates
│   └── ...
├── scripts/              # Utility scripts
│   ├── seed_admin_and_editor.py
│   └── load_all.py
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- MySQL 8.0 or higher
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/s4l1hs/Database-Management-System.git
cd Database-Management-System
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up MySQL Database

1. Create a MySQL database:
```sql
CREATE DATABASE WDI CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Run the database schema script:
```bash
mysql -u root -p WDI < SQL/database.sql
```

3. Load initial data:
```bash
# Load countries
mysql -u root -p WDI < SQL/load-countries.sql

# Load other domain data (run as needed)
mysql -u root -p WDI < SQL/load_greenhouse_emissions.sql
mysql -u root -p WDI < SQL/load_health_system.sql
# ... etc
```

Alternatively, use Python scripts:
```bash
python scripts/load_all.py
```

## ⚙️ Configuration

### Database Configuration

Update database credentials in `App/db.py`:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "WDI",
    "charset": "utf8mb4"
}
```

### Flask Configuration

The application uses Flask's default configuration. For production, set environment variables:

```bash
export FLASK_ENV=production
export FLASK_SECRET_KEY=your_secret_key_here
```

## 💻 Usage

### Starting the Application

```bash
python main.py
```

The application will be available at `http://localhost:5000`

### Default Users

After running the seed script, you can log in with:

- **Admin**: Student Number `820230326`
- **Editor**: Student Number `820230327`

To add more users, run:
```bash
python scripts/seed_admin_and_editor.py
```

### Navigation

- **Dashboard**: Overview of key indicators and trends
- **Countries**: Browse countries and regional data
- **Health**: Health indicators and statistics
- **GHG Emissions**: Greenhouse gas emissions by country and year
- **Energy**: Energy consumption and production data
- **Freshwater**: Freshwater resources and usage
- **Sustainability**: Sustainability metrics and environmental indicators

## 🗄️ Database Schema

### Core Tables

- **countries**: Country information (name, code, region)
- **students**: User accounts with role assignments
- **audit_logs**: Track data modifications

### Domain-Specific Tables

- **greenhouse_emissions**: GHG emission data
- **ghg_indicator_details**: GHG indicator metadata
- **health_system**: Health indicator data
- **health_indicator_details**: Health indicator metadata
- **energy_data**: Energy consumption/production data
- **energy_indicator_details**: Energy indicator metadata
- **freshwater_data**: Freshwater resource data
- **freshwater_indicator_details**: Freshwater indicator metadata
- **sustainability_data**: Sustainability metrics
- **sustainability_indicator_details**: Sustainability indicator metadata

See `SQL/database.sql` for complete schema definition.

## 🔐 Role-Based Access Control

### Viewer (Default)
- Read-only access to all dashboards and data
- No add, edit, or delete capabilities
- No access to admin interfaces

### Editor
- Can add new records
- Can edit existing records
- Cannot delete records
- Cannot manage users or system settings

### Admin
- Full CRUD access (Create, Read, Update, Delete)
- User and role management
- System administration capabilities
- Audit log access

## 📊 Data Domains

### 1. Countries
- Country profiles with comprehensive statistics
- Regional aggregations
- Interactive world map
- Country comparison tools

### 2. GHG Emissions
- CO₂ total emissions
- CO₂ per capita
- Total greenhouse gas emissions
- Trend analysis with percentage changes
- Global CO₂ per capita trend visualization

### 3. Health
- Health system indicators
- Population health metrics
- Cross-country health comparisons

### 4. Energy
- Energy consumption data
- Energy production statistics
- Renewable energy indicators

### 5. Freshwater
- Freshwater resource availability
- Water usage metrics
- Water quality indicators

### 6. Sustainability
- Environmental sustainability metrics
- Resource management indicators
- Long-term sustainability trends

## 🔌 API Endpoints

### Authentication
- `GET/POST /login` - User authentication
- `GET /logout` - User logout

### Dashboard
- `GET /dashboard` - Main dashboard overview

### Countries
- `GET /countries` - List all countries
- `GET /countries/<country_id>` - Country profile
- `GET /countries/api/stats` - Global statistics API

### GHG Emissions
- `GET /ghg` - List GHG emissions data
- `POST /ghg/api/add` - Add new GHG record (Editor/Admin)
- `POST /ghg/api/edit/<id>` - Edit GHG record (Editor/Admin)
- `POST /ghg/api/delete/<id>` - Delete GHG record (Admin)
- `GET /ghg/api/get/<id>` - Get single GHG record

Similar endpoints exist for Health, Energy, Freshwater, and Sustainability domains.

## 🧪 Development

### Running in Development Mode

```bash
export FLASK_ENV=development
python main.py
```

### Database Migrations

For schema changes, update `SQL/database.sql` and run migration scripts.

### Adding New Domains

1. Create domain table in `SQL/database.sql`
2. Add route handler in `App/routes/`
3. Create template in `frontend/css/templates/`
4. Update navigation in `frontend/css/templates/base.html`


## 📄 License

This project is developed for educational purposes as part of the BLG-317E Database Systems course.



- World Bank for providing World Development Indicators (WDI) dataset
- Flask and Bootstrap communities for excellent documentation
- Chart.js for powerful visualization capabilities

---

**Note**: This project is for educational purposes. Ensure proper data attribution when using WDI data in production environments.
