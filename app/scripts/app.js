/*
Copyright (c) 2015 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at
http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at
http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at
http://polymer.github.io/PATENTS.txt
*/

(function (app) {
'use strict';

// Imports are loaded and elements have been registered.
window.addEventListener('WebComponentsReady', function () {
  setInterval(function () {
    updateDurations(app.selectedCalendar);
  }, 1000);

  app.$.apiManager.signIn(true);
});

//
// Constants
//

var CalendarStatus = {
  GOOD: 0,
  EMPTY: 1,
  LOADING: 2,
  ERRORED: 3,
  SIGNED_OUT: 4,
};

//
// Data
//

// Settings.
app.showHiddenCalendars = false;
app.showHiddenEvents = false;

//
// Getters
//

app.getSignedOutClass = function (signedOut) {
  return signedOut ? 'signed-out' : '';
};

app.getHiddenEventsToggleText = function (showHiddenEvents) {
  return showHiddenEvents ? 'Hide Hidden Events' : 'Show Hidden Events';
};

app.getHiddenCalendarToggleText = function (showHiddenCalendars) {
  return showHiddenCalendars ? 'Hide Hidden Calendars' :
                               'Show Hidden Calendars';
};

app.getHideHiddenCalendarToggle = function (hasHiddenCalendars,
                                            selectedHidden) {
  return selectedHidden || !hasHiddenCalendars;
};

app.getUrlEncoded = function (string) {
  return encodeURIComponent(string);
};

app.getUrlDecoded = function (string) {
  return decodeURIComponent(string);
};

app.getCalendarFilter = function (showHiddenCalendars) {
  if (!showHiddenCalendars) {
    return function (calendar) {
      return !calendar.hidden && !calendar.calendarLoading &&
             !calendar.calendarErrored;
    };
  } else {
    return null;
  }
};

app.getCalendarErrored = function (signedOut, calendarErrored, eventsErrored) {
  return getCalendarStatus(signedOut, calendarErrored, eventsErrored) ===
         CalendarStatus.ERRORED;
};

app.getCalendarLoading = function (signedOut, calendarErrored, eventsErrored,
                                   eventsLoading, nextPageToken) {
  return getCalendarStatus(signedOut, calendarErrored, eventsErrored,
                           eventsLoading, nextPageToken) ===
         CalendarStatus.LOADING;
};

app.getCalendarEmpty = function (signedOut, calendarErrored, eventsErrored,
                                 eventsLoading, nextPageToken, events) {
  return getCalendarStatus(signedOut, calendarErrored, eventsErrored,
                           eventsLoading, nextPageToken, events) ===
         CalendarStatus.EMPTY;
};

//
// Actions
//

app.showInstalledToast = function () {
  // Check to make sure caching is actually enabled—it won't be in the dev
  // environment.
  // if (!Polymer.dom(document).querySelector('platinum-sw-cache').disabled) {
  //   app.$.cachingComplete.show();
  // }
};

app.showErrorToast = function () {
  app.$.error.show();
};

app.showNetworkErrorToast = function () {
  app.$.networkError.show();
};

/**
 * Close drawer after menu item is selected if drawerPanel is narrow.
 */
app.closeDrawer = function () {
  var drawerPanel = app.$.paperDrawerPanel;
  if (drawerPanel.narrow) {
    drawerPanel.closeDrawer();
  }
};

/**
 * Scroll page to top and expand header.
 */
app.scrollPageToTop = function () {
  app.$.mainArea.$.mainContainer.scrollTop = 0;
};

app.selectCalendar = function (calendarId) {
  var calendar;
  if (calendarId) {
    calendar = app.$.apiManager.getCalendarById(calendarId);
  } else {
    calendar = app.selectedCalendar;
  }

  if (calendar.hidden) {
    app.showHiddenCalendars = true;
  }

  app.$.eventList.openedIndex = 0;

  console.log(calendar);
  app.$$scal = calendar;

  console.log(app.calendars);

  app.$.calendarSelector.select(calendar);
};

app.toggleShowHiddenEvents = function () {
  app.showHiddenEvents = !app.showHiddenEvents;
};

app.toggleShowHiddenCalendars = function () {
  setTimeout(function () {
    app.showHiddenCalendars = !app.showHiddenCalendars;
  }, 20);
};

app.showSigninPopup = function () {
  if (app.userInfo.signedOut) {
    app.$.apiManager.signIn(false);
  }
};

app.refreshThisCalendar = function () {
  app.$.apiManager.reloadEvents(app.selectedCalendar);
  app.$.eventList.openedIndex = 0;
};

//
// Event handlers
//

app.onCalendarsLoaded = function () {
  app.selectCalendar();
};

app.onEventChanged = function (event) {
  app.$.apiManager.patchEvent(event.detail);
};

app.onCalendarHiddenToggled = function (event) {
  app.$.apiManager.patchCalendar({
    calendarId: event.target.calendarId,
    hidden: event.detail.value,
  });
};

//
// Utility Functions
//

function getCalendarStatus(signedOut, calendarErrored, eventsErrored,
                           eventsLoading, nextPageToken, events) {
  if (signedOut) {
    return CalendarStatus.SIGNED_OUT;
  }

  if (calendarErrored || eventsErrored) {
    return CalendarStatus.ERRORED;
  }

  if (eventsLoading || nextPageToken) {
    return CalendarStatus.LOADING;
  }

  if (!Boolean((events || []).length)) {
    return CalendarStatus.EMPTY;
  }

  return CalendarStatus.GOOD;
}

function updateDurations(calendar) {
  // TODO: Optimize this.
  var now = Date.now();

  calendar.events.forEach(function (calendarEvent, i) {
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
        app.$.apiManager.deleteEventById(calendarEvent.calendarId,
                                         calendarEvent.eventId);
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
}

})(app);
