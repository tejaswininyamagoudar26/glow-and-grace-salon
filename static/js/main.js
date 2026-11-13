/**
 * Glow & Grace Luxury Salon - Interactive Scripts
 * Handles mobile navigation, sticky header, gallery filtering, lightbox modal,
 * appointment date constraints, and flash messages.
 */

document.addEventListener('DOMContentLoaded', function () {
  'use strict';

  // 1. Mobile Navigation Menu Toggle
  const navToggleBtn = document.querySelector('.nav-toggle-btn');
  const navLinks = document.querySelector('.nav-links');

  if (navToggleBtn && navLinks) {
    navToggleBtn.addEventListener('click', function () {
      const isOpen = navLinks.classList.toggle('is-open');
      navToggleBtn.classList.toggle('is-active', isOpen);
      navToggleBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    // Close mobile nav when clicking a link
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('is-open');
        navToggleBtn.classList.remove('is-active');
        navToggleBtn.setAttribute('aria-expanded', 'false');
      });
    });

    // Close when clicking outside header
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.site-header') && navLinks.classList.contains('is-open')) {
        navLinks.classList.remove('is-open');
        navToggleBtn.classList.remove('is-active');
        navToggleBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // 2. Header elevation on scroll
  const siteHeader = document.querySelector('.site-header');
  if (siteHeader) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 20) {
        siteHeader.classList.add('scrolled');
      } else {
        siteHeader.classList.remove('scrolled');
      }
    });
  }

  // 3. Smooth scrolling for internal anchor links
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId && targetId !== '#') {
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
          e.preventDefault();
          targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });

  // 4. Gallery Category Filtering
  const galleryFilterContainer = document.getElementById('gallery-filter-tabs');
  if (galleryFilterContainer) {
    const galleryButtons = galleryFilterContainer.querySelectorAll('.filter-btn');
    const galleryItems = document.querySelectorAll('.gallery-item');
    galleryButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        galleryButtons.forEach(function (b) { b.classList.remove('active'); });
        this.classList.add('active');
        const filter = this.getAttribute('data-filter');

        galleryItems.forEach(function (item) {
          const itemCategory = item.getAttribute('data-category');
          if (filter === 'all' || itemCategory === filter) {
            item.style.display = 'block';
            setTimeout(function () {
              item.style.opacity = '1';
              item.style.transform = 'scale(1)';
            }, 10);
          } else {
            item.style.opacity = '0';
            item.style.transform = 'scale(0.96)';
            setTimeout(function () {
              item.style.display = 'none';
            }, 250);
          }
        });
      });
    });
  }

  // 5. Service Catalogue Filtering & Live Search
  const servicesFilterContainer = document.getElementById('services-filter-tabs');
  const serviceSearchInput = document.getElementById('service-search-input');
  const serviceSearchClear = document.getElementById('service-search-clear');
  const serviceCards = document.querySelectorAll('#catalogue-grid .service-card');
  const noServicesMsg = document.getElementById('no-services-message');

  let activeCategory = 'all';
  let searchQuery = '';

  function applyServiceFilters() {
    let visibleCount = 0;
    serviceCards.forEach(function (card) {
      const cardCategory = card.getAttribute('data-category') || '';
      const cardTitle = (card.querySelector('h3') ? card.querySelector('h3').textContent : '').toLowerCase();
      const cardDesc = (card.querySelector('.service-description') ? card.querySelector('.service-description').textContent : '').toLowerCase();
      const cardCategoryLabel = (card.querySelector('.service-category-indicator') ? card.querySelector('.service-category-indicator').textContent : '').toLowerCase();

      const matchesCategory = (activeCategory === 'all' || cardCategory === activeCategory);
      const matchesSearch = !searchQuery || cardTitle.includes(searchQuery) || cardDesc.includes(searchQuery) || cardCategoryLabel.includes(searchQuery);

      if (matchesCategory && matchesSearch) {
        card.style.display = 'flex';
        setTimeout(function () {
          card.style.opacity = '1';
          card.style.transform = 'scale(1)';
        }, 10);
        visibleCount++;
      } else {
        card.style.opacity = '0';
        card.style.transform = 'scale(0.96)';
        setTimeout(function () {
          card.style.display = 'none';
        }, 200);
      }
    });

    if (noServicesMsg) {
      if (visibleCount === 0) {
        noServicesMsg.style.display = 'block';
      } else {
        noServicesMsg.style.display = 'none';
      }
    }
  }

  if (servicesFilterContainer) {
    const serviceButtons = servicesFilterContainer.querySelectorAll('.filter-btn');
    serviceButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        serviceButtons.forEach(function (b) { b.classList.remove('active'); });
        this.classList.add('active');
        activeCategory = this.getAttribute('data-filter') || 'all';
        applyServiceFilters();
      });
    });
  }

  if (serviceSearchInput) {
    serviceSearchInput.addEventListener('input', function () {
      searchQuery = this.value.trim().toLowerCase();
      if (serviceSearchClear) {
        serviceSearchClear.classList.toggle('visible', searchQuery.length > 0);
      }
      applyServiceFilters();
    });

    if (serviceSearchClear) {
      serviceSearchClear.addEventListener('click', function () {
        serviceSearchInput.value = '';
        searchQuery = '';
        serviceSearchClear.classList.remove('visible');
        applyServiceFilters();
        serviceSearchInput.focus();
      });
    }
  }

  // 6. Gallery Lightbox Modal with Next/Prev Navigation
  const lightboxModal = document.getElementById('gallery-lightbox');
  const lightboxImg = document.getElementById('lightbox-image');
  const lightboxCategory = document.getElementById('lightbox-category-text');
  const lightboxCaption = document.getElementById('lightbox-caption-text');
  const lightboxCounter = document.getElementById('lightbox-counter-text');
  const lightboxClose = document.getElementById('lightbox-close-btn');
  const lightboxPrev = document.getElementById('lightbox-prev-btn');
  const lightboxNext = document.getElementById('lightbox-next-btn');

  let currentGalleryList = [];
  let currentImageIndex = 0;

  function getVisibleGalleryItems() {
    const allItems = Array.from(document.querySelectorAll('.gallery-item'));
    return allItems.filter(function (item) {
      return item.style.display !== 'none';
    });
  }

  function displayLightboxItem(index) {
    if (!currentGalleryList.length) return;
    if (index < 0) index = currentGalleryList.length - 1;
    if (index >= currentGalleryList.length) index = 0;
    currentImageIndex = index;

    const item = currentGalleryList[currentImageIndex];
    const img = item.querySelector('.gallery-image');
    const categoryEl = item.querySelector('.gallery-category');
    const captionEl = item.querySelector('.gallery-caption');

    if (img && lightboxImg) {
      lightboxImg.style.opacity = '0.3';
      setTimeout(function () {
        lightboxImg.src = img.src;
        lightboxImg.alt = img.alt || 'Glow & Grace Salon gallery photo';
        lightboxImg.style.opacity = '1';
      }, 100);

      if (lightboxCategory) {
        lightboxCategory.textContent = categoryEl ? categoryEl.textContent : '';
      }
      if (lightboxCaption) {
        lightboxCaption.textContent = captionEl ? captionEl.textContent : '';
      }
      if (lightboxCounter) {
        lightboxCounter.textContent = `${currentImageIndex + 1} of ${currentGalleryList.length}`;
      }
    }
  }

  if (lightboxModal && lightboxImg) {
    document.querySelectorAll('.gallery-item').forEach(function (item) {
      item.addEventListener('click', function () {
        currentGalleryList = getVisibleGalleryItems();
        const clickedIndex = currentGalleryList.indexOf(item);
        displayLightboxItem(clickedIndex !== -1 ? clickedIndex : 0);
        lightboxModal.classList.add('is-open');
        document.body.style.overflow = 'hidden';
      });
    });

    const closeLightbox = function () {
      lightboxModal.classList.remove('is-open');
      document.body.style.overflow = '';
    };

    if (lightboxClose) {
      lightboxClose.addEventListener('click', closeLightbox);
    }

    if (lightboxPrev) {
      lightboxPrev.addEventListener('click', function (e) {
        e.stopPropagation();
        displayLightboxItem(currentImageIndex - 1);
      });
    }

    if (lightboxNext) {
      lightboxNext.addEventListener('click', function (e) {
        e.stopPropagation();
        displayLightboxItem(currentImageIndex + 1);
      });
    }

    lightboxModal.addEventListener('click', function (e) {
      if (e.target === lightboxModal || e.target.classList.contains('lightbox-content')) {
        closeLightbox();
      }
    });

    document.addEventListener('keydown', function (e) {
      if (!lightboxModal.classList.contains('is-open')) return;
      if (e.key === 'Escape') {
        closeLightbox();
      } else if (e.key === 'ArrowLeft') {
        displayLightboxItem(currentImageIndex - 1);
      } else if (e.key === 'ArrowRight') {
        displayLightboxItem(currentImageIndex + 1);
      }
    });
  }

  // 6. Appointment Form Enhancements & Dynamic Service Cascading
  const dateInput = document.getElementById('date');
  if (dateInput) {
    // Set minimum date to today (cannot book in the past)
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
  }

  // Dynamic Service Cascading: Category -> Service
  const categorySelect = document.getElementById('category');
  const serviceSelect = document.getElementById('service');
  const previewCard = document.getElementById('service-preview-card');
  const spcName = document.getElementById('spc-name');
  const spcPrice = document.getElementById('spc-price');
  const spcDuration = document.getElementById('spc-duration');
  const spcDesc = document.getElementById('spc-desc');
  const spcDiscount = document.getElementById('spc-discount');

  // Load services data from script tag
  let servicesCatalog = [];
  const servicesDataTag = document.getElementById('services-data');
  if (servicesDataTag) {
    try {
      servicesCatalog = JSON.parse(servicesDataTag.textContent);
    } catch (e) {
      console.error('Error parsing services data:', e);
    }
  }

  function showServicePreview(serviceObj) {
    if (!previewCard || !serviceObj) return;
    if (spcName) spcName.textContent = serviceObj.name || '';
    if (spcPrice) spcPrice.textContent = serviceObj.price || serviceObj.offer_price_formatted || '';
    if (spcDuration) spcDuration.textContent = '⏱ ' + (serviceObj.duration || '60 mins');
    if (spcDesc) spcDesc.textContent = serviceObj.description || '';
    if (spcDiscount) {
      if (serviceObj.discount_percent && serviceObj.discount_percent > 0) {
        spcDiscount.textContent = serviceObj.discount_percent + '% OFF';
        spcDiscount.style.display = 'inline-block';
      } else {
        spcDiscount.style.display = 'none';
      }
    }
    previewCard.style.display = 'flex';
  }

  function hideServicePreview() {
    if (previewCard) previewCard.style.display = 'none';
  }

  function populateServicesForCategory(categoryName, preselectedService) {
    if (!serviceSelect) return;
    serviceSelect.innerHTML = '<option value="" disabled selected>-- Select a specific service --</option>';
    serviceSelect.disabled = false;

    const filtered = servicesCatalog.filter(function (s) {
      return s.category && s.category.toLowerCase() === categoryName.toLowerCase();
    });

    filtered.forEach(function (s) {
      const opt = document.createElement('option');
      opt.value = s.name;
      opt.textContent = `${s.name} (${s.price || s.offer_price_formatted} • ${s.duration})`;
      if (preselectedService && preselectedService.toLowerCase() === s.name.toLowerCase()) {
        opt.selected = true;
      }
      serviceSelect.appendChild(opt);
    });

    if (preselectedService) {
      const match = filtered.find(function (s) {
        return s.name.toLowerCase() === preselectedService.toLowerCase();
      });
      if (match) {
        showServicePreview(match);
      }
    } else {
      hideServicePreview();
    }
  }

  if (categorySelect && serviceSelect) {
    categorySelect.addEventListener('change', function () {
      const selectedCat = this.value;
      if (selectedCat) {
        populateServicesForCategory(selectedCat, null);
      } else {
        serviceSelect.innerHTML = '<option value="" disabled selected>-- Select category first --</option>';
        serviceSelect.disabled = true;
        hideServicePreview();
      }
    });

    serviceSelect.addEventListener('change', function () {
      const chosenName = this.value;
      const found = servicesCatalog.find(function (s) {
        return s.name === chosenName;
      });
      if (found) {
        showServicePreview(found);
      } else {
        hideServicePreview();
      }
    });

    // Check URL parameters for pre-selected service
    const urlParams = new URLSearchParams(window.location.search);
    const serviceParam = urlParams.get('service');
    if (serviceParam) {
      const matchedSvc = servicesCatalog.find(function (s) {
        return s.name.toLowerCase().includes(serviceParam.toLowerCase());
      });
      if (matchedSvc) {
        // Select matching category
        for (let i = 0; i < categorySelect.options.length; i++) {
          if (categorySelect.options[i].value.toLowerCase() === matchedSvc.category.toLowerCase()) {
            categorySelect.selectedIndex = i;
            break;
          }
        }
        populateServicesForCategory(matchedSvc.category, matchedSvc.name);
      }
    }
  }

  // Client-side quick validation feedback on mobile input
  const phoneInput = document.getElementById('phone');
  if (phoneInput) {
    phoneInput.addEventListener('input', function () {
      const cleaned = this.value.replace(/[\s\-\(\)]/g, '');
      const valid = /^(\+91|91|0)?[6-9]\d{9}$/.test(cleaned);
      if (this.value.length >= 10) {
        if (!valid) {
          this.style.borderColor = 'var(--color-blush-500)';
        } else {
          this.style.borderColor = 'var(--color-sage-500)';
        }
      } else {
        this.style.borderColor = '';
      }
    });
  }

  // 7. Flash message close buttons
  document.querySelectorAll('.flash-close-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const parent = this.closest('.flash-message');
      if (parent) {
        parent.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        parent.style.opacity = '0';
        parent.style.transform = 'translateY(-10px)';
        setTimeout(function () {
          parent.remove();
        }, 300);
      }
    });
  });

  // 8. Back-to-Top Button
  const backToTopBtn = document.getElementById('back-to-top');
  if (backToTopBtn) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 350) {
        backToTopBtn.classList.add('is-visible');
      } else {
        backToTopBtn.classList.remove('is-visible');
      }
    });

    backToTopBtn.addEventListener('click', function () {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }

  // 9. Subtle Scroll-Reveal Animation via IntersectionObserver
  if ('IntersectionObserver' in window) {
    const revealElements = document.querySelectorAll(
      '.category-service-card, .service-card, .package-card, .testimonial-card, ' +
      '.pillar-card, .transformation-card, .info-card, .form-card, .about-split-grid, ' +
      '.gallery-item, .home-contact-card'
    );

    const revealObserver = new IntersectionObserver(function (entries, observer) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('has-revealed');
          observer.unobserve(entry.target);
        }
      });
    }, {
      rootMargin: '0px 0px -40px 0px',
      threshold: 0.1
    });

    revealElements.forEach(function (el) {
      el.classList.add('reveal-on-scroll');
      revealObserver.observe(el);
    });
  }

  // 10. Form Submission Feedback (Prevent double-submission & show loading state)
  const allForms = document.querySelectorAll('form:not([data-no-feedback])');
  allForms.forEach(function (form) {
    form.addEventListener('submit', function (e) {
      // Check HTML5 validity first if available
      if (form.checkValidity && !form.checkValidity()) {
        return; // Allow browser or custom validation to display errors
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        const originalText = submitBtn.innerHTML;
        // Mark button as submitting
        submitBtn.setAttribute('data-original-text', originalText);
        submitBtn.disabled = true;
        submitBtn.classList.add('is-submitting');
        submitBtn.innerHTML = `
          <span class="btn-spinner" aria-hidden="true"></span>
          <span>Processing…</span>
        `;
        // Re-enable after 10s timeout safeguard
        setTimeout(function () {
          if (submitBtn.disabled) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('is-submitting');
            submitBtn.innerHTML = originalText;
          }
        }, 10000);
      }
    });
  });
});
