# Train Booking Flask App

This is a simple Flask-based Train Ticket Booking System. It includes user interaction via a web interface and handles train booking logic on the backend.

## Features

- Flask web application
- Train booking logic
- Easy setup with virtual environment and `requirements.txt`

---

## 🛠 Installation & Setup

Follow these steps to get the project running on your local machine.

## 1. Clone or Download the Repository

If you haven't already, extract the contents of the ZIP you downloaded into a working directory.

## 2. Create a Virtual Environment (Recommended)

It's best to use a Python virtual environment to isolate dependencies.
```bash
#Navigate into the project folder
cd TrainBookingFlask

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

## 3. Install Dependencies
Make sure you're in the activated virtual environment, then run:
```bash
pip install -r requirements.txt
```

## 4. Redis Install
Get it from [here](https://github.com/microsoftarchive/redis/releases/tag/win-3.0.504) (it's safe, trust me)
1. Download and extract to C:/
2. open cmd in extracted folder
3. run "redis-server.exe"
4. leave in background

## 5. MongoDB
On Windows
1. Download the installer from the MongoDB Community Server
2. Follow the installation steps and select "Complete"
3. Make sure MongoDB is added to your system PATH
4. Open Command Prompt and run "mongod" to start server
---
On Linux
```bash
sudo apt update
sudo apt install -y mongodb
sudo systemctl enable mongodb
sudo systemctl start mongodb
```
Verify that it is running:
```bash
sudo systemctl status mongodb
```
To check if MongoDB responds:
```bash
mongo
```
---
## 🚀 Running the Application
Once the dependencies are installed, run the app:

```bash
python trainbook.py
```

The app should start on http://127.0.0.1:5000 by default.