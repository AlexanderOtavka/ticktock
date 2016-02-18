/*
Copyright (c) 2015 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/

/* globals Promise, GAPIManager */

(function(app) {
'use strict';

// Imports are loaded and elements have been registered.
window.addEventListener('WebComponentsReady', function() {
  setInterval(function() {
    updateDurations(app.selectedCalendar);
  }, 1000);

  signIn(true)
    .then(loadAllData)
    .catch(logError);
});

//
// API configuration
//

GAPIManager.setClientId(
  '208366307202-00824keo9p663g1uhkd8misc52e1c5pa.apps.googleusercontent.com');
GAPIManager.setScopes([
  'https://www.googleapis.com/auth/userinfo.email',
  'https://www.googleapis.com/auth/plus.me',
  'https://www.googleapis.com/auth/calendar.readonly'
]);

var LOCAL_API_ROOT = '//' + window.location.host + '/_ah/api';
var loadedTickTockAPI = GAPIManager.loadAPI('ticktock', 'v1', LOCAL_API_ROOT);
var loadedOauth2API = GAPIManager.loadAPI('oauth2', 'v2');

//
// Data
//

// User data.
var SIGNED_OUT_USER_INFO = {
  name: 'Sign In with Google',
  picture: '/images/google-logo.svg',
  loading: false,
  signedOut: true
};
var LOADING_USER_INFO = {
  name: 'Loading...',
  picture: '',
  loading: true,
  signedOut: false
};
app.userInfo = LOADING_USER_INFO;

// Calendar and event data.
var ALL_CALENDAR = {
  kind: 'pseudo:all',
  name: 'All Calendars',
  calendarId: '*',
  color: '#e91e63',
  errored: false,
  loading: true,
  hidden: false,
  events: [],
  nextPageToken: null
};
var LOADING_CALENDAR = {
  kind: 'pseudo:loading',
  name: 'TickTock',
  calendarId: ALL_CALENDAR.calendarId,
  color: '#e91e63',
  errored: false,
  loading: true,
  hidden: false,
  events: [],
  nextPageToken: null
};
var ERROR_CALENDAR = {
  kind: 'pseudo:error',
  name: 'TickTock',
  calendarId: '',
  color: '#e91e63',
  errored: true,
  loading: false,
  hidden: false,
  events: [],
  nextPageToken: null
};
app.selectedCalendar = LOADING_CALENDAR;

app.calendars = [];
app.listedCalendars = [];
app.hasHiddenCalendars = false;

// Settings.
app.showHiddenCalendars = false;
app.showHiddenEvents = false;

//
// Getters
//

app.getSignedOutClass = function(signedOut) {
  return signedOut ? 'signed-out' : '';
};

app.getHiddenEventsToggleText = function(showHiddenEvents) {
  return showHiddenEvents ? 'Hide Hidden Events' : 'Show Hidden Events';
};

app.getHiddenCalendarToggleText = function(showHiddenCalendars) {
  return showHiddenCalendars ? 'Hide Hidden Calendars' :
                               'Show Hidden Calendars';
};

app.getUrlEncoded = function(string) {
  return encodeURIComponent(string);
};

app.getUrlDecoded = function(string) {
  return decodeURIComponent(string);
};

(function() {
  var calendarStatus = function(signedOut, calendarErrored, eventsLoading,
                                nextPageToken, events) {
    if (signedOut) {
      return calendarStatus.Status.SIGNED_OUT;
    }
    if (calendarErrored) {
      return calendarStatus.Status.ERRORED;
    }
    if (eventsLoading || nextPageToken) {
      return calendarStatus.Status.LOADING;
    }
    if (!Boolean((events || []).length)) {
      return calendarStatus.Status.EMPTY;
    }
    return calendarStatus.Status.GOOD;
  };
  calendarStatus.Status = {
    GOOD: 0,
    EMPTY: 1,
    LOADING: 2,
    ERRORED: 3,
    SIGNED_OUT: 4
  };

  app.getCalendarEmpty = function(signedOut, calendarErrored, eventsLoading,
                                  nextPageToken, events) {
    return calendarStatus(signedOut, calendarErrored, eventsLoading,
                          nextPageToken, events) ===
           calendarStatus.Status.EMPTY;
  };

  app.getCalendarErrored = function(signedOut, calendarErrored) {
    return calendarStatus(signedOut, calendarErrored) ===
           calendarStatus.Status.ERRORED;
  };

  app.getCalendarLoading = function(signedOut, calendarErrored, eventsLoading,
                                    nextPageToken) {
    return calendarStatus(signedOut, calendarErrored, eventsLoading,
                          nextPageToken) ===
           calendarStatus.Status.LOADING;
  };
})();

//
// Actions
//

app.displayInstalledToast = function() {
  // Check to make sure caching is actually enabled—it won't be in the dev environment.
  // if (!Polymer.dom(document).querySelector('platinum-sw-cache').disabled) {
  //   app.$.cachingComplete.show();
  // }
};

/**
 * Close drawer after menu item is selected if drawerPanel is narrow.
 */
app.closeDrawer = function() {
  var drawerPanel = app.$.paperDrawerPanel;
  if (drawerPanel.narrow) {
    drawerPanel.closeDrawer();
  }
};

/**
 * Scroll page to top and expand header.
 */
app.scrollPageToTop = function() {
  app.$.mainArea.$.mainContainer.scrollTop = 0;
};

/**
 * Select calendar, or que up calendar to be selected.
 *
 * If no calendar ID is provided, the selectedCalendar will be forced off the
 * LOADING_CALENDAR, either on to a proper calendar, or the ERROR_CALENDAR.
 */
app.selectCalendar = function(calendarId) {
  if (!calendarId) {
    calendarId = app.selectedCalendar.calendarId;
  } else if (app.selectedCalendar === LOADING_CALENDAR) {
    LOADING_CALENDAR.calendarId = calendarId;
    return;
  }
  var calendar = getCalendarById(calendarId);
  if (calendar) {
    app.selectedCalendar = calendar;
  } else {
    ERROR_CALENDAR.calendarId = calendarId;
    app.selectedCalendar = ERROR_CALENDAR;
  }
  updateListedCalendars();
  app.$.eventList.openedIndex = 0;
};

app.toggleShowHiddenEvents = function() {
  app.showHiddenEvents = !app.showHiddenEvents;
};

app.toggleShowHiddenCalendars = function() {
  setTimeout(function() {
    app.showHiddenCalendars = !app.showHiddenCalendars;
    updateListedCalendars();
  }, 20);
};

app.showSigninPopup = function() {
  signIn(false)
    .then(loadAllData)
    .catch(logError);
};

app.refreshThisCalendar = function() {
  if (app.selectedCalendar === LOADING_CALENDAR ||
      app.selectedCalendar === ERROR_CALENDAR ||
      app.selectedCalendar.loading ||
      app.userInfo.signedOut) {
    return;
  }

  var calendars;
  var doAllCalendars = (app.selectedCalendar === ALL_CALENDAR);

  if (doAllCalendars) {
    calendars = app.calendars;
  } else {
    calendars = [app.selectedCalendar];
  }

  loadEvents(calendars)
    .catch(logError);
};

//
// Event handlers
//

app.onEventChanged = function(event) {
  singleSortEvent(event.detail.eventId, event.detail.calendarId);
  patchEvent(event.detail)
    .catch(handleHTTPError)
    .catch(logError);
};

app.onCalendarHiddenToggled = function(event) {
  var calendar = getCalendarById(event.target.calendarId);
  if (calendar) {
    calendar.events.forEach(function(calendarEvent) {
      calendarEvent.calendarHidden = calendar.hidden;
    });
    if (calendar === app.selectedCalendar) {
      calendar.events.forEach(function(calendarEvent, i) {
        app.notifyPath(['selectedCalendar', 'events', i, 'calendarHidden'],
                       calendar.hidden);
      });
    } else if (app.selectedCalendar === ALL_CALENDAR) {
      ALL_CALENDAR.events.forEach(function(calendarEvent, i) {
        if (calendarEvent.calendarId === event.target.calendarId) {
          app.notifyPath(['selectedCalendar', 'events', i, 'calendarHidden'],
                         calendar.hidden);
        }
      });
    }
  }
  updateListedCalendars();
  patchCalendar({
    calendarId: event.target.calendarId,
    hidden: event.detail.value
  })
    .catch(handleHTTPError)
    .catch(logError);
};

//
// Network
//

var handleHTTPError = function(err) {
  if (err instanceof GAPIManager.HTTPError) {
    console.error(err);
    if (err.code === -1) {
      app.$.networkError.show();
    } else if (err.code === 401) {
      signOut();
    } else {
      app.$.error.show();
    }
  } else {
    throw err;
  }
};

var handleAuthError = function(err) {
  if (err.code === 401) {
    console.error(err);
    return signIn(true);
  } else {
    throw err;
  }
};

var sendReAuthedRequest = function(request) {
  return request
    .catch(function(err) {
      return handleAuthError(err)
        .then(function() {
          return request;
        });
    });
};

var updateAllCalendarState = function() {
  ALL_CALENDAR.events = [];
  app.calendars.forEach(function(calendar) {
    ALL_CALENDAR.events = ALL_CALENDAR.events.concat(calendar.events);
  });
  sortEvents(ALL_CALENDAR);

  ALL_CALENDAR.loading = false;
  ALL_CALENDAR.errored = true;
  app.calendars.forEach(function(calendar) {
    if (calendar.loading) {
      ALL_CALENDAR.loading = true;
    }
    if (!calendar.errored) {
      ALL_CALENDAR.errored = false;
    }
  });

  if (ALL_CALENDAR === app.selectedCalendar) {
    app.notifyPath('selectedCalendar.events', ALL_CALENDAR.events);
    app.notifyPath('selectedCalendar.loading', ALL_CALENDAR.loading);
    app.notifyPath('selectedCalendar.errored', ALL_CALENDAR.errored);
  }
};

var signIn = function(mode) {
  return GAPIManager.authorize(mode)
    .then(function() {
      app.userInfo = LOADING_USER_INFO;
      app.$.userBar.removeEventListener('tap', app.showSigninPopup);
    })
    .catch(function(err) {
      if (err instanceof GAPIManager.AuthError && err.accessDenied) {
        signOut();
      }
      throw err;
    });
};

var signOut = function() {
  app.userInfo = SIGNED_OUT_USER_INFO;
  app.$.userBar.addEventListener('tap', app.showSigninPopup);
  updateListedCalendars();
};

var patchEvent = function(params) {
  return sendReAuthedRequest(loadedTickTockAPI
    .then(function(ticktock) {
      return ticktock.events.patch({
        calendarId: encodeURIComponent(params.calendarId),
        eventId: params.eventId,
        starred: params.starred,
        hidden: params.hidden
      });
    }));
};

var patchCalendar = function(params) {
  return sendReAuthedRequest(loadedTickTockAPI
    .then(function(ticktock) {
      return ticktock.calendars.patch({
        calendarId: encodeURIComponent(params.calendarId),
        hidden: params.hidden
      });
    }));
};

var loadAllData = function() {
  return Promise.all([
    loadProfile()
      .catch(handleHTTPError),
    loadCalendars()
      .then(loadEvents)
      .catch(handleHTTPError)
  ]);
};

var loadProfile = function() {
  return sendReAuthedRequest(loadedOauth2API
    .then(function(oauth2) {
      return oauth2.userinfo.v2.me.get({
        fields: 'name,picture'
      });
    }))
    .then(function(resp) {
      resp.loading = false;
      resp.signedOut = false;
      app.userInfo = resp;
    });
};

var loadCalendars = function() {
  LOADING_CALENDAR.calendarId = app.selectedCalendar.calendarId;
  app.selectedCalendar = LOADING_CALENDAR;
  return sendReAuthedRequest(loadedTickTockAPI
    .then(function(ticktock) {
      return ticktock.calendars.list({
        hidden: null
      });
    }))
    .then(function(resp) {
      var calendars = resp.items || [];
      calendars.forEach(function(calendar) {
        calendar.events = [];
        calendar.errored = false;
        calendar.nextPageToken = null;
      });
      app.calendars = calendars;
      app.selectCalendar();
      return calendars;
    });
};

var loadEvents = function(calendars) {
  var timeZone;
  try {
    timeZone =  Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (err) {
    timeZone = null;
  }

  app.$.eventList.openedIndex = 0;

  var promise = Promise.all(calendars.map(function(calendar) {
    calendar.events = [];
    calendar.errored = false;
    calendar.loading = true;
    if (calendar === app.selectedCalendar) {
      app.notifyPath('selectedCalendar.errored', false);
      app.notifyPath('selectedCalendar.loading', true);
    }

    return sendReAuthedRequest(loadedTickTockAPI
      .then(function(ticktock) {
        return ticktock.events.list({
          calendarId: encodeURIComponent(calendar.calendarId),
          hidden: null,
          maxResults: 10,
          timeZone: timeZone
        });
      }))
      .then(function(resp) {
        if (resp.items) {
          resp.items.forEach(function(calendarEvent) {
            calendarEvent.color = calendar.color;
            calendarEvent.calendarHidden = calendar.hidden;
          });
          calendar.events = resp.items;
          sortEvents(calendar);
        }
      })
      .catch(function(err) {
        calendar.errored = true;
        if (calendar === app.selectedCalendar) {
          app.notifyPath('selectedCalendar.errored', true);
        }
        throw err;
      })
      .catch(handleHTTPError)
      .then(function() {
        calendar.loading = false;
        if (calendar === app.selectedCalendar) {
          app.notifyPath('selectedCalendar.events', calendar.events);
          app.notifyPath('selectedCalendar.loading', false);
        }
      });
  }))
    .then(updateAllCalendarState);

  updateAllCalendarState();

  return promise;
};

//
// Utility Functions
//

var logError = function(err) {
  console.error(err);
  throw err;
};

var getCalendarById = function(calendarId) {
  if (calendarId === ALL_CALENDAR.calendarId) {
    return ALL_CALENDAR;
  } else {
    return app.calendars.find(function(calendar) {
      return calendar.calendarId === calendarId;
    });
  }
};

var getEventIndexById = function(calendar, eventId, calendarId) {
  return calendar.events.findIndex(function(calendarEvent) {
    return calendarEvent.eventId === eventId &&
           calendarEvent.calendarId === (calendarId || calendar.calendarId);
  });
};

var deleteEventById = function(calendarId, eventId) {
  var i;
  var calendar = getCalendarById(calendarId);
  if (calendar) {
    i = getEventIndexById(calendar, eventId);
    if (i >= 0) {
      var removed = calendar.events.splice(i, 1);
      if (calendar === app.selectedCalendar) {
        app.notifySplices('selectedCalendar.events', [{
          index: i,
          removed: removed,
          addedCount: 0,
          object: app.selectedCalendar.events,
          type: 'splice'
        }]);
      }
    }
  }
  i = getEventIndexById(ALL_CALENDAR, eventId, calendarId);
  if (i >= 0) {
    var removed = ALL_CALENDAR.events.splice(i, 1);
    if (calendar === app.selectedCalendar) {
      app.notifySplices('selectedCalendar.events', [{
        index: i,
        removed: removed,
        addedCount: 0,
        object: app.selectedCalendar.events,
        type: 'splice'
      }]);
    }
  }
};

var updateDurations = function(calendar) {
  // TODO: Optimize this.
  var now = Date.now();

  calendar.events.forEach(function(calendarEvent, i) {
    var timeToStart = 0;
    var timeToEnd = 0;
    if (calendarEvent.startDate) {
      var eventStart = Date.parse(calendarEvent.startDate);
      timeToStart = Math.floor((eventStart - now) / 1000);
    }

    if (timeToStart <= 0) {
      timeToStart = 0;
      delete calendarEvent.startDate;

      var eventEnd = Date.parse(calendarEvent.endDate);
      timeToEnd = Math.floor((eventEnd - now) / 1000);

      if (timeToEnd < 0) {
        deleteEventById(calendarEvent.calendarId, calendarEvent.eventId);
      }
    }

    calendarEvent.duration = timeToStart || timeToEnd;
    calendarEvent.durationFromStart = Boolean(timeToStart);
    if (calendar === app.selectedCalendar) {
      app.notifyPath(['selectedCalendar', 'events', i, 'duration'],
                     calendarEvent.duration);
      app.notifyPath(['selectedCalendar', 'events', i, 'durationFromStart'],
                     calendarEvent.durationFromStart);
    }
  });
};

var updateListedCalendars = function() {
  if (app.userInfo.signedOut) {
    app.listedCalendars = [];
    app.hasHiddenCalendars = false;
    return;
  }

  if (app.selectedCalendar.hidden) {
    app.showHiddenCalendars = true;
  }

  var hasHidden = false;
  var listed = [];
  app.calendars.forEach(function(calendar) {
    if (!hasHidden && calendar.hidden) {
      hasHidden = true;
    }
    if (!calendar.hidden || app.showHiddenCalendars) {
      listed.push(calendar);
    }
  });
  app.listedCalendars = listed;
  app.hasHiddenCalendars = hasHidden;
};

var singleSortEvent, sortEvents;
(function() {
  /**
   * Move an event to its proper place in its calendar and the ALL_CALENDAR.
   *
   * Uses the insertion sort algorithm, and notifies splices.
   *
   * @param {String} eventId - The event's ID.
   * @param {String} calendarId - The event's calendar's ID.
   */
  singleSortEvent = function(eventId, calendarId) {
    var calendar = getCalendarById(calendarId);
    if (calendar) {
      singleSortByCalendar(calendar, eventId);
      if (calendar !== ALL_CALENDAR) {
        singleSortByCalendar(ALL_CALENDAR, eventId);
      }
    }
  };

  /**
   * Sort all of a calendar's events.
   *
   * Does not notify.
   *
   * @param {Object} calendar - The calendar object whose events should be
   *   sorted.
   */
  sortEvents = function(calendar) {
    calendar.events = calendar.events.sort(compareEvents);
  };

  var singleSortByCalendar = function(calendar, eventId) {
    /************************
    Algorithm Summary Drawing
    *************************
                  *-3
    [1, 6, 9, 15, 19, 22]
        ^
    (1, 3)? yes
       (6, 3)? no

    [1, 6, 9, 15, 3, 19, 22]
            - to -
    [1, 3, 6, 9, 15, 19, 22]
    -----------------------------
        *-16
    [1, 9, 15, 17, 19, 22]
               ^
    (1, 16)? yes
       (9, 16)? yes
          (15, 16)? yes
              (17, 16)? no

    [1, 16, 9, 15, 17, 19, 22]
             - to -
    [1, 9, 15, 16, 17, 19, 22]
    ************************/
    var misplacedIndex = calendar.events.findIndex(function(calendarEvent) {
      return calendarEvent.eventId === eventId;
    });
    var misplacedEvent = calendar.events.splice(misplacedIndex, 1)[0];

    var targetIndex = calendar.events.findIndex(function(calendarEvent) {
      return compareEvents(calendarEvent, misplacedEvent) > 0;
    });
    calendar.events.splice(targetIndex, 0, misplacedEvent);

    if (calendar === app.selectedCalendar) {
      app.notifySplices('selectedCalendar.events', [{
        index: misplacedIndex,
        removed: [misplacedEvent],
        addedCount: 0,
        object: app.selectedCalendar.events,
        type: 'splice'
      }, {
        index: targetIndex,
        removed: [],
        addedCount: 1,
        object: app.selectedCalendar.events,
        type: 'splice'
      }]);
    }
  };

  var compareBools = function(a, b) {
    // True is first.
    return b - a;
  };

  var compareStrings = function(a, b) {
    // Sort alphabetically, any language, case insensitive.
    return a.localeCompare(b);
  };

  var compareEvents = function(a, b) {
    // Sort order: starred, duration, alphabetical, id.
    return compareBools(a.starred, b.starred) ||
           compareStrings(a.startDate || a.endDate,
                          b.startDate || b.endDate) ||
           compareStrings(a.name, b.name) ||
           compareStrings(a.eventId, b.eventId) ||
           0;
  };
})();

})(app);
