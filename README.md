# 💖 Sidney Dating App – Backend API

Scalable **Django REST API backend** for a modern dating application with real-time chat, subscription system, matchmaking logic, and high-performance async architecture.

🔗 **GitHub Repository**: https://github.com/TechbyAbrar/dating_app.git
🎨 **Figma Design**: https://www.figma.com/design/O4YKjMg3xUvgfgpR9sWRqc/carricamp-%7C%7C-Sidneby’s-Dating-App%7C%7C
🌐 **Live Link**: *(Add when deployed)*

---

## 📌 Overview

Sidney Dating App Backend is designed for a **real-time, scalable dating platform** supporting:

* user authentication (multi-login)
* matchmaking system
* real-time messaging
* subscription-based access
* notifications & engagement

The system is built with **async-first architecture** and supports:

* WebSocket communication
* background jobs (Celery)
* caching (Redis)
* scalable mobile APIs

---

## 🧠 Core Features

* 🔐 JWT Authentication (SimpleJWT)
* 👤 Custom User Model (`account.User`)
* 🔑 Multi-login (email / phone / username)
* ❤️ Matchmaking System (mutual system)
* 💬 Real-time Chat (Django Channels)
* 🔔 Notification System
* 💳 Subscription System (Stripe + RevenueCat)
* ⚡ Redis Caching Layer
* 🧠 Background Jobs (Celery + Celery Beat)
* 📧 Email Integration (SMTP)
* 📜 Advanced Logging System
* 📡 API Documentation (drf-spectacular)

---

## 🏗️ Architecture Overview

Client (Mobile App)
↓
Frontend (Figma-based UI)
↓
Django REST API Backend
↓

| Auth Layer (Custom Backend + JWT) |
| Matchmaking Engine (Mutual Logic) |
| Chat System (WebSocket Layer)     |
| Subscription & Billing System     |
| Notification System              |
| Background Task Processing       |
| Logging & Monitoring             |

```id="a1d9s8"
    ↓
```

PostgreSQL Database
↓
External Services:

* Redis (Channels + Cache + Celery Broker)
* Stripe API
* RevenueCat API
* SMTP Email Server

---

## ⚙️ Tech Stack

| Category     | Technology            |
| ------------ | --------------------- |
| Language     | Python 3.11+          |
| Framework    | Django 5.2.x          |
| API          | Django REST Framework |
| Realtime     | Django Channels       |
| Broker       | Redis                 |
| Cache        | Redis (django-redis)  |
| Background   | Celery + Celery Beat  |
| Database     | PostgreSQL            |
| Auth         | Simple JWT            |
| API Docs     | drf-spectacular       |
| Payments     | Stripe + RevenueCat   |
| Static Files | WhiteNoise            |
| Logging      | Timed Rotating Logs   |

---

## 📁 Project Structure

```text id="b7c4d2"
core/
account/
privacy/
subscription/
mutual_system/
chat/
notification/

media/
staticfiles/
logs/

manage.py
requirements.txt
README.md
```

---

## 🔐 Authentication System

Supports login via:

* email
* phone
* username

### JWT Configuration

* Access Token: 15 days
* Refresh Token: 30 days

```text id="c2f8e1"
Authorization: Bearer <access_token>
```

---

## ❤️ Matchmaking System

* Mutual interaction-based matching
* Story/view tracking
* Redis-powered engagement counters
* Scheduled cleanup via Celery

---

## 💬 Real-time Chat System

* Built with Django Channels
* Redis channel layer
* WebSocket-based messaging

---

## 💳 Subscription System

* Stripe payment integration
* RevenueCat webhook handling
* Access control based on subscription

---

## 🔔 Notification System

* Real-time & async notifications
* Extendable for:

  * push notifications
  * email alerts
  * in-app messages

---

## ⚡ Background Jobs (Celery)

* Periodic tasks using Celery Beat:

| Task                         | Schedule     |
| ---------------------------- | ------------ |
| Cleanup expired stories      | Hourly       |
| Sync Redis view counts to DB | Every 10 min |

---

## 📡 API Features

* JWT-secured endpoints
* Pagination enabled
* Multipart/form-data support
* Custom exception handling
* Swagger documentation

---

## 📡 API Documentation

```text id="d9a7e2"
/api/schema/swagger-ui/
```

---

## 🌐 Environment Configuration

Create `.env` file:

```env id="e4b9c3"
SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_URL=postgres://user:password@host:port/dbname

EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password

STRIPE_SECRET_KEY=your-secret
STRIPE_WEBHOOK_SECRET=your-webhook

REVENUECAT_WEBHOOK_SECRET=your-secret
REVENUECAT_API_KEY=your-api-key

SITE_BASE_URL=http://localhost:8000
```

---

## 🚀 Installation & Setup

```bash id="f3c8d1"
git clone https://github.com/TechbyAbrar/dating_app.git
cd dating_app

python -m venv env
source env/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

---

## ⚡ Run Services (Required)

### Start Redis

```bash id="g7d2a4"
redis-server --port 6379
```

Verify:

```bash id="h8e1c9"
redis-cli ping
# Output: PONG
```

---

### Run Celery Worker

```bash id="i5f3b2"
celery -A core worker -l info
```

---

### Run Celery Beat

```bash id="j6c7d8"
celery -A core beat -l info
```

---

## 🚀 Production Deployment (ASGI)

```bash id="k9e2f1"
gunicorn core.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --workers 4 \
  --threads 2 \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --max-requests 2000 \
  --max-requests-jitter 200 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

---

## 🧾 Logging System

Logs stored in `/logs/`:

| File       | Purpose      |
| ---------- | ------------ |
| access.log | Request logs |
| error.log  | Error logs   |

* Daily rotation
* 7-day retention

---

## 🧪 Future Improvements

* AI-based matchmaking
* Recommendation engine
* Push notifications (FCM)
* Docker + Kubernetes deployment
* Microservices architecture

---

## 🔐 Security Notes

* Use `.env` for secrets
* Disable DEBUG in production
* Configure ALLOWED_HOSTS
* Restrict CORS origins
* Enable HTTPS

---

## 🤝 Contribution

Pull requests are welcome.

---

## 📄 License

Private / Proprietary

---

## 👨‍💻 Author

**Abraham Qureshi**
Backend Engineer | Django | FastAPI | AI Systems

🔗 GitHub: https://github.com/TechbyAbrar
