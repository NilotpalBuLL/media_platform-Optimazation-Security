# Media Platform Analytics (Task-3)

A FastAPI-based project that provides authentication and analytics features with Redis integration.  
This project demonstrates building APIs with secure user signup/login, token-based authentication, and real-time data storage.

---

## 🚀 Features
- User authentication (signup & login) with JWT tokens  
- Redis integration for session/token caching  
- FastAPI auto-generated Swagger docs  
- Modular code structure (auth, models, services)

---

## 🛠️ Tech Stack
- **Backend:** FastAPI (Python)  
- **Database:** Redis (Dockerized)  
- **Auth:** JWT (JSON Web Tokens)  
- **Containerization:** Docker (optional)

---

````

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/YOUR-USERNAME/media-platform-T3.git
cd media-platform-T3
````

### 2️⃣ Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
.venv\Scripts\activate       # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run Redis (via Docker)

```bash
docker run -p 6379:6379 -d redis:7
```

### 5️⃣ Start FastAPI

```bash
uvicorn app.main:app --reload
```

Now open 👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 API Endpoints

### 🔹 User Signup

`POST /auth/signup`

Request:

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "mypassword"
}
```

### 🔹 User Login

`POST /auth/login`

Request:

```json
{
  "username": "testuser",
  "password": "mypassword"
}
```

Response:

```json
{
  "access_token": "your-jwt-token",
  "token_type": "bearer"
}
```

---

## 📦 Deployment

You can upload this repo to GitHub and later deploy with services like:

* Docker + VPS
* Render / Railway / Azure / AWS

---

## 👨‍💻 Author

Developed by **Nilotpal Sarma** 🚀