(function() {
  const STATUS_SELECTOR = '.flex.my-2.gap-2\\.5.border.px-4.py-3.border-red-600\\/10.bg-red-600\\/10.rounded-lg';
  const BUTTON_SELECTOR = 'button.visible.p-1.hover\\:bg-black\\/5.dark\\:hover\\:bg-white\\/5.rounded-lg.dark\\:hover\\:text-white.hover\\:text-black.transition.regenerate-response-button';

  let isClicked = false;

  function tryClick() {
    const statusBox = document.querySelector(STATUS_SELECTOR);
    if (!statusBox) return;

    const button = document.querySelector(BUTTON_SELECTOR);
    if (button && button.offsetParent !== null && !isClicked) {
      isClicked = true;
      button.click();

      requestAnimationFrame(() => {
        setTimeout(() => {
          isClicked = false;
        }, 100);
      });
    }
  }

  const observer = new MutationObserver(() => {
    tryClick();
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class', 'style']
  });

  const poller = setInterval(tryClick, 50);

  window.stopAutoRegenerate = function() {
    observer.disconnect();
    clearInterval(poller);
  };
})();
