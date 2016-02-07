/*
Copyright (c) 2015 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/

/* globals GAPIManager, Promise */

(function(app) {
'use strict';

// Imports are loaded and elements have been registered.
window.addEventListener('WebComponentsReady', function() {
  setInterval(updateDurations, 1000);

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
app.listedEvents = [];
app.hasHiddenCalendars = false;
app.calculatingListedEvents = false;

// Settings.
app.showHiddenCalendars = false;
app.showHiddenEvents = false;

// Other global state properties.
app.noEventAnimations = false;

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
                                nextPageToken, calculating, events) {
    if (signedOut) {
      return calendarStatus.Status.SIGNED_OUT;
    }
    if (calendarErrored) {
      return calendarStatus.Status.ERRORED;
    }
    if (eventsLoading || nextPageToken || calculating) {
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
                                  nextPageToken, calculating, events) {
    return calendarStatus(signedOut, calendarErrored, eventsLoading,
                          nextPageToken, calculating, events) ===
           calendarStatus.Status.EMPTY;
  };

  app.getCalendarErrored = function(signedOut, calendarErrored) {
    return calendarStatus(signedOut, calendarErrored) ===
           calendarStatus.Status.ERRORED;
  };

  app.getCalendarLoading = function(signedOut, calendarErrored, eventsLoading,
                                    nextPageToken, calculating) {
    return calendarStatus(signedOut, calendarErrored, eventsLoading,
                          nextPageToken, calculating) ===
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
 * Close drawer after menu item is selected if drawerPanel is narrow
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
  updateListedCalendars(true);
};

app.closeAllEvents = function() {
  var i = app.listedEvents.findIndex(function(listedEvent) {
    return listedEvent.opened;
  });
  app.set(['listedEvents', i, 'opened'], false);
};

app.toggleShowHiddenEvents = function() {
  app.showHiddenEvents = !app.showHiddenEvents;
  updateListedEvents(false);
};

app.toggleShowHiddenCalendars = function() {
  setTimeout(function() {
    app.showHiddenCalendars = !app.showHiddenCalendars;
    updateListedCalendars(false);
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

app.onEventOpenedToggled = function(event) {
  if (event.detail.value) {
    var i = app.listedEvents.findIndex(function(listedEvent) {
      return listedEvent.opened &&
             listedEvent.eventId !== event.target.eventId;
    });
    app.set(['listedEvents', i, 'opened'], false);
  }
};

app.onEventStarredToggled = function(event) {
  // TODO: move this logic to the element
  console.log(event);
  var starred = event.detail.value;
  var hidden = null;
  if (starred && event.target.eventHidden) {
    hidden = false;
    event.target.set('eventHidden', false);
  }
  updateListedEvents(false);
  patchEvent({
    calendarId: event.target.calendarId,
    eventId: event.target.eventId,
    hidden: hidden,
    starred: starred
  })
    .catch(handleHTTPError)
    .catch(logError);
};

app.onEventHiddenToggled = function(event) {
  console.log(event);
  var hidden = event.detail.value;
  var starred = null;
  if (hidden && event.target.starred) {
    starred = false;
    event.target.set('starred', false);
  }
  updateListedEvents(false);
  patchEvent({
    calendarId: event.target.calendarId,
    eventId: event.target.eventId,
    hidden: hidden,
    starred: starred
  })
    .catch(handleHTTPError)
    .catch(logError);
};

app.onCalendarHiddenToggled = function(event) {
  var calendarIndex = app.calendars.findIndex(function(calendar) {
    return calendar.calendarId === event.target.calendarId;
  });
  if (calendarIndex !== -1) {
    var calendar = app.calendars[calendarIndex];
    calendar.events.forEach(function(calendarEvent, i) {
      app.set(['calendars', calendarIndex, 'events', i, 'calendarHidden'],
              calendar.hidden);
    });
  }
  updateListedCalendars(false);
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
  ALL_CALENDAR.loading = false;
  ALL_CALENDAR.errored = true;
  app.listedCalendars.forEach(function(calendar) {
    if (calendar.loading) {
      ALL_CALENDAR.loading = true;
    }
    if (!calendar.errored) {
      ALL_CALENDAR.errored = false;
    }
  });
  if (app.selectedCalendar === ALL_CALENDAR) {
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
            calendarEvent.opened = false;
            calendarEvent.calendarHidden = calendar.hidden;
          });
          resp.items[0].opened = true;
          calendar.events = resp.items;
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
          app.notifyPath('selectedCalendar.loading', false);
          updateListedEvents(true);
        }
      });
  }))
    .then(updateAllCalendarState)
    .then(function() {
      if (app.selectedCalendar === ALL_CALENDAR) {
        updateListedEvents(true);
      }
    });

  updateAllCalendarState();
  updateListedEvents(true);

  return promise;
};

