document.addEventListener("DOMContentLoaded", () => {
  const addToCartButtons = document.querySelectorAll(".add-to-cart, .add-to-cart-detail")

  addToCartButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const productName = this.getAttribute("data-name")
      const productPrice = this.getAttribute("data-price")
      const productType = this.getAttribute("data-type")

      addToCart({
        name: productName,
        price: productPrice,
        type: productType,
      })

      this.textContent = "Adăugat! ✓"
      this.style.backgroundColor = "#28a745"

      setTimeout(() => {
        this.textContent = this.classList.contains("add-to-cart-detail") ? "Adaugă în coș" : "Adaugă în coș"
        this.style.backgroundColor = ""
      }, 2000)
    })
  })
})

function addToCart(product) {
  const cart = JSON.parse(localStorage.getItem("cart")) || []
  cart.push(product)
  localStorage.setItem("cart", JSON.stringify(cart))
  updateCartCount()
  // Declare the updateMobileCartBadge function or import it before using
  const updateMobileCartBadge = () => {
    // Function implementation here
  }
  if (typeof updateMobileCartBadge === "function") {
    updateMobileCartBadge()
  }
}

function updateCartCount() {
  const cart = JSON.parse(localStorage.getItem("cart")) || []
  const cartCount = document.getElementById("cart-count")
  if (cartCount) {
    cartCount.textContent = cart.length
  }
}
