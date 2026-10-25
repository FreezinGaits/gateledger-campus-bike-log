/**
 * GateLedger — Main Frontend JavaScript Module
 * Handles dynamic vehicle lookup, UI state management, and modal interactions.
 * Zero external dependencies (pure vanilla JS).
 */

document.addEventListener("DOMContentLoaded", () => {
  initLoginDemoHelpers();
  initEventTypeSelector();
  initVehicleLookup();
  initBlockInspectorModals();
});

/**
 * 1. Demo Login Helper Buttons
 */
function initLoginDemoHelpers() {
  const btnAdmin = document.getElementById("fill-demo-admin");
  const btnGuard = document.getElementById("fill-demo-guard");
  const userInput = document.getElementById("username");
  const passInput = document.getElementById("password");

  if (btnAdmin && userInput && passInput) {
    btnAdmin.addEventListener("click", () => {
      userInput.value = "admin@campus.local";
      passInput.value = "Admin@123";
    });
  }

  if (btnGuard && userInput && passInput) {
    btnGuard.addEventListener("click", () => {
      userInput.value = "guard@campus.local";
      passInput.value = "Guard@123";
    });
  }
}

/**
 * 2. Event Type Toggle Selector (ENTRY vs EXIT)
 */
function initEventTypeSelector() {
  const entryRadio = document.getElementById("type-entry");
  const exitRadio = document.getElementById("type-exit");
  const entryCard = document.getElementById("card-type-entry");
  const exitCard = document.getElementById("card-type-exit");
  const submitBtn = document.getElementById("submit-event-btn");

  function updateTypeUI() {
    if (!entryRadio || !exitRadio) return;

    if (entryRadio.checked) {
      if (entryCard) entryCard.classList.add("selected-entry");
      if (exitCard) exitCard.classList.remove("selected-exit");
      if (submitBtn) {
        submitBtn.innerHTML = "Log Vehicle ENTRY & Append Block";
        submitBtn.className = "btn btn-primary btn-lg";
      }
    } else if (exitRadio.checked) {
      if (exitCard) exitCard.classList.add("selected-exit");
      if (entryCard) entryCard.classList.remove("selected-entry");
      if (submitBtn) {
        submitBtn.innerHTML = "Log Vehicle EXIT & Append Block";
        submitBtn.className = "btn btn-warning btn-lg";
        submitBtn.style.backgroundColor = "var(--amber-600)";
        submitBtn.style.color = "#ffffff";
      }
    }
  }

  if (entryRadio && exitRadio) {
    entryRadio.addEventListener("change", updateTypeUI);
    exitRadio.addEventListener("change", updateTypeUI);
    updateTypeUI();
  }
}

/**
 * 3. Vehicle Lookup & Instant Autofill
 */
