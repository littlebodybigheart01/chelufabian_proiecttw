/* =========================================================
   main.js - script principal pentru funcționalități generale
   ========================================================= */

/* Rulează totul într-un scope privat ca să nu “murdărești” globalul */
(() => {
  "use strict";

  /* -----------------------------
     Helpers (utilitare)
     ----------------------------- */

  // Citește cart-ul din localStorage, safe (dacă JSON e corupt, revine la [])
  function getCart() {
    try {
      const raw = localStorage.getItem("cart");
      const cart = raw ? JSON.parse(raw) : [];
      return Array.isArray(cart) ? cart : [];
    } catch {
      return [];
    }
  }

  // Salvează cart-ul în localStorage
  function setCart(cart) {
    localStorage.setItem("cart", JSON.stringify(cart || []));
  }

  // Asigură un număr valid (ex. price, quantity)
  function toNumber(v, fallback = 0) {
    const n = Number(v);
    return Number.isFinite(n) ? n : fallback;
  }

  // Creează un element HTML rapid (și evită innerHTML pentru texte dinamice)
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  /* -----------------------------
     Cart core
     ----------------------------- */

  // Actualizează badge-ul din meniu: “Coș (X)”
  function updateCartCount() {
    const cart = getCart();
    const cartCount = document.getElementById("cart-count");
    const totalQty = cart.reduce((s, it) => s + (toNumber(it.quantity, 0)), 0);
    if (cartCount) {
      cartCount.textContent = totalQty;
      cartCount.setAttribute("aria-label", `Cos: ${totalQty} produse`);
    }
  }

  // Badge mobil (bulina roșie)
  function updateMobileCartBadge() {
    const cart = getCart();
    const totalQty = cart.reduce((s, it) => s + (toNumber(it.quantity, 0)), 0);
    const mobileBadge = document.getElementById("mobile-cart-badge");
    if (!mobileBadge) return;

    if (totalQty > 0) {
      mobileBadge.textContent = totalQty;
      mobileBadge.classList.remove("hidden");
      mobileBadge.setAttribute("aria-hidden", "false");
    } else {
      mobileBadge.classList.add("hidden");
      mobileBadge.setAttribute("aria-hidden", "true");
    }
  }

  // Pulse animation pe badge când adaugi în coș
  function animateCartBadge() {
    const mobileBadge = document.getElementById("mobile-cart-badge");
    const cartCount = document.getElementById("cart-count");

    if (mobileBadge) {
      mobileBadge.classList.add("pulse");
      setTimeout(() => mobileBadge.classList.remove("pulse"), 650);
    }
    if (cartCount) {
      cartCount.classList.add("pulse");
      setTimeout(() => cartCount.classList.remove("pulse"), 650);
    }
  }

  // Adaugă produs în coș (sau crește cantitatea dacă există)
  function addToCart(product) {
    const cart = getCart();

    const id = toNumber(product?.id, 0);
    const price = toNumber(product?.price, NaN);
    if (!id || !Number.isFinite(price)) return; // prevenim NaN în total

    const existing = cart.find((p) => toNumber(p.id, 0) === id);
    if (existing) {
      existing.quantity = toNumber(existing.quantity, 1) + toNumber(product.quantity, 1);
      existing.name = existing.name || product.name;
      existing.type = existing.type || product.type;
      existing.image_url = existing.image_url || product.image_url || null;
      existing.price = Number.isFinite(toNumber(existing.price, NaN)) ? existing.price : price;
    } else {
      cart.push({
        id,
        name: product.name || "Produs",
        type: product.type || "",
        price,
        quantity: Math.max(1, toNumber(product.quantity, 1)),
        image_url: product.image_url || null,
      });
    }

    setCart(cart);
    updateCartCount();
    updateMobileCartBadge();
    animateCartBadge();

    // Dacă modalul e deschis, re-render
    const cartModal = document.getElementById("cart-modal");
    if (cartModal && cartModal.style.display === "block") {
      displayCart();
    }
  }

  // Schimbă cantitatea (delta = +1 / -1); dacă ajunge la 0, șterge produsul
  function changeQuantity(id, delta) {
    const cart = getCart();
    const idx = cart.findIndex((i) => toNumber(i.id, 0) === toNumber(id, 0));
    if (idx === -1) return;

    const nextQty = Math.max(0, toNumber(cart[idx].quantity, 1) + toNumber(delta, 0));
    if (nextQty === 0) cart.splice(idx, 1);
    else cart[idx].quantity = nextQty;

    setCart(cart);
    displayCart();
    updateCartCount();
    updateMobileCartBadge();
  }

  // Șterge produs după id
  function removeFromCartById(id) {
    const cart = getCart();
    const newCart = cart.filter((i) => toNumber(i.id, 0) !== toNumber(id, 0));
    setCart(newCart);
    displayCart();
    updateCartCount();
    updateMobileCartBadge();
  }

  // Render coș în modal
  function displayCart() {
    const cart = getCart();
    const cartItems = document.getElementById("cart-items");
    const cartTotal = document.getElementById("cart-total");

    if (!cartItems || !cartTotal) return;

    // Curățăm containerul (fără innerHTML dinamic)
    cartItems.innerHTML = "";

    if (cart.length === 0) {
      const empty = el("p", "empty-cart", "Coșul tău este gol");
      cartItems.appendChild(empty);
      cartTotal.textContent = "0.00";
      // dezactivează buton checkout din modal dacă există
      const checkoutBtnEl = document.querySelector(".checkout-btn");
      if (checkoutBtnEl) checkoutBtnEl.disabled = true;
      return;
    }

    let total = 0;

    cart.forEach((item) => {
      const id = toNumber(item.id, 0);
      const qty = Math.max(1, toNumber(item.quantity, 1));
      const price = toNumber(item.price, 0);
      const line = price * qty;
      total += line;

      const row = el("div", "cart-item");
      row.dataset.id = String(id);

      // Thumbnail
      const thumb = el("div", "cart-item-thumb");
      if (item.image_url) {
        const img = document.createElement("img");
        img.src = item.image_url;
        img.alt = item.name || "Produs";
        thumb.appendChild(img);
      }
      row.appendChild(thumb);

      // Info
      const info = el("div", "cart-item-info");
      info.appendChild(el("h4", "", item.name || "Produs"));
      info.appendChild(el("p", "", item.type || ""));

      // Qty controls
      const qtyControl = el("div", "qty-control");
      const btnDec = el("button", "qty-decrease", "−");
      btnDec.setAttribute("aria-label", "Scade cantitate");
      btnDec.dataset.id = String(id);

      const qtySpan = el("span", "qty", String(qty));

      const btnInc = el("button", "qty-increase", "+");
      btnInc.setAttribute("aria-label", "Crește cantitate");
      btnInc.dataset.id = String(id);

      qtyControl.appendChild(btnDec);
      qtyControl.appendChild(qtySpan);
      qtyControl.appendChild(btnInc);
      info.appendChild(qtyControl);

      row.appendChild(info);

      // Price
      row.appendChild(el("div", "cart-item-price", `${line.toFixed(2)} RON`));

      // Remove
      const rm = el("button", "remove-item", "Șterge");
      rm.setAttribute("aria-label", "Șterge");
      rm.dataset.id = String(id);
      row.appendChild(rm);

      cartItems.appendChild(row);
    });

    cartTotal.textContent = total.toFixed(2);

    // activează checkout dacă există
    const checkoutBtnEl = document.querySelector(".checkout-btn");
    if (checkoutBtnEl) {
      const isDisabled = cart.length === 0;
      checkoutBtnEl.disabled = isDisabled;
      checkoutBtnEl.setAttribute("aria-disabled", isDisabled ? "true" : "false");
    }

    // Atașează handlers (simplu, după render)
    cartItems.querySelectorAll(".remove-item").forEach((btn) => {
      btn.addEventListener("click", () => removeFromCartById(btn.dataset.id));
    });
    cartItems.querySelectorAll(".qty-increase").forEach((btn) => {
      btn.addEventListener("click", () => changeQuantity(btn.dataset.id, +1));
    });
    cartItems.querySelectorAll(".qty-decrease").forEach((btn) => {
      btn.addEventListener("click", () => changeQuantity(btn.dataset.id, -1));
    });
  }

  /* -----------------------------
     Fly-to-cart animation
     ----------------------------- */
  function animateFlyToCart(imgSrc, sourceEl) {
    if (!imgSrc || !sourceEl) return;

    const img = document.createElement("img");
    img.src = imgSrc;
    img.className = "fly-image";

    const srcRect = sourceEl.getBoundingClientRect();
    img.style.left = srcRect.left + srcRect.width / 2 - 24 + "px";
    img.style.top = srcRect.top + srcRect.height / 2 - 24 + "px";
    document.body.appendChild(img);

    // Țintă: badge mobil dacă există, altfel link-ul coșului
    const target = document.getElementById("mobile-cart-badge") || document.getElementById("cart-link");
    if (!target) {
      setTimeout(() => img.remove(), 900);
      return;
    }

    const dstRect = target.getBoundingClientRect();
    const dx = dstRect.left + dstRect.width / 2 - (srcRect.left + srcRect.width / 2);
    const dy = dstRect.top + dstRect.height / 2 - (srcRect.top + srcRect.height / 2);

    requestAnimationFrame(() => {
      img.style.transform = `translate(${dx}px, ${dy}px) scale(0.18)`;
      img.style.opacity = "0.25";
    });

    setTimeout(() => img.remove(), 900);
  }

  /* -----------------------------
     UI general (hamburger, modal, etc.)
     ----------------------------- */
  function initUI() {
    updateCartCount();
    updateMobileCartBadge();

    // Hamburger menu principal
    const hamburger = document.getElementById("hamburger");
    const navMenu = document.getElementById("nav-menu");

    if (hamburger && navMenu) {
      const isMobileNav = () => window.matchMedia("(max-width: 900px)").matches;
      const setNavState = (open) => {
        hamburger.setAttribute("aria-expanded", open ? "true" : "false");
        navMenu.setAttribute("aria-hidden", isMobileNav() ? (open ? "false" : "true") : "false");
      };
      setNavState(false);

      hamburger.addEventListener("click", () => {
        const isOpen = hamburger.classList.toggle("active");
        navMenu.classList.toggle("active", isOpen);
        setNavState(isOpen);
      });

      document.querySelectorAll(".nav-menu a").forEach((link) => {
        link.addEventListener("click", () => {
          hamburger.classList.remove("active");
          navMenu.classList.remove("active");
          setNavState(false);
        });
      });

      document.addEventListener("click", (e) => {
        if (!hamburger.contains(e.target) && !navMenu.contains(e.target)) {
          hamburger.classList.remove("active");
          navMenu.classList.remove("active");
          setNavState(false);
        }
      });

      window.addEventListener("resize", () => {
        setNavState(hamburger.classList.contains("active"));
      });
    }

    // Modal coș (deschidere/închidere)
    const cartLink = document.getElementById("cart-link");
    const cartModal = document.getElementById("cart-modal");
    const closeModal = document.querySelector(".close");

    let lastFocus = null;
    const closeCartModal = () => {
      if (!cartModal) return;
      cartModal.style.display = "none";
      cartModal.setAttribute("aria-hidden", "true");
      if (lastFocus) lastFocus.focus();
    };

    if (cartLink && cartModal) {
      cartLink.addEventListener("click", (e) => {
        e.preventDefault();
        lastFocus = document.activeElement;
        displayCart();
        cartModal.style.display = "block";
        cartModal.setAttribute("aria-hidden", "false");
        if (closeModal) closeModal.focus();
      });
    }

    if (closeModal && cartModal) {
      closeModal.addEventListener("click", closeCartModal);
    }

    window.addEventListener("click", (e) => {
      if (cartModal && e.target === cartModal) {
        closeCartModal();
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && cartModal && cartModal.style.display === "block") {
        closeCartModal();
      }
    });

    // Buton “Finalizează comanda” (din modal)
    const checkoutBtn = document.querySelector(".checkout-btn");
    if (checkoutBtn) {
      checkoutBtn.addEventListener("click", () => {
        window.location.href = "/checkout";
      });
    }
    // Newsletter submit: allow server handler when action is set
    const newsletterForm = document.querySelector(".newsletter-form");
    if (newsletterForm) {
      newsletterForm.addEventListener("submit", function (e) {
        if (!newsletterForm.getAttribute("action")) {
          e.preventDefault();
          alert("Multumim pentru abonare!");
          this.reset();
        }
      });
    }

    // Back to top
    const backToTop = document.querySelector(".back-to-top");
    if (backToTop) {
      window.addEventListener("scroll", () => {
        if (window.scrollY > 300) backToTop.classList.add("show");
        else backToTop.classList.remove("show");
      });

      backToTop.addEventListener("click", (e) => {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }
  }

  /* -----------------------------
     Dashboard sidebar (hamburger)
     ----------------------------- */
  function initDashboardSidebar() {
    const dashboardHamburger = document.getElementById("dashboardHamburger");
    const dashboardSidebar = document.querySelector(".dashboard-sidebar");
    const dashboardOverlay = document.getElementById("dashboardOverlay");
    const closeDashboardBtn = document.getElementById("closeDashboardBtn");

    if (!dashboardHamburger || !dashboardSidebar) return;

    const closeSidebar = () => {
      dashboardSidebar.classList.remove("active");
      if (dashboardOverlay) dashboardOverlay.classList.remove("active");
    };

    dashboardHamburger.addEventListener("click", () => {
      dashboardSidebar.classList.add("active");
      if (dashboardOverlay) dashboardOverlay.classList.add("active");
    });

    if (closeDashboardBtn) closeDashboardBtn.addEventListener("click", closeSidebar);
    if (dashboardOverlay) dashboardOverlay.addEventListener("click", closeSidebar);
  }

  /* -----------------------------
     Table filters (client-side)
     ----------------------------- */
  function initTableFilters() {
    const inputs = document.querySelectorAll("[data-filter-table]");
    inputs.forEach((input) => {
      const tableId = input.getAttribute("data-filter-table");
      const table = document.getElementById(tableId);
      if (!table) return;

      const rows = Array.from(table.querySelectorAll("tbody tr"));
      input.addEventListener("input", () => {
        const query = (input.value || "").trim().toLowerCase();
        rows.forEach((row) => {
          const match = row.textContent.toLowerCase().includes(query);
          row.style.display = match ? "" : "none";
        });
      });
    });
  }

  /* -----------------------------
     Add-to-cart buttons wiring
     ----------------------------- */
  function initAddToCartButtons() {
    const buttons = document.querySelectorAll(".add-to-cart, .add-to-cart-detail");
    if (!buttons.length) return;

    buttons.forEach((button) => {
      button.addEventListener("click", function () {
        const productId = toNumber(this.getAttribute("data-id"), 0);
        const productName = this.getAttribute("data-name") || "Produs";
        const productPrice = toNumber(this.getAttribute("data-price"), NaN);
        const productType = this.getAttribute("data-type") || "";
        const productImage = this.getAttribute("data-image") || null;

        if (!productId || !Number.isFinite(productPrice)) return;

        addToCart({
          id: productId,
          name: productName,
          price: productPrice,
          type: productType,
          image_url: productImage,
          quantity: 1,
        });

        // animație fly-to-cart
        try {
          animateFlyToCart(productImage, this);
        } catch {
          /* ignore */
        }

        // feedback pe buton
        const prev = this.innerHTML;
        this.textContent = "Adaugat!";
        this.classList.add("added");
        setTimeout(() => {
          this.innerHTML = prev;
          this.classList.remove("added");
        }, 1200);
      });
    });
  }

  /* -----------------------------
     Boot
     ----------------------------- */
  document.addEventListener("DOMContentLoaded", () => {
    initUI();
    initDashboardSidebar();
    initAddToCartButtons();
    initTableFilters();
  });

  /* ---------------------------------------------------------
     Export global (pentru checkout.html / alte pagini)
     --------------------------------------------------------- */
  window.displayCart = displayCart;
  window.addToCart = addToCart;
  window.updateCartCount = updateCartCount;
  window.updateMobileCartBadge = updateMobileCartBadge;

})();

