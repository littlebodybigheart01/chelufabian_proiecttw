// This script will handle dynamic product loading when connected to a database
document.addEventListener("DOMContentLoaded", () => {
  // Get product ID from URL parameters
  const urlParams = new URLSearchParams(window.location.search)
  const productId = urlParams.get("id")

  if (productId) {
    // When database is connected, fetch product details here
    loadProductFromDatabase(productId)
  } else {
    // Show example product for demo purposes
    loadExampleProduct()
  }

  // Add to cart functionality for detail page
  const addToCartBtn = document.getElementById("add-to-cart-detail-btn")
  if (addToCartBtn) {
    addToCartBtn.addEventListener("click", function () {
      const productName = document.getElementById("product-name").textContent
      const productPrice = document.getElementById("product-price").textContent.replace(" RON", "")
      const productType = document.getElementById("product-type").textContent

      // Declare the addToCart function
      function addToCart(product) {
        console.log("Product added to cart:", product)
        // Here you can implement the logic to add the product to the cart
      }

      addToCart({
        id: productId || "example",
        name: productName,
        price: productPrice,
        type: productType,
      })

      this.textContent = "Adăugat în coș! ✓"
      this.style.backgroundColor = "#28a745"

      setTimeout(() => {
        this.textContent = "Adaugă în coș"
        this.style.backgroundColor = ""
      }, 2000)
    })
  }
})

// Function to load product from database (to be implemented when database is connected)
function loadProductFromDatabase(productId) {
  console.log("[v0] Loading product with ID:", productId)

  // TODO: When database is connected, replace this with actual database query
  // Example: fetch(`/api/products/${productId}`)
  //   .then(response => response.json())
  //   .then(data => {
  //     document.getElementById('product-name').textContent = data.name
  //     document.getElementById('product-type').textContent = data.type
  //     document.getElementById('product-price').textContent = data.price + ' RON'
  //     document.getElementById('product-description').textContent = data.description
  //     document.getElementById('product-image').src = data.image
  //     // Load features dynamically
  //     const featuresContainer = document.getElementById('product-features')
  //     featuresContainer.innerHTML = ''
  //     data.features.forEach(feature => {
  //       const li = document.createElement('li')
  //       li.textContent = feature
  //       featuresContainer.appendChild(li)
  //     })
  //   })

  // For now, load example product
  loadExampleProduct()
}

// Load example product for demonstration
function loadExampleProduct() {
  const exampleProduct = {
    name: "Britney Spears - Glory",
    type: "Vinyl",
    price: "149.99",
    description:
      "Albumul 'Glory' al lui Britney Spears este o colecție spectaculoasă de melodii pop moderne. Lansat în 2016, acest album marchează revenirea triumfală a reginei pop-ului cu hituri precum 'Make Me' și 'Slumber Party'. Un must-have pentru orice fan adevărat!",
    image: "/images/glory.jpeg",
    features: [
      "Vinyl original sigilat",
      "Booklet cu fotografii exclusive",
      "Calitate audio superioară",
      "Ediție de colecție",
      "Livrare gratuită pentru comenzi peste 200 RON",
    ],
  }
  // </CHANGE>

  document.getElementById("product-name").textContent = exampleProduct.name
  document.getElementById("product-type").textContent = exampleProduct.type
  document.getElementById("product-price").textContent = exampleProduct.price + " RON"
  document.getElementById("product-description").textContent = exampleProduct.description
  document.getElementById("product-image").src = exampleProduct.image
  document.getElementById("product-image").alt = exampleProduct.name

  const featuresContainer = document.getElementById("product-features")
  featuresContainer.innerHTML = ""
  exampleProduct.features.forEach((feature) => {
    const li = document.createElement("li")
    li.textContent = feature
    featuresContainer.appendChild(li)
  })
}
