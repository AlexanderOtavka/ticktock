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

  // var CLIENT_ID = '208366307202-00824keo9p663g1uhkd8misc52e1c5pa.apps.googleusercontent.com';
  // var SCOPES = [
  //   'https://www.googleapis.com/auth/userinfo.email',
  //   'https://www.googleapis.com/auth/plus.me',
  //   'https://www.googleapis.com/auth/calendar.readonly'
  // ];

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
    app.updateListedEvents();
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

  var openOnlyOne = function(events) {
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
  };

  app.updateListedEvents = function() {
    var events = [];
    if (!app.selectedCalendar) {
      for (var i = 0; i < app.calendars.length; i++) {
        events = events.concat(app.calendars[i].events);
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
    openOnlyOne(events);
    events = sortedEvents(events);
    runWithoutAnimation(function() {
      app.listedEvents = events;
    });
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
      app.updateListedEvents();
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
    app.updateListedEvents();
  };

  app.eventHiddenToggled = function() {
    // TODO: send api query
    app.updateListedEvents();
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

  app.toggleHiddenCalendars = function() {
    setTimeout(function() {
      app.showHiddenCalendars = !app.showHiddenCalendars;
    }, 20);
  };

  app.updateCalendars = function() {
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

  var signin = function(mode) {
    // app.$.ticktockApi.auth.authorize(
    //   {client_id: CLIENT_ID, scope: SCOPES, immediate: mode}, // jshint ignore:line
    //   loadCalendars);
    console.log('signin mode = ' + mode);
    app.$.userBar.removeEventListener('tap', app.showSigninPopup);
    (function() {
      getProfileInfo(mode);
      loadCalendars();
    })();
  };

  var getProfileInfo = function(mode) {
    var EXAMPLE_PROFILE_INFO = {
      'id': '104276020854823045712',
      'email': 'zotavka@gmail.com',
      'verified_email': true,
      'name': 'Zander Otavka',
      'given_name': 'Zander',
      'family_name': 'Otavka',
      'link': 'https://plus.google.com/104276020854823045712',
      'picture': 'https://lh4.googleusercontent.com/-CmWsvY70cjE/AAAAAAAAAAI/AAAAAAAADio/jahTG8VV1ek/photo.jpg',
      'locale': 'en'
    };
    EXAMPLE_PROFILE_INFO.loading = false;
    mode = false;
    if (mode) {
      app.userInfo = SIGNED_OUT_USER_INFO;
    } else {
      app.userInfo = EXAMPLE_PROFILE_INFO;
    }

    if (app.userInfo.signedOut) {
      app.$.userBar.addEventListener('tap', app.showSigninPopup);
    }
  };

  var loadCalendars = function() {
    var EXAMPLE_CALENDARS = [{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','color':'#a47ae2','hidden':false,'name':'TickTock Test'},{'calendarId':'zotavka@gmail.com','color':'#34a864','hidden':true,'name':'Zander'}];
    if (!app.userInfo.signedOut) {
      app.calendars = EXAMPLE_CALENDARS;
    }
    app.updateCalendars();
    loadAllEvents();
    // app.$.ticktockApi.api.calendars.list({
    //   }).execute(function(resp) {
    //     console.log(resp);
    //     if (resp.code && resp.code === 401) {
    //       console.log('UNAUTHORIZED');
    //     } else if (resp.code) {
    //       console.log('ERROR');
    //     } else {
    //       app.calendars = resp.items || [];
    //       loadAllEvents();
    //     }
    //   });
  };

  var loadAllEvents = function() {
    var EXAMPLE_EVENTS = [{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-01-19T00:01:00-08:00','eventId':'f2inmdp5vsplf0i6o7331s2etk','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=ZjJpbm1kcDV2c3BsZjBpNm83MzMxczJldGsgb241MjkydG5xZ2NrYm5mZXR2NGU3dHBqbm9AZw&ctz=America/Los_Angeles','name':'Starred all day','starred':true,'startDate':'2016-01-18T00:01:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-01-19T00:00:00-08:00','eventId':'8une1glii8bbbuntveru3ohcv4','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=OHVuZTFnbGlpOGJiYnVudHZlcnUzb2hjdjQgb241MjkydG5xZ2NrYm5mZXR2NGU3dHBqbm9AZw&ctz=America/Los_Angeles','name':'Unstarred','starred':false,'startDate':'2016-01-18T00:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-01-18T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160118T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…hUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-01-18T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-01-25T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160125T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…VUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-01-25T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-02-01T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160201T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…FUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-02-01T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-02-08T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160208T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…hUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-02-08T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-02-15T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160215T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…VUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-02-15T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-02-22T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160222T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…JUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-02-22T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-02-29T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160229T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…lUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-02-29T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-03-07T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160307T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…dUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-03-07T10:00:00-08:00','color':'#a47ae2'}];
    for (var i in EXAMPLE_EVENTS) {
      EXAMPLE_EVENTS[i].opened = false;
    }
    EXAMPLE_EVENTS[0].opened = true;
    if (!app.userInfo.signedOut) {
      app.calendars[0].events = EXAMPLE_EVENTS;
      app.calendars[1].events = [];
    }

    app.updateListedEvents();
    updateDurations();

    // app.allEvents = [];
    // var addEvents = function(calendar) {
    //   return function(resp) {
    //     if (resp.code) {
    //       console.log('ERROR');
    //     } else {
    //       var events = resp.items || [];
    //       for (var i = 0; i < events.length; i++) {
    //         events[i].color = calendar.color;
    //       }
    //       calendar.events = events;
    //       app.allEvents = app.allEvents.concat(events);
    //
    //       console.log(app.allEvents);
    //     }
    //   };
    // };
    //
    // for (var i = 0; i < app.calendars.length; i++) {
    //   app.$.ticktockApi.api.events.list({
    //       calendarId: app.calendars[i].calendarId,
    //       hidden: false,
    //       maxResults: 10
    //     }).execute(addEvents(app.calendars[i]));
    // }
  };

})(document);
