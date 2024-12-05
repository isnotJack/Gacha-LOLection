const BASE_URL = "https://localhost:5001/auth_service";
const CERT_OPTIONS = { rejectUnauthorized: false }; // Gestione certificati autofirmati

// Login
document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
  
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;
  
    try {
      // Crea il body della richiesta come application/x-www-form-urlencoded
      const body = new URLSearchParams();
      body.append("username", username);
      body.append("password", password);
  
      const response = await fetch(`${BASE_URL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded", // Cambia il Content-Type
        },
        body: body.toString(), // Invia i dati codificati
        credentials: "include", // Per includere cookie o credenziali
      });
  
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        document.getElementById("login-result").textContent = "Login successful!";
        showLogoutSection();
      } else {
        document.getElementById("login-result").textContent = data.Error || "Login failed";
      }
    } catch (error) {
      document.getElementById("login-result").textContent = "Error: " + error.message;
    }
  });
  

// Signup
// Signup
document.getElementById("signup-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("signup-username").value;
    const password = document.getElementById("signup-password").value;
    const email = document.getElementById("signup-email").value;

    try {
        // Crea il body della richiesta come application/x-www-form-urlencoded
        const body = new URLSearchParams();
        body.append("username", username);
        body.append("password", password);
        body.append("email", email);

        const response = await fetch(`${BASE_URL}/signup`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded", // Cambia il Content-Type
            },
            body: body.toString(), // Invia i dati codificati
            credentials: "include", // Per includere cookie o credenziali
        });

        const data = await response.json();
        if (response.ok) {
            document.getElementById("signup-result").textContent = "Signup successful!";
        } else {
            document.getElementById("signup-result").textContent = data.Error || "Signup failed";
        }
    } catch (error) {
        document.getElementById("signup-result").textContent = "Error: " + error.message;
    }
});

  

// Logout
document.getElementById("logout-button").addEventListener("click", async () => {
  const refreshToken = localStorage.getItem("refresh_token");

  try {
    const response = await fetch(`${BASE_URL}/logout`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    });

    if (response.ok) {
      document.getElementById("logout-result").textContent = "Logout successful!";
      localStorage.clear();
      hideLogoutSection();
    } else {
      const data = await response.json();
      document.getElementById("logout-result").textContent = data.Error || "Logout failed";
    }
  } catch (error) {
    document.getElementById("logout-result").textContent = "Error: " + error.message;
  }
});

function showLogoutSection() {
  document.getElementById("logout-section").style.display = "block";
  document.getElementById("login-section").style.display = "none";
  document.getElementById("signup-section").style.display = "none";
}

function hideLogoutSection() {
  document.getElementById("logout-section").style.display = "none";
  document.getElementById("login-section").style.display = "block";
  document.getElementById("signup-section").style.display = "block";
}
