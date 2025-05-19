
# 📚 Kitaabi Keeda - Library Management System

## Overview

**Kitaabi Keeda** is a multi-user e-book lending web application designed to facilitate seamless interaction between users and librarians. Users can request, read, and return e-books, while librarians manage sections, control access, and analyze usage through dashboards.

## 🔧 Tech Stack

- **Languages**: Python, HTML/CSS, JavaScript (Minor)
- **Frameworks & Libraries**: Flask, Flask-RESTful, SQLite3, Matplotlib, fpdf
- **Tools**: DBeaver (for DB), SQLite3, REST APIs

## 🎯 Core Functionalities

### 👥 User Side

- View sections and books by category
- Request to borrow books for desired days
- View issued books and return before due date
- Review books and influence book rankings
- Search books by name or author
- Download PDF version after payment

### 🛠️ Admin Side

- Manage sections and books (Add/Edit/Delete)
- Approve/reject book issue requests
- View current borrows and revoke if needed
- Auto-remove expired book access
- View analytics dashboard with graphs (usage, demand, etc.)

### 🔒 Security & Validation

- Backend & frontend form validations
- SQL injection prevention with parameterized queries
- Automatic field filling for integrity
- Secure API access with data validation

## 📊 Analytics Dashboard

Admins can access a visual dashboard with Matplotlib graphs reflecting system metrics, usage trends, and popular books.

## 🗂️ Database Schema

- **sections**: Category list of books
- **books**: Details of each book
- **users**: Registered users
- **issuerequest**: Pending requests
- **issuedata**: Approved issued books
- **feedback**: User reviews and ratings

## 🚀 Business/Startup Viability

### Problem
New indie authors struggle to get visibility and fair compensation through traditional publishing.

### Solution
Transform Kitaabi Keeda into a book-testing platform where:
- Indie authors upload books for feedback and exposure
- Readers pay a small fee to rent and review books
- Analytics & ratings help authors pitch to publishers

## 🧪 Demo

📽️ [Watch Project Demo](https://drive.google.com/file/d/1oH88q8s8Ym5y6uboN0FJPptN0_1JTEo6/view?usp=sharing)

## 📁 Project Structure

```
KitaabiKeeda/
├── project/
│   ├── static/           # Graphs, Images, PDFs
│   ├── templates/        # HTML templates (18 files)
│   ├── api.py            # Backend API
│   ├── app.py            # Main Flask App
│   ├── maindb.db         # SQLite Database
│   └── requirements.txt  # Python Dependencies
└── Project Report.pdf
```
