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
  app.calendarsLoaded = false;
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
    return app.calendars.find(function(calendar) {
      return calendar.calendarId === calendarId;
    });
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

  var raiseError = function(object) {
    app.$.error.show();
    if (object) {
      console.error(object);
    }
  };

  var raiseNetworkError = function(object) {
    app.$.networkError.show();
    if (object) {
      console.error(object);
    }
  };

  // Getters

  app.signedOutClass = function(signedOut) {
    return signedOut ? 'signed-out' : '';
  };

  app.getViewName = function(selectedCalendar, calendarsLoaded) {
    var ALL_CALENDARS = 'All Calendars';

    if (!selectedCalendar) {
      return ALL_CALENDARS;
    } else if (!calendarsLoaded) {
      return 'TickTock';
    } else {
      var calendar = getCalendarById(selectedCalendar);
      return calendar ? calendar.name : ALL_CALENDARS;
    }
  };

  app.hiddenEventsToggleText = function(showHiddenEvents) {
    return showHiddenEvents ? 'Hide Hidden Events' : 'Show Hidden Events';
  };

  app.calendarEmpty = function(calendarId, listedEvents, eventsLoaded, calculating) {
    return eventsLoaded && !calculating && !Boolean(listedEvents.length) &&
           !app.calendarErrored(calendarId, eventsLoaded);
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

  app.calendarErrored = function(calendarId, eventsLoaded) {
    if (!eventsLoaded) {
      return false;
    } else {
      return Boolean(calendarId) &&
             (getCalendarById(calendarId) || {error: true}).error;
    }
  };

  app.spinnerHidden = function(signedOut, calendarId, eventsLoaded, calculating) {
    if (calculating) {
      return false;
    } else if (signedOut) {
      return true;
    } else if (!eventsLoaded) {
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

  // Actions

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
      if (!app.selectedCalendar) {
        var calendars = app.unhiddenCalendars;
        calendars.forEach(function(calendar) {
          events = events.concat(calendar.events);
        });
      } else {
        var calendar = getCalendarById(app.selectedCalendar);
        events = calendar ? calendar.events.slice() : [];
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
    //   document.querySelector('#caching-complete').show();
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
        if (calendar.calendarId === app.selectedCalendar) {
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
    signin(false);
  };

  app.refreshThisCalendar = function() {
    if (!app.calendarsLoaded || !app.eventsLoaded || app.userInfo.signedOut) {
      return;
    }
    var calendars;
    if (app.selectedCalendar) {
      var c = getCalendarById(app.selectedCalendar);
      if (c) {
        calendars = [c];
      } else {
        return;
      }
    } else {
      calendars = app.calendars;
    }
    loadEvents(calendars, true);
    app.updateListedEvents(false);
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
    pushEventState(event.target.eventId, event.target.calendarId, hidden, starred, true);
  };

  app.eventHiddenToggled = function(event) {
    console.log(event);
    var hidden = event.detail.value;
    var starred = null;
    if (hidden && event.target.starred) {
      starred = false;
      event.target.set('starred', false);
    }
    pushEventState(event.target.eventId, event.target.calendarId, hidden, starred, true);
  };

  app.calendarHiddenToggled = function(event) {
    pushCalendarState(event.target.calendarId, event.detail.value, true);
  };

  // Close drawer after menu item is selected if drawerPanel is narrow
  app.onDataRouteClick = function() {
    var drawerPanel = document.querySelector('#paperDrawerPanel');
    if (drawerPanel.narrow) {
      drawerPanel.closeDrawer();
    }
  };

  app.onAPILoaded = function() {
    if (app.$.ticktockApi.api && app.$.oauth2Api.api) {
      signin(true);
    }
  };

  // Network

  var pushEventState = function(eventId, calendarId, hidden, starred, signinMode) {
    app.$.ticktockApi.api.events.patch({
        calendarId: encodeURIComponent(calendarId),
        eventId: eventId,
        starred: starred,
        hidden: hidden
      }).execute(function(resp) {
        if (!resp || resp.code) {
          if (resp.code === -1) {
            raiseNetworkError(resp);
          } else if (resp.code === 401) {
            if (signinMode) {
              console.warn(resp);
              signin(true, pushEventState(eventId, calendarId, hidden, starred, false));
            } else {
              app.userInfo = SIGNED_OUT_USER_INFO;
              app.$.userBar.addEventListener('tap', app.showSigninPopup);
            }
          } else {
            raiseError(resp);
          }
        }
      });
    app.updateListedEvents(false);
  };

  var pushCalendarState = function(calendarId, hidden, signinMode) {
    app.$.ticktockApi.api.calendars.patch({
        calendarId: encodeURIComponent(calendarId),
        hidden: hidden
      }).execute(function(resp) {
        if (!resp || resp.code) {
          if (resp.code === -1) {
            raiseNetworkError(resp);
          } else if (resp.code === 401) {
            if (signinMode) {
              console.warn(resp);
              signin(true, pushCalendarState(calendarId, hidden, false));
            } else {
              app.userInfo = SIGNED_OUT_USER_INFO;
              app.$.userBar.addEventListener('tap', app.showSigninPopup);
            }
          } else {
            raiseError(resp);
          }
        }
      });
    app.updateCalendars(false);
  };

  var signin = function(mode, callback) {
    app.$.oauth2Api.auth.authorize({
        client_id: CLIENT_ID, // jshint ignore:line
        scope: SCOPES,
        immediate: mode
      }, callback || initialLoad);
    app.userInfo = LOADING_USER_INFO;
    app.$.userBar.removeEventListener('tap', app.showSigninPopup);
  };

  var initialLoad = function() {
    getProfileInfo();
    loadCalendars(true);
  };

  var getProfileInfo = function() {
    app.$.oauth2Api.api.userinfo.v2.me.get({
        fields: 'name,picture'
      }).execute(function(resp) {
        if (!resp || resp.code) {
          if (resp.code === -1) {
            raiseNetworkError(resp);
          } else if (resp.code === 401) {
            app.userInfo = SIGNED_OUT_USER_INFO;
            app.$.userBar.addEventListener('tap', app.showSigninPopup);
          } else {
            raiseError(resp);
          }
        } else {
          resp.loading = false;
          resp.signedOut = false;
          app.userInfo = resp;
        }
      });
  };

  var loadCalendars = function(silentAuthError) {
    app.calendarsLoaded = false;
    app.eventsLoaded = false;
    app.$.ticktockApi.api.calendars.list({
        hidden: null
      }).execute(function(resp) {
        if (!resp || resp.code) {
          resp = resp || {};
          if (resp.code === -1) {
            raiseNetworkError(resp);
          } else if (resp.code === 401 && silentAuthError) {
            console.warn(resp);
          } else {
            raiseError(resp);
          }
        } else {
          var calendars = resp.items || [];
          calendars.forEach(function(c) {
            c.events = [];
            c.error = false;
          });
          app.calendars = calendars;
          app.calendarsLoaded = true;
          app.updateCalendars(false);
          loadEvents(calendars, true);
        }
      });
  };

  var loadEvents = function(calendars, signinMode) {
    app.eventsLoaded = false;

    var remainingCalendarCount = calendars.length;
    var addEvents = function(calendar) {
      return function(resp) {
        if (!resp || resp.code) {
          calendar.error = true;
          if (resp.code === -1) {
            raiseNetworkError(resp);
          } else if (resp.code === 401) {
            if (signinMode) {
              console.warn(resp);
              signin(true, loadEvents([calendar], false));
            } else {
              app.userInfo = SIGNED_OUT_USER_INFO;
              app.$.userBar.addEventListener('tap', app.showSigninPopup);
            }
          } else {
            raiseError(resp);
          }
        } else {
          calendar.error = false;
          if (resp.items) {
            resp.items.forEach(function(calendarEvent) {
              calendarEvent.color = calendar.color;
              calendarEvent.opened = false;
            });
            resp.items[0].opened = true;
            calendar.events = resp.items;
          }
        }
        if (!--remainingCalendarCount) {
          app.eventsLoaded = true;
          app.updateCalendars(true);
          updateDurations();
        }
      };
    };

    var timeZone;
    try {
      timeZone =  Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch (err) {
      timeZone = null;
    }
    calendars.forEach(function(c) {
      c.events = [];
      app.$.ticktockApi.api.events.list({
          calendarId: encodeURIComponent(c.calendarId),
          hidden: null,
          maxResults: 10,
          timeZone: timeZone
        }).execute(addEvents(c));
    });
  };

})(document);
