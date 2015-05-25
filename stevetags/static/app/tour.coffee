angular.module('stevetags')

.config(['$routeProvider', 'CONST', ($routeProvider, CONST) ->
  $routeProvider.when('/tour/:step', {
    controller: 'TourCtrl'
    templateUrl: "#{ CONST.URL_PREFIX }/app/tour.html"
  })
])

.controller('TourCtrl',
['$scope', '$http', '$routeParams', '$location', 'CONST',
($scope, $http, $routeParams, $location, CONST) ->
  $scope.step = Number($routeParams.step)
  $scope.root =
    path: '/'

  $scope.nextPage = ->
    if CONST.USER.settings.roots.length == 0
      alert("You must select at least one folder")
      return
    CONST.USER.settings.tour_step++
    $location.path("/tour/#{ $scope.step + 1 }")
    if $scope.step > 1
      CONST.USER.settings.tour_complete = true
      $http.post('/user/settings', settings: CONST.USER.settings).then ->
        $location.path("/")
])
