// static/lazyloaddemo.js

// This event listener ensures that the code runs after the DOM content is fully loaded.
document.addEventListener("DOMContentLoaded", function () {
    const lazyElem = document.querySelectorAll(".lazy");
    const lazyLoad = function () {
      lazyElem.forEach(function (elem) {
        elem.style.display = "block";
        if (elem.getBoundingClientRect().top <= window.innerHeight && elem.getBoundingClientRect().bottom >= 0) {
          elem.style.display = "block";
        } else {
          // Element is not in the viewport or is still visible, hide.
          elem.style.display = "none";
        }
        return;
      });
    };
  
    // Initially run the lazyLoad function to load images visible on page load.
    lazyLoad();
  
    // Add event listeners to call the lazyLoad function when the page is scrolled, resized, or the orientation changes.
    document.addEventListener("scroll", lazyLoad);
    window.addEventListener("resize", lazyLoad);
    window.addEventListener("orientationchange", lazyLoad);
  });