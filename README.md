# Koun Banega Crorepati (KBC++)

A fun and interactive quiz game inspired by the popular KBC show. This project features a dynamic game interface, multiple lifelines, real-time score tracking, and an engaging user experience.

---

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Features](#features)
- [Configuration](#configuration)
- [Tech Stack](#tech-stack)
- [Folder Structure](#folder-structure)
- [Contributing](#contributing)
- [Authors & Acknowledgments](#authors--acknowledgments)
- [Contact Information](#contact-information)

---

## Installation

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/hadwikp/KBC_Project.git
   cd KBC_project
   ```

2. **Install Dependencies**  
   Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup MySQL Database**  
   Create a MySQL database named `kbc_game` and run the following SQL script to create the necessary table:
   ```sql
   CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    dob DATE NOT NULL,
    qualification VARCHAR(100) NOT NULL,
    status ENUM('waiting', 'accepted', 'rejected') DEFAULT 'waiting'
   );
   
   CREATE TABLE questions (
       id INT AUTO_INCREMENT PRIMARY KEY,
       question TEXT NOT NULL,
       difficulty VARCHAR(10) NOT NULL,
       category VARCHAR(50),
       correct_answer VARCHAR(255) NOT NULL,
       incorrect_answers JSON NOT NULL
   );
   ```

4. **Configure Environment Variables**  
   Update your database credentials and secret key in your configuration (e.g., in `app.py` or a `.env` file).

---

## Usage

1. **Run the Application**  
   ```bash
   python questions.py
   python app.py
   ```

2. **Access the Application**  
   - Open your browser and go to `http://127.0.0.1:5000/` to view the login page.
   - Use separate browsers or incognito mode to test multiple user sessions.

3. **Admin Login**  
   - Switch to the Administrator tab on the login page.
   - Use the default credentials:  
     **Admin ID:** `admin`  
     **Password:** `password`

---

## Features

- **Dynamic Game Interface:**  
  Interactive game screen with a question area, multiple-choice options, lifelines.
  
- **Real-Time Score Tracking:**  
  Visual representation of question levels and earnings.

- **Lifelines:**  
  Options like 50:50, Question Swap, and Audience Poll to assist players.

- **Responsive Design:**  
  Optimized for both desktop and mobile devices.

- **Role-Based Access:**  
  Separate interfaces for users and administrators.

---

## Configuration

- **Database Settings:**  
  Update your MySQL credentials in your configuration:
  ```python
  app.config['MYSQL_HOST'] = 'localhost'
  app.config['MYSQL_USER'] = 'root'
  app.config['MYSQL_PASSWORD'] = 'your_password' // your password of MYSQL
  app.config['MYSQL_DB'] = 'kbc_game'
  ```
  
- **Secret Key:**  
  Replace `'your_secret_key_here'` with a secure key for session management.

- **Static Assets:**  
  Place all images and other static files in the `static/` directory.

---

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript
- **Libraries:** flask-mysqldb, uuid

---

## Folder Structure

```

The project is organized as follows:

      
      KBC/
      │── __pycache__/              # Compiled Python files
      │── .github/workflows/        # GitHub Actions CI/CD pipeline
      │   └── ci.yml                # CI configuration file
      │── questions/                # Contains question-related data
      │   ├── _kbc_db.sql           # Database file
      |   │── easy.json                 # JSON file for easy-level questions
      |   │── medium.json               # JSON file for medium-level questions
      |   │── hard.json                 # JSON file for hard-level questions
      │── static/                   # Static files (CSS, JS, etc.)
      │   ├── css/                  # Stylesheets
      │   │   ├── admin_page.css
      │   │   ├── game.css
      │   │   ├── index.css
      │   │   ├── not_selected.css
      │   │   ├── waiting.css
      │   └── js/                   # JavaScript files
      │── templates/                # HTML templates for Flask
      │   ├── admin_page.html
      │   ├── exit.html
      │   ├── game.html
      │   ├── index.html
      │   ├── not_selected.html
      │   ├── waiting.html
      │── app.py                    # Flask application entry point
      │── questions.py              # For inserting questions in Database
      │── requirements.txt
      |── test_cmds.txt
      │── test_kbc.py               # Tests file
   
   ```

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Create a Pull Request.

---

## Authors & Acknowledgments

- **Primary Developer:** Hadwik , Rithvik
- **Special Thanks:** Prof. Debasis Samanta

---

## Contact Information

For questions or collaboration, please reach out at:
- **Email:** phadwik65@gmail.com  , rikki010620@gmail.com
- **GitHub:** https://github.com/hadwikp  ,  https://github.com/rikkicoder

---

Feel free to modify this template as needed for your KBC++ project!
