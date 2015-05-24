angular.module('stevetags')

.directive('stFiletypes', ['$http', 'CONST', ($http, CONST) ->
  restrict: 'A'
  replace: true
  templateUrl: "#{ CONST.URL_PREFIX }/app/filetypes.html"
  scope:
    userFiletypes: '=stFiletypes'
    onChange: '&'
  link: (scope, element, attrs) ->
    scope.filetypes = {}
    unwatch = scope.$watch 'userFiletypes', ->
      scope.allFiletypes = not scope.userFiletypes? or scope.userFiletypes.length == 0
      for type in CONST.USER._mime_types
        scope.filetypes[type] = type in scope.userFiletypes
      unwatch()
    , true

    scope.toggleAllFiletypes = ->
      scope.allFiletypes = not scope.allFiletypes
      if not scope.allFiletypes
        scope.filetypes[k] = true for k of scope.filetypes
      return

    rebuildFiletypes = ->
      scope.userFiletypes.length = 0
      if not scope.allFiletypes
        scope.userFiletypes.push key for key, v of scope.filetypes when v
      return

    scope.$watch 'allFiletypes', (newVal, oldVal) ->
      if newVal != oldVal
        rebuildFiletypes()

    scope.$watch 'filetypes', (newVal, oldVal) ->
      if not angular.equals(newVal, oldVal)
        rebuildFiletypes()
    , true
])