//
// Utility Functions
//

var logError = function(err) {
  console.error(err);
  throw err;
};

var runWithoutAnimation = function(callback) {
  // TODO: de-hackify this
  app.noEventAnimations = true;
  setTimeout(function() {
    callback();
    setTimeout(function() {
      app.noEventAnimations = false;
    }, 5);
  }, 5);
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

var deleteEventById = function(eventId, calendarId) {
  var calendar = getCalendarById(calendarId);
  if (calendar) {
    var i = calendar.events.findIndex(function(calendarEvent) {
      return calendarEvent.eventId === eventId;
    });
    if (i >= 0) {
      return calendar.events.splice(i, 1);
    }
  }
};

var updateDurations = function() {
  // TODO: Optimize this.
  var now = Date.now();
  var needsUpdate = false;

  app.listedEvents.forEach(function(listedEvent, i) {
    var timeToStart = 0;
    var timeToEnd = 0;
    if (listedEvent.startDate) {
      var eventStart = Date.parse(listedEvent.startDate);
      timeToStart = Math.floor((eventStart - now) / 1000);
    }

    if (timeToStart <= 0) {
      timeToStart = 0;
      delete listedEvent.startDate;

      var eventEnd = Date.parse(listedEvent.endDate);
      timeToEnd = Math.floor((eventEnd - now) / 1000);

      if (timeToEnd < 0) {
        if (listedEvent.opened) {
          app.set(['listedEvents', i + 1, 'opened'], true);
        }
        deleteEventById(listedEvent.eventId,
                    listedEvent.calendarId);
        needsUpdate = true;
      }
    }

    app.set(['listedEvents', i, 'duration'], timeToStart || timeToEnd);
    app.set(['listedEvents', i, 'durationFromStart'], Boolean(timeToStart));
  });
  if (needsUpdate) {
    updateListedEvents(false);
  }
};

var updateListedCalendars = function(forceOpenTopEvent) {
  if (app.userInfo.signedOut) {
    app.listedCalendars = [];
    app.hasHiddenCalendars = false;
    updateListedEvents(false);
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

  updateListedEvents(forceOpenTopEvent);
  if (forceOpenTopEvent) {
    app.set('listedEvents.0.opened', true);
  }
};

var updateListedEvents;
(function() {
  var compareBools = function(a, b) {
    // True is first
    return b - a;
  };

  var compareStrings = function(a, b) {
    // Sort alphabetically
    return a.localeCompare(b);
  };

  var sortedEvents = function(events) {
    // Sort order: starred, duration, alphabetical, id
    return events.sort(function(a, b) {
      if (a.starred !== b.starred) {
        return compareBools(a.starred, b.starred);
      }
      if (a.startDate !== b.startDate || a.endDate !== b.endDate) {
        return compareStrings(a.startDate || a.endDate,
                              b.startDate || b.endDate);
      }
      if (a.name !== b.name) {
        return compareStrings(a.name, b.name);
      }
      if (a.eventId !== b.eventId) {
        return compareStrings(a.eventId, b.eventId);
      }
      return 0;
    });
  };

  var prunedEvents = function(events, keep) {
    var pruned = [];
    events.forEach(function(calendarEvent) {
      if (keep(calendarEvent)) {
        pruned.push(calendarEvent);
      }
    });
    return pruned;
  };

  var openOnlyOne = function(events, openTopEvent) {
    if (!events.length) {
      return;
    }
    var foundOpened = false;
    events.forEach(function(calendarEvent) {
      if (calendarEvent.opened) {
        if (foundOpened) {
          calendarEvent.opened = false;
        } else {
          foundOpened = true;
        }
      }
    });
    if (openTopEvent && !foundOpened) {
      events[0].opened = true;
    }
  };

  updateListedEvents = function(openTopEvent) {
    app.calculatingListedEvents = true;
    var events = [];
    if (app.selectedCalendar === ALL_CALENDAR) {
      var calendars = app.listedCalendars;
      calendars.forEach(function(calendar) {
        events = events.concat(calendar.events);
      });
    } else {
      events = app.selectedCalendar.events.slice();
    }
    if (!app.showHiddenEvents) {
      events = prunedEvents(events, function(unprunedEvent) {
        return !unprunedEvent.hidden;
      });
    }
    events = sortedEvents(events);
    openOnlyOne(events, openTopEvent);
    runWithoutAnimation(function() {
      app.listedEvents = events;
      updateDurations();
      app.calculatingListedEvents = false;
    });
  };
})();

})(app);
