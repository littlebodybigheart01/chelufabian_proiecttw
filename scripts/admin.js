document.addEventListener("DOMContentLoaded", () => {
  let adminProducts = JSON.parse(localStorage.getItem("adminProducts")) || []
  let adminNews = JSON.parse(localStorage.getItem("adminNews")) || []

  updateStats()

  const productForm = document.getElementById("product-form")
  if (productForm) {
    productForm.addEventListener("submit", function (e) {
      e.preventDefault()

      const product = {
        id: Date.now(),
        name: document.getElementById("product-name").value,
        type: document.getElementById("product-type").value,
        price: document.getElementById("product-price").value,
        image: document.getElementById("product-image").value || "/placeholder.svg?height=250&width=250",
        description: document.getElementById("product-description").value,
      }

      adminProducts.push(product)
      localStorage.setItem("adminProducts", JSON.stringify(adminProducts))

      displayProducts()
      updateStats()
      this.reset()

      showSuccessMessage("Produs adăugat cu succes!")
      console.log("[v0] Product added:", product)
    })
  }

  const newsForm = document.getElementById("news-form")
  if (newsForm) {
    newsForm.addEventListener("submit", function (e) {
      e.preventDefault()

      const news = {
        id: Date.now(),
        title: document.getElementById("news-title").value,
        date: document.getElementById("news-date").value,
        image: document.getElementById("news-image").value || "/placeholder.svg?height=200&width=300",
        content: document.getElementById("news-content").value,
      }

      adminNews.push(news)
      localStorage.setItem("adminNews", JSON.stringify(adminNews))

      displayNews()
      updateStats()
      this.reset()

      showSuccessMessage("Noutate publicată cu succes!")
      console.log("[v0] News added:", news)
    })
  }

  displayProducts()
  displayNews()

  function displayProducts() {
    const productsList = document.getElementById("admin-products-list")
    adminProducts = JSON.parse(localStorage.getItem("adminProducts")) || []

    if (adminProducts.length === 0) {
      productsList.innerHTML =
        '<p class="info-message">Produsele adăugate vor apărea aici. Momentan funcționează doar în sesiunea curentă (fără bază de date).</p>'
      return
    }

    let html = ""
    adminProducts.forEach((product) => {
      html += `
                <div class="admin-item">
                    <div class="admin-item-info">
                        <h4>${product.name}</h4>
                        <p>Tip: ${product.type} | Preț: ${product.price} RON</p>
                        <p>${product.description || "Fără descriere"}</p>
                    </div>
                    <button class="delete-btn" onclick="deleteProduct(${product.id})">Șterge</button>
                </div>
            `
    })

    productsList.innerHTML = html
  }

  function displayNews() {
    const newsList = document.getElementById("admin-news-list")
    adminNews = JSON.parse(localStorage.getItem("adminNews")) || []

    if (adminNews.length === 0) {
      newsList.innerHTML =
        '<p class="info-message">Noutățile adăugate vor apărea aici. Momentan funcționează doar în sesiunea curentă (fără bază de date).</p>'
      return
    }

    let html = ""
    adminNews.forEach((news) => {
      html += `
                <div class="admin-item">
                    <div class="admin-item-info">
                        <h4>${news.title}</h4>
                        <p>Data: ${news.date}</p>
                        <p>${news.content.substring(0, 100)}...</p>
                    </div>
                    <button class="delete-btn" onclick="deleteNews(${news.id})">Șterge</button>
                </div>
            `
    })

    newsList.innerHTML = html
  }

  function updateStats() {
    adminProducts = JSON.parse(localStorage.getItem("adminProducts")) || []
    adminNews = JSON.parse(localStorage.getItem("adminNews")) || []

    const statsProducts = document.getElementById("stats-products")
    const statsNews = document.getElementById("stats-news")

    if (statsProducts) statsProducts.textContent = adminProducts.length
    if (statsNews) statsNews.textContent = adminNews.length
  }

  function showSuccessMessage(message) {
    const successDiv = document.createElement("div")
    successDiv.className = "success-message"
    successDiv.textContent = message

    const firstSection = document.querySelector(".admin-section")
    firstSection.insertBefore(successDiv, firstSection.firstChild)

    setTimeout(() => {
      successDiv.remove()
    }, 3000)
  }

  window.deleteProduct = (id) => {
    if (confirm("Sigur vrei să ștergi acest produs?")) {
      adminProducts = adminProducts.filter((p) => p.id !== id)
      localStorage.setItem("adminProducts", JSON.stringify(adminProducts))
      displayProducts()
      updateStats()
      console.log("[v0] Product deleted:", id)
    }
  }

  window.deleteNews = (id) => {
    if (confirm("Sigur vrei să ștergi această noutate?")) {
      adminNews = adminNews.filter((n) => n.id !== id)
      localStorage.setItem("adminNews", JSON.stringify(adminNews))
      displayNews()
      updateStats()
      console.log("[v0] News deleted:", id)
    }
  }

  window.displayProducts = displayProducts
  window.displayNews = displayNews
  window.updateStats = updateStats
})
