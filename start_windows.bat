@echo off
echo 🚀 Starting HuddleUp FAQ System...

echo 📡 Starting backend server...
cd backend
start "Backend Server" python main.py

echo Waiting for backend to initialize...
timeout /t 5

echo 🌐 Starting frontend server...
cd ..\frontend
start "Frontend Server" npm start

echo.
echo ✅ System started!
echo 🌐 Frontend: http://localhost:3000
echo 📡 Backend: http://localhost:8000  
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit...
pause