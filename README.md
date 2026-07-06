# Traditional Knowledge Archive System with Multilingual OCR Annotation

A Flask-based web application for preserving, managing, and retrieving traditional knowledge manuscripts using **Optical Character Recognition (OCR)** and a hybrid database architecture powered by **MySQL** and **MongoDB**.

---

## Project Overview

Traditional knowledge manuscripts contain valuable cultural and historical information but are often stored as handwritten or printed documents, making them difficult to preserve, search, and manage digitally.

This project provides a web-based platform for digitizing, annotating, storing, and retrieving multilingual traditional knowledge manuscripts. It integrates **Tesseract OCR** for text extraction and supports **English**, **Tamil**, and **Sanskrit** languages.

A hybrid database approach is used to efficiently manage both structured manuscript metadata and OCR annotation data.

- **MySQL** – Stores structured manuscript records.
- **MongoDB** – Stores OCR annotation data.

---

## Key Features

- Secure role-based authentication (Admin & User)
- Traditional knowledge record management
- OCR-based manuscript text extraction
- Multilingual OCR support
- Advanced search by title and author
- Admin approval workflow
- Update and delete records
- Hybrid database architecture (MySQL + MongoDB)
- Responsive Bootstrap-based user interface

---

## System Architecture

```
                 User
                   │
                   ▼
        Flask Web Application
                   │
      ┌────────────┴────────────┐
      ▼                         ▼
 Tesseract OCR             MySQL Database
      │                         │
      ▼                         ▼
 MongoDB (OCR Data)     Manuscript Metadata
      │
      ▼
 Search & Retrieval
```

---

## OCR Workflow

1. Upload a manuscript image.
2. Select the OCR language (English, Tamil, or Sanskrit).
3. Extract text using Tesseract OCR.
4. Store manuscript information in MySQL.
5. Store OCR annotations in MongoDB.
6. Search and retrieve manuscripts through the web interface.

---

## Technologies Used

| Category | Technologies |
|----------|--------------|
| Programming Language | Python |
| Backend | Flask |
| Frontend | HTML5, CSS3, Bootstrap 5 |
| OCR | Tesseract OCR, PyTesseract |
| Image Processing | Pillow |
| Database | MySQL, MongoDB |

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
├── render.yaml
├── README.md
│
├── static/
├── templates/
├── uploads/
├── database/
│   └── README.md
│
└── sanskrit_dict.json
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/MangaiS20/traditional_knowledge_app.git
```

Navigate to the project directory:

```bash
cd traditional_knowledge_app
```

Install the required packages:

```bash
pip install -r requirements.txt
```

---

## Prerequisites

Before running the application, install the following:

- Python 3.x
- Tesseract OCR
- MySQL
- MongoDB

Ensure that **Tesseract OCR** is installed and configured in your system PATH.

---

## Usage

Run the Flask application:

```bash
python app.py
```

Open your browser and visit:

```
http://127.0.0.1:5000
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

SASTRA Deemed to be University

**Python | Flask | OCR | MySQL | MongoDB | Data Science**

📧 **Email:** mangaiofficial20@gmail.com

💼 **LinkedIn:** https://www.linkedin.com/in/mangais20

---

⭐ If you find this project useful, consider giving it a star.
