const BASE_URL = "https://localhost:5001/auth_service";
const BASE_URL_PAYMENT = "https://localhost:5001/payment_service";
const BASE_URL_AUCTION = "https://localhost:5001/auction_service";
const BASE_URL_GACHA = "https://localhost:5001/gacha_roll";
const BASE_URL_GACHA_SYSTEM = "https://localhost:5001/gachasystem_service";
const BASE_URL_PROFILE_SETTING = "https://localhost:5001/profile_setting";

const CERT_OPTIONS = { rejectUnauthorized: false }; // Gestione certificati autofirmati

// Login
document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;

  try {
    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);

    const response = await fetch(`${BASE_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: body.toString(),
      credentials: "include",
    });

    const data = await response.json();
    if (response.ok) {
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("logged_username", username);
      document.getElementById("login-result").textContent = "Login successful!";
      showMenuSection(); // Mostra il menu dei servizi
    } else {
      document.getElementById("login-result").textContent = data.Error || "Login failed";
    }
  } catch (error) {
    document.getElementById("login-result").textContent = "Error: " + error.message;
  }
});

// Signup
document.getElementById("signup-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("signup-username").value;
  const password = document.getElementById("signup-password").value;
  const email = document.getElementById("signup-email").value;

  try {
    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);
    body.append("email", email);

    const response = await fetch(`${BASE_URL}/signup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: body.toString(),
      credentials: "include",
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

// Show Menu Section
function showMenuSection() {
  document.getElementById("menu-section").style.display = "block";
  document.getElementById("login-section").style.display = "none";
  document.getElementById("signup-section").style.display = "none";
}
function hideMenuSection() {
  document.getElementById("menu-section").style.display = "none";
  document.getElementById("login-section").style.display = "block";
  document.getElementById("signup-section").style.display = "block";
}

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
      document.getElementById("account-service-result").textContent = "Logout successful!";
      localStorage.clear();
      hideMenuSection();
    } else {
      const data = await response.json();
      document.getElementById("logout-result").textContent = data.Error || "Logout failed";
    }
  } catch (error) {
    document.getElementById("logout-result").textContent = "Error: " + error.message;
  }
});

// Delete Account
document.getElementById("delete-account-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const username = localStorage.getItem("logged_username"); // Assume username is stored at login
  const password = prompt("Enter your password to confirm deletion:");

  if (!password) {
    alert("Password is required to delete your account.");
    return;
  }

  try {
    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);

    const response = await fetch(`${BASE_URL}/delete`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded", // Gateway requires form data
        Authorization: `Bearer ${accessToken}`,
      },
      body: body.toString(),
    });

    const data = await response.json();
    if (response.ok) {
      alert("Account deleted successfully. Redirecting to the main menu.");
      localStorage.clear(); // Clear storage
      hideMenuSection(); // Redirect to login/signup
    } else {
      alert(data.Error || "Failed to delete account");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
});

// Buy Currency
document.getElementById("buy-currency-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const username = localStorage.getItem("logged_username"); // Usa l'username salvato al login
  const amount = prompt("Enter amount to buy:");
  const method = prompt("Enter payment method:");

  if (!username) {
    document.getElementById("service-result").textContent = "Error: Username not found. Please log in again.";
    return;
  }

  try {
    // Crea il body della richiesta come application/x-www-form-urlencoded
    const body = new URLSearchParams();
    body.append("username", username);
    body.append("amount", amount);
    body.append("payment_method", method);

    const response = await fetch(`${BASE_URL_PAYMENT}/buycurrency`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded", // Cambia il Content-Type
        Authorization: `Bearer ${accessToken}`,
      },
      body: body.toString(), // Invia i dati codificati
    });

    const data = await response.json();
    if (response.ok) {
      document.getElementById("payment-service-result").textContent = `Currency purchased! Balance: ${data.balance}`;
    } else {
      document.getElementById("service-result").textContent = data.Error || "Failed to purchase currency";
    }
  } catch (error) {
    document.getElementById("service-result").textContent = "Error: " + error.message;
  }
});

