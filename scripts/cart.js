document.addEventListener("DOMContentLoaded", () => {
  const addToCartButtons = document.querySelectorAll(".add-to-cart")

  addToCartButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const productId = this.getAttribute("data-id")
      const productName = this.getAttribute("data-name")
      const productPrice = this.getAttribute("data-price")
      const productType = this.getAttribute("data-type")

      addToCart({
        id: productId,
        name: productName,
        price: productPrice,
        type: productType,
      })

      this.textContent = "Adăugat! ✓"
      this.style.backgroundColor = "#28a745"

      setTimeout(() => {
        this.textContent = "Adaugă în coș"
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

  console.log("[v0] Product added to cart:", product)
}

function updateCartCount() {
  const cart = JSON.parse(localStorage.getItem("cart")) || []
  const cartCount = document.getElementById("cart-count")
  if (cartCount) {
    cartCount.textContent = cart.length
  }
}
