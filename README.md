# Gacha LOLection

## Introduction
Gacha LOLection is a platform that integrates the thrill of meme-based gacha rolls with auctions for trading gacha items. The backend architecture consists of microservices exposed with REST API for: authentication, profile management, gacha operations, auctions, and payment. 
This README provides instructions for setting up the backend, testing its functionality, and ensuring its security.
![Gacha LOLection Banner](./sfondo.webp)

https://github.com/user-attachments/assets/80846b2a-2239-47db-957a-4d4821d314a1
---

## Get Started

### Prerequisites
- Docker and Docker Compose installed
- Python 3.9+ installed (for local testing)
- locust installed (for performance testing)

### Installation
1. Clone the repository:
   ```bash
   git clone [https://github.com/username/gacha-lollection.git](https://github.com/isnotJack/SSE-project.git)
   cd gacha-lollection
   ```

2. Build and start the backend services using Docker Compose:
   ```bash
   docker compose up --build
   ```

3. Verify the services are running:
   Open `https://localhost:5001` in your browser to check the gateway, or use Postman to test individual endpoints.

---

## MicroFreshener Analysis
To analyze the microservices architecture:

1. Download MicroFreshener:
   ```bash
   docker pull microfreshener/microfreshener
   ```

2. Start MicroFreshener:
   ```bash
   docker compose up --build
   ```

3. Access it at `http://127.0.0.1:8080`.

---

## Testing

### CI/CD Testing
The project includes comprehensive CI/CD pipelines for automated testing:

1. **Unit Testing:**
   - Each microservice contains its unit tests.
   - Unit tests mock interactions with other services.
   - Postman collections for unit tests are available in every microservice folder.

2. **Integration Testing:**
   - Integration tests are defined in `.github/workflows`.
   - Postman collections for integration tests are exported and stored in this directory.
   - Both types of tests are defined as separate jobs in GitHub Actions and trigger on each push.

3. **Performance Testing:**
   - Install Locust:
     ```bash
     pip install locust
     ```
   - Ensure backend services are running.
   - Start Locust:
     ```bash
     locust -f locustfile.py
     ```
   - Access results at `http://localhost:8089`.

---

## Security Enhancements

### HTTPS Configuration
To enable secure communication between microservices we used https and set `verify=False` in service calls during local testing to avoid certificate errors.

### Data Sanitization
Sanitization ensures secure handling of user input:
- String sanitization is applied across microservices to prevent SQL injection and XSS.
- Numeric inputs are validated for correct types (e.g., integer vs. float).
- Refer to `sanitize_input()` functions in `app.py` for details.

### Vulnerability Scanning

1. Static Code Analysis:
   - Use Bandit to detect vulnerabilities:
     ```bash
     bandit -r .
     ```

2. Dependency Auditing:
   - Run `pip-audit` to check for vulnerable Python packages:
     ```bash
     pip-audit
     ```
   - Integrated with Dependabot to automatically flag dependency vulnerabilities in GitHub.

3. Docker Image Scanning:
   - Use Docker Scout to scan for vulnerabilities in images:
     ```bash
     docker scout quickview <image_name>
     ```

---

## Demo Space
The frontend client provides an interactive user interface for Gacha LOLection. Players can:
- Roll gachas to collect memes.
- Participate in auctions.
- Manage their profiles.

Ensure the backend services are running before starting the demo:

Install the CORS Unblock extension in your browser to bypass cross-origin restrictions. This is necessary because the client and backend services are served from different origins, and the extension allows communication between them. Download link `[https://webextension.org/listing/access-control.html](https://chromewebstore.google.com/detail/cors-unblock/lfhmikememgdcahcdlaciloancbhjino)`

Access `https://localhost:5001`, navigate to advanced settings, and accept the self-signed certificate to ensure secure communication.

Start the local server for the client (run it in the root directory):
```bash
python3 -m http.server 8000
```
Access the demo at `http://localhost:8000`.

A demonstration video:
https://github.com/user-attachments/assets/80846b2a-2239-47db-957a-4d4821d314a1


---

For further details, refer to the uploaded documentation or reach out to the authors.


