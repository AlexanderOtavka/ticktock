// Use window.location.origin in unsupported browsers.

if (!window.location.origin) {
  window.location.origin = window.location.protocol + '//' +
                           window.location.host;
}
