// Full-size overlay for figures in the note body (see ImageZoom.tsx).
document.addEventListener("nav", () => {
  const close = () => document.querySelector(".image-zoom-overlay")?.remove()
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") close()
  }

  const open = (e: Event) => {
    const img = e.currentTarget as HTMLImageElement
    close()
    const overlay = document.createElement("div")
    overlay.className = "image-zoom-overlay"
    const big = document.createElement("img")
    big.src = img.currentSrc || img.src
    big.alt = img.alt
    overlay.appendChild(big)
    overlay.addEventListener("click", close)
    document.body.appendChild(overlay)
  }

  for (const img of document.querySelectorAll<HTMLImageElement>("article img")) {
    if (img.closest("a")) continue // linked images keep their link
    img.classList.add("zoomable")
    img.addEventListener("click", open)
    window.addCleanup(() => img.removeEventListener("click", open))
  }
  document.addEventListener("keydown", onKey)
  window.addCleanup(() => {
    document.removeEventListener("keydown", onKey)
    close()
  })
})
