document.addEventListener("DOMContentLoaded", () => {
  const contactForm = document.getElementById("contact-form")

  if (contactForm) {
    contactForm.addEventListener("submit", function (e) {
      e.preventDefault()

      const formData = {
        name: document.getElementById("name").value,
        email: document.getElementById("email").value,
        phone: document.getElementById("phone").value,
        subject: document.getElementById("subject").value,
        message: document.getElementById("message").value,
      }

      console.log("[v0] Contact form submitted:", formData)

      alert(
        "Mulțumim pentru mesaj! Vom reveni cu un răspuns în cel mai scurt timp. (Funcționalitatea completă va fi implementată cu baza de date)",
      )

      this.reset()
    })
  }
})
