# Database Management System
**A comprehensive web-based database management and visualization system for analyzing World Development Indicators (WDI) data across multiple domains**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-Educational-yellow.svg)](LICENSE)

*Developed as a term project for **BLG-317E (Database Systems)** course*

</div>

---

## Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
  - [Prerequisites](#prerequisites)
  - [Step-by-Step Setup](#step-by-step-setup)
  - [Database Setup](#database-setup)
  - [Environment Configuration](#environment-configuration)
  - [Data Loading Scripts](#-important-data-loading-scripts)
- [Usage](#-usage)
- [Database Schema](#-database-schema)
- [Role-Based Access Control](#-role-based-access-control)
- [Data Domains](#-data-domains)
- [API Endpoints](#-api-endpoints)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## Overview

This **Database Management System** provides an interactive platform for exploring, analyzing, and managing multi-domain indicator data from the World Development Indicators dataset. The system enables users to:

- Browse and filter country-level and regional data
- Visualize trends through interactive charts and maps
- Perform cross-country comparisons
-  Analyze time-series data with trend calculations
- Manage data through role-based CRUD operations
- Track data modifications via audit logging

---

## Features

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
- **Pagination**: Efficient handling of large datasets (50 records per page)

### User Experience

- **Responsive Design**: Works seamlessly on desktop and tablet devices
- **Smooth Animations**: Subtle UI animations for enhanced user experience
- **Tooltips & Helpers**: Contextual information throughout the interface
- **Search Functionality**: Quick search across countries and indicators

### Security & Access Control

- **Role-Based Access Control (RBAC)**: Three distinct user roles
  - **Viewer**: Read-only access to all data
  - **Editor**: Can add and edit records
  - **Admin**: Full CRUD access including delete operations
- **Audit Logging**: Track data modifications with user attribution
- **Session Management**: Secure authentication and session handling

---

## Technology Stack

### Backend
- **Python 3.11+** - Programming language
- **Flask** - Web framework
- **MySQL 8.0+** - Relational database management system
- **mysql-connector-python** - MySQL database connector
- **python-dotenv** - Environment variable management

### Frontend
- **HTML5/CSS3** - Structure and styling
- **JavaScript (ES6+)** - Interactive functionality
- **Bootstrap 5.3** - Responsive UI framework
- **Chart.js 4.4** - Interactive chart rendering
- **Font Awesome 6.5** - Icon library

### Development Tools
- **Python Virtual Environment** - Dependency isolation
- **Git** - Version control

---

##  Project Structure

```
Database-Management-System/
├── App/
│   ├── routes/              # Flask route handlers
│   │   ├── __init__.py      # Application factory
│   │   ├── dashboard.py     # Dashboard overview
│   │   ├── countries.py     # Country management
│   │   ├── ghg.py           # GHG emissions domain
│   │   ├── health.py        # Health indicators domain
│   │   ├── energy.py        # Energy data domain
│   │   ├── freshwater.py    # Freshwater resources domain
│   │   ├── sustainability.py # Sustainability metrics
│   │   ├── login.py         # Authentication & RBAC
│   │   └── about.py         # About page
│   ├── db.py                # Database connection utilities
│   ├── models.py            # Data models
│   └── db_setup.py          # Database setup utilities
├── Data/                    # CSV data files
│   ├── countries.csv
│   ├── greenhouse_emissions.csv
│   ├── health_system.csv
│   ├── energy_data.csv
│   ├── freshwater_data.csv
│   ├── sustainability_data.csv
│   └── *_indicator_details.csv
├── SQL/                     # SQL scripts
│   ├── database.sql         # Database schema
│   └── load_*.sql           # Data loading scripts
├── frontend/
│   ├── css/
│   │   ├── style.css        # Global styles
│   │   └── templates/       # Jinja2 templates
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       ├── ghg_list.html
│   │       └── ...
├── scripts/                 # Utility scripts
│   ├── load_all.py          # Load all CSV data
│   ├── load_user.py         # Seed user accounts
│   └── load_countries.py    # Load country data
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
└── README.md                # This file
```

---

## Installation

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher** - [Download Python](https://www.python.org/downloads/)
- **MySQL 8.0 or higher** - [Download MySQL](https://dev.mysql.com/downloads/mysql/)
- **pip** - Python package manager (usually comes with Python)
- **Git** - [Download Git](https://git-scm.com/downloads)

### Step-by-Step Setup

#### Step 1: Clone the Repository

```bash
git clone https://github.com/s4l1hs/Database-Management-System.git
cd Database-Management-System
```

#### Step 2: Create Virtual Environment

Create and activate a virtual environment to isolate project dependencies:

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Note**: If you encounter execution policy issues on Windows PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
 ```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Set Up MySQL Database

1. **Start MySQL Server** (if not already running)

2. **Create the Database:**
   ```sql
   CREATE DATABASE wdi_project CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. **Run the Database Schema Script:**
   ```bash
   # Windows
   mysql -u root -p wdi_project < SQL/database.sql
   
   # Linux/Mac
   mysql -u root -p wdi_project < SQL/database.sql
   ```

### Environment Configuration

Create a `.env` file in the project root directory with your database credentials:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=wdi_project
DB_PORT=3306
```

**Important**: Replace `root` with your actual MySQL root password if different.

The application will automatically load these environment variables using `python-dotenv`.

### Important: Data Loading Scripts

**CRITICAL**: You must run the data loading scripts in the correct order for the application to work properly.

#### Step 5: Load All Data (Run First!)

This script loads all CSV data files into the database. **This must be run BEFORE loading users.**

```bash
# Using venv Python (recommended)
.\venv\bin\python.exe scripts/load_all.py

# Or if venv is activated
python scripts/load_all.py
```

**What this script does:**
- Creates/drops and recreates the database schema
- Loads all CSV files from the `Data/` directory:
  - Countries data
  - GHG emissions data and indicators
  - Health system data and indicators
  - Energy data and indicators
  - Freshwater data and indicators
  - Sustainability data and indicators
- Handles data deduplication and foreign key relationships
- Disables foreign key checks during bulk loading for performance

#### Step 6: Load User Accounts (Run Second!)

After loading all data, seed the user accounts. **This must be run AFTER load_all.py.**

```bash
# Using venv Python (recommended)
.\venv\bin\python.exe scripts/load_user.py

# Or if venv is activated
python scripts/load_user.py
```

**What this script does:**
- Creates user accounts in the `students` table
- Sets up admin users (team_no = 1):
  - `820230313` - Salih Sefer
  - `820230334` - Atahan Evintan
  - `820230326` - Fatih Serdar Çakmak
  - `820230314` - Muhammet Tuncer
  - `150210085` - Gülbahar Karabaş
- Sets up editor user (team_no = 2):
  - `5454` - Editor User

 **Why this order matters:**
- `load_all.py` creates the database schema and loads all domain data
- `load_user.py` requires the database to exist and uses Flask app context
- Running `load_user.py` before `load_all.py` will fail because tables don't exist yet

---

## Usage

### Starting the Application

```bash
# Activate virtual environment first (if not already activated)
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run the application
python main.py
```

The application will start and be available at: **http://localhost:5000**

### Default Login Credentials

After running `load_user.py`, you can log in with any of these accounts:

**Admin Accounts** (Full CRUD access):
- Student Number: `820230326` (Fatih Serdar Çakmak)
- Student Number: `820230313` (Salih Sefer)
- Student Number: `820230334` (Atahan Evintan)
- Student Number: `820230314` (Muhammet Tuncer)
- Student Number: `150210085` (Gülbahar Karabaş)

**Editor Account** (Add/Edit only):
- Student Number: `5454` (Editor User)

**Note**: Password is not required - authentication is based on student number only for this educational project.

### Navigation

- **Dashboard** (`/dashboard`) - Overview of key indicators and trends
- **Countries** (`/countries`) - Browse countries and regional data
- **Health** (`/health`) - Health indicators and statistics
- **GHG Emissions** (`/ghg`) - Greenhouse gas emissions by country and year
- **Energy** (`/energy`) - Energy consumption and production data
- **Freshwater** (`/freshwater`) - Freshwater resources and usage
- **Sustainability** (`/sustainability`) - Sustainability metrics and environmental indicators

---

## Database Schema

### Core Tables

- **`countries`** - Country information (name, code, region)
- **`students`** - User accounts with role assignments (team_no determines role)
- **`audit_logs`** - Track data modifications with user attribution

### Domain-Specific Tables

- **`greenhouse_emissions`** + **`ghg_indicator_details`** - GHG emission data
- **`health_system`** + **`health_indicator_details`** - Health indicator data
- **`energy_data`** + **`energy_indicator_details`** - Energy consumption/production data
- **`freshwater_data`** + **`freshwater_indicator_details`** - Freshwater resource data
- **`sustainability_data`** + **`sustainability_indicator_details`** - Sustainability metrics

See `SQL/database.sql` for complete schema definition with relationships and constraints.

---

## Role-Based Access Control

The system uses `team_no` field in the `students` table to determine user roles:

### Viewer (Default)
- Read-only access to all dashboards and data
- No add, edit, or delete capabilities
- No access to admin interfaces

### Editor (team_no = 2)
- Can add new records
- Can edit existing records
- Cannot delete records
- Cannot manage users or system settings

### Admin (team_no = 1)
- Full CRUD access (Create, Read, Update, Delete)
- User and role management
- System administration capabilities
- Audit log access

---

## Data Domains

### 1. Countries
- Country profiles with comprehensive statistics
- Regional aggregations
- Interactive world map visualization
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

---

## API Endpoints

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
- `GET /ghg` - List GHG emissions data (paginated, 50 per page)
- `POST /ghg/api/add` - Add new GHG record (Editor/Admin)
- `POST /ghg/api/edit/<id>` - Edit GHG record (Editor/Admin)
- `POST /ghg/api/delete/<id>` - Delete GHG record (Admin)
- `GET /ghg/api/get/<id>` - Get single GHG record
- `GET /ghg/api/countries` - Autocomplete countries

Similar endpoints exist for Health, Energy, Freshwater, and Sustainability domains.

---

## Troubleshooting

### Common Issues

**1. Database Connection Error**
- Verify MySQL server is running
- Check `.env` file exists and has correct credentials
- Ensure database `wdi_project` exists

**2. Import Errors**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

**3. Script Execution Order Error**
- **Always run `load_all.py` BEFORE `load_user.py`**
- If you ran them in wrong order, drop database and start over:
  ```sql
  DROP DATABASE wdi_project;
  CREATE DATABASE wdi_project CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```
  Then run scripts in correct order again.

**4. PowerShell Execution Policy Error (Windows)**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**5. Module Not Found Errors**
- Ensure you're in the project root directory
- Verify virtual environment is activated
- Check that all dependencies are installed

---

## License

This project is developed for **educational purposes** as part of the **BLG-317E Database Systems** course.

---

## Acknowledgments

- **World Bank** for providing World Development Indicators (WDI) dataset
- **Flask** and **Bootstrap** communities for excellent documentation
- **Chart.js** for powerful visualization capabilities
- Course instructors and teaching assistants

---
</div>
