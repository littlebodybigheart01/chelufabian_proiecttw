document.addEventListener("DOMContentLoaded", () => {
  updateCartCount()

  const hamburger = document.getElementById("hamburger")
  const navMenu = document.getElementById("nav-menu")

  if (hamburger && navMenu) {
    hamburger.addEventListener("click", () => {
      hamburger.classList.toggle("active")
      navMenu.classList.toggle("active")
    })

    document.querySelectorAll(".nav-menu a").forEach((link) => {
      link.addEventListener("click", () => {
        hamburger.classList.remove("active")
        navMenu.classList.remove("active")
      })
    })

    document.addEventListener("click", (e) => {
      if (!hamburger.contains(e.target) && !navMenu.contains(e.target)) {
        hamburger.classList.remove("active")
        navMenu.classList.remove("active")
      }
    })
  }

  const cartLink = document.getElementById("cart-link")
  const cartModal = document.getElementById("cart-modal")
  const closeModal = document.querySelector(".close")

  if (cartLink) {
    cartLink.addEventListener("click", (e) => {
      e.preventDefault()
      displayCart()
      cartModal.style.display = "block"
    })
  }

  if (closeModal) {
    closeModal.addEventListener("click", () => {
      cartModal.style.display = "none"
    })
  }

  window.addEventListener("click", (e) => {
    if (e.target === cartModal) {
      cartModal.style.display = "none"
    }
  })

  const checkoutBtn = document.querySelector(".checkout-btn")
  if (checkoutBtn) {
    checkoutBtn.addEventListener("click", () => {
      alert("Funcționalitatea de checkout va fi implementată când se va conecta baza de date.")
    })
  }

  const newsletterForm = document.querySelector(".newsletter-form")
  if (newsletterForm) {
    newsletterForm.addEventListener("submit", function (e) {
      e.preventDefault()
      alert("Mulțumim pentru abonare! Funcționalitatea va fi implementată complet cu baza de date.")
      this.reset()
    })
  }

  const backToTop = document.querySelector(".back-to-top")
  if (backToTop) {
    backToTop.addEventListener("click", (e) => {
      e.preventDefault()
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      })
    })
  }
})

function updateCartCount() {
  const cart = JSON.parse(localStorage.getItem("cart")) || []
  const cartCount = document.getElementById("cart-count")
  if (cartCount) {
    cartCount.textContent = cart.length
  }
}

function displayCart() {
  const cart = JSON.parse(localStorage.getItem("cart")) || []
  const cartItems = document.getElementById("cart-items")
  const cartTotal = document.getElementById("cart-total")

  if (cart.length === 0) {
    cartItems.innerHTML = '<p class="empty-cart">Coșul tău este gol</p>'
    cartTotal.textContent = "0.00"
    return
  }

  let total = 0
  let html = ""

  cart.forEach((item, index) => {
    total += Number.parseFloat(item.price)
    html += `
            <div class="cart-item">
                <div class="cart-item-info">
                    <h4>${item.name}</h4>
                    <p>${item.type}</p>
                </div>
                <div class="cart-item-price">${item.price} RON</div>
                <button class="remove-item" data-index="${index}">Șterge</button>
            </div>
        `
  })

  cartItems.innerHTML = html
  cartTotal.textContent = total.toFixed(2)

  document.querySelectorAll(".remove-item").forEach((button) => {
    button.addEventListener("click", function () {
      const index = Number.parseInt(this.getAttribute("data-index"))
      removeFromCart(index)
    })
  })
}

function removeFromCart(index) {
  const cart = JSON.parse(localStorage.getItem("cart")) || []
  cart.splice(index, 1)
  localStorage.setItem("cart", JSON.stringify(cart))
  displayCart()
  updateCartCount()
}
