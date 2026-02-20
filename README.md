# StudyItUp - AI Study Planner

An intelligent study planning application that generates personalized study schedules, quizzes, and analytics using Azure OpenAI.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Azure OpenAI API Key**

---

## 🚀 Quick Start (Windows)

Open three separate terminals to run the full stack:

### Terminal 1: Backend Server
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: MLflow UI (Tracking)
```bash
cd backend
venv\Scripts\activate
mlflow ui
```
*Access MLflow at: http://localhost:5000*

### Terminal 3: Frontend Client
```bash
cd frontend
npm run dev
```
*Access App at: http://localhost:5173*

---

## 🛠️ Detailed Setup

### 1. Backend Setup

Navigate to the backend directory:
```bash
cd backend
```

**Create and Activate Virtual Environment:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Install Dependencies:**
```bash
pip install -r requirements.txt
```

**Configuration:**
1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```
2. Open `.env` and configure your Azure OpenAI credentials and Database URL.

### 2. Frontend Setup

Navigate to the frontend directory:
```bash
cd frontend
```

**Install Dependencies:**
```bash
npm install
```

**Configuration:**
1. Create a `.env` file in the `frontend` directory:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

## 📚 Features available

- **AI Study Planner:** Generates detailed study schedules based on your goals.
- **Knowledge Validator:** Take AI-generated quizzes to test your understanding.
- **Test Center:** Upload documents or paste text to generate exam-style questions.
- **Analytics:** Track your progress with detailed metrics and MLflow integration.