// View Transactions
document.getElementById("view-transactions-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const username = localStorage.getItem("logged_username"); // Usa l'username salvato al login

  if (!username) {
    document.getElementById("service-result").textContent = "Error: Username not found. Please log in again.";
    return;
  }

  try {
    const response = await fetch(`${BASE_URL_PAYMENT}/viewTrans?username=${encodeURIComponent(username)}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const data = await response.json();
    if (response.ok) {
      const transactions = data.map(
        (t) =>
          `ID: ${t.id}, Payer: ${t.payer_us}, Receiver: ${t.receiver_us}, Amount: ${t.amount}, Date: ${new Date(
            t.date
          ).toLocaleString()}`
      );
      document.getElementById("payment-service-result").innerHTML = transactions.join("<br>");
    } else {
      document.getElementById("service-result").textContent = data.Error || "Failed to fetch transactions";
    }
  } catch (error) {
    document.getElementById("service-result").textContent = "Error: " + error.message;
  }
});

// See Auctions
document.getElementById("see-auctions-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");

  try {
    const auctionId = prompt("Enter Auction ID (optional):");
    const status = prompt("Enter Auction Status (default: active):") || "active";
    const query = auctionId
      ? `?auction_id=${auctionId}&status=${status}`
      : `?status=${status}`;

    const response = await fetch(`${BASE_URL_AUCTION}/see${query}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const data = await response.json();
    if (response.ok) {
      const auctions = Array.isArray(data)
        ? data.map(
            (a) =>
              `ID: ${a.id}, Gacha: ${a.gacha_name}, Seller: ${a.seller_username}, Current Bid: ${a.current_bid}, Status: ${a.status}, End Date: ${new Date(
                a.end_date
              ).toLocaleString()}`
          )
        : [`Auction: ${JSON.stringify(data)}`];
        document.getElementById("auction-service-result").innerHTML = auctions.join("<br>");
      } else {
      document.getElementById("service-result").textContent =
        data.error || "Failed to fetch auctions";
    }
  } catch (error) {
    document.getElementById("service-result").textContent = "Error: " + error.message;
  }
});

// Create Auction
document.getElementById("create-auction-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const username = localStorage.getItem("logged_username");

  const gachaName = prompt("Enter Gacha Name:");
  const basePrice = prompt("Enter Base Price:");
  const endDate = prompt(
    "Enter End Date (ISO format, e.g., 2024-12-31T23:59:59):"
  );

  if (!gachaName || !basePrice || !endDate) {
    alert("All fields are required!");
    return;
  }

  try {
    const body = {
      seller_username: username,
      gacha_name: gachaName,
      basePrice: parseFloat(basePrice),
      endDate,
    };

    const response = await fetch(`${BASE_URL_AUCTION}/create`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    if (response.ok) {
      alert("Auction created successfully!");
      document.getElementById("auction-service-result").textContent = JSON.stringify(data);
    } else {
      alert(data.error || "Failed to create auction");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
});

// Place a Bid
document.getElementById("bid-auction-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const username = localStorage.getItem("logged_username");

  const auctionId = prompt("Enter Auction ID:");
  const newBid = prompt("Enter Your Bid:");

  if (!auctionId || !newBid) {
    alert("Auction ID and bid amount are required!");
    return;
  }

  try {
    const query = `?username=${username}&auction_id=${auctionId}&newBid=${newBid}`;

    const response = await fetch(`${BASE_URL_AUCTION}/bid${query}`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const data = await response.json();
    if (response.ok) {
      alert("Bid placed successfully!");
      document.getElementById("auction-service-result").textContent = JSON.stringify(data);
    } else {
      alert(data.error || "Failed to place bid");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
});

let resultTimeout = null; // To store the current timeout reference


// Gacha Roll
document.querySelectorAll(".gacha-package").forEach((button) => {
  button.addEventListener("click", async () => {
    const accessToken = localStorage.getItem("access_token");
    const username = localStorage.getItem("logged_username");
    const level = button.getAttribute("data-level");

    if (!username || !level) {
      alert("Error: Missing username or roll level!");
      return;
    }

    const animationSection = document.getElementById("gacha-roll-animation");
    const resultSection = document.getElementById("gacha-roll-result");
    const gachaImage = document.getElementById("gacha-roll-image");
    const gachaDetails = document.getElementById("gacha-roll-details");

    // Hide result and show animation
    resultSection.style.display = "none";
    animationSection.style.display = "block";

    // Simulate rolling animation
    await new Promise((resolve) => setTimeout(resolve, 3000)); // Wait for 3 seconds

    try {
      const response = await fetch(`${BASE_URL_GACHA}/gacharoll`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ username, level }),
      });

      const data = await response.json();

      if (response.ok) {
        // Hide animation and show result
        animationSection.style.display = "none";
        gachaImage.src = data.img;
        gachaDetails.innerHTML = `
          <strong>Name:</strong> ${data.gacha_name}<br>
          <strong>Rarity:</strong> ${data.rarity}<br>
          <strong>Description:</strong> ${data.description}
        `;
        resultSection.style.display = "block";

      // Clear any existing timeout
      if (resultTimeout) {
        clearTimeout(resultTimeout);
      }

      // Set a new timeout
      resultTimeout = setTimeout(() => {
        resultSection.style.display = "none";
        resultTimeout = null; // Clear the reference after timeout
      }, 20000); // 20 seconds
      
      } else {
        alert(data.Error || "Gacha Roll Failed");
        animationSection.style.display = "none";
      }
    } catch (error) {
      alert("Error: " + error.message);
      animationSection.style.display = "none";
    }
  });
});



// View Gacha Collection
document.getElementById("view-gacha-collection-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");

  const gachaName = prompt("Enter Gacha Names (comma-separated) or leave blank for full collection:");

  try {
    // Prepara il body della richiesta come application/x-www-form-urlencoded
    const body = new URLSearchParams();
    if (gachaName) {
      gachaName.split(",").forEach((name) => body.append("gacha_name", name.trim()));
    }

    const response = await fetch(`${BASE_URL_GACHA_SYSTEM}/get_gacha_collection`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded", // Cambiato il Content-Type
        Authorization: `Bearer ${accessToken}`,
      },
      body: body.toString(), // Invia i dati codificati
    });

    const data = await response.json();

    if (response.ok) {
      // Mostra i risultati (già funzionante)
      const gachaContainer = document.getElementById("gacha-system-result");
      gachaContainer.innerHTML = ""; // Resetta il contenuto precedente
      data.forEach((gacha) => {
        const gachaElement = document.createElement("div");
        gachaElement.className = "gacha-item";
        gachaElement.innerHTML = `
          <img src="${gacha.img}" alt="${gacha.gacha_name}">
          <p><strong>Name:</strong> ${gacha.gacha_name}</p>
          <p><strong>Rarity:</strong> ${gacha.rarity}</p>
          <p><strong>Description:</strong> ${gacha.description}</p>
        `;
        gachaContainer.appendChild(gachaElement);
      });
    } else {
      alert(data.Error || "Failed to fetch Gacha Collection");
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
});

