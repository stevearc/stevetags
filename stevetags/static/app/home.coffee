angular.module('stevetags')

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/', {
    controller: 'HomeCtrl'
    templateUrl: "#{ CONST.URL_PREFIX }/app/home.html"
  })
])

.controller('HomeCtrl', ['$scope', '$http', ($scope, $http) ->

])


.directive('stRecent', ['$http', 'CONST', ($http, CONST) ->
  restrict: 'A'
  replace: true
  templateUrl: "#{ CONST.URL_PREFIX }/app/recent.html"
  scope: {}
  link: (scope, element, attrs) ->
    scope.refreshing = false
    scope.files = null
    scope.hadFilesEver = false

    fetchFiles = ->
      $http.get('/files').then (response) ->
        scope.files = response.data.files
        scope.hadFilesEver = scope.files.length > 0
      return
    fetchFiles()

    scope.refresh = ->
      scope.refreshing = true
      $http.get('/files/refresh').then ->
        fetchFiles()
      .then ->
        scope.refreshing = false
      , ->
        scope.refreshing = false
      return

    scope.maybeFetchMore = ->
      if scope.files? and scope.files.length < 10
        $http.get('/files').then (response) ->
          allPaths = (f.path for f in scope.files)
          for file in response.data.files when file.path not in allPaths
            scope.files.push(file)
          return
      return

    scope.earnedCookie = ->
      return scope.files? and scope.files.length == 0 and scope.hadFilesEver
])

.directive('stSearch', ['$http', '$timeout', 'CONST', ($http, $timeout, CONST) ->
  restrict: 'A'
  replace: true
  templateUrl: "#{ CONST.URL_PREFIX }/app/search.html"
  scope: {}
  link: (scope, element, attrs) ->
    scope.results = []
    scope.everSearched = false

    timer = null
    scope.maybeSearch = (e, searchtext) ->
      # Ignore keyup for enter
      return if e.keyCode == 13
      $timeout.cancel(timer) if timer?
      timer = $timeout ->
        timer = null
        scope.search searchtext
      , 500

    scope.search = (searchtext) ->
      $timeout.cancel(timer) if timer?
      timer = null
      params = query: searchtext ? ''
      scope.searching = true
      scope.everSearched = true
      $http.get('/files/search', params: params).then (response) ->
        scope.searching = false
        scope.results = response.data.files
      , ->
        scope.searching = false

])
