 **Backend Setup**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

**Configure Environment**
```bash
# Copy example env file
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac


**Run the Application**

Terminal 1 (Backend):
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```
