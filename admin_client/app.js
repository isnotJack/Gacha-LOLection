const BASE_URL = "https://localhost:5009/auth_service";
const BASE_URL_PAYMENT = "https://localhost:5009/payment_service";
const BASE_URL_AUCTION = "https://localhost:5009/auction_service";
const BASE_URL_GACHASYS = "https://localhost:5009/gachasystem_service";


const CERT_OPTIONS = { rejectUnauthorized: false }; // Gestione certificati autofirmati
async function get_newToken() {
  const refreshToken = localStorage.getItem("refresh_token");
  try {
    const response = await fetch(`${BASE_URL}/newToken`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    });

    const data = await response.json();
    if (response.ok) {
      localStorage.setItem("access_token", data.access_token);
      return ; // Ritorna il nuovo token 
      }
    else
      throw new Error("Failed to refresh token");}
  catch (error) {
    throw new Error("Failed to refresh token");
  }
};

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
      document.getElementById("logout-result").textContent = "Logout successful!";
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
      document.getElementById("service-result").innerHTML = auctions.join("<br>");
    } else {
      document.getElementById("service-result").textContent =
        data.error || "Failed to fetch auctions";
    }
  } catch (error) {
    document.getElementById("service-result").textContent = "Error: " + error.message;
  }
});


// Modify Auctions
document.getElementById("modify-auction-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");

  try {
    const auctionId = prompt("Enter Auction ID:");
    const seller_username = prompt("Enter Seller username:");
    const gacha_name = prompt("Enter gacha_name:");
    const base_price = prompt("Enter base price:");
    const end_date = prompt("Enter end date:");
    
    const auctionData = {
      auctionId: auctionId,
      seller_username: seller_username,
      gacha_name: gacha_name,
      base_price: parseFloat(base_price), // Converte il prezzo in numero
      end_date: end_date
  };

    const response = await fetch(`${BASE_URL_AUCTION}/modify`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(auctionData),
    });

    const data = await response.json();
    if (response.ok) {
      document.getElementById("service-result").textContent = "You have successfully update auction" + auctionId
    } else {
      document.getElementById("service-result").textContent =
        data.error || "Failed to update auction";
    }
  } catch (error) {
    document.getElementById("service-result").textContent = "Error: " + error.message;
  }
});



document.getElementById("addGachaForm").addEventListener("submit", async function(event) {
  event.preventDefault(); // Evita il ricaricamento della pagina
  const accessToken = localStorage.getItem("access_token");
  // Raccogli i dati dal modulo
  const form = new FormData();
  form.append("gacha_name", document.getElementById("gacha_name").value);
  form.append("rarity", document.getElementById("rarity").value);
  form.append("description", document.getElementById("description").value);
  form.append("image", document.getElementById("image").files[0]); // Aggiungi il file

  try {
      // Invia la richiesta al server
      const response = await fetch(BASE_URL_GACHASYS + "/add_gacha", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
          body: form, // Il corpo è il FormData
      });

      if (response.ok) {
          const data = await response.json();
          document.getElementById("service-result").textContent = "Gacha correctly added to the system!"
      }else {
            const data = await response.json();
            document.getElementById("service-result").textContent = data.Error || "Adding failed";
          }
    } catch (error) {
      document.getElementById("service-result").textContent = "Error: " + error.message;
    }
});

document.getElementById("delete-gacha-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const gacha_name = prompt("Enter the name of the gacha to delete:");

  try {
    const params = new URLSearchParams(); // Inizializza URLSearchParams
    params.append("gacha_name", gacha_name); // Aggiungi i parametri al form

    // Esegui la richiesta
    const response = await fetch(BASE_URL_GACHASYS + "/delete_gacha", {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: params.toString(), // Converte in formato URL encoded
    });

    if (response.ok) {
      const data = await response.json();
      document.getElementById("service-result").textContent = "Gacha correctly removed from the system!";
    } else {
      const data = await response.json();
      document.getElementById("service-result").textContent = data.Error || "Deletion failed";
    }
  } catch (error) {
    document.getElementById("service-result").textContent = "Error: " + error.message;
  }
});


// Modify Auctions
document.getElementById("update-gacha-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const gacha_name = prompt("Enter gacha_name:");
  const rarity = prompt("Enter base price:");
  const description = prompt("Enter end date:");

  try {
    const gachaData = new URLSearchParams();

    if (!gacha_name) {
      alert("The name of the gacha is required to update it");
      return;
    }
    
    gachaData.append("gacha_name",gacha_name);
    gachaData.append("rarity",rarity);
    gachaData.append("description",description);


    const response = await fetch(`${BASE_URL_GACHASYS}/update_gacha`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/x-www-form-urlencoded",      
      },
      body: gachaData.toString(),
    });

    const data = await response.json();
    if (response.ok) {
      document.getElementById("service-result").textContent = "You have successfully update the gacha" + gacha_name
    } else {
      document.getElementById("service-result").textContent =
        data.error || "Failed to update gacha";
    }
  } catch (error) {
    document.getElementById("service-result").textContent = "Error: " + error.message;
  }
});


document.getElementById("get-collection-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");

  // Prompt per ottenere i nomi di gacha
  const gachaNames = prompt("Enter the names of the gachas, separated by commas: (optional)").split(",");

  try {
    // Prepara i parametri come application/x-www-form-urlencoded
    const params = new URLSearchParams();
    gachaNames.forEach(name => params.append("gacha_name", name.trim())); // Aggiungi ogni valore

    // Esegui la richiesta
    const response = await fetch(BASE_URL_GACHASYS + "/get_gacha_collection", {
      method: "POST", // Usa POST o GET a seconda delle esigenze del server
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: params.toString(), // Invia i parametri come form-urlencoded
    });

    if (response.ok) {
      const data = await response.json();
      console.log("Gacha collection:", data);
      document.getElementById("service-result").textContent = JSON.stringify(data, null, 2);
    } else {
      const data = await response.json();
      document.getElementById("service-result").textContent = data.Error || "Failed to fetch gacha collection";
    }
  } catch (error) {
    document.getElementById("service-result").textContent = "Error: " + error.message;
  }
});
