// Copyright (c) 2016 Drake Developers Club All Rights Reserved.

/**
 * Define a Class function for easy creation of classes.
 *
 * Usage:
 * var MyClass = Class({
 *   // Defines the constructor.  Optional, defaults to calling the superclass
 *   // constructor without arguments.
 *   constructor: function (foo) {
 *     this.foo = foo;
 *   },
 *
 *   // Members and methods here are static.
 *   static: {
 *     baz: 5,
 *
 *     increment: function () {
 *       // Methods are bound such that `this` refers to the class itself,
 *       // not an instance.
 *       return ++this.baz;
 *     },
 *   },
 *
 *   // Instance method
 *   print: function () {
 *     console.log(this.foo);
 *   },
 * });
 *
 * var MySubclass = Class({
 *   // Extend a superclass.  Optional, defaults to Object.
 *   extends: MyClass,
 *
 *   constructor: function () {
 *     // Call the superclass constructor.  MySubclass.super is equivalent to
 *     // MyClass.prototype.
 *     MySubclass.super.constructor.call(this, 'Subclass foo...');
 *   },
 *
 *   // Override a function
 *   print: function () {
 *     // Call a superclass method
 *     MySubclass.super.print.call(this);
 *     console.log('Printed from subclass!');
 *   },
 * });
 */
(function () {
'use strict';

var Class = function (config) {
  config = config || {};

  if (!(config instanceof Object)) {
    throw new TypeError('Invalid argument to Class.');
  }

  if (config.hasOwnProperty('constructor') &&
      !(config.constructor instanceof Function)) {
    throw new TypeError('Class constructor must be a function.');
  }

  if (config.hasOwnProperty('extends') &&
      !(config.extends instanceof Function)) {
    throw new TypeError('Class must extend a function.');
  }

  if (config.hasOwnProperty('static') && !(config.static instanceof Object)) {
    throw new TypeError('Invalid static property for Class.');
  }

  var newClass;
  if (config.hasOwnProperty('constructor')) {
    newClass = config.constructor;
  } else {
    newClass = function DefaultConstructor() {
      newClass.super.constructor.call(this);
    };
  }

  var keys = Object.keys(config);

  var extendsIndex = keys.indexOf('extends');
  var extendClass;
  if (extendsIndex !== -1) {
    extendClass = config.extends;
    keys.splice(extendsIndex, 1);
  } else {
    extendClass = Object;
  }

  newClass.prototype = Object.create(extendClass.prototype);
  newClass.super = extendClass.prototype;

  var staticIndex = keys.indexOf('static');
  if (staticIndex !== -1) {
    Object.keys(config.static).forEach(function (key) {
      var value = config.static[key];
      if (value instanceof Function) {
        newClass[key] = value.bind(newClass);
      } else {
        newClass[key] = value;
      }
    });

    keys.splice(staticIndex, 1);
  }

  keys.forEach(function (key) {
    newClass.prototype[key] = config[key];
  });

  return newClass;
};

window.Class = Class;

})();
