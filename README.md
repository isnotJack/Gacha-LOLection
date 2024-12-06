# SSE-project
# Gacha LOLection

## Introduction
Gacha LOLection is a platform that integrates the thrill of meme-based gacha rolls with auctions for trading gacha items. The backend architecture consists of microservices for authentication, profile management, gacha operations, auctions, and payment. This README provides instructions for setting up the backend, testing its functionality, and ensuring its security.

---

## Get Started

### Prerequisites
- Docker and Docker Compose installed
- Python 3.9+ installed (for local testing)
- locust installed (for performance testing)

### Installation
1. Clone the repository:
   ```bash
   git clone da rendere publica
   cd gacha-lollection
   ```

2. Build and start the backend services using Docker Compose:
   ```bash
   docker-compose up --build
   ```

3. Verify the services are running:
   Open `https://localhost:5001` in your browser to check the gateway, or use Postman to test individual endpoints.

---

## MicroFreshener Analysis
To analyze the microservices architecture:

1. Install MicroFreshener:
   ```bash
   npm install -g microfreshener
   ```

2. Generate the architecture visualization:
   ```bash
   microfreshener-cli analyze -f architecture.yaml -o output.json
   ```

3. Open the output JSON file with the MicroFreshener web interface to review architectural smells and dependencies.

---

## Testing

### CI/CD Testing
The project includes comprehensive CI/CD pipelines for automated testing:

1. **Unit Testing:**
   - Each microservice contains a `tests` folder with unit tests.
   - Run locally using:
     ```bash
     pytest tests/
     ```
   - Run in CI using GitHub Actions. The workflow automatically executes unit tests with mocked dependencies.

2. **Integration Testing:**
   - Postman collections are provided for end-to-end testing of service interactions.
   - Run integration tests:
     ```bash
     newman run tests/integration.postman_collection.json -e tests/environment.json
     ```

3. **Performance Testing:**
   - Locust simulates multiple users interacting with the system:
     ```bash
     locust -f locustfile.py --host=http://localhost
     ```
   - Configure user tasks and weights in `locustfile.py`.

---

## Security Enhancements

### HTTPS Configuration
To enable secure communication between microservices:

1. Generate TLS certificates:
   ```bash
   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
   ```

2. Update `docker-compose.yml`:
   ```yaml
   secrets:
     service_cert:
       file: ./cert.pem
     service_key:
       file: ./key.pem
   ```

3. Configure Flask services to use certificates:
   ```bash
   CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--cert=cert.pem", "--key=key.pem"]
   ```

4. Set `verify=False` in service calls during local testing to avoid certificate errors.

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
   - Enable Dependabot in GitHub to automatically flag dependency vulnerabilities.

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
```bash
python3 -m http.server 8000
```
Access the demo at `http://localhost:8000`.

---

For further details, refer to the uploaded documentation or reach out to the authors.

