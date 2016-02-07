// Copyright (c) 2016 Drake Developers Club All Rights Reserved.

/* globals Promise */

/**
 * Defines GAPIManager object for promise oriented GAPI communication.
 *
 * Client library must be loaded after gapi-manager.js with callback named
 * 'GAPIManager', eg:
 * ```
 *   <script src="https://apis.google.com/js/client.js?onload=GAPIManager"></script>
 * ```
 */
(function() {
'use strict';

var _scopes = [];
var _clientId = '';
var _loadedAPIs = [];

var GAPIManager, _loadedGAPI;
(function() {
  var _onLoad;

  /**
   * Promise that resolves to the gapi object.
   */
  _loadedGAPI = new Promise(function(resolve) {
    _onLoad = function() {
      resolve(window.gapi);
    };
  });

  /**
   * Callback called when gapi loads.
   */
  GAPIManager = function() {
    _onLoad();
  };
})();

/**
 * Load an api with the given data.
 *
 * @return Promise that resolves to an API object.
 */
GAPIManager.loadAPI = function(name, version, apiRoot) {
  return _loadedGAPI
    .then(function($gapi) {
      var loadedAPI = new Promise(function(resolve, reject) {
        $gapi.client.load(name, version, null, apiRoot).then(function(resp) {
          if (resp && resp.error) {
            reject(new HTTPError(resp.error.code, resp.error.message));
          } else if (!$gapi.client[name]) {
            reject(new HTTPError(404, 'Not Found.'));
          } else {
            resolve(_patchifyAPI($gapi.client[name]));
          }
        });
      });
      _loadedAPIs.push(loadedAPI);
      return loadedAPI;
    });
};

/**
 * Finish loading all APIs set to load with APIManager.loadAPI.
 *
 * @return Promise that resolves when all loadAPI promises previously made
 *   have resolved.
 */
GAPIManager.loadAllAPIs = function() {
  return Promise.all(_loadedAPIs);
};

/**
 * Set scopes to authorize.
 *
 * This should be done before calling GAPIManager.authenticate().
 */
GAPIManager.setScopes = function(scopes) {
  _scopes = scopes;
};

/**
 * Set client ID to authorize with.
 *
 * This should be done before calling GAPIManager.authenticate().
 */
GAPIManager.setClientId = function(clientId) {
  _clientId = clientId;
};

/**
 * Authenticate with the clientId and scopes set previously.
 *
 * @return Promise that resolves with undefined when authenticated.
 */
GAPIManager.authorize = function(mode) {
  return _loadedGAPI
    .then(function($gapi) {
      return new Promise(function(resolve, reject) {
        $gapi.auth.authorize({
          client_id: _clientId, // jshint ignore:line
          scope: _scopes,
          immediate: mode,
          cookie_policy: window.location.origin // jshint ignore:line
        }, function(resp) {
          if (resp.error) {
            reject(new AuthError(resp.error, resp.error_subtype)); // jshint ignore:line
          } else {
            resolve(resp);
          }
        });
      });
    });
};

/**
 * Sign the currently authed user out.
 */
GAPIManager.signOut = function() {
  _loadedGAPI
    .then(function($gapi) {
      $gapi.auth.signOut();
    });
};

/**
 * Error with an HTTP status code, thrown when API request fails.
 */
var HTTPError = function(code, message) {
  Error.call(this);
  this.message = message;
  this.code = code;
};
HTTPError.prototype = Object.create(Error.prototype);
HTTPError.prototype.constructor = HTTPError;
GAPIManager.HTTPError = HTTPError;

/**
 * Error signaling authorization failed.
 */
var AuthError = function(errorType, errorSubtype) {
  Error.call(this);
  this.message = errorType + ': ' + errorSubtype;
  this.type = errorType;
  this.subtype = errorSubtype;

  this.accessDenied = (errorSubtype === 'access_denied');
};
AuthError.prototype = Object.create(Error.prototype);
AuthError.prototype.constructor = AuthError;
GAPIManager.AuthError = AuthError;

/**
 * Recursively crawl the API and return a modified copy that uses promises.
 */
var _patchifyAPI = function(apiObject, notInAPIRoot) {
  if (apiObject instanceof Function) {
    return function(params) {
      return new Promise(function(resolve, reject) {
        apiObject(params).execute(function(resp) {
          if (!resp) {
            reject(new HTTPError(404, 'Not Found.'));
          } else if (resp.code) {
            reject(new HTTPError(resp.code, resp.message));
          } else {
            resolve(resp);
          }
        });
      });
    };
  } else {
    var copy = {};
    Object.keys(apiObject).forEach(function(name) {
      if (notInAPIRoot || name !== 'kB') {
        copy[name] = _patchifyAPI(apiObject[name], true);
      }
    });
    return copy;
  }
};

window.GAPIManager = GAPIManager;

})();
