angular.module('stevetags')

.directive('qbNavbar', ['CONST', (CONST) ->
  templateUrl: "#{ CONST.URL_PREFIX }/app/navbar/navbar.html"
  restrict: 'A'
  replace: true
  controller: 'NavCtrl'
])

.controller('NavCtrl',
['$scope', '$timeout', '$http', 'CONST',
($scope, $timeout, $http, CONST) ->
  $scope.showDropdown = false
  $scope.toggleDropdown = ->
    $scope.showDropdown = !$scope.showDropdown
])
