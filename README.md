# Traditional Knowledge Database with Multilingual OCR Annotation

A Flask-based web application for preserving, managing, and retrieving traditional knowledge manuscripts using **Optical Character Recognition (OCR)** and a hybrid database architecture with **MySQL** and **MongoDB**.

---

## Project Overview

Traditional knowledge manuscripts often exist as handwritten or printed documents that are difficult to digitize, search, and preserve. This project provides a web-based platform that enables users to digitize, annotate, store, and retrieve multilingual traditional knowledge documents efficiently.

The application integrates **Tesseract OCR** to extract text from manuscript images and supports **English**, **Tamil**, and **Sanskrit** languages.

A hybrid database architecture is adopted:

- **MySQL** stores structured manuscript metadata.
- **MongoDB** stores OCR annotation data.

---

## Key Features

- Secure role-based authentication (Admin & User)
- Add and manage traditional knowledge records
- OCR-based manuscript text extraction
- Multilingual OCR support
- Advanced search by title and author
- Approval workflow for submitted manuscripts
- Update and delete records (Admin)
- Responsive Bootstrap user interface
- Hybrid database architecture (MySQL + MongoDB)

---

## System Architecture

```
User
      │
      ▼
Flask Web Application
      │
      ├──────────────┐
      ▼              ▼
Tesseract OCR     MySQL Database
      │              │
      ▼              ▼
MongoDB (OCR Annotations)
      │
      ▼
Search & Retrieval
```

---

## OCR Workflow

1. Upload manuscript image.
2. Select OCR language (English, Tamil, or Sanskrit).
3. Extract text using Tesseract OCR.
4. Store manuscript metadata in MySQL.
5. Store OCR annotations in MongoDB.
6. Retrieve and search manuscripts through the web interface.

---

## Technologies Used

| Category | Technologies |
|----------|--------------|
| Backend | Flask, Python |
| Database | MySQL, MongoDB |
| OCR | Tesseract OCR, PyTesseract |
| Image Processing | Pillow |
| Frontend | HTML5, CSS3, Bootstrap 5 |

---

## OCR Language Support

- English
- Tamil
- Sanskrit

---

## Project Structure

```
traditional_knowledge_app
│
├── app.py
├── requirements.txt
├── README.md
├── templates/
├── static/
├── uploads/
└── database/
```

---

## Screenshots

> Add screenshots of the following pages:

- Home Page
- Login Page
- OCR Annotation Page
- Search Page
- Admin Dashboard

---

## Installation

Clone the repository:

```bash
git clone https://github.com/MangaiS20/traditional_knowledge_app.git
```

Move into the project directory:

```bash
cd traditional_knowledge_app
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

---

## Future Enhancements

- Cloud deployment
- AI-assisted OCR error correction
- Semantic search for manuscripts
- Knowledge graph integration
- Translation support
- PDF and document OCR
- Export OCR results to PDF and Word

---

## Internship Project

This project was developed as part of the **Active Learning 2025 Internship** under the **Database Design and Retrieval Systems** theme.

The project was carried out under the guidance of **Dr. B. Santhi**, **Dean, Srinivasa Ramanujan Centre (SRC), SASTRA Deemed to be University**.

It demonstrates the integration of Optical Character Recognition (OCR), multilingual text processing, relational and NoSQL databases, and web application development for preserving and managing traditional knowledge manuscripts.

---

## Author

**Mangai S**

**M.Sc. Data Science**

SASTRA Deemed To Be University

Python | Flask | OCR | MySQL | MongoDB | Data Science

📧 Email: **mangaiofficial20@gmail.com**

💼 LinkedIn: **https://www.linkedin.com/in/mangais20**
