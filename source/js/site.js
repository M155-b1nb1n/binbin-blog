(() => {
  const enhance = () => {
    const siteInfo = document.querySelector('#site-info');
    const siteTitle = document.querySelector('#site-title');

    if (siteInfo && siteTitle && !siteInfo.querySelector('.binbin-eyebrow')) {
      const eyebrow = document.createElement('div');
      eyebrow.className = 'binbin-eyebrow';
      eyebrow.textContent = 'M155.B1NB1N / SECURITY LOG';
      siteInfo.insertBefore(eyebrow, siteTitle);
    }

    document.querySelectorAll('#recent-posts > .recent-post-item').forEach((card, index) => {
      card.style.setProperty('--card-order', String(index));
    });

    requestAnimationFrame(() => document.documentElement.classList.add('binbin-ready'));
  };

  document.addEventListener('DOMContentLoaded', enhance, { once: true });
  document.addEventListener('pjax:complete', enhance);
})();
