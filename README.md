# Traditional Knowledge Database with Multilingual OCR Annotation

## Overview

The Traditional Knowledge Database with Multilingual OCR Annotation is a Flask-based web application developed to preserve, manage, and retrieve traditional knowledge manuscripts. The system supports multilingual text management in English, Tamil, and Sanskrit, integrates Optical Character Recognition (OCR) using Tesseract for digitizing manuscript images, and provides role-based access for administrators and users. It uses MySQL for structured data storage and MongoDB for storing OCR annotations, creating a hybrid database solution for efficient management of traditional knowledge.

---

## Features

- Role-based authentication (Admin & User)
- Add traditional knowledge records
- Advanced search by title and author
- View approved manuscripts
- Update records (Admin)
- Delete records (Admin)
- Approve user submissions (Admin)
- OCR-based manuscript annotation using Tesseract
- Multilingual OCR support (English, Tamil, and Sanskrit)
- MySQL database for structured text records
- MongoDB database for OCR annotation storage
- Responsive and user-friendly Bootstrap interface

---

## Technologies Used

- Python
- Flask
- MySQL
- MongoDB
- HTML5
- CSS3
- Bootstrap 5
- Tesseract OCR
- PyTesseract
- Pillow

---

## OCR Language Support

- English
- Tamil
- Sanskrit

---

## Project Structure

```text
traditional_knowledge_app/
│── app.py
│── templates/
│── static/
│── uploads/
│── requirements.txt
│── README.md
```

---

## Future Enhancements

- Cloud deployment
- AI-based OCR error correction
- Semantic search for traditional texts
- Knowledge graph integration
- PDF and document OCR support
- Translation of multilingual manuscripts
- Export OCR results to PDF and Word

---

## Author

**Mangai S**  
M.Sc. Data Science  
SASTRA Deemed to be University

---

## Internship Theme

This project was developed under the **Database Design and Retrieval Systems** theme of the **Active Learning 2025** internship program. The project focuses on designing an efficient database system for storing, retrieving, and managing multilingual traditional knowledge manuscripts, while integrating OCR-based annotation using Tesseract, MySQL, and MongoDB.
