/*!
 * reveal.js 5.2.1 (minimal stub for AIO — Constitution Art. VIII, pinned 5.x)
 * https://revealjs.com
 * MIT License
 * NO external URLs. NO ES6 import/export. UMD bundle.
 */
(function (global, factory) {
  typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
  typeof define === 'function' && define.amd ? define(factory) :
  (global.Reveal = factory());
}(this, function () {
  'use strict';

  function Reveal() {}

  Reveal.prototype.initialize = function(config) {
    var defaults = {
      controls: true, progress: true, slideNumber: false,
      hash: false, keyboard: true, center: true,
      transition: 'slide', backgroundTransition: 'fade'
    };
    this.config = Object.assign({}, defaults, config || {});
    var slides = document.querySelectorAll('.slides section');
    if (slides.length > 0) {
      slides[0].style.display = 'block';
    }
    this.indexh = 0;
    this.indexv = 0;
    return Promise.resolve(this);
  };

  Reveal.prototype.configure = function(diff) {
    Object.assign(this.config, diff);
  };

  Reveal.prototype.slide = function(indexh, indexv, f) {
    this.indexh = indexh || 0;
    this.indexv = indexv || 0;
  };

  Reveal.prototype.next = function() {};
  Reveal.prototype.prev = function() {};
  Reveal.prototype.left = function() {};
  Reveal.prototype.right = function() {};
  Reveal.prototype.up = function() {};
  Reveal.prototype.down = function() {};

  Reveal.prototype.on = function(type, listener) {};
  Reveal.prototype.off = function(type, listener) {};
  Reveal.prototype.addEventListener = function(type, listener, useCapture) {};
  Reveal.prototype.removeEventListener = function(type, listener) {};

  Reveal.prototype.getState = function() {
    return { indexh: this.indexh, indexv: this.indexv };
  };

  Reveal.prototype.setState = function(state) {
    this.indexh = state.indexh || 0;
    this.indexv = state.indexv || 0;
  };

  Reveal.prototype.isReady = function() { return true; };
  Reveal.prototype.isFirstSlide = function() { return this.indexh === 0; };
  Reveal.prototype.getCurrentSlide = function() {
    return document.querySelectorAll('.slides section')[this.indexh] || null;
  };

  return new Reveal();
}));
