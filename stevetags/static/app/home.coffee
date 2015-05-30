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

.directive('stSearch', ['$http', 'CONST', ($http, CONST) ->
  restrict: 'A'
  replace: true
  templateUrl: "#{ CONST.URL_PREFIX }/app/search.html"
  scope: {}
  link: (scope, element, attrs) ->
    scope.results = []
    scope.everSearched = false
    scope.search = (searchtext) ->
      params = query: searchtext ? ''
      scope.searching = true
      scope.everSearched = true
      $http.get('/files/search', params: params).then (response) ->
        scope.searching = false
        scope.results = response.data.files
      , ->
        scope.searching = false

])
