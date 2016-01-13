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
  app.dataLoaded = false;

  app.calendars = [];
  app.selectedCalendar = '';

  var getCalendarById = function(calendarId) {
    for (var i = 0; i < app.calendars.length; i++) {
      if (app.calendars[i].calendarId === calendarId) {
        return app.calendars[i];
      }
    }
    return null;
  };

  app.getSelectedCalendarName = function(selectedCalendar, dataLoaded) {
    if (!dataLoaded) {
      return '';
    }

    var ALL_CALENDARS = 'All Calendars';

    if (!selectedCalendar) {
      return ALL_CALENDARS;
    } else {
      var calendar = getCalendarById(selectedCalendar);
      return calendar ? calendar.name : ALL_CALENDARS;
    }
  };

  app.getEvents = function(selectedCalendar, dataLoaded) {
    if (!dataLoaded) {
      return [];
    }

    if (!selectedCalendar) {
      var events = [];
      for (var i = 0; i < app.calendars.length; i++) {
        events = events.concat(app.calendars[i].events);
      }
      return events;
    } else {
      var calendar = getCalendarById(selectedCalendar);
      return calendar ? calendar.events : [];
    }
  };

  app.displayInstalledToast = function() {
    // Check to make sure caching is actually enabled—it won't be in the dev environment.
    if (!document.querySelector('platinum-sw-cache').disabled) {
      document.querySelector('#caching-complete').show();
    }
  };

  // Listen for template bound event to know when bindings
  // have resolved and content has been stamped to the page
  app.addEventListener('dom-change', function() {
    console.log('Our app is ready to rock!');
  });

  // See https://github.com/Polymer/polymer/issues/1381
  window.addEventListener('WebComponentsReady', function() {
    // imports are loaded and elements have been registered
  });

  // Main area's paper-scroll-header-panel custom condensing transformation of
  // the appName in the middle-container and the bottom title in the bottom-container.
  // The appName is moved to top and shrunk on condensing. The bottom sub title
  // is shrunk to nothing on condensing.
  addEventListener('paper-header-transform', function(e) {
    var appName = document.querySelector('#mainToolbar .app-name');
    var middleContainer = document.querySelector('#mainToolbar .middle-container');
    var bottomContainer = document.querySelector('#mainToolbar .bottom-container');
    var detail = e.detail;
    var heightDiff = detail.height - detail.condensedHeight;
    var yRatio = Math.min(1, detail.y / heightDiff);
    var maxMiddleScale = 0.50;  // appName max size when condensed. The smaller the number the smaller the condensed size.
    var scaleMiddle = Math.max(maxMiddleScale, (heightDiff - detail.y) / (heightDiff / (1-maxMiddleScale))  + maxMiddleScale);
    var scaleBottom = 1 - yRatio;

    // Move/translate middleContainer
    Polymer.Base.transform('translate3d(0,' + yRatio * 100 + '%,0)', middleContainer);

    // Scale bottomContainer and bottom sub title to nothing and back
    Polymer.Base.transform('scale(' + scaleBottom + ') translateZ(0)', bottomContainer);

    // Scale middleContainer appName
    Polymer.Base.transform('scale(' + scaleMiddle + ') translateZ(0)', appName);
  });

  // Close drawer after menu item is selected if drawerPanel is narrow
  app.onDataRouteClick = function() {
    var drawerPanel = document.querySelector('#paperDrawerPanel');
    if (drawerPanel.narrow) {
      drawerPanel.closeDrawer();
    }
  };

  // Scroll page to top and expand header
  app.scrollPageToTop = function() {
    document.getElementById('mainContainer').scrollTop = 0;
  };

  app.onTicktockdataLoaded = function() {
    signin(true);
  };

  app.showSigninPopup = function() {
    signin(false);
  };

  var signin = function(mode) {
    // app.$.ticktockApi.auth.authorize(
    //   {client_id: CLIENT_ID, scope: SCOPES, immediate: mode}, // jshint ignore:line
    //   loadCalendars);
    console.log('signin mode = ' + mode);
    loadCalendars();
    app.$.signinButton.setAttribute('hidden', '');
  };

  var loadCalendars = function() {
    var EXAMPLE_CALENDARS = [{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','color':'#a47ae2','hidden':false,'name':'TickTock Test'}];
    app.calendars = EXAMPLE_CALENDARS;
    loadAllEvents();
    // app.$.ticktockApi.api.calendars.list({
    //     hidden: false
    //   }).execute(function(resp) {
    //     console.log(resp);
    //     if (resp.code && resp.code === 401) {
    //       app.$.signinButton.removeAttribute('hidden');
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
    var EXAMPLE_EVENTS = [{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-01-14T00:00:00-08:00','eventId':'f2inmdp5vsplf0i6o7331s2etk','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=ZjJpbm1kcDV2c3BsZjBpNm83MzMxczJldGsgb241MjkydG5xZ2NrYm5mZXR2NGU3dHBqbm9AZw&ctz=America/Los_Angeles','name':'Starred all day','starred':true,'startDate':'2016-01-13T00:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-01-14T00:00:00-08:00','eventId':'8une1glii8bbbuntveru3ohcv4','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=OHVuZTFnbGlpOGJiYnVudHZlcnUzb2hjdjQgb241MjkydG5xZ2NrYm5mZXR2NGU3dHBqbm9AZw&ctz=America/Los_Angeles','name':'Unstarred','starred':false,'startDate':'2016-01-13T00:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-01-18T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160118T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…hUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-01-18T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-01-25T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160125T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…VUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-01-25T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-02-01T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160201T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…FUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-02-01T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-02-08T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160208T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…hUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-02-08T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-02-15T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160215T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…VUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-02-15T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-02-22T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160222T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…JUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-02-22T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-02-29T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160229T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…lUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-02-29T10:00:00-08:00','color':'#a47ae2'},{'calendarId':'on5292tnqgckbnfetv4e7tpjno@group.calendar.google.com','endDate':'2016-03-07T11:00:00-08:00','eventId':'uf6qv5a5365cj3k0ue8jndltbs_20160307T180000Z','hidden':false,'link':'https://calendar.google.com/calendar/event?eid=dWY2cXY1YTUzNjVjajNrMHVlOGpu…dUMTgwMDAwWiBvbjUyOTJ0bnFnY2tibmZldHY0ZTd0cGpub0Bn&ctz=America/Los_Angeles','name':'Repeated','recurrenceId':'uf6qv5a5365cj3k0ue8jndltbs','starred':false,'startDate':'2016-03-07T10:00:00-08:00','color':'#a47ae2'}];
    for (var i in EXAMPLE_EVENTS) {
      EXAMPLE_EVENTS[i].opened = false;
    }
    EXAMPLE_EVENTS[0].opened = true;
    app.calendars[0].events = EXAMPLE_EVENTS;
    app.allEvents = EXAMPLE_EVENTS;

    app.dataLoaded = true;

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