function initVehicleLookup() {
  const regInput = document.getElementById("registration_number");
  const statusContainer = document.getElementById("vehicle-status-indicator");
  const riderInput = document.getElementById("rider_name");
  const ownerTypeSelect = document.getElementById("owner_type");
  const campusIdInput = document.getElementById("campus_id");
  const phoneInput = document.getElementById("phone");
  const makeModelInput = document.getElementById("make_model");
  const entryRadio = document.getElementById("type-entry");
  const exitRadio = document.getElementById("type-exit");

  if (!regInput) return;

  let lookupTimeout = null;

  async function performLookup() {
    const rawValue = regInput.value.trim();
    if (rawValue.length < 3) {
      if (statusContainer) statusContainer.innerHTML = "";
      return;
    }

    try {
      const resp = await fetch(`/api/vehicle/lookup?reg=${encodeURIComponent(rawValue)}`);
      const data = await resp.json();

      if (data.found && data.vehicle) {
        const v = data.vehicle;
        if (riderInput && !riderInput.value) riderInput.value = v.owner_name;
        if (ownerTypeSelect && v.owner_type) ownerTypeSelect.value = v.owner_type;
        if (campusIdInput && !campusIdInput.value) campusIdInput.value = v.campus_id || "";
        if (phoneInput && !phoneInput.value) phoneInput.value = v.phone || "";
        if (makeModelInput && !makeModelInput.value) makeModelInput.value = v.make_model || "";

        // Render status banner
        if (statusContainer) {
          const isInside = v.current_status === "INSIDE";
          const statusClass = isInside ? "alert-success" : "alert-info";
          const statusText = isInside ? "INSIDE CAMPUS" : "OUTSIDE CAMPUS";
          const recommendation = isInside
            ? "Ready for EXIT. (Logging ENTRY will be rejected)"
            : "Ready for ENTRY. (Logging EXIT will be rejected)";

          statusContainer.innerHTML = `
            <div class="alert ${statusClass}" style="margin-bottom: 0.5rem;">
              <div>
                <strong>Registered Vehicle Found:</strong> ${v.display_registration} (${v.owner_name} - ${v.owner_type})<br>
                <span>Current Status: <strong>${statusText}</strong> &bull; ${recommendation}</span>
              </div>
            </div>
          `;

          // Smartly auto-select appropriate toggle if user hasn't explicitly changed it
          if (isInside && exitRadio && !exitRadio.checked) {
            exitRadio.checked = true;
            exitRadio.dispatchEvent(new Event("change"));
          } else if (!isInside && entryRadio && !entryRadio.checked) {
            entryRadio.checked = true;
            entryRadio.dispatchEvent(new Event("change"));
          }
        }
      } else {
        if (statusContainer) {
          statusContainer.innerHTML = `
            <div class="alert alert-info" style="margin-bottom: 0.5rem;">
              <span>New Vehicle Registration. Complete the profile details below.</span>
            </div>
          `;
        }
      }
    } catch (err) {
      console.warn("Lookup failed:", err);
    }
  }

  regInput.addEventListener("input", () => {
    clearTimeout(lookupTimeout);
    lookupTimeout = setTimeout(performLookup, 450);
  });

  regInput.addEventListener("blur", performLookup);

  // If page loaded with pre-filled registration, run lookup immediately
  if (regInput.value.trim().length >= 3) {
    performLookup();
  }
}

/**
 * 4. Blockchain Block Details Inspector Modal
 */
function initBlockInspectorModals() {
  const modal = document.getElementById("block-detail-modal");
  if (!modal) return;

  const closeBtns = modal.querySelectorAll(".close-modal");
  const modalContent = document.getElementById("modal-block-json");
  const modalTitle = document.getElementById("modal-block-title");

  closeBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      modal.style.display = "none";
    });
  });

  window.addEventListener("click", e => {
    if (e.target === modal) {
      modal.style.display = "none";
    }
  });

  // Attach inspection handlers to all inspect buttons
  const inspectButtons = document.querySelectorAll(".btn-inspect-block");
  inspectButtons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const blockIndex = btn.getAttribute("data-block-index");
      if (!blockIndex) return;

      try {
        const resp = await fetch(`/api/blockchain/block/${blockIndex}`);
        if (!resp.ok) throw new Error("Failed to load block");
        const blk = await resp.json();

        if (modalTitle) modalTitle.innerText = `Blockchain Block #${blk.block_index}`;
        if (modalContent) {
          // Parse data_json nicely
          let parsedData;
          try {
            parsedData = JSON.parse(blk.data_json);
          } catch (e) {
            parsedData = blk.data_json;
          }

          const displayObj = {
            block_index: blk.block_index,
            timestamp_utc: blk.timestamp_utc,
            event_id: blk.event_id,
            previous_hash: blk.previous_hash,
            nonce: blk.nonce,
            block_hash: blk.block_hash,
            data: parsedData,
          };

          modalContent.textContent = JSON.stringify(displayObj, null, 2);
        }

        modal.style.display = "flex";
      } catch (err) {
        alert("Error loading block data: " + err.message);
      }
    });
  });
}
