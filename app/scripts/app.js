/*
Copyright (c) 2015 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/

/* globals GAPIManager, Promise */

(function(document) {
'use strict';

// Grab a reference to our auto-binding template
// and give it some initial binding values
// Learn more about auto-binding templates at http://goo.gl/Dx1u2g
var app = document.querySelector('#app');

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

var ALL_CALENDAR = {
  name: 'All Calendars',
  calendarId: '*',
  color: '#e91e63',
  error: false,
  hidden: false,
  events: [],
  nextPageToken: null
};
var LOADING_CALENDAR = {
  name: 'TickTock',
  calendarId: ALL_CALENDAR.calendarId,
  color: '#e91e63',
  error: false,
  hidden: false,
  events: [],
  nextPageToken: null
};
var ERROR_CALENDAR = {
  name: 'TickTock',
  calendarId: '',
  color: '#e91e63',
  error: true,
  hidden: false,
  events: [],
  nextPageToken: null
};
app.calendars = [];
app.hiddenCalendars = [];
app.unhiddenCalendars = [];
app.listedEvents = [];
app.selectedCalendar = LOADING_CALENDAR;
// TODO: move events loaded to each calendar.
app.eventsLoaded = false;
app.calculatingListedEvents = false;

app.showHiddenCalendars = false;
app.showHiddenEvents = false;

app.noEventAnimations = false;

// See https://github.com/Polymer/polymer/issues/1381
window.addEventListener('WebComponentsReady', function() {
  // imports are loaded and elements have been registered
});

// Listen for template bound event to know when bindings
// have resolved and content has been stamped to the page
app.addEventListener('dom-change', function() {
  // Calculate durations
  setInterval(updateDurations, 1000);

  signIn(true).then(loadAllData);
});

// Utility functions

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

var deleteEvent = function(eventId, calendarId) {
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
  var now = Date.now();
  var needsUpdate = false;

  app.listedEvents.forEach(function(listedEvent, i) {
    var timeToStart = 0;
    var timeToEnd = 0;
    if (listedEvent.startDate) {
      var eventStart = Date.parse(listedEvent.startDate);
      timeToStart = Math.floor((eventStart - now) / 1000);
    }

    if (timeToStart < 0) {
      timeToStart = 0;
      delete listedEvent.startDate;
    }

    if (!timeToStart) {
      var eventEnd = Date.parse(listedEvent.endDate);
      timeToEnd = Math.floor((eventEnd - now) / 1000);

      if (timeToEnd < 0) {
        if (listedEvent.opened) {
          app.set(['listedEvents', i + 1, 'opened'], true);
        }
        deleteEvent(listedEvent.eventId,
                    listedEvent.calendarId);
        needsUpdate = true;
      }
    }

    app.set(['listedEvents', i, 'duration'], timeToStart || timeToEnd);
    app.set(['listedEvents', i, 'durationFromStart'], Boolean(timeToStart));
  });
  if (needsUpdate) {
    app.updateListedEvents(false);
  }
};

var logError = function(err) {
  console.error(err);
  throw err;
};

var eatError = function() {
  return null;
};

// Getters

app.signedOutClass = function(signedOut) {
  return signedOut ? 'signed-out' : '';
};

app.hiddenEventsToggleText = function(showHiddenEvents) {
  return showHiddenEvents ? 'Hide Hidden Events' : 'Show Hidden Events';
};

app.arrayEmpty = function(array) {
  return !Boolean(array.length);
};

app.hiddenCalendarToggleText = function(showHiddenCalendars) {
  return showHiddenCalendars ? 'Hide Hidden Calendars' :
                               'Show Hidden Calendars';
};

app.urlEncode = function(string) {
  return encodeURIComponent(string);
};

app.urlDecode = function(string) {
  return decodeURIComponent(string);
};

(function() {
  var calendarStatus = function(signedOut, calendarErrored, eventsLoaded,
                                nextPageToken, calculating, events) {
    if (signedOut) {
      return calendarStatus.Status.SIGNED_OUT;
    }
    if (calendarErrored) {
      return calendarStatus.Status.ERRORED;
    }
    if (!eventsLoaded || nextPageToken || calculating) {
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

  app.calendarEmpty = function(signedOut, calendarErrored, eventsLoaded,
                               nextPageToken, calculating, events) {
    return calendarStatus(signedOut, calendarErrored, eventsLoaded,
                          nextPageToken, calculating, events) ===
           calendarStatus.Status.EMPTY;
  };

  app.calendarErrored = function(signedOut, calendarErrored) {
    return calendarStatus(signedOut, calendarErrored) ===
           calendarStatus.Status.ERRORED;
  };

  app.calendarLoading = function(signedOut, calendarErrored, eventsLoaded,
                                 nextPageToken, calculating) {
    return calendarStatus(signedOut, calendarErrored, eventsLoaded,
                          nextPageToken, calculating) ===
           calendarStatus.Status.LOADING;
  };
})();

// Actions

/**
 * Select calendar, or que up calendar to be selected.
 */
app.selectCalendar = function(calendarId) {
  if (calendarId === undefined) {
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
};

app.toggleShowHiddenEvents = function() {
  app.showHiddenEvents = !app.showHiddenEvents;
  app.updateListedEvents(false);
};

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

  app.updateListedEvents = function(openTopEvent) {
    app.calculatingListedEvents = true;
    var events = [];
    if (app.selectedCalendar === ALL_CALENDAR) {
      var calendars = app.unhiddenCalendars;
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

app.displayInstalledToast = function() {
  // Check to make sure caching is actually enabled—it won't be in the dev environment.
  // if (!document.querySelector('platinum-sw-cache').disabled) {
  //   app.$.cachingComplete.show();
  // }
};

app.closeAllEvents = function() {
  var i = app.listedEvents.findIndex(function(listedEvent) {
    return listedEvent.opened;
  });
  app.set(['listedEvents', i, 'opened'], false);
};

app.toggleShowHiddenCalendars = function() {
  setTimeout(function() {
    app.showHiddenCalendars = !app.showHiddenCalendars;
  }, 20);
};

app.updateCalendars = function(openTopEvent) {
  var hidden = [];
  var unhidden = [];
  app.calendars.forEach(function(calendar) {
    calendar.events.forEach(function(calendarEvent) {
      calendarEvent.calendarHidden = calendar.hidden;
    });
    if (calendar.hidden) {
      hidden.push(calendar);
      if (calendar === app.selectedCalendar) {
        app.showHiddenCalendars = true;
      }
    } else {
      unhidden.push(calendar);
    }
  });
  app.hiddenCalendars = hidden;
  app.unhiddenCalendars = unhidden;
  app.updateListedEvents(openTopEvent);
};

// Scroll page to top and expand header
app.scrollPageToTop = function() {
  document.getElementById('mainContainer').scrollTop = 0;
};

app.showSigninPopup = function() {
  signIn(false).then(loadAllData);
};

app.refreshThisCalendar = function() {
  if (app.selectedCalendar !== LOADING_CALENDAR &&
      app.selectedCalendar !== ERROR_CALENDAR &&
      app.eventsLoaded && !app.userInfo.signedOut) {
    var calendars;
    if (app.selectedCalendar === ALL_CALENDAR) {
      calendars = app.calendars;
    } else {
      calendars = [app.selectedCalendar];
    }
    app.eventsLoaded = false;
    loadEvents(calendars)
      .catch(logError)
      .catch(eatError)
      .then(function() {
        app.eventsLoaded = true;
        app.updateListedEvents(true);
      });
    app.updateListedEvents(true);
  }
};

// Event handlers

app.eventOpenedToggled = function(event) {
  if (event.detail.value) {
    var i = app.listedEvents.findIndex(function(listedEvent) {
      return listedEvent.opened &&
             listedEvent.eventId !== event.target.eventId;
    });
    app.set(['listedEvents', i, 'opened'], false);
  }
};

app.eventStarredToggled = function(event) {
  // TODO: move this logic to the element
  console.log(event);
  var starred = event.detail.value;
  var hidden = null;
  if (starred && event.target.eventHidden) {
    hidden = false;
    event.target.set('eventHidden', false);
  }
  app.updateListedEvents(false);
  patchEvent({
    calendarId: event.target.calendarId,
    eventId: event.target.eventId,
    hidden: hidden,
    starred: starred
  })
    .catch(handleHTTPError)
    .catch(logError);
};

app.eventHiddenToggled = function(event) {
  console.log(event);
  var hidden = event.detail.value;
  var starred = null;
  if (hidden && event.target.starred) {
    starred = false;
    event.target.set('starred', false);
  }
  app.updateListedEvents(false);
  patchEvent({
    calendarId: event.target.calendarId,
    eventId: event.target.eventId,
    hidden: hidden,
    starred: starred
  })
    .catch(handleHTTPError)
    .catch(logError);
};

app.calendarHiddenToggled = function(event) {
  app.updateCalendars(false);
  patchCalendar({
    calendarId: event.target.calendarId,
    hidden: event.detail.value
  })
    .catch(handleHTTPError)
    .catch(logError);
};

// Close drawer after menu item is selected if drawerPanel is narrow
app.onDataRouteClick = function() {
  var drawerPanel = document.querySelector('#paperDrawerPanel');
  if (drawerPanel.narrow) {
    drawerPanel.closeDrawer();
  }
};

// Network

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

var signIn = function(mode) {
  app.userInfo = LOADING_USER_INFO;
  app.$.userBar.removeEventListener('tap', app.showSigninPopup);
  return GAPIManager.authorize(mode)
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
  app.eventsLoaded = false;
  ALL_CALENDAR.error = false;
  if (app.selectedCalendar === ALL_CALENDAR) {
    app.notifyPath('selectedCalendar.error', false);
  }

  return Promise.all([
    loadProfile()
      .catch(handleHTTPError),
    loadCalendars()
      .then(loadEvents)
      .catch(handleHTTPError)
      .catch(function(err) {
        if (err instanceof AllCalendarsError) {
          ALL_CALENDAR.error = true;
          if (app.selectedCalendar === ALL_CALENDAR) {
            app.notifyPath('selectedCalendar.error', false);
          }
        } else {
          throw err;
        }
      })
      .catch(logError)
      .catch(eatError)
      .then(function() {
        app.eventsLoaded = true;
        app.updateListedEvents(true);
      })
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
        calendar.error = false;
        calendar.nextPageToken = null;
      });
      app.calendars = calendars;
      app.selectCalendar();
      app.updateCalendars(false);
      return calendars;
    })
    .catch(logError);
};

var loadEvents = function(calendars) {
  var timeZone;
  try {
    timeZone =  Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (err) {
    timeZone = null;
  }

  var allCalendarsErrored = true;

  return Promise.all(calendars.map(function(calendar) {
    calendar.events = [];
    calendar.error = false;
    if (calendar === app.selectedCalendar) {
      app.notifyPath('selectedCalendar.error', false);
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
        allCalendarsErrored = false;
      })
      .catch(function(err) {
        calendar.error = true;
        if (calendar === app.selectedCalendar) {
          app.notifyPath('selectedCalendar.error', true);
        }
        throw err;
      })
      .catch(handleHTTPError);
  }))
    .then(function() {
      if (allCalendarsErrored) {
        throw new AllCalendarsError();
      }
    });
};

var AllCalendarsError = function() {
  this.message = 'All calendars failed to load.';
};
AllCalendarsError.prototype = Object.create(Error);
AllCalendarsError.prototype.constructor = AllCalendarsError;

})(document);
