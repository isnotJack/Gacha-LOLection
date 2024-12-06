const BASE_URL = "https://localhost:5009/auth_service";
const BASE_URL_PAYMENT = "https://localhost:5009/payment_service";
const BASE_URL_AUCTION = "https://localhost:5009/auction_service";
const BASE_URL_GACHASYS = "https://localhost:5009/gachasystem_service";


const CERT_OPTIONS = { rejectUnauthorized: false }; // Gestione certificati autofirmati
async function get_newToken(url,payload) {
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
      console.log("response_OK");
      localStorage.setItem("access_token", data.access_token);
      payload.headers["Authorization"] = "Bearer "+data.access_token; // Sovrascrive il valore
      const res= await fetch(url,payload);
      const resData = await res.json();
      return { success: true, data: resData };
    }else {
      // Se la risposta per ottenere il token non è OK
      console.log("response token non_OK");
      const errorData = await response.json();
      return { success: false, message: errorData.message || "Errore durante la richiesta di un nuovo token" };
    }
  } catch (error) {
    // Gestione degli errori, ad esempio problemi di rete
    return { success: false, message: error.message || "Errore sconosciuto" };
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
    token_valid=false;      
    if (response.ok){
      token_valid=true;
      const data = await response.json();
    }
    else if(response.status == 401){
      console.log("Trying");
      const tokenRes= await get_newToken(`${BASE_URL}/delete`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded", // Gateway requires form data
        Authorization: `Bearer ${accessToken}`,
      },
      body: body.toString(),
    });
      console.log(tokenRes.success, tokenRes.data);
      if (tokenRes.success){
          token_valid=true;
          const data = tokenRes.data;
        }
    }
    if (token_valid) {
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

    token_valid=false;      
    if (response.ok){
      token_valid=true;
      const data = await response.json();
    }
    else if(response.status == 401){
      console.log("Trying");
      const tokenRes= await get_newToken(`${BASE_URL_AUCTION}/see${query}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
      console.log(tokenRes.success, tokenRes.data);
      if (tokenRes.success){
          token_valid=true;
          const data = tokenRes.data;
        }
    }
    if (token_valid) {
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
      document.getElementById("auction-service-result").textContent =
        data.error || "Failed to fetch auctions";
    }
  } catch (error) {
    document.getElementById("auction-service-result").textContent = "Error: " + error.message;
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

    token_valid=false;      
    if (response.ok){
      token_valid=true;
      const data = await response.json();
    }
    else if(response.status == 401){
      console.log("Trying");
      const tokenRes= await get_newToken(`${BASE_URL_AUCTION}/modify`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(auctionData),
    });
      console.log(tokenRes.success, tokenRes.data);
      if (tokenRes.success){
          token_valid=true;
          const data = tokenRes.data;
        }
    }
    if (token_valid) {
      document.getElementById("auction-service-result").textContent = "You have successfully update auction" + auctionId
    } else {
      document.getElementById("auction-service-result").textContent =
        data.error || "Failed to update auction";
    }
  } catch (error) {
    document.getElementById("auction-service-result").textContent = "Error: " + error.message;
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

    token_valid=false;      
    if (response.ok){
      token_valid=true;
      const data = await response.json();
    }
    else if(response.status == 401){
      console.log("Trying");
      const tokenRes= await get_newToken(BASE_URL_GACHASYS + "/add_gacha", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
        body: form, // Il corpo è il FormData
    });
      console.log(tokenRes.success, tokenRes.data);
      if (tokenRes.success){
          token_valid=true;
          const data = tokenRes.data;
        }
    }
      if (token_valid) {
          document.getElementById("gacha-system-result").textContent = "Gacha correctly added to the system!"
      }else {
            const data = await response.json();
            document.getElementById("gacha-system-result").textContent = data.Error || "Adding failed";
          }
    } catch (error) {
      document.getElementById("gacha-system-result").textContent = "Error: " + error.message;
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

    token_valid=false;      
    if (response.ok){
      token_valid=true;
      const data = await response.json();
    }
    else if(response.status == 401){
      console.log("Trying");
      const tokenRes= await get_newToken(BASE_URL_GACHASYS + "/delete_gacha", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: params.toString(), // Converte in formato URL encoded
      });
      console.log(tokenRes.success, tokenRes.data);
      if (tokenRes.success){
          token_valid=true;
          const data = tokenRes.data;
        }
    }
    if (token_valid) {
      document.getElementById("gacha-system-result").textContent = "Gacha correctly removed from the system!";
    } else {
      const data = await response.json();
      document.getElementById("gacha-system-result").textContent = data.Error || "Deletion failed";
    }
  } catch (error) {
    document.getElementById("gacha-system-result").textContent = "Error: " + error.message;
  }
});


// Modify Auctions
document.getElementById("update-gacha-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const gacha_name = prompt("Enter gacha_name:");
  const rarity = prompt("Enter rarity:");
  const description = prompt("Enter description:");

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

    token_valid=false;      
    if (response.ok)
      token_valid=true;
    else if(response.status == 401){
      console.log("Trying");
      const tokenRes= await get_newToken(`${BASE_URL_GACHASYS}/update_gacha`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/x-www-form-urlencoded",      
      },
      body: gachaData.toString(),
    });
      console.log(tokenRes.success, tokenRes.data);
      if (tokenRes.success){
          token_valid=true;
          data=tokenRes.data;
        }
    }
    if (token_valid) {
      document.getElementById("gacha-system-result").textContent = "You have successfully update the gacha " + gacha_name
    } else {
      document.getElementById("gacha-system-result").textContent =
        data.error || "Failed to update gacha";
    }
  } catch (error) {
    document.getElementById("gacha-system-result").textContent = "Error: " + error.message;
  }
});

document.getElementById("get-collection-button").addEventListener("click", async () => {
  const accessToken = localStorage.getItem("access_token");
  const gachaName = prompt("Enter Gacha Names (comma-separated) or leave blank for full collection:");

  try {
    // Prepara il body della richiesta come application/x-www-form-urlencoded
    const body = new URLSearchParams();
    if (gachaName) {
      gachaName.split(",").forEach((name) => body.append("gacha_name", name.trim()));
    }

    const response = await fetch(`${BASE_URL_GACHASYS}/get_gacha_collection`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded", // Cambiato il Content-Type
        Authorization: `Bearer ${accessToken}`,
      },
      body: body.toString(), // Invia i dati codificati
    });

    data = await response.json();
    token_valid=false;      
    if (response.ok)
      token_valid=true;
    else if(response.status == 401){
      console.log("Trying");
      const tokenRes= await get_newToken(`${BASE_URL_GACHASYS}/get_gacha_collection`, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded", // Cambiato il Content-Type
            Authorization: `Bearer ${accessToken}`,
          },
          body: body.toString(), // Invia i dati codificati
        })
        console.log(tokenRes.success, tokenRes.data);
      if (tokenRes.success){
          token_valid=true;
          data=tokenRes.data;
        }
    }
    if (token_valid) {
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
