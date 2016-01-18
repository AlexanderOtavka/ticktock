/*
Copyright (c) 2015 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/

(function(document) {
  'use strict';

  // Grab a reference to our auto-binding template
  // and give it some initial binding values
  // Learn more about auto-binding templates at http://goo.gl/Dx1u2g
  var app = document.querySelector('#app');

  var CLIENT_ID = '208366307202-00824keo9p663g1uhkd8misc52e1c5pa.apps.googleusercontent.com';
  var SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/plus.me',
    'https://www.googleapis.com/auth/calendar.readonly'
  ];
  app.apiRoot = '//' + window.location.host + '/_ah/api';

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

  app.calendars = [];
  app.hiddenCalendars = [];
  app.unhiddenCalendars = [];
  app.listedEvents = [];
  app.selectedCalendar = '';
  app.dataLoaded = false;
  app.calculatingListedCalendars = false;

  app.showHiddenCalendars = false;
  app.showHiddenEvents = false;

  app.noEventAnimations = false;
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

  app.signedOutClass = function(signedOut) {
    return signedOut ? 'signed-out' : '';
  };

  // TODO: replace for loops with forEach
  // but profile both first, and choose the fastest

  var getCalendarIndexById = function(calendarId) {
    for (var i = 0; i < app.calendars.length; i++) {
      if (app.calendars[i].calendarId === calendarId) {
        return i;
      }
    }
    return null;
  };

  var getCalendarById = function(calendarId) {
    return app.calendars[getCalendarIndexById(calendarId)];
  };

  app.getViewName = function(selectedCalendar) {
    var ALL_CALENDARS = 'All Calendars';

    if (!selectedCalendar) {
      return ALL_CALENDARS;
    } else {
      var calendar = getCalendarById(selectedCalendar);
      return calendar ? calendar.name : ALL_CALENDARS;
    }
  };

  app.toggleShowHiddenEvents = function() {
    app.showHiddenEvents = !app.showHiddenEvents;
    app.updateListedEvents(false);
  };

  app.hiddenEventsToggleText = function(showHiddenEvents) {
    return showHiddenEvents ? 'Hide Hidden Events' : 'Show Hidden Events';
  };

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
    events.forEach(function(e) {
      if (keep(e)) {
        pruned.push(e);
      }
    });
    return pruned;
  };

  var openOnlyOne = function(events, openTopEvent) {
    if (!events.length) {
      return;
    }
    var foundOpened = false;
    events.forEach(function(e) {
      if (e.opened) {
        if (foundOpened) {
          e.opened = false;
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
    app.calculatingListedCalendars = true;
    var events = [];
    if (!app.selectedCalendar) {
      var calendars = app.unhiddenCalendars;
      for (var i = 0; i < calendars.length; i++) {
        events = events.concat(calendars[i].events);
      }
    } else {
      var calendar = getCalendarById(app.selectedCalendar);
      events = calendar ? calendar.events.slice() : [];
    }
    if (!app.showHiddenEvents) {
      events = prunedEvents(events, function(event) {
        return !event.hidden;
      });
    }
    events = sortedEvents(events);
    openOnlyOne(events, openTopEvent);
    runWithoutAnimation(function() {
      app.listedEvents = events;
      app.calculatingListedCalendars = false;
    });
  };

  app.calendarEmpty = function(calendarId, listedEvents, dataLoaded, calculating) {
    return dataLoaded && !calculating && !Boolean(listedEvents.length) &&
           !app.calendarErrored(calendarId, dataLoaded);
  };

  var deleteEvent = function(eventId, calendarId) {
    var calendar = getCalendarById(calendarId);
    if (calendar) {
      for (var i = 0; i < calendar.events.length; i++) {
        if (calendar.events[i].eventId === eventId) {
          return calendar.events.splice(i, 1);
        }
      }
    }
  };

  app.displayInstalledToast = function() {
    // Check to make sure caching is actually enabled—it won't be in the dev environment.
    if (!document.querySelector('platinum-sw-cache').disabled) {
      document.querySelector('#caching-complete').show();
    }
  };

  var updateDurations = function() {
    var now = Date.now();
    var needsUpdate = false;
    for (var i = 0; i < app.listedEvents.length; i++) {
      var timeToStart = 0;
      var timeToEnd = 0;
      if (app.listedEvents[i].startDate) {
        var eventStart = Date.parse(app.listedEvents[i].startDate);
        timeToStart = Math.floor((eventStart - now) / 1000);
      }

      if (timeToStart < 0) {
        timeToStart = 0;
        delete app.listedEvents[i].startDate;
      }

      if (!timeToStart) {
        var eventEnd = Date.parse(app.listedEvents[i].endDate);
        timeToEnd = Math.floor((eventEnd - now) / 1000);

        if (timeToEnd < 0) {
          if (app.listedEvents[i].opened) {
            app.set(['listedEvents', i + 1, 'opened'], true);
          }
          deleteEvent(app.listedEvents[i].eventId,
                      app.listedEvents[i].calendarId);
          needsUpdate = true;
        }
      }

      app.set(['listedEvents', i, 'duration'], timeToStart || timeToEnd);
    }
    if (needsUpdate) {
      app.updateListedEvents(false);
    }
  };

  // Listen for template bound event to know when bindings
  // have resolved and content has been stamped to the page
  app.addEventListener('dom-change', function() {
    // Calculate durations
    setInterval(updateDurations, 1000);
  });

  app.eventOpenedToggled = function(event) {
    if (event.detail.value) {
      for (var i = 0; i < app.listedEvents.length; i++) {
        if (app.listedEvents[i].opened &&
            app.listedEvents[i].eventId !== event.srcElement.eventId) {
          app.set(['listedEvents', i, 'opened'], false);
        }
      }
    }
  };

  app.eventStarredToggled = function() {
    // TODO: send api query
    app.updateListedEvents(false);
  };

  app.eventHiddenToggled = function() {
    // TODO: send api query
    app.updateListedEvents(false);
  };

  app.closeAllEvents = function() {
    for (var i = 0; i < app.listedEvents.length; i++) {
      if (app.listedEvents[i].opened) {
        app.set(['listedEvents', i, 'opened'], false);
        return;
      }
    }
  };

  // See https://github.com/Polymer/polymer/issues/1381
  window.addEventListener('WebComponentsReady', function() {
    // imports are loaded and elements have been registered
  });

  // Close drawer after menu item is selected if drawerPanel is narrow
  app.onDataRouteClick = function() {
    var drawerPanel = document.querySelector('#paperDrawerPanel');
    if (drawerPanel.narrow) {
      drawerPanel.closeDrawer();
    }
  };

  app.toggleShowHiddenCalendars = function() {
    setTimeout(function() {
      app.showHiddenCalendars = !app.showHiddenCalendars;
    }, 20);
  };

  app.updateCalendars = function(event) {
    var hidden = [];
    var unhidden = [];
    for (var i = 0; i < app.calendars.length; i++) {
      if (app.calendars[i].hidden) {
        hidden.push(app.calendars[i]);
        if (app.calendars[i].calendarId === app.selectedCalendar) {
          app.showHiddenCalendars = true;
        }
      } else {
        unhidden.push(app.calendars[i]);
      }
    }
    app.hiddenCalendars = hidden;
    app.unhiddenCalendars = unhidden;
    app.updateListedEvents(!event);
  };

  app.arrayEmpty = function(array) {
    return !Boolean(array.length);
    // return false;
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

  // Scroll page to top and expand header
  app.scrollPageToTop = function() {
    document.getElementById('mainContainer').scrollTop = 0;
  };

  app.onAPILoaded = function() {
    if (app.$.ticktockApi.api && app.$.oauth2Api.api) {
      signin(true);
    }
  };

  app.showSigninPopup = function() {
    signin(false);
  };

  app.calendarErrored = function(calendarId, dataLoaded) {
    if (!dataLoaded) {
      return false;
    } else {
      return Boolean(calendarId) &&
             (getCalendarById(calendarId) || {error: true}).error;
    }
  };

  app.spinnerHidden = function(signedOut, calendarId, dataLoaded, calculating) {
    if (calculating) {
      return false;
    } else if (signedOut) {
      return true;
    } else if (!dataLoaded) {
      return false;
    } else if (!calendarId) {
      var nextPageToken = false;
      var error = true;
      app.calendars.forEach(function(c) {
        if (!c.error) {
          error = false;
        }
        if (c.nextPageToken) {
          nextPageToken = true;
        }
      });
      return error || !nextPageToken;
    } else {
      var calendar = getCalendarById(calendarId);
      if ((calendar || {error: true}).error) {
        return true;
      } else {
        return !Boolean(calendar.nextPageToken);
      }
    }
  };

  var raiseError = function(object) {
    app.$.error.show();
    if (object) {
      console.error(object);
    }
  };

  var signin = function(mode) {
    app.$.oauth2Api.auth.authorize({
        client_id: CLIENT_ID, // jshint ignore:line
        scope: SCOPES,
        immediate: mode
      }, function() {
        getProfileInfo();
        loadCalendars();
      });
    app.userInfo = LOADING_USER_INFO;
    app.$.userBar.removeEventListener('tap', app.showSigninPopup);
  };

  var getProfileInfo = function() {
    app.$.oauth2Api.api.userinfo.v2.me.get({
        fields: 'name,picture'
      }).execute(function(resp) {
        if (resp.code === 401) {
          app.userInfo = SIGNED_OUT_USER_INFO;
          app.$.userBar.addEventListener('tap', app.showSigninPopup);
        } else if (resp.code) {
          raiseError(resp);
        } else {
          resp.loading = false;
          resp.signedOut = false;
          app.userInfo = resp;
        }
      });
  };

  var loadCalendars = function() {
    app.dataLoaded = false;
    app.$.ticktockApi.api.calendars.list({
        hidden: null
      }).execute(function(resp) {
        if (resp.code) {
          raiseError(resp);
        } else {
          var calendars = resp.items || [];
          calendars.forEach(function(c) {
            c.events = [];
            c.error = false;
          });
          app.calendars = calendars;
          app.updateCalendars();
          loadAllEvents();
        }
      });
  };

  var loadAllEvents = function() {
    var calendarsToLoad = app.calendars.length;
    var addEvents = function(calendar) {
      return function(resp) {
        if (!resp || resp.code) {
          calendar.error = true;
          raiseError(resp);
        } else {
          if (resp.items) {
            resp.items.forEach(function(e) {
              e.color = calendar.color;
              e.opened = false;
            });
            resp.items[0].opened = true;
            calendar.events = resp.items;
          }
        }
        if (!--calendarsToLoad) {
          app.dataLoaded = true;
          app.updateListedEvents(true);
          updateDurations();
        }
      };
    };

    app.calendars.forEach(function(c) {
      app.$.ticktockApi.api.events.list({
          calendarId: c.calendarId,
          hidden: false,
          maxResults: 10,
          timeZone: 'UTC'
        }).execute(addEvents(c));
    });
  };

})(document);