document.getElementById("check-profile-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const username = localStorage.getItem("logged_username");

  if (!username) {
    alert("Error: Username not found. Please log in again.");
    return;
  }

  try {
    const response = await fetch(`${BASE_URL_PROFILE_SETTING}/checkprofile?username=${encodeURIComponent(username)}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const data = await response.json();
    const resultContainer = document.getElementById("profile-result");

    if (response.ok) {
      resultContainer.innerHTML = `
        <p><strong>Username:</strong> ${data.username}</p>
        <p><strong>Email:</strong> ${data.email}</p>
        <p><strong>Currency Balance:</strong> ${data.currency_balance}</p>
        <img src="${data.profile_image}" alt="Profile Image">
      `;
    } else {
      resultContainer.innerHTML = `<p>${data.error || "Failed to fetch profile"}</p>`;
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
});

document.getElementById("retrieve-gacha-collection-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const username = localStorage.getItem("logged_username");

  if (!username) {
    alert("Error: Username not found. Please log in again.");
    return;
  }

  try {
    const response = await fetch(`${BASE_URL_PROFILE_SETTING}/retrieve_gachacollection?username=${encodeURIComponent(username)}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const data = await response.json();
    const resultContainer = document.getElementById("profile-result");

    if (response.ok) {
      if (Array.isArray(data) && data.length > 0) {
        resultContainer.innerHTML = data
          .map(
            (gacha) => `
              <div class="gacha-item">
                <img src="${gacha.img}" alt="${gacha.gacha_name}">
                <p><strong>Name:</strong> ${gacha.gacha_name}</p>
                <p><strong>Rarity:</strong> ${gacha.rarity}</p>
                <p><strong>Description:</strong> ${gacha.description}</p>
              </div>
            `
          )
          .join("");
      } else {
        resultContainer.innerHTML = `<p>No gacha items found for this user.</p>`;
      }
    } else {
      resultContainer.innerHTML = `<p>${data.error || "Failed to fetch gacha collection"}</p>`;
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
});

document.getElementById("info-gacha-collection-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const username = localStorage.getItem("logged_username");

  const gachaName = prompt("Enter Gacha Name:");

  if (!username || !gachaName) {
    alert("Error: Missing username or gacha name.");
    return;
  }

  try {
    const response = await fetch(
      `${BASE_URL_PROFILE_SETTING}/info_gachacollection?username=${encodeURIComponent(
        username
      )}&gacha_name=${encodeURIComponent(gachaName)}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      }
    );

    const data = await response.json();
    const resultContainer = document.getElementById("profile-result");

    if (response.ok) {
      // Verifica se è una lista e itera
      if (Array.isArray(data)) {
        resultContainer.innerHTML = data
          .map(
            (gacha) => `
            <div class="gacha-item">
              <img src="${gacha.img}" alt="${gacha.gacha_name}">
              <p><strong>Name:</strong> ${gacha.gacha_name}</p>
              <p><strong>Rarity:</strong> ${gacha.rarity}</p>
              <p><strong>Description:</strong> ${gacha.description}</p>
            </div>
          `
          )
          .join("");
      } else {
        // Gestione singolo oggetto (fallback)
        resultContainer.innerHTML = `
          <div class="gacha-item">
            <img src="${data.img}" alt="${data.gacha_name}">
            <p><strong>Name:</strong> ${data.gacha_name}</p>
            <p><strong>Rarity:</strong> ${data.rarity}</p>
            <p><strong>Description:</strong> ${data.description}</p>
          </div>
        `;
      }
    } else {
      resultContainer.innerHTML = `<p>${data.error || "Failed to fetch gacha info"}</p>`;
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
});
