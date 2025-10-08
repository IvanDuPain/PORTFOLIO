const navToggle = document.querySelector('.nav-toggle');
const navList = document.getElementById('primary-nav');
if (navToggle && navList) {
  navToggle.addEventListener('click', () => {
    const expanded = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!expanded));
    navList.classList.toggle('show');
  });
}

// Data structure to be filled from PDF parsing
const siteData = {
  about: '',
  contact: { email: '', phone: '', location: '', linkedin: '', github: '' },
  experiences: [],
  projects: [],
  skills: []
};

// Toggle dynamic rendering for certain sections (useful for GitHub Pages)
const RENDER_EXPERIENCES_FROM_JSON = false;

function renderSite(data){
  const about = document.getElementById('about-text');
  if (about && data.about) about.textContent = data.about;

  const email = document.getElementById('contact-email');
  if (email && data.contact.email){ email.textContent = data.contact.email; email.href = `mailto:${data.contact.email}`; }
  const phone = document.getElementById('contact-phone');
  if (phone && data.contact.phone){ phone.textContent = data.contact.phone; }
  const location = document.getElementById('contact-location');
  if (location && data.contact.location){ location.textContent = data.contact.location; }
  const linkedin = document.getElementById('contact-linkedin');
  if (linkedin && data.contact.linkedin){ linkedin.textContent = 'Profil LinkedIn'; linkedin.href = data.contact.linkedin; }
  const github = document.getElementById('contact-github');
  if (github && data.contact.github){ github.textContent = 'GitHub'; github.href = data.contact.github; }

  const expList = document.getElementById('experience-list');
  if (RENDER_EXPERIENCES_FROM_JSON && expList && Array.isArray(data.experiences)){
    data.experiences.forEach(exp => {
      const card = document.createElement('article');
      card.className = 'card';
      card.innerHTML = `
        <h3>${exp.title || ''}</h3>
        <p class="meta">${[exp.company, exp.period, exp.location].filter(Boolean).join(' • ')}</p>
        <p>${exp.description || ''}</p>
      `;
      expList.appendChild(card);
    });
  }

  const projects = document.getElementById('projects-grid');
  if (projects && Array.isArray(data.projects)){
    data.projects.forEach(p => {
      const card = document.createElement('article');
      card.className = 'project';
      card.innerHTML = `
        <h3>${p.name || ''}</h3>
        <p>${p.summary || ''}</p>
        ${p.link ? `<a href="${p.link}" target="_blank" rel="noopener">Voir le projet</a>` : ''}
      `;
      projects.appendChild(card);
    });
  }

  const skills = document.getElementById('skills-list');
  if (skills && Array.isArray(data.skills)){
    skills.innerHTML = '';
    data.skills.forEach(s => {
      const li = document.createElement('li');
      li.textContent = s;
      skills.appendChild(li);
    });
  }
}

// Allow selecting a local image to preview in hero
const portraitInput = document.getElementById('portraitFile');
if (portraitInput) {
  portraitInput.addEventListener('change', e => {
    const file = portraitInput.files && portraitInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const img = document.querySelector('.portrait-img');
      if (img) img.src = String(reader.result);
    };
    reader.readAsDataURL(file);
  });
}

// Try to load parsed content if present
fetch('site_content.json')
  .then(r => r.ok ? r.json() : null)
  .then(json => { if (json) renderSite(json); })
  .catch(() => {});

